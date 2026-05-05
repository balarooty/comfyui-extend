# Workflow Notes

Build the workflow one node at a time.

## Step 1: Extract Frame

Load `workflows/01_extract_frame.json`.

Replace `LoadImage` with any node that outputs an `IMAGE` batch:

- LTX generated frames
- VHS loaded video frames
- any image batch

Use this for grabbing a first frame, last frame, or mid-frame key image.

## Step 2: Extract Tail

Load `workflows/02_extract_tail.json`.

This is the important piece for Flow-style extension. A single last frame can continue visual identity, but it loses motion context. A short tail segment preserves more action.

Start with:

```text
tail_length = 17
```

Then feed `tail_frames` into an LTX continuation or multi-condition workflow as the conditioning media for the next clip.

## Step 3: Scene Builder

Load `workflows/03_scene_builder.json`.

Replace the example `LoadImage` nodes with completed clip frame batches:

```text
clip_1 = first LTX clip
clip_2 = first extension
clip_3 = second extension
```

Keep `deduplicate_joins = true` when each new clip starts from the previous final frame.

## Qwen + LTX Structure

Use Qwen to create keyframes:

```text
story prompt -> Qwen Image -> first frame
scene target -> Qwen Image Edit -> last frame
```

Use LTX to animate:

```text
first frame -> LTX I2V -> clip
clip tail -> LTX continuation -> next clip
start frame + end frame -> LTX first/last frame -> bridge clip
```

Use these custom nodes to connect the pieces:

```text
LTX clip -> Extract Tail -> next LTX clip
all LTX clips -> Scene Builder -> video combine
```

## Proper LTX Guide Workflow

Use:

```text
workflows/04_ltxflow_first_last_wdc_ltx23.json
```

This is based on the WhatDreamsCost two-stage LTX 2.3 workflow. The important change is replacing the dynamic `LTXSequencer` section with:

```text
MultiImageLoader.multi_output
  -> ExtractFrame index 0
  -> First/Last Guide first_frame

MultiImageLoader.multi_output
  -> ExtractFrame index -1
  -> First/Last Guide last_frame
```

The `First/Last Guide` node receives the real LTX conditioning, VAE, and latent inputs, then returns updated conditioning and latent outputs to the existing sampler path.

This is the right pattern for first/last frame video. The earlier utility workflows are only tests for our helper nodes.
