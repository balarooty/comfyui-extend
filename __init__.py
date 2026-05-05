from .nodes.extract_frame import LTXFlowExtractFrame
from .nodes.extract_tail import LTXFlowExtractTail
from .nodes.first_last_guide import LTXFlowFirstLastGuide
from .nodes.scene_builder import LTXFlowSceneBuilder
from .nodes.tail_guide import LTXFlowTailGuide
from .nodes.trim_frames import LTXFlowTrimFrames


NODE_CLASS_MAPPINGS = {
    "LTXFlowExtractFrame": LTXFlowExtractFrame,
    "LTXFlowExtractTail": LTXFlowExtractTail,
    "LTXFlowFirstLastGuide": LTXFlowFirstLastGuide,
    "LTXFlowSceneBuilder": LTXFlowSceneBuilder,
    "LTXFlowTailGuide": LTXFlowTailGuide,
    "LTXFlowTrimFrames": LTXFlowTrimFrames,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXFlowExtractFrame": "LTX Flow - Extract Frame",
    "LTXFlowExtractTail": "LTX Flow - Extract Tail",
    "LTXFlowFirstLastGuide": "LTX Flow - First/Last Guide",
    "LTXFlowSceneBuilder": "LTX Flow - Scene Builder",
    "LTXFlowTailGuide": "LTX Flow - Tail Guide",
    "LTXFlowTrimFrames": "LTX Flow - Trim Frames",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
