from .guide_utils import add_ltx_guide, make_noise_mask


class LTXFlowTailGuide:
    CATEGORY = "LTXFlow/LTX Guides"
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT", "INT")
    RETURN_NAMES = ("positive", "negative", "latent", "overlap_frames")
    FUNCTION = "apply_tail_guides"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "vae": ("VAE",),
                "latent": ("LATENT",),
                "tail_frames": ("IMAGE",),
                "guide_mode": (["last_only", "first_mid_last"], {"default": "first_mid_last"}),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "frame_spacing": (
                    "INT",
                    {
                        "default": 8,
                        "min": 1,
                        "max": 64,
                        "step": 1,
                        "tooltip": "Pixel-frame spacing for tail keyframes. LTX commonly aligns well on 8-frame intervals.",
                    },
                ),
            }
        }

    def apply_tail_guides(self, positive, negative, vae, latent, tail_frames, guide_mode, strength, frame_spacing):
        frame_count = int(tail_frames.shape[0])
        if frame_count == 0:
            raise ValueError("LTXFlowTailGuide received an empty tail frame batch.")

        latent_image = latent["samples"].clone()
        noise_mask = make_noise_mask(latent, latent_image)

        if guide_mode == "last_only" or frame_count == 1:
            selections = [(frame_count - 1, 0)]
            overlap_frames = 1
        else:
            mid = frame_count // 2
            selections = [(0, 0), (mid, frame_spacing), (frame_count - 1, frame_spacing * 2)]
            overlap_frames = min(frame_count, frame_spacing * 2 + 1)

        for source_index, target_frame in selections:
            image = tail_frames[source_index : source_index + 1]
            positive, negative, latent_image, noise_mask = add_ltx_guide(
                positive, negative, vae, latent_image, noise_mask, image, target_frame, strength
            )

        return (positive, negative, {"samples": latent_image, "noise_mask": noise_mask}, int(overlap_frames))
