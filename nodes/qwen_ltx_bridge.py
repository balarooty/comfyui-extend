class LTXFlowQwenEditBridge:
    CATEGORY = "LTXFlow/Qwen"
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("first_frame", "last_frame", "keyframe_batch")
    FUNCTION = "bridge"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source_image": ("IMAGE",),
                "qwen_edited_image": ("IMAGE",),
                "first_frame_source": (["source_image", "qwen_edited_image"], {"default": "source_image"}),
                "resize_to": (["source_image", "qwen_edited_image"], {"default": "source_image"}),
                "multiple_of": ("INT", {"default": 32, "min": 0, "max": 512, "step": 1}),
            }
        }

    def _resize_image(self, image, width, height):
        import comfy.utils

        if image.shape[1] == height and image.shape[2] == width:
            return image

        resized = comfy.utils.common_upscale(
            image.movedim(-1, 1),
            width,
            height,
            "lanczos",
            "center",
        )
        return resized.movedim(1, -1)

    def bridge(self, source_image, qwen_edited_image, first_frame_source, resize_to, multiple_of):
        import torch

        source = source_image[:1, :, :, :3]
        edited = qwen_edited_image[:1, :, :, :3]

        target = source if resize_to == "source_image" else edited
        target_height = int(target.shape[1])
        target_width = int(target.shape[2])

        if multiple_of and multiple_of > 1:
            target_width = max(multiple_of, target_width - (target_width % multiple_of))
            target_height = max(multiple_of, target_height - (target_height % multiple_of))

        source = self._resize_image(source, target_width, target_height)
        edited = self._resize_image(edited, target_width, target_height)

        first = source if first_frame_source == "source_image" else edited
        last = edited
        keyframe_batch = torch.cat((first, last), dim=0)
        return (first, last, keyframe_batch)
