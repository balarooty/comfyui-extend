class LTXFlowExtractTail:
    CATEGORY = "LTXFlow/Frame Tools"
    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("tail_frames", "actual_frame_count")
    FUNCTION = "extract_tail"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_frames": ("IMAGE",),
                "tail_length": (
                    "INT",
                    {
                        "default": 17,
                        "min": 1,
                        "max": 257,
                        "step": 8,
                        "tooltip": "Use 9, 17, or 25 for LTX-style continuation segments.",
                    },
                ),
            }
        }

    def extract_tail(self, video_frames, tail_length):
        frame_count = video_frames.shape[0]
        if frame_count == 0:
            raise ValueError("LTXFlowExtractTail received an empty frame batch.")

        actual_count = min(int(tail_length), int(frame_count))
        tail_frames = video_frames[-actual_count:]
        return (tail_frames, actual_count)
