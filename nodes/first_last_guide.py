from .guide_utils import add_ltx_guide, make_noise_mask


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
        latent_image = latent["samples"].clone()
        noise_mask = make_noise_mask(latent, latent_image)

        positive, negative, latent_image, noise_mask = add_ltx_guide(
            positive, negative, vae, latent_image, noise_mask, first_frame[:1], 0, first_strength
        )
        positive, negative, latent_image, noise_mask = add_ltx_guide(
            positive, negative, vae, latent_image, noise_mask, last_frame[:1], last_frame_index, last_strength
        )

        return (positive, negative, {"samples": latent_image, "noise_mask": noise_mask})
