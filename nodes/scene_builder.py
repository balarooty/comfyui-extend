class LTXFlowSceneBuilder:
    CATEGORY = "LTXFlow/Scene Tools"
    RETURN_TYPES = ("IMAGE", "INT", "FLOAT")
    RETURN_NAMES = ("merged_frames", "total_frames", "duration_seconds")
    FUNCTION = "build"

    @classmethod
    def INPUT_TYPES(cls):
        optional_clips = {f"clip_{index}": ("IMAGE",) for index in range(2, 7)}
        return {
            "required": {
                "clip_1": ("IMAGE",),
                "deduplicate_joins": ("BOOLEAN", {"default": True}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 240, "step": 1}),
            },
            "optional": optional_clips,
        }

    def build(self, clip_1, deduplicate_joins, fps, **optional_clips):
        import torch

        clips = [clip_1]
        for index in range(2, 7):
            clip = optional_clips.get(f"clip_{index}")
            if clip is not None:
                clips.append(clip)

        merged = clips[0]
        for clip in clips[1:]:
            if clip.shape[1:] != merged.shape[1:]:
                raise ValueError(
                    "All clips must have the same height, width, and channel count. "
                    f"Expected {tuple(merged.shape[1:])}, got {tuple(clip.shape[1:])}."
                )

            next_clip = clip[1:] if deduplicate_joins and clip.shape[0] > 1 else clip
            merged = torch.cat((merged, next_clip), dim=0)

        total_frames = int(merged.shape[0])
        duration_seconds = round(total_frames / int(fps), 3)
        return (merged, total_frames, duration_seconds)
