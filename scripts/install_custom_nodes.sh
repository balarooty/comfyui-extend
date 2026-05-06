#!/usr/bin/env bash
# ================================================================== #
#  ComfyUI-LTXFlow - Custom Node Installer
#
#  Installs or updates custom node packs used by:
#    workflows/05_qwen_edit_to_ltx_first_last.json
#
#  Usage:
#    COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_nodes.sh
# ================================================================== #
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
CUSTOM_NODES_DIR="${COMFYUI_DIR}/custom_nodes"

log() { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }

find_python() {
    if [ -n "${COMFYUI_PYTHON:-}" ]; then
        printf '%s\n' "${COMFYUI_PYTHON}"
        return
    fi

    if [ -x "${COMFYUI_DIR}/venv/bin/python" ]; then
        printf '%s\n' "${COMFYUI_DIR}/venv/bin/python"
        return
    fi

    if [ -x "${COMFYUI_DIR}/python_embeded/python.exe" ]; then
        printf '%s\n' "${COMFYUI_DIR}/python_embeded/python.exe"
        return
    fi

    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi

    if command -v python >/dev/null 2>&1; then
        command -v python
        return
    fi

    return 1
}

clone_or_update() {
    local repo_url="$1"
    local target_name="$2"
    local target_dir="${CUSTOM_NODES_DIR}/${target_name}"

    if [ -d "${target_dir}/.git" ]; then
        log "Updating ${target_name}"
        git -C "${target_dir}" pull --ff-only
        return
    fi

    if [ -e "${target_dir}" ]; then
        warn "${target_dir} exists but is not a git checkout; leaving it unchanged."
        return
    fi

    log "Cloning ${target_name}"
    git clone "${repo_url}" "${target_dir}"
}

install_requirements() {
    local python_bin="$1"
    local requirements_path="${CUSTOM_NODES_DIR}/ComfyUI-KJNodes/requirements.txt"

    if [ ! -f "${requirements_path}" ]; then
        warn "KJNodes requirements.txt not found; skipping pip install."
        return
    fi

    log "Installing ComfyUI-KJNodes requirements"
    "${python_bin}" -m pip install -r "${requirements_path}"
}

install_easy_use() {
    local install_script="${CUSTOM_NODES_DIR}/ComfyUI-Easy-Use/install.sh"

    if [ ! -f "${install_script}" ]; then
        warn "ComfyUI-Easy-Use install.sh not found; skipping Easy-Use dependency install."
        return
    fi

    log "Running ComfyUI-Easy-Use install.sh"
    (cd "${CUSTOM_NODES_DIR}/ComfyUI-Easy-Use" && sh ./install.sh)
}

echo ""
echo "  =================================================="
echo "   ComfyUI-LTXFlow Custom Node Installer"
echo "   Qwen Image Edit 2511 + LTX 2.3 workflow"
echo "  =================================================="
echo ""
log "ComfyUI dir:        ${COMFYUI_DIR}"
log "Custom nodes dir:   ${CUSTOM_NODES_DIR}"
echo ""

[ -d "${COMFYUI_DIR}" ] || die "COMFYUI_DIR does not exist: ${COMFYUI_DIR}"
mkdir -p "${CUSTOM_NODES_DIR}"

PYTHON_BIN="$(find_python)" || die "Could not find Python. Set COMFYUI_PYTHON to the Python that launches ComfyUI."
log "Python:             ${PYTHON_BIN}"
echo ""

clone_or_update "https://github.com/kijai/ComfyUI-KJNodes.git" "ComfyUI-KJNodes"
clone_or_update "https://github.com/WhatDreamsCost/WhatDreamsCost-ComfyUI.git" "WhatDreamsCost-ComfyUI"
clone_or_update "https://github.com/yolain/ComfyUI-Easy-Use.git" "ComfyUI-Easy-Use"

echo ""
install_requirements "${PYTHON_BIN}"
install_easy_use

echo ""
echo "  =================================================="
echo "   Custom node installation complete."
echo "   Restart ComfyUI, refresh the browser, then load:"
echo "   workflows/05_qwen_edit_to_ltx_first_last.json"
echo "  =================================================="
echo ""
