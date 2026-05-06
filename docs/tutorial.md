# ComfyUI-LTXFlow Tutorial

A step-by-step guide to creating AI video from still images using **Qwen Image Edit** and **LTX Video 2.3**, orchestrated by the LTXFlow custom nodes.

---

## Table of Contents

1. [What This Pack Does](#what-this-pack-does)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Downloading Models](#downloading-models)
5. [Workflow 05 — Qwen Edit to LTX First/Last](#workflow-05--qwen-edit-to-ltx-firstlast)
6. [Workflow 04 — LTX First/Last (No Qwen)](#workflow-04--ltx-firstlast-no-qwen)
7. [Node Reference](#node-reference)
8. [Building a Multi-Scene Video](#building-a-multi-scene-video)
9. [Recommended Settings](#recommended-settings)
10. [Troubleshooting](#troubleshooting)

---

## What This Pack Does

ComfyUI-LTXFlow adds workflow glue between **Qwen Image Edit 2511** and **LTX Video 2.3**. The core idea:

```
Source photo  →  Qwen edits it  →  LTX animates from original to edited
```

The pack provides seven custom nodes that handle frame extraction, guide injection, image bridging, and scene stitching. It does **not** replace the official LTX or Qwen nodes — it connects them.

### The Pipeline at a Glance

```
┌─────────────┐      ┌──────────────────┐      ┌───────────────────────┐
│  LoadImage   │─────▶│  Qwen Image Edit │─────▶│  Qwen Edit Bridge     │
│  (source)    │      │  (2511 subgraph) │      │  (resize + prepare)   │
└─────────────┘      └──────────────────┘      └───────┬───────────────┘
                                                        │
                                              first_frame + last_frame
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  First/Last     │
                                               │  Guide          │
                                               │  (inject into   │
                                               │   LTX cond.)    │
                                               └────────┬────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  LTX 2.3        │
                                               │  Sampler +      │
                                               │  Upscale +      │
                                               │  Decode         │
                                               └────────┬────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  SaveVideo      │
                                               └─────────────────┘
```

---

## Prerequisites

- **ComfyUI** — latest version ([update guide](https://docs.comfy.org/installation/update_comfyui))
- **GPU** — 24 GB VRAM recommended (48 GB for best quality). The fp8 models can run on 24 GB cards.
- **Python 3.10+**
- **aria2** — the download script installs it automatically if missing

---

## Installation

### 1. Clone or Copy the Node Pack

Place this repository inside your ComfyUI custom nodes folder:

```bash
cd /path/to/ComfyUI/custom_nodes/
git clone https://github.com/balarooty/comfyui-extend.git ComfyUI-LTXFlow
```

Or if you already have the folder locally, symlink it:

```bash
ln -s /path/to/comfyui-extend /path/to/ComfyUI/custom_nodes/ComfyUI-LTXFlow
```

### 2. Install Required Custom Node Packs

The workflows depend on three external packs. Install them automatically:

```bash
COMFYUI_DIR=/path/to/ComfyUI bash scripts/install_custom_nodes.sh
```

This installs:

| Pack | Provides |
|------|----------|
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | `LazySwitchKJ`, `VAELoaderKJ`, `LTX2SamplingPreviewOverride` |
| [WhatDreamsCost-ComfyUI](https://github.com/WhatDreamsCost/WhatDreamsCost-ComfyUI) | `LTXSequencer`, `MultiImageLoader` |
| [ComfyUI Easy Use](https://github.com/yolain/ComfyUI-Easy-Use) | `easy mathInt` |

Alternatively, install through **ComfyUI Manager** if you prefer the GUI.

### 3. Restart ComfyUI

After installing, restart the ComfyUI server and refresh the browser.

---

## Downloading Models

The download script fetches every model needed by the main workflow:

```bash
COMFYUI_DIR=/path/to/ComfyUI bash scripts/download_models.sh
```

Set `COMFYUI_DIR` to your actual ComfyUI root. The script downloads:

### Qwen Image Edit 2511 Models

| File | Directory | Size (approx.) |
|------|-----------|-----------------|
| `qwen_image_edit_2511_bf16.safetensors` | `models/diffusion_models/` | ~14 GB |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `models/text_encoders/` | ~8 GB |
| `qwen_image_vae.safetensors` | `models/vae/` | ~150 MB |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | `models/loras/` | ~14 GB |

### LTX Video 2.3 Models

| File | Directory | Size (approx.) |
|------|-----------|-----------------|
| `ltx-2.3-22b-dev-fp8.safetensors` | `models/checkpoints/` | ~22 GB |
| `gemma_3_12B_it_fp8_scaled.safetensors` | `models/text_encoders/` | ~12 GB |
| `ltx-2.3-22b-distilled-lora-384.safetensors` | `models/loras/` | ~700 MB |
| `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` | `models/latent_upscale_models/` | ~500 MB |

### Optional: Hugging Face Auth

If any model is gated:

```bash
HF_TOKEN=hf_xxxxx COMFYUI_DIR=/path/to/ComfyUI bash scripts/download_models.sh
```

### Optional: Custom Download Speed

The script uses `aria2` with 16 parallel connections by default:

```bash
ARIA2_CONNECTIONS=8 ARIA2_SPLITS=8 COMFYUI_DIR=/path/to/ComfyUI bash scripts/download_models.sh
```

---

## Workflow 05 — Qwen Edit to LTX First/Last

This is the **main workflow**. It takes a source image, runs it through Qwen Image Edit to create a modified version, then animates the transition using LTX Video 2.3.

### Loading the Workflow

1. Open ComfyUI in your browser
2. Click **Load** → select `workflows/05_qwen_edit_to_ltx_first_last.json`
3. If ComfyUI shows "Installation Required", install the missing packs (see [Installation](#2-install-required-custom-node-packs))

### Step-by-Step Walkthrough

#### Step 1: Load Your Source Image

Find the **LoadImage** node on the left side of the canvas. Upload your source image here. This is the starting frame of your video.

> **Tip:** Use images with clear subjects. Portraits, objects, and scenes with distinct features work best.

#### Step 2: Load a Reference/Style Image

Find the second **LoadImage** node. Upload a reference image that shows the target look, material, or style you want Qwen to apply to the source.

For example:
- Source: a leather sofa
- Reference: a velvet texture photo
- Result: Qwen edits the sofa to look velvet, then LTX animates the transformation

#### Step 3: Set the Prompt

In the **Model Loader** subgraph (node labeled with a "↓ Select your own models" note), find the **Prompt** field. Write a description of the final scene.

Example prompts:
- `"A cozy velvet sofa in a warm living room, soft lighting"`
- `"A futuristic cityscape at sunset, neon lights reflecting on wet streets"`

#### Step 4: Configure Video Length

In the same Model Loader subgraph, set **length (seconds)**. Start with `5` seconds for testing. Each second generates about 24 frames.

#### Step 5: Queue the Prompt

Click **Queue Prompt** (or press `Ctrl+Enter`). The execution order is:

1. Qwen Image Edit processes the source + reference into an edited image
2. The **Qwen Edit Bridge** prepares first frame (source) and last frame (edited)
3. **First/Last Guide** injects both frames into LTX conditioning
4. LTX 2.3 generates the video with 3-stage upscaling
5. The decoded video is saved

### Understanding the Qwen Edit Bridge

The bridge node (`LTX Flow - Qwen Edit Bridge`) has two important settings:

| Setting | Options | What It Does |
|---------|---------|--------------|
| `first_frame_source` | `source_image` / `qwen_edited_image` | Which image becomes the first frame of the video |
| `resize_to` | `source_image` / `qwen_edited_image` | Which image's dimensions are used as the target size |

**Default behavior:** The source image is the first frame, the Qwen-edited image is the last frame. This creates a smooth transformation video.

**Alternative:** Set `first_frame_source = qwen_edited_image` to animate only within the edited scene (no visible transition from original).

### Understanding First/Last Guide

The guide node (`LTX Flow - First/Last Guide`) controls how strongly the first and last frames influence generation:

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| `first_strength` | `1.0` | `0.0–1.0` | How strongly the first frame anchors frame 0 |
| `last_strength` | `1.0` | `0.0–1.0` | How strongly the last frame anchors the final frame |
| `last_frame_index` | `-1` | any integer | `-1` = last frame of the latent. Use a specific number for earlier anchoring. |

> **Tip:** Keep both strengths at `1.0` for reliable transitions. Lower the last strength to `0.7–0.8` if you want more creative freedom in how LTX reaches the target frame.

---

## Workflow 04 — LTX First/Last (No Qwen)

If you just want to use LTX Video 2.3 with first/last frame guidance (without Qwen editing), use:

```
workflows/04_ltxflow_first_last_wdc_ltx23.json
```

This is based on the [WhatDreamsCost](https://github.com/WhatDreamsCost/WhatDreamsCost-ComfyUI) reference workflow. The key difference is that the dynamic `LTXSequencer` section is replaced with our `First/Last Guide` node.

### How to Use

1. Load the workflow
2. In the **MultiImageLoader** node, load your first and last frame images
3. The `Extract Frame` nodes automatically pull index `0` (first) and index `-1` (last)
4. Set your prompt and video length in the Model Loader subgraph
5. Queue the prompt

---

## Node Reference

### LTX Flow - Extract Frame

**Category:** `LTXFlow/Frame Tools`

Pulls a single frame from an image batch.

| Input | Type | Description |
|-------|------|-------------|
| `video_frames` | IMAGE | A batch of frames |
| `index` | INT | Frame index. `0` = first, `-1` = last, `-2` = second-to-last, etc. |

| Output | Type | Description |
|--------|------|-------------|
| `frame` | IMAGE | The extracted single frame |
| `resolved_index` | INT | The actual positive index that was used |

### LTX Flow - Extract Tail

**Category:** `LTXFlow/Frame Tools`

Extracts the last N frames from a clip. Essential for continuation workflows.

| Input | Type | Description |
|-------|------|-------------|
| `video_frames` | IMAGE | A batch of frames |
| `tail_length` | INT | Number of frames to keep. Default: `17`. Good values: `9`, `17`, `25`. |

| Output | Type | Description |
|--------|------|-------------|
| `tail_frames` | IMAGE | The extracted tail segment |
| `actual_frame_count` | INT | How many frames were actually extracted (may be less than requested) |

> **Why 17?** LTX works with 8-frame chunks + 1 overlap. A 17-frame tail gives 2 full chunks of motion context.

### LTX Flow - First/Last Guide

**Category:** `LTXFlow/LTX Guides`

Injects first and last frame guidance into LTX conditioning using `LTXVAddGuide` internals.

| Input | Type | Description |
|-------|------|-------------|
| `positive` | CONDITIONING | Positive conditioning from the LTX text encoder |
| `negative` | CONDITIONING | Negative conditioning |
| `vae` | VAE | The LTX video VAE |
| `latent` | LATENT | Empty LTX latent |
| `first_frame` | IMAGE | Image to anchor at frame 0 |
| `last_frame` | IMAGE | Image to anchor at the final frame |
| `first_strength` | FLOAT | Guidance strength for first frame (0.0–1.0) |
| `last_strength` | FLOAT | Guidance strength for last frame (0.0–1.0) |
| `last_frame_index` | INT | Frame position for last frame. `-1` = final frame. |

| Output | Type | Description |
|--------|------|-------------|
| `positive` | CONDITIONING | Updated positive conditioning |
| `negative` | CONDITIONING | Updated negative conditioning |
| `latent` | LATENT | Updated latent with noise mask |

### LTX Flow - Qwen Edit Bridge

**Category:** `LTXFlow/Qwen`

Prepares Qwen-edited images for the First/Last Guide by resizing to matching dimensions.

| Input | Type | Description |
|-------|------|-------------|
| `source_image` | IMAGE | Original source image |
| `qwen_edited_image` | IMAGE | Output from Qwen Image Edit |
| `first_frame_source` | ENUM | `source_image` or `qwen_edited_image` |
| `resize_to` | ENUM | Which image's size to use as the target |
| `multiple_of` | INT | Enforce dimension divisibility (default: `32`) |

| Output | Type | Description |
|--------|------|-------------|
| `first_frame` | IMAGE | Ready for First/Last Guide |
| `last_frame` | IMAGE | Ready for First/Last Guide |
| `keyframe_batch` | IMAGE | Both frames stacked as a 2-frame batch |

### LTX Flow - Tail Guide

**Category:** `LTXFlow/LTX Guides`

For Flow-style video extension. Takes the tail segment of a previous clip and uses it to condition the next clip's generation.

| Input | Type | Description |
|-------|------|-------------|
| `tail_frames` | IMAGE | Tail frames from Extract Tail |
| `positive` | CONDITIONING | LTX conditioning |
| `negative` | CONDITIONING | LTX conditioning |
| `vae` | VAE | LTX video VAE |
| `latent` | LATENT | Target latent for the new clip |
| `tail_strength` | FLOAT | How strongly the tail influences the next clip |

| Output | Type | Description |
|--------|------|-------------|
| `positive` | CONDITIONING | Updated conditioning |
| `negative` | CONDITIONING | Updated conditioning |
| `latent` | LATENT | Updated latent with overlap |
| `overlap_frames` | INT | Number of frames that overlap with the previous clip |

### LTX Flow - Trim Frames

**Category:** `LTXFlow/Frame Tools`

Removes frames from the start or end of a clip. Needed after overlap-based extension to avoid duplicate frames.

### LTX Flow - Scene Builder

**Category:** `LTXFlow/Scene Tools`

Concatenates up to 6 clips into a single frame batch for video export.

| Input | Type | Description |
|-------|------|-------------|
| `clip_1` | IMAGE | First clip (required) |
| `clip_2` through `clip_6` | IMAGE | Additional clips (optional) |
| `deduplicate_joins` | BOOLEAN | Drop the first frame of each subsequent clip to avoid duplicates |
| `fps` | INT | Frames per second for duration calculation |

| Output | Type | Description |
|--------|------|-------------|
| `merged_frames` | IMAGE | All clips concatenated |
| `total_frames` | INT | Total frame count |
| `duration_seconds` | FLOAT | Estimated video duration |

> **Important:** All clips must have the same height, width, and channel count. Resize them before merging if needed.

---

## Building a Multi-Scene Video

The full pipeline for creating a multi-scene video:

### Step 1: Generate Your First Clip

Use Workflow 05 to generate a Qwen-edited transition video from your source image.

### Step 2: Extract the Tail

Feed the generated clip into `Extract Tail` with `tail_length = 17`.

### Step 3: Generate the Next Clip

Use the `Tail Guide` node to condition the next LTX generation with the previous clip's tail. Write a new prompt for the continuation.

### Step 4: Trim the Overlap

After generating the next clip, use `Trim Frames` to remove the overlapping frames at the start.

### Step 5: Stitch Together

Feed all clips into `Scene Builder`:

```
clip_1 = first generated clip
clip_2 = second clip (trimmed)
clip_3 = third clip (trimmed)
deduplicate_joins = true
fps = 24
```

### Step 6: Export

Send `merged_frames` to `SaveVideo` or `VHS_VideoCombine` to export your final video.

---

## Recommended Settings

### Qwen Image Edit

| Parameter | Recommended |
|-----------|-------------|
| Steps | 40 |
| CFG | 4.0 |
| Lightning LoRA steps | 4 |

### LTX Video 2.3

| Parameter | Recommended |
|-----------|-------------|
| Video length | 5 seconds (start here) |
| First/Last strength | 1.0 / 1.0 |
| Upscale 2x on Stage 3 | `true` |
| Tail length (for continuation) | 17 frames |

### VRAM Management

| VRAM | Recommendation |
|------|----------------|
| 24 GB | Use fp8 models. Enable optimized decoding (tiled VAE). Keep video length ≤ 5 seconds. |
| 48 GB | Full models possible. Can extend to 8–10 second clips. |
| < 24 GB | Not recommended. Consider cloud GPU (VastAI, RunPod). |

---

## Troubleshooting

### "No outer link found for slot [0] image"

This means a node's image input isn't connected. Check that:
- The `LoadImage` nodes have valid images selected
- All wires between nodes are intact (click and drag to reconnect)
- You're using the latest version of the workflow from this repo

### "Installation Required" dialog on load

Install the missing custom node packs:

```bash
COMFYUI_DIR=/path/to/ComfyUI bash scripts/install_custom_nodes.sh
```

Or install through ComfyUI Manager.

### Models not found in dropdowns

Make sure models are in the correct subdirectories:

```
ComfyUI/models/
├── checkpoints/
│   └── ltx-2.3-22b-dev-fp8.safetensors
├── diffusion_models/
│   └── qwen_image_edit_2511_bf16.safetensors
├── latent_upscale_models/
│   └── ltx-2.3-spatial-upscaler-x2-1.1.safetensors
├── loras/
│   ├── ltx-2.3-22b-distilled-lora-384.safetensors
│   └── Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors
├── text_encoders/
│   ├── gemma_3_12B_it_fp8_scaled.safetensors
│   └── qwen_2.5_vl_7b_fp8_scaled.safetensors
└── vae/
    └── qwen_image_vae.safetensors
```

Restart ComfyUI after placing models.

### Video looks blurry or inconsistent

- Enable **Upscale 2x on Stage 3** in the sampler subgraph
- Increase `first_strength` and `last_strength` to `1.0`
- Try a longer video (more frames = smoother interpolation)
- Write a more detailed prompt

### Out of VRAM

- Enable **Optimized Decoding** (tiled VAE) in the decode subgraph
- Reduce video length
- Use the fp8 model variants (already included in the download script)
- Close other GPU applications

---

## Further Resources

- [LTX Video 2.3 on HuggingFace](https://huggingface.co/Lightricks/LTX-2.3)
- [Qwen Image Edit on HuggingFace](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI)
- [Awesome LTX 2 — Community Resources](https://github.com/wildminder/awesome-ltx2)
- [ComfyUI Documentation](https://docs.comfy.org/)
