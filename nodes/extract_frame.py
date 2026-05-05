class LTXFlowExtractFrame:
    CATEGORY = "LTXFlow/Frame Tools"
    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("frame", "resolved_index")
    FUNCTION = "extract"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_frames": ("IMAGE",),
                "index": (
                    "INT",
                    {
                        "default": -1,
                        "min": -100000,
                        "max": 100000,
                        "step": 1,
                        "tooltip": "-1 returns the last frame, 0 returns the first frame.",
                    },
                ),
            }
        }

    def extract(self, video_frames, index):
        frame_count = video_frames.shape[0]
        if frame_count == 0:
            raise ValueError("LTXFlowExtractFrame received an empty frame batch.")

        resolved_index = index % frame_count
        frame = video_frames[resolved_index : resolved_index + 1]
        return (frame, int(resolved_index))
