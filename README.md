# ComfyUI-LTXFlow

Small ComfyUI custom nodes for building a Flow-style video continuation workflow with LTX 2.3.

This package does not replace the official LTX or Qwen nodes. It adds the missing workflow glue:

- extract a specific frame from a generated clip
- extract a final tail segment for better continuation
- stitch multiple clips into one frame batch

## Install

Place this folder in:

```text
ComfyUI/custom_nodes/ComfyUI-LTXFlow
```

Then restart ComfyUI.

## Download Models

From this repo:

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

Change `COMFYUI_DIR` to your actual ComfyUI path. The script downloads every model needed by:

```text
workflows/05_qwen_edit_to_ltx_first_last.json
```

It supports Hugging Face auth if needed:

```bash
HF_TOKEN=hf_xxxxx COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

This script only downloads model files. It does not install ComfyUI custom node packs.

## Install Workflow Custom Nodes

The Qwen Edit to LTX workflow also depends on custom node packs outside this repo. If ComfyUI shows an "Installation Required" dialog for `workflows/05_qwen_edit_to_ltx_first_last.json`, install these packs with ComfyUI Manager:

- `ComfyUI-KJNodes` - provides `LazySwitchKJ`, `VAELoaderKJ`, and `LTX2SamplingPreviewOverride`
- `WhatDreamsCost-ComfyUI` - provides `LTXSequencer`
- `ComfyUI Easy Use` - provides `easy mathInt`

Manual install:

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_nodes.sh
```

Change `COMFYUI_DIR` to your actual ComfyUI path. The helper clones or updates:

- <https://github.com/kijai/ComfyUI-KJNodes>
- <https://github.com/WhatDreamsCost/WhatDreamsCost-ComfyUI>
- <https://github.com/yolain/ComfyUI-Easy-Use>

Restart ComfyUI after installing custom nodes, then refresh the browser page.

## Frontend

Custom frontend code lives here:

```text
js/ltxflow_ui.js
```

The package exposes it through:

```python
WEB_DIRECTORY = "./js"
```

This frontend adds node colors, short in-node notes, and default widget adjustments for LTXFlow nodes. The main node interfaces still come from each Python node's `INPUT_TYPES`, which is how ComfyUI builds standard node widgets.

## Nodes

Proper LTX 2.3 first/last workflow, based on the WhatDreamsCost reference workflow:

```text
workflows/04_ltxflow_first_last_wdc_ltx23.json
```

Use this one for the first real test. It requires the same dependencies as the reference workflow:

- WhatDreamsCost-ComfyUI
- official LTX/ComfyUI LTX nodes used by that workflow
- VideoHelperSuite `SaveVideo`/video combine dependencies
- this `ComfyUI-LTXFlow` package

Qwen Image Edit to LTX first/last workflow:

```text
workflows/05_qwen_edit_to_ltx_first_last.json
```

This is the main Qwen + LTX workflow. It wires:

```text
source image + reference image
  -> Image Edit (Qwen-Image 2511)
  -> LTX Flow - Qwen Edit Bridge
  -> LTX Flow - First/Last Guide
  -> LTX sampler/video output
```

The bridge sends the original source image as the LTX first frame and the Qwen-edited image as the LTX last frame.

Required custom node packs:

- `ComfyUI-KJNodes` for `LazySwitchKJ`, `VAELoaderKJ`, and `LTX2SamplingPreviewOverride`
- `WhatDreamsCost-ComfyUI` for `LTXSequencer`
- `ComfyUI Easy Use` for `easy mathInt`

Required Qwen models from the official ComfyUI template:

- `qwen_2.5_vl_7b_fp8_scaled.safetensors` in `ComfyUI/models/text_encoders/`
- `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` in `ComfyUI/models/loras/`
- `qwen_image_edit_2511_bf16.safetensors` in `ComfyUI/models/diffusion_models/`
- `qwen_image_vae.safetensors` in `ComfyUI/models/vae/`

Required LTX 2.3 models:

- `ltx-2.3-22b-dev-fp8.safetensors` in `ComfyUI/models/checkpoints/`
- `gemma_3_12B_it_fp8_scaled.safetensors` in `ComfyUI/models/text_encoders/`
- `ltx-2.3-22b-distilled-lora-384.safetensors` in `ComfyUI/models/loras/`
- `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` in `ComfyUI/models/latent_upscale_models/`

You do not need `ltx-av-step-1751000_vocoder_24K.safetensors` for this workflow. That was an older/reference workflow name, not the current LTX 2.3 filename we use here.

The workflow uses the official Qwen Image Edit 2511 subgraph node from ComfyUI's workflow templates.

The guide section is:

```text
MultiImageLoader
  -> LTX Flow - Extract Frame (index 0)
  -> LTX Flow - First/Last Guide first_frame

MultiImageLoader
  -> LTX Flow - Extract Frame (index -1)
  -> LTX Flow - First/Last Guide last_frame

LTXVConditioning + video VAE + EmptyLTXVLatentVideo
  -> LTX Flow - First/Last Guide
  -> sampler path
```

Combined workflow:

```text
workflows/00_ltxflow_utilities_combined.json
```

This puts `Extract Frame`, `Extract Tail`, and `Scene Builder` on one canvas. Use it as the main starting workflow.

### LTX Flow - Extract Frame

Input: `video_frames`

Output:

- `frame`
- `resolved_index`

Use `index = -1` for the last frame, `0` for the first frame, or any positive/negative frame index.

Workflow:

```text
workflows/01_extract_frame.json
```

### LTX Flow - Extract Tail

Input: `video_frames`

Output:

- `tail_frames`
- `actual_frame_count`

Use this before an LTX continuation workflow. For best continuation behavior, start with `tail_length = 17`. Good values are `9`, `17`, and `25`.

Workflow:

```text
workflows/02_extract_tail.json
```

### LTX Flow - First/Last Guide

Input:

- `positive`
- `negative`
- `vae`
- `latent`
- `first_frame`
- `last_frame`

Output:

- guided `positive`
- guided `negative`
- guided `latent`

This is the important node for Frames-to-Video style generation. It uses ComfyUI's `LTXVAddGuide` internals to inject the first frame at frame `0` and the last frame at frame `-1`.

### LTX Flow - Qwen Edit Bridge

Input:

- `source_image`
- `qwen_edited_image`

Output:

- `first_frame`
- `last_frame`
- `keyframe_batch`

This node resizes the source and Qwen-edited image to matching dimensions, enforces a configurable multiple such as `32`, and prepares them for `LTX Flow - First/Last Guide`.

### LTX Flow - Tail Guide

Input:

- previous clip tail frames
- LTX conditioning
- video VAE
- target latent

Output:

- guided `positive`
- guided `negative`
- guided `latent`
- `overlap_frames`

This is for the next step: Flow-style extension. Use `Extract Tail` from the previous clip, feed it into `Tail Guide`, generate the next clip, then trim the overlapped frames before stitching.

### LTX Flow - Trim Frames

Removes frames from the start/end of a generated batch. This is needed after overlap-based extension, because the first generated frames repeat the previous clip's tail.

### LTX Flow - Scene Builder

Inputs:

- `clip_1`
- optional `clip_2` through `clip_6`
- `deduplicate_joins`
- `fps`

Output:

- `merged_frames`
- `total_frames`
- `duration_seconds`

Send `merged_frames` to `VHS_VideoCombine` or another video saver node.

Workflow:

```text
workflows/03_scene_builder.json
```

## Recommended Full Pipeline

```text
Qwen Image / Qwen Image Edit
  -> keyframe image
  -> official LTX 2.3 image-to-video workflow
  -> LTX Flow - Extract Tail
  -> official LTX 2.3 continuation / multi-condition workflow
  -> LTX Flow - Scene Builder
  -> VHS Video Combine
```

Qwen is best used for first frames, last frames, character references, and visual consistency. LTX is best used for motion and clip continuation.
