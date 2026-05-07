#!/usr/bin/env bash
# ================================================================== #
#  ComfyUI-LTXFlow — Qwen Edit + LTX 2.3 Model Downloader
#
#  Downloads all models used by:
#    workflows/05_qwen_edit_to_ltx_first_last.json
#
#  Usage:
#    COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#
#  Optional:
#    HF_TOKEN=hf_xxxxx COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#    ARIA2_CONNECTIONS=8 ARIA2_SPLITS=8 bash scripts/download_models.sh
# ================================================================== #
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
BASE_DIR="${COMFYUI_DIR}/models"

ARIA2_CONNECTIONS="${ARIA2_CONNECTIONS:-16}"
ARIA2_SPLITS="${ARIA2_SPLITS:-16}"
ARIA2_CHUNK_SIZE="${ARIA2_CHUNK_SIZE:-1M}"

log() { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }

install_aria2() {
    if command -v aria2c >/dev/null 2>&1; then
        log "aria2 already installed ($(aria2c --version | head -1))"
        return
    fi

    log "aria2 not found, installing..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y aria2
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update -qq
        sudo apt install -y aria2
    elif command -v brew >/dev/null 2>&1; then
        brew install aria2
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm aria2
    else
        die "Could not install aria2 automatically. Install aria2 and rerun."
    fi
}

download_file() {
    local target_dir="$1"
    local output_name="$2"
    local url="$3"
    local target_path="${target_dir}/${output_name}"

    mkdir -p "${target_dir}"

    if [ -s "${target_path}" ]; then
        local size
        size=$(du -h "${target_path}" 2>/dev/null | cut -f1)
        log "Skipping existing ${output_name} (${size})"
        return
    fi

    log "Downloading ${output_name}"
    log "  -> ${target_dir}"

    local args=(
        -x "${ARIA2_CONNECTIONS}"
        -s "${ARIA2_SPLITS}"
        -k "${ARIA2_CHUNK_SIZE}"
        --continue=true
        --auto-file-renaming=false
        --allow-overwrite=true
        --summary-interval=30
        -d "${target_dir}"
        -o "${output_name}"
    )

    if [ -n "${HF_TOKEN:-}" ]; then
        args+=(--header "Authorization: Bearer ${HF_TOKEN}")
    fi

    aria2c "${args[@]}" "${url}"

    local final_size
    final_size=$(du -h "${target_path}" 2>/dev/null | cut -f1)
    log "Downloaded ${output_name} (${final_size})"
}

echo ""
echo "  =================================================="
echo "   ComfyUI-LTXFlow Model Downloader"
echo "   Qwen Image Edit 2511 + LTX 2.3"
echo "  =================================================="
echo ""
log "ComfyUI dir: ${COMFYUI_DIR}"
log "Models dir:  ${BASE_DIR}"
[ -n "${HF_TOKEN:-}" ] && log "HF auth:     token provided" || log "HF auth:     none"
echo ""

install_aria2

log "Creating model directories..."
mkdir -p \
    "${BASE_DIR}/checkpoints" \
    "${BASE_DIR}/diffusion_models" \
    "${BASE_DIR}/latent_upscale_models" \
    "${BASE_DIR}/loras" \
    "${BASE_DIR}/text_encoders" \
    "${BASE_DIR}/vae"

echo ""
log "━━━ Downloading Qwen Image Edit 2511 models ━━━"
echo ""

download_file \
    "${BASE_DIR}/diffusion_models" \
    "qwen_image_edit_2511_bf16.safetensors" \
    "https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors"

download_file \
    "${BASE_DIR}/text_encoders" \
    "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

download_file \
    "${BASE_DIR}/vae" \
    "qwen_image_vae.safetensors" \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"

download_file \
    "${BASE_DIR}/loras" \
    "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors" \
    "https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"

echo ""
log "━━━ Downloading LTX 2.3 models ━━━"
echo ""

download_file \
    "${BASE_DIR}/checkpoints" \
    "ltx-2.3-22b-dev-fp8.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-22b-dev-fp8.safetensors"

download_file \
    "${BASE_DIR}/text_encoders" \
    "gemma_3_12B_it_fp8_scaled.safetensors" \
    "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors"

download_file \
    "${BASE_DIR}/loras" \
    "ltx-2.3-22b-distilled-lora-384.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-22b-distilled-lora-384.safetensors"

download_file \
    "${BASE_DIR}/latent_upscale_models" \
    "ltx-2.3-spatial-upscaler-x2-1.1.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors"

echo ""
log "━━━ Downloading LTX 2.3 VAEs (Kijai) ━━━"
echo ""

download_file \
    "${BASE_DIR}/vae" \
    "taeltx2_3.safetensors" \
    "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/taeltx2_3.safetensors"

download_file \
    "${BASE_DIR}/vae" \
    "LTX23_video_vae_bf16.safetensors" \
    "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/LTX23_video_vae_bf16.safetensors"

download_file \
    "${BASE_DIR}/vae" \
    "LTX23_audio_vae_bf16.safetensors" \
    "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/LTX23_audio_vae_bf16.safetensors"

echo ""
echo "  =================================================="
echo "   Downloads complete."
echo "   Restart ComfyUI, then load:"
echo "   workflows/05_qwen_edit_to_ltx_first_last.json"
echo "  =================================================="
echo ""
