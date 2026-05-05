# ComfyUI-LTXFlow — Custom Node Package Plan

> Replicate Google Flow's video continuation pipeline using LTX 2.3 inside ComfyUI.
> Core idea: every node passes its **last frame** forward as the start frame of the next generation.

---

## Overview

**Package name:** `ComfyUI-LTXFlow`  
**Total nodes:** 5  
**Model:** LTX Video 2.3 (Lightricks) — 22B distilled FP8  
**Inspiration:** Google Flow's Extend, Frames to Video, and SceneBuilder features

### Node Pipeline

```
LTXFlowI2V → LTXFlowExtractFrame → LTXFlowExtend → LTXFlowFirstLastFrame → LTXFlowSceneBuilder
```

---

## What LTX 2.3 Supports (Confirmed)

| Feature | Status | Notes |
|---|---|---|
| Image to Video (I2V) | Official | Start frame → generate 8s clip |
| First + Last Frame (FLF2V) | Community | Via Kijai nodes + LTXVAddGuide |
| First + Mid + Last Frame | Official | 3-keyframe DiT conditioning |
| Text to Video (T2V) | Official | Pure prompt → video |
| Frame extraction | Pure Python | IMAGE tensor slicing via torch |
| Clip concatenation | Pure Python | `torch.cat` along frame dimension |

---

## Dependencies

| Package | Purpose |
|---|---|
| `ComfyUI-LTXVideo` | Official Lightricks nodes (LTXVScheduler, LTXVSampler, etc.) |
| `ComfyUI-LTXTricks` | logtd's guide nodes — LTXVAddGuide, LTXVCropGuides |
| LTX-2.3 FP8 checkpoint | `ltx-video-2b-v0.9.7-distilled-04-25.safetensors` |
| Gemma 3 12B text encoder | Improved prompt understanding for LTX 2.3 |

---

## Folder Structure

```
ComfyUI/
└── custom_nodes/
    └── ComfyUI-LTXFlow/
        ├── __init__.py              # register all nodes
        ├── nodes/
        │   ├── ltx_flow_i2v.py      # LTXFlowI2V
        │   ├── ltx_flow_extract.py  # LTXFlowExtractFrame
        │   ├── ltx_flow_extend.py   # LTXFlowExtend
        │   ├── ltx_flow_flf.py      # LTXFlowFirstLastFrame
        │   └── ltx_flow_scene.py    # LTXFlowSceneBuilder
        ├── utils/
        │   ├── ltx_helpers.py       # sampler wrapper
        │   └── guide_builder.py     # LTXVAddGuide wrapper
        └── requirements.txt
```

---

## Node Registration (`__init__.py`)

```python
from .nodes.ltx_flow_i2v import LTXFlowI2V
from .nodes.ltx_flow_extract import LTXFlowExtractFrame
from .nodes.ltx_flow_extend import LTXFlowExtend
from .nodes.ltx_flow_flf import LTXFlowFirstLastFrame
from .nodes.ltx_flow_scene import LTXFlowSceneBuilder

NODE_CLASS_MAPPINGS = {
    "LTXFlowI2V": LTXFlowI2V,
    "LTXFlowExtractFrame": LTXFlowExtractFrame,
    "LTXFlowExtend": LTXFlowExtend,
    "LTXFlowFirstLastFrame": LTXFlowFirstLastFrame,
    "LTXFlowSceneBuilder": LTXFlowSceneBuilder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXFlowI2V": "LTX Flow - Image to Video",
    "LTXFlowExtractFrame": "LTX Flow - Extract Frame",
    "LTXFlowExtend": "LTX Flow - Extend (Last Frame)",
    "LTXFlowFirstLastFrame": "LTX Flow - First+Last Frame",
    "LTXFlowSceneBuilder": "LTX Flow - Scene Builder",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
```

---

## Node 1 — `LTXFlowI2V`

**Category:** `LTXFlow`  
**Role:** Entry point. Takes a start image and generates the first clip.  
**Google Flow equivalent:** Creating the very first shot in a new project.

### Inputs

| Name | Type | Default | Notes |
|---|---|---|---|
| `start_image` | IMAGE | — | Your opening frame |
| `positive_prompt` | STRING | — | Scene description |
| `negative_prompt` | STRING | — | What to avoid |
| `model` | LTXV_MODEL | — | Loaded LTX 2.3 model |
| `vae` | VAE | — | LTX VAE |
| `width` | INT | 768 | Must be divisible by 32 |
| `height` | INT | 512 | Must be divisible by 32 |
| `num_frames` | INT | 97 | ~4s at 24fps |
| `steps` | INT | 30 | Denoising steps |
| `seed` | INT | — | Reproducibility |

### Outputs

| Name | Type | Notes |
|---|---|---|
| `video_frames` | IMAGE | Full frame batch [N, H, W, C] |
| `last_frame` | IMAGE | Single last frame [1, H, W, C] |
| `metadata` | LTXFLOW_META | Prompt, seed, clip index |

### Code Skeleton

```python
class LTXFlowI2V:
    CATEGORY = "LTXFlow"
    RETURN_TYPES = ("IMAGE", "IMAGE", "LTXFLOW_META")
    RETURN_NAMES = ("video_frames", "last_frame", "metadata")
    FUNCTION = "generate"

    def generate(self, start_image, model, vae,
                 positive_prompt, negative_prompt,
                 width, height, num_frames, steps, seed):
        # Encode start image as LTX guide at frame 0
        latents = self._encode_with_guide(
            model, vae, start_image, width, height, num_frames
        )
        # Run sampler and decode
        frames = self._sample_and_decode(
            latents, model, vae,
            positive_prompt, negative_prompt, steps, seed
        )
        last_frame = frames[-1].unsqueeze(0)  # [1, H, W, C]
        meta = {"prompt": positive_prompt, "seed": seed, "clip_index": 0}
        return (frames, last_frame, meta)
```

---

## Node 2 — `LTXFlowExtractFrame`

**Category:** `LTXFlow`  
**Role:** Pull any frame from a video batch by index.  
**Google Flow equivalent:** Right-click → "Save frame as image" on any video frame.

### Inputs

| Name | Type | Default | Notes |
|---|---|---|---|
| `video_frames` | IMAGE | — | Full frame batch |
| `index` | INT | -1 | -1 = last frame, 0 = first frame |

### Outputs

| Name | Type | Notes |
|---|---|---|
| `frame` | IMAGE | Single extracted frame [1, H, W, C] |
| `frame_index` | INT | Actual resolved index |

### Code Skeleton

```python
class LTXFlowExtractFrame:
    CATEGORY = "LTXFlow"
    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("frame", "frame_index")
    FUNCTION = "extract"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "video_frames": ("IMAGE",),
            "index": ("INT", {
                "default": -1,
                "min": -9999,
                "max": 9999,
                "tooltip": "-1 always returns the last frame"
            })
        }}

    def extract(self, video_frames, index):
        n = video_frames.shape[0]
        real_idx = index % n  # handles negative indexing cleanly
        frame = video_frames[real_idx].unsqueeze(0)
        return (frame, real_idx)
```

---

## Node 3 — `LTXFlowExtend` ⭐ Core Node

**Category:** `LTXFlow`  
**Role:** Continues video seamlessly from the last frame of the previous clip.  
**Google Flow equivalent:** The "Extend" button in SceneBuilder — reads the final second of your clip and continues the action.

> Leave `next_prompt` empty to let LTX 2.3 decide the continuation naturally based on the incoming frame's motion context.

### Inputs

| Name | Type | Default | Notes |
|---|---|---|---|
| `last_frame` | IMAGE | — | Output from previous I2V or Extend node |
| `next_prompt` | STRING | "" | Leave empty for automatic continuation |
| `negative_prompt` | STRING | — | What to avoid |
| `model` | LTXV_MODEL | — | Loaded LTX 2.3 model |
| `vae` | VAE | — | LTX VAE |
| `num_frames` | INT | 97 | Frames for the next clip |
| `steps` | INT | 30 | Denoising steps |
| `seed` | INT | — | New seed per clip recommended |
| `prev_metadata` | LTXFLOW_META | — | Carries forward context from previous node |

### Outputs

| Name | Type | Notes |
|---|---|---|
| `video_frames` | IMAGE | New clip's frame batch |
| `last_frame` | IMAGE | This clip's last frame (chain to next Extend) |
| `metadata` | LTXFLOW_META | Updated metadata with incremented clip index |

### Code Skeleton

```python
class LTXFlowExtend:
    CATEGORY = "LTXFlow"
    RETURN_TYPES = ("IMAGE", "IMAGE", "LTXFLOW_META")
    RETURN_NAMES = ("video_frames", "last_frame", "metadata")
    FUNCTION = "extend"

    def extend(self, last_frame, model, vae,
               next_prompt, negative_prompt,
               num_frames, steps, seed, prev_metadata):
        # If no prompt given, inherit from previous clip
        prompt = next_prompt.strip() or prev_metadata.get("prompt", "")

        # Use last_frame as the I2V conditioning (frame 0 guide)
        w = last_frame.shape[2]
        h = last_frame.shape[1]
        latents = self._encode_with_guide(
            model, vae, last_frame, w, h, num_frames
        )
        frames = self._sample_and_decode(
            latents, model, vae,
            prompt, negative_prompt, steps, seed
        )
        new_last = frames[-1].unsqueeze(0)
        meta = {
            **prev_metadata,
            "prompt": prompt,
            "seed": seed,
            "clip_index": prev_metadata["clip_index"] + 1
        }
        return (frames, new_last, meta)
```

---

## Node 4 — `LTXFlowFirstLastFrame`

**Category:** `LTXFlow`  
**Role:** Provide a start AND end image — LTX generates all the motion in between.  
**Google Flow equivalent:** "Frames to Video" mode — drag images to "+ Add start frame" and "+ Add end frame".

### Inputs

| Name | Type | Default | Notes |
|---|---|---|---|
| `start_frame` | IMAGE | — | Where the clip begins |
| `end_frame` | IMAGE | — | Where the clip ends |
| `positive_prompt` | STRING | — | Describe the transition/action |
| `negative_prompt` | STRING | — | What to avoid |
| `model` | LTXV_MODEL | — | Loaded LTX 2.3 model |
| `vae` | VAE | — | LTX VAE |
| `num_frames` | INT | 97 | Length of the bridging clip |
| `steps` | INT | 30 | Denoising steps |
| `seed` | INT | — | Reproducibility |

### Outputs

| Name | Type | Notes |
|---|---|---|
| `video_frames` | IMAGE | Full bridging clip |
| `last_frame` | IMAGE | The end frame (can chain to Extend) |
| `metadata` | LTXFLOW_META | Prompt, seed, clip index, mode = "FLF" |

### Code Skeleton

```python
class LTXFlowFirstLastFrame:
    CATEGORY = "LTXFlow"
    RETURN_TYPES = ("IMAGE", "IMAGE", "LTXFLOW_META")
    RETURN_NAMES = ("video_frames", "last_frame", "metadata")
    FUNCTION = "generate_flf"

    def generate_flf(self, start_frame, end_frame, model, vae,
                     positive_prompt, negative_prompt,
                     num_frames, steps, seed):
        # Condition on frame 0 (start)
        guide_start = self._make_guide(
            model, vae, start_frame,
            frame_idx=0, total_frames=num_frames
        )
        # Condition on frame N-1 (end)
        guide_end = self._make_guide(
            model, vae, end_frame,
            frame_idx=num_frames - 1, total_frames=num_frames
        )
        guides = self._merge_guides(guide_start, guide_end)
        latents = self._init_latents(model, num_frames)
        frames = self._sample_guided(
            latents, guides, model, vae,
            positive_prompt, negative_prompt, steps, seed
        )
        last = frames[-1].unsqueeze(0)
        meta = {
            "prompt": positive_prompt,
            "seed": seed,
            "clip_index": 0,
            "mode": "FLF"
        }
        return (frames, last, meta)
```

---

## Node 5 — `LTXFlowSceneBuilder`

**Category:** `LTXFlow`  
**Role:** Concatenates up to 6 video clips (IMAGE batches) into one long video.  
**Google Flow equivalent:** The SceneBuilder timeline — assembles individual clips into the final film.

> Handles **frame deduplication** at join points — removes the duplicate last/first frame so cuts are seamless.

### Inputs

| Name | Type | Default | Notes |
|---|---|---|---|
| `clip_1` to `clip_6` | IMAGE | optional | Any VIDEO_FRAMES batch |
| `deduplicate_joins` | BOOL | True | Removes duplicate frame at each join |
| `fps` | INT | 24 | Used to compute output duration |

### Outputs

| Name | Type | Notes |
|---|---|---|
| `merged_frames` | IMAGE | Single combined frame batch |
| `total_frames` | INT | Total frame count |
| `duration_sec` | FLOAT | Total duration in seconds |

### Code Skeleton

```python
class LTXFlowSceneBuilder:
    CATEGORY = "LTXFlow"
    RETURN_TYPES = ("IMAGE", "INT", "FLOAT")
    RETURN_NAMES = ("merged_frames", "total_frames", "duration_sec")
    FUNCTION = "build"

    def build(self, fps=24, deduplicate_joins=True, **clips):
        import torch
        parts = [v for k, v in sorted(clips.items()) if v is not None]
        if not parts:
            raise ValueError("At least one clip required")

        merged = parts[0]
        for clip in parts[1:]:
            if deduplicate_joins:
                clip = clip[1:]  # drop duplicate first frame at join point
            merged = torch.cat([merged, clip], dim=0)

        n = merged.shape[0]
        dur = round(n / fps, 2)
        return (merged, n, dur)
```

---

## Workflows

### Workflow A — Basic Extend Chain (Flow Extend)

```
LoadImage
  └─► LTXFlowI2V ──────────────────────────────────────┐
        └─ last_frame ─► LTXFlowExtend #1               │
                           └─ last_frame ─► LTXFlowExtend #2
                                                         │
        video_frames ◄───────────────────────────────────┘
          └─► LTXFlowSceneBuilder ─► VHS_VideoCombine
```

### Workflow B — Frames to Video Bridge (Flow FLF)

```
Image A (start) ─┐
                  ├─► LTXFlowFirstLastFrame ─► SceneBuilder ─► SaveVideo
Image B (end)   ─┘
```

### Workflow C — Full Film Pipeline (Combined)

```
I2V (scene 1) ─► Extend (scene 2) ─► Extend (scene 3)
                                            │
                          ExtractFrame ◄────┘ (grab any mid frame)
                              │
                              └─► FLF (transition clip) ─► Extend (scene 4)

All clips ─► SceneBuilder ─► VHS_VideoCombine ─► final.mp4
```

---

## GPU Requirements

| Setup | VRAM | Recommended Settings |
|---|---|---|
| Minimum — RTX 3090 | 24 GB | 512×512, 49 frames, FP8 distilled |
| Recommended — RTX 4090 | 24 GB | 768×512, 97 frames, full FP8 |
| Cloud — RunPod A100 | 80 GB | 1080p, BF16, no VRAM limits |

> **Important:** LTX 2.3 requires width and height to be **divisible by 32**.  
> e.g. 704, 768, 1088, 1280 — not 720 or 1080.

---

## Key Implementation Notes

- `_encode_with_guide` and `_sample_and_decode` are helper wrappers around the official `ComfyUI-LTXVideo` nodes (`LTXVScheduler`, `LTXVSampler`). You are not re-implementing LTX — you are wrapping it with a cleaner interface.
- For `LTXFlowFirstLastFrame`, use `logtd`'s `ComfyUI-LTXTricks` which provides `LTXVAddGuide` with multi-frame conditioning support out of the box.
- The `LTXFLOW_META` type is a Python `dict` passed between nodes. It carries `prompt`, `seed`, and `clip_index` forward through the chain for session awareness.
- Chain as many `LTXFlowExtend` nodes as needed. Each adds ~4–8 seconds. SceneBuilder handles stitching.

---

## References

- LTX 2.3 model weights: [HuggingFace — Lightricks/LTX-Video](https://huggingface.co/Lightricks/LTX-Video)
- Official ComfyUI nodes: [github.com/Lightricks/ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)
- LTXTricks (FLF guide nodes): [github.com/logtd/ComfyUI-LTXTricks](https://github.com/logtd/ComfyUI-LTXTricks)
- LTX 2.3 docs: [docs.ltx.video](https://docs.ltx.video)
