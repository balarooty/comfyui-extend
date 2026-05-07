from .guide_utils import add_ltx_guide, make_noise_mask


def _is_av_latent(latent):
    """Check if a latent dict contains a combined audio-video NestedTensor."""
    try:
        import comfy.nested_tensor

        return isinstance(latent.get("samples"), comfy.nested_tensor.NestedTensor)
    except Exception:
        return False


def _separate_av(latent):
    """Split a combined AV latent into (video_latent_dict, audio_latent_dict)."""
    samples = latent["samples"].unbind()
    video_latent = latent.copy()
    video_latent["samples"] = samples[0]
    audio_latent = latent.copy()
    audio_latent["samples"] = samples[1]

    if "noise_mask" in latent and latent["noise_mask"] is not None:
        masks = latent["noise_mask"].unbind()
        video_latent["noise_mask"] = masks[0]
        audio_latent["noise_mask"] = masks[1]
    else:
        video_latent.pop("noise_mask", None)
        audio_latent.pop("noise_mask", None)

    return video_latent, audio_latent


def _combine_av(video_latent, audio_latent):
    """Recombine video and audio latents into a single AV latent dict."""
    import comfy.nested_tensor

    output = {}
    output.update(video_latent)
    output["samples"] = comfy.nested_tensor.NestedTensor(
        (video_latent["samples"], audio_latent["samples"])
    )

    video_mask = video_latent.get("noise_mask")
    audio_mask = audio_latent.get("noise_mask")
    if video_mask is not None or audio_mask is not None:
        import torch

        if video_mask is None:
            video_mask = torch.ones_like(video_latent["samples"])
        if audio_mask is None:
            audio_mask = torch.ones_like(audio_latent["samples"])
        output["noise_mask"] = comfy.nested_tensor.NestedTensor(
            (video_mask, audio_mask)
        )

    return output


class LTXFlowFirstLastGuide:
    CATEGORY = "LTXFlow/LTX Guides"
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("positive", "negative", "latent")
    FUNCTION = "apply_guides"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "vae": ("VAE",),
                "latent": ("LATENT",),
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "first_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "last_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "last_frame_index": (
                    "INT",
                    {
                        "default": -1,
                        "min": -100000,
                        "max": 100000,
                        "step": 1,
                        "tooltip": "-1 means the final frame of the LTX latent.",
                    },
                ),
            }
        }

    def apply_guides(
        self,
        positive,
        negative,
        vae,
        latent,
        first_frame,
        last_frame,
        first_strength,
        last_strength,
        last_frame_index,
    ):
        # If we received a combined AV latent, separate it, apply guides to
        # the video portion only, then recombine before returning.
        is_av = _is_av_latent(latent)
        audio_latent = None
        if is_av:
            video_latent, audio_latent = _separate_av(latent)
        else:
            video_latent = latent

        latent_image = video_latent["samples"].clone()
        noise_mask = make_noise_mask(video_latent, latent_image)

        positive, negative, latent_image, noise_mask = add_ltx_guide(
            positive, negative, vae, latent_image, noise_mask, first_frame[:1], 0, first_strength
        )
        positive, negative, latent_image, noise_mask = add_ltx_guide(
            positive, negative, vae, latent_image, noise_mask, last_frame[:1], last_frame_index, last_strength
        )

        result_video = {"samples": latent_image, "noise_mask": noise_mask}

        if is_av and audio_latent is not None:
            result = _combine_av(result_video, audio_latent)
        else:
            result = result_video

        return (positive, negative, result)
