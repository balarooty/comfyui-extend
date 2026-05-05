class LTXFlowTrimFrames:
    CATEGORY = "LTXFlow/Frame Tools"
    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("trimmed_frames", "remaining_frames")
    FUNCTION = "trim"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_frames": ("IMAGE",),
                "trim_start": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "trim_end": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
            }
        }

    def trim(self, video_frames, trim_start, trim_end):
        frame_count = int(video_frames.shape[0])
        start = min(int(trim_start), frame_count)
        end = frame_count - min(int(trim_end), max(frame_count - start, 0))
        if end <= start:
            raise ValueError(
                f"Trim removes all frames: frame_count={frame_count}, trim_start={trim_start}, trim_end={trim_end}."
            )

        trimmed = video_frames[start:end]
        return (trimmed, int(trimmed.shape[0]))
