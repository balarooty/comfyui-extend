import { app } from "../../scripts/app.js";

const NODE_HELP = {
  LTXFlowExtractFrame: {
    color: "#315a7d",
    bgcolor: "#172638",
    title: "Extract one frame from a clip batch. Use index -1 for the final frame.",
  },
  LTXFlowExtractTail: {
    color: "#7d6731",
    bgcolor: "#352b15",
    title: "Extract a final tail segment for LTX continuation. Try 9, 17, or 25 frames.",
  },
  LTXFlowFirstLastGuide: {
    color: "#4f7d44",
    bgcolor: "#1e301b",
    title: "Inject first and last frames into the real LTX conditioning and latent path.",
  },
  LTXFlowTailGuide: {
    color: "#7d4f31",
    bgcolor: "#341f14",
    title: "Inject tail frames from a previous clip into the next LTX generation.",
  },
  LTXFlowTrimFrames: {
    color: "#6b527d",
    bgcolor: "#2a2034",
    title: "Trim overlap frames before stitching extension clips.",
  },
  LTXFlowSceneBuilder: {
    color: "#4d6d75",
    bgcolor: "#1c2a2e",
    title: "Merge finished clip frame batches for video combine/export.",
  },
};

function addLtxFlowNote(node, text) {
  if (!node.widgets) {
    node.widgets = [];
  }

  const exists = node.widgets.some((widget) => widget.name === "ltxflow_note");
  if (exists) {
    return;
  }

  node.addWidget("text", "ltxflow_note", text, () => {}, {
    multiline: true,
  });
}

app.registerExtension({
  name: "comfyui-ltxflow.ui",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    const help = NODE_HELP[nodeData.name];
    if (!help) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated?.apply(this, arguments);

      this.color = help.color;
      this.bgcolor = help.bgcolor;
      this.title = this.title || nodeData.display_name || nodeData.name;
      addLtxFlowNote(this, help.title);

      if (nodeData.name === "LTXFlowFirstLastGuide") {
        const lastFrameIndex = this.widgets?.find((widget) => widget.name === "last_frame_index");
        if (lastFrameIndex) {
          lastFrameIndex.value = -1;
        }
      }

      if (nodeData.name === "LTXFlowExtractTail") {
        const tailLength = this.widgets?.find((widget) => widget.name === "tail_length");
        if (tailLength && ![9, 17, 25].includes(Number(tailLength.value))) {
          tailLength.value = 17;
        }
      }

      return result;
    };
  },
});
