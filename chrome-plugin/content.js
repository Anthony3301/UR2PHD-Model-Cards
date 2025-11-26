// content.js

// Only activate on Hugging Face
if (window.location.hostname === "huggingface.co") {
  setupEvaluationUI();
}

let lastGradeData = null;
let panelVisible = false;
let isGrading = false;

/* ---------------- Inject styles for spinner / glow / polish ---------------- */

function injectStylesOnce() {
  if (document.getElementById("hf-modelcard-grade-style")) return;

  const style = document.createElement("style");
  style.id = "hf-modelcard-grade-style";
  style.textContent = `
    #hf-modelcard-grade-badge {
      backdrop-filter: blur(10px);
      transition: box-shadow 0.2s ease, transform 0.1s ease, border-color 0.2s ease;
    }

    #hf-modelcard-grade-badge:hover {
      transform: translateY(-1px);
      box-shadow: 0 10px 28px rgba(15,23,42,0.75);
      border-color: rgba(248, 250, 252, 0.9);
    }

    #hf-modelcard-grade-spinner {
      width: 14px;
      height: 14px;
      border-radius: 999px;
      border: 2px solid rgba(249, 250, 251, 0.35);
      border-top-color: #fbbf24;
      animation: hf-modelcard-spin 0.8s linear infinite;
    }

    @keyframes hf-modelcard-spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* Glow / pulse after grading until user clicks */
    #hf-modelcard-grade-badge.hf-modelcard-badge-pulse {
      animation: hf-modelcard-pulse 1.2s ease-in-out infinite;
    }

    @keyframes hf-modelcard-pulse {
      0% {
        box-shadow: 0 8px 24px rgba(34,197,94,0.3);
        transform: translateY(0);
      }
      50% {
        box-shadow: 0 12px 36px rgba(34,197,94,0.9);
        transform: translateY(-2px);
      }
      100% {
        box-shadow: 0 8px 24px rgba(34,197,94,0.3);
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(style);
}

/* ---------------- Utilities ---------------- */

function modelCardTabIsActive() {
  // Look for an <a class="tab-alternate active"> whose text contains "Model card"
  const tabs = Array.from(document.querySelectorAll("a.tab-alternate.active"));
  return tabs.some((a) => a.textContent.toLowerCase().includes("model card"));
}

/* ---------------- Badge / Button ---------------- */

function createBadge(text) {
  injectStylesOnce();

  const badge = document.createElement("div");
  badge.id = "hf-modelcard-grade-badge";
  badge.setAttribute("data-state", "idle");

  // Prominent pill styling
  badge.style.position = "fixed";
  badge.style.bottom = "20px";
  badge.style.right = "20px";
  badge.style.padding = "10px 18px";
  badge.style.background = "linear-gradient(135deg, #0f172a, #1f2937)"; // dark gradient
  badge.style.color = "white";
  badge.style.fontSize = "13px";
  badge.style.borderRadius = "999px";
  badge.style.zIndex = "999999";
  badge.style.fontFamily = "system-ui, -apple-system, BlinkMacSystemFont, sans-serif";
  badge.style.boxShadow = "0 8px 24px rgba(15,23,42,0.65)";
  badge.style.maxWidth = "320px";
  badge.style.lineHeight = "1.5";
  badge.style.cursor = "pointer";
  badge.style.display = "flex";
  badge.style.alignItems = "center";
  badge.style.gap = "8px";
  badge.style.border = "1px solid rgba(148, 163, 184, 0.9)";

  // Colored dot
  const dot = document.createElement("span");
  dot.id = "hf-modelcard-grade-badge-dot";
  dot.style.width = "10px";
  dot.style.height = "10px";
  dot.style.borderRadius = "999px";
  dot.style.background = "#22c55e"; // green by default
  dot.style.boxShadow = "0 0 0 2px rgba(15,23,42,0.8)";
  badge.appendChild(dot);

  // Spinner (hidden by default)
  const spinner = document.createElement("div");
  spinner.id = "hf-modelcard-grade-spinner";
  spinner.style.display = "none";
  badge.appendChild(spinner);

  // Label text
  const labelSpan = document.createElement("span");
  labelSpan.id = "hf-modelcard-grade-badge-label";
  labelSpan.textContent = text;
  badge.appendChild(labelSpan);

  // Click behavior:
  // - If we haven't graded yet -> start grading
  // - If we have a result -> toggle panel
  badge.addEventListener("click", async () => {
    // Any click removes the glow (if present)
    const badgeEl = document.getElementById("hf-modelcard-grade-badge");
    if (badgeEl) {
      badgeEl.classList.remove("hf-modelcard-badge-pulse");
    }

    if (isGrading) return;

    if (!lastGradeData) {
      await maybeStartEvaluation();
    } else {
      panelVisible = !panelVisible;
      togglePanelVisibility(panelVisible, lastGradeData);
    }
  });

  document.body.appendChild(badge);
  return badge;
}

function updateBadge(text, dotColor) {
  let badge = document.getElementById("hf-modelcard-grade-badge");
  if (!badge) {
    badge = createBadge(text);
  }

  const labelSpan = document.getElementById("hf-modelcard-grade-badge-label");
  if (labelSpan) labelSpan.textContent = text;

  if (dotColor) {
    const dotEl = document.getElementById("hf-modelcard-grade-badge-dot");
    if (dotEl) {
      dotEl.style.background = dotColor;
    }
  }
}

function setSpinnerVisible(show) {
  const spinner = document.getElementById("hf-modelcard-grade-spinner");
  if (spinner) {
    spinner.style.display = show ? "inline-block" : "none";
  }
}

function startAttentionGlow() {
  const badge = document.getElementById("hf-modelcard-grade-badge");
  if (!badge) return;
  badge.classList.add("hf-modelcard-badge-pulse");
}

/* ---------------- Panel ---------------- */

function createPanel() {
  const panel = document.createElement("div");
  panel.id = "hf-modelcard-grade-panel";

  panel.style.position = "fixed";
  panel.style.top = "72px";
  panel.style.right = "20px";
  panel.style.width = "360px";
  panel.style.maxHeight = "80vh";
  panel.style.background = "white";
  panel.style.color = "#111827"; // gray-900
  panel.style.borderRadius = "14px";
  panel.style.boxShadow = "0 18px 40px rgba(15,23,42,0.45)";
  panel.style.zIndex = "999998";
  panel.style.fontFamily = "system-ui, -apple-system, BlinkMacSystemFont, sans-serif";
  panel.style.display = "none";
  panel.style.overflow = "hidden";
  panel.style.border = "1px solid #e5e7eb";

  const header = document.createElement("div");
  header.style.display = "flex";
  header.style.justifyContent = "space-between";
  header.style.alignItems = "center";
  header.style.padding = "10px 14px";
  header.style.borderBottom = "1px solid #e5e7eb";
  header.style.background = "linear-gradient(135deg, #f9fafb, #e5e7eb)";

  const title = document.createElement("div");
  title.id = "hf-modelcard-panel-title";
  title.style.fontWeight = "600";
  title.style.fontSize = "13px";
  title.textContent = "Model card audit";

  const closeBtn = document.createElement("button");
  closeBtn.textContent = "×";
  closeBtn.style.border = "none";
  closeBtn.style.background = "transparent";
  closeBtn.style.fontSize = "18px";
  closeBtn.style.cursor = "pointer";
  closeBtn.style.lineHeight = "1";
  closeBtn.style.color = "#6b7280";
  closeBtn.addEventListener("click", () => {
    panelVisible = false;
    togglePanelVisibility(false, lastGradeData);
  });

  header.appendChild(title);
  header.appendChild(closeBtn);

  const content = document.createElement("div");
  content.id = "hf-modelcard-panel-content";
  content.style.padding = "10px 14px";
  content.style.fontSize = "12px";
  content.style.overflowY = "auto";
  content.style.maxHeight = "calc(80vh - 44px)";

  panel.appendChild(header);
  panel.appendChild(content);

  document.body.appendChild(panel);
  return panel;
}

function getOrCreatePanel() {
  let panel = document.getElementById("hf-modelcard-grade-panel");
  if (!panel) {
    panel = createPanel();
  }
  return panel;
}

function togglePanelVisibility(show, data) {
  const panel = getOrCreatePanel();
  panel.style.display = show ? "block" : "none";
  if (show && data) {
    renderPanelContent(data);
  }
}

function renderPanelContent(data) {
  const content = document.getElementById("hf-modelcard-panel-content");
  if (!content) return;
  content.innerHTML = "";

  const {
    score,
    raw_total,
    max_total,
    label,
    details,
    basic_info,
    category_scores,
    standards_summary,
    gaps,
    filled_markdown,
  } = data;

  /* --- Basic info / header --- */
  const titleBlock = document.createElement("div");
  titleBlock.style.marginBottom = "8px";

  if (basic_info && (basic_info.title || basic_info.url)) {
    const title = document.createElement("div");
    title.style.fontWeight = "600";
    title.style.fontSize = "13px";
    title.style.marginBottom = "2px";
    title.textContent = basic_info.title || (basic_info.url || "Hugging Face model");

    titleBlock.appendChild(title);

    if (basic_info.url) {
      const link = document.createElement("a");
      link.href = basic_info.url;
      link.textContent = "View on Hugging Face";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.style.fontSize = "11px";
      link.style.color = "#2563eb";
      titleBlock.appendChild(link);
    }
  } else {
    const fallback = document.createElement("div");
    fallback.textContent = "Model card audit";
    fallback.style.fontWeight = "600";
    fallback.style.fontSize = "13px";
    titleBlock.appendChild(fallback);
  }

  if (basic_info && (basic_info.type || basic_info.owner || basic_info.version)) {
    const meta = document.createElement("div");
    meta.style.fontSize = "11px";
    meta.style.color = "#6b7280";
    const bits = [];
    if (basic_info.type) bits.push(basic_info.type);
    if (basic_info.owner) bits.push(`Owner: ${basic_info.owner}`);
    if (basic_info.version) bits.push(basic_info.version);
    meta.textContent = bits.join(" • ");
    titleBlock.appendChild(meta);
  }

  content.appendChild(titleBlock);

  /* --- Overall score --- */
  const overallBlock = document.createElement("div");
  overallBlock.style.display = "flex";
  overallBlock.style.alignItems = "center";
  overallBlock.style.justifyContent = "space-between";
  overallBlock.style.marginBottom = "8px";

  const left = document.createElement("div");
  const scoreLabel = document.createElement("div");
  scoreLabel.style.fontSize = "11px";
  scoreLabel.style.color = "#6b7280";
  scoreLabel.textContent = "Overall score";

  const scoreValue = document.createElement("div");
  scoreValue.style.fontSize = "22px";
  scoreValue.style.fontWeight = "700";

  let badgeColor = "#6b7280";
  if (typeof score === "number") {
    scoreValue.textContent = score.toFixed(0);
    if (score >= 85) badgeColor = "#16a34a";
    else if (score >= 70) badgeColor = "#f97316";
    else badgeColor = "#dc2626";
  } else {
    scoreValue.textContent = "N/A";
  }

  const labelEl = document.createElement("div");
  labelEl.style.fontSize = "11px";
  labelEl.style.color = "#374151";
  labelEl.textContent = label ? label : "";

  left.appendChild(scoreLabel);
  left.appendChild(scoreValue);
  if (labelEl.textContent) left.appendChild(labelEl);

  const right = document.createElement("div");
  right.style.flexShrink = "0";
  right.style.marginLeft = "8px";

  const barOuter = document.createElement("div");
  barOuter.style.width = "130px";
  barOuter.style.height = "6px";
  barOuter.style.borderRadius = "999px";
  barOuter.style.background = "#e5e7eb";
  barOuter.style.overflow = "hidden";

  const barInner = document.createElement("div");
  barInner.style.height = "100%";
  barInner.style.borderRadius = "999px";
  barInner.style.background = badgeColor;
  barInner.style.width = typeof score === "number" ? `${Math.max(5, Math.min(100, score))}%` : "0%";

  barOuter.appendChild(barInner);
  right.appendChild(barOuter);

  overallBlock.appendChild(left);
  overallBlock.appendChild(right);
  content.appendChild(overallBlock);

  if (details) {
    const detailsEl = document.createElement("div");
    detailsEl.style.fontSize = "11px";
    detailsEl.style.color = "#6b7280";
    detailsEl.style.marginBottom = "8px";
    detailsEl.textContent = details;
    content.appendChild(detailsEl);
  }

  /* --- Category breakdown --- */
  if (Array.isArray(category_scores) && category_scores.length > 0) {
    const catTitle = document.createElement("div");
    catTitle.style.fontSize = "11px";
    catTitle.style.fontWeight = "600";
    catTitle.style.margin = "8px 0 4px";
    catTitle.textContent = "Category scores (0–3)";
    content.appendChild(catTitle);

    const list = document.createElement("div");
    list.style.display = "grid";
    list.style.gridTemplateColumns = "1fr 1fr";
    list.style.gap = "4px 8px";
    list.style.marginBottom = "6px";

    category_scores.forEach((cat) => {
      const item = document.createElement("div");
      item.style.display = "flex";
      item.style.alignItems = "center";
      item.style.justifyContent = "space-between";
      item.style.fontSize = "11px";

      const nameEl = document.createElement("span");
      nameEl.textContent = cat.name;

      const rightEl = document.createElement("span");
      rightEl.style.display = "inline-flex";
      rightEl.style.alignItems = "center";
      rightEl.style.gap = "4px";

      const dot = document.createElement("span");
      dot.style.width = "8px";
      dot.style.height = "8px";
      dot.style.borderRadius = "999px";

      const val = typeof cat.score === "number" ? cat.score : null;
      let dotColor = "#9ca3af";
      if (val === 3) dotColor = "#16a34a";
      else if (val === 2) dotColor = "#f97316";
      else if (val === 1) dotColor = "#facc15";
      else if (val === 0) dotColor = "#dc2626";
      dot.style.background = dotColor;

      const scoreText = document.createElement("span");
      scoreText.textContent = val !== null ? val.toString() : "-";

      rightEl.appendChild(dot);
      rightEl.appendChild(scoreText);

      item.appendChild(nameEl);
      item.appendChild(rightEl);
      list.appendChild(item);
    });

    content.appendChild(list);
  }

  /* --- Standards coverage --- */
  if (
    standards_summary &&
    typeof standards_summary.total_items === "number" &&
    standards_summary.total_items > 0
  ) {
    const stTitle = document.createElement("div");
    stTitle.style.fontSize = "11px";
    stTitle.style.fontWeight = "600";
    stTitle.style.margin = "8px 0 4px";
    stTitle.textContent = "Standards coverage";
    content.appendChild(stTitle);

    const chips = document.createElement("div");
    chips.style.display = "flex";
    chips.style.flexWrap = "wrap";
    chips.style.gap = "4px";
    chips.style.marginBottom = "4px";

    function makeChip(label, value, bg, textColor) {
      const chip = document.createElement("span");
      chip.style.fontSize = "10px";
      chip.style.padding = "2px 6px";
      chip.style.borderRadius = "999px";
      chip.style.background = bg;
      chip.style.color = textColor;
      chip.textContent = `${label}: ${value}`;
      return chip;
    }

    chips.appendChild(makeChip("Present", standards_summary.present, "#dcfce7", "#166534"));
    chips.appendChild(makeChip("Partial", standards_summary.partial, "#fef3c7", "#92400e"));
    chips.appendChild(makeChip("Missing", standards_summary.missing, "#fee2e2", "#b91c1c"));

    content.appendChild(chips);

    if (Array.isArray(standards_summary.missing_items) && standards_summary.missing_items.length > 0) {
      const missTitle = document.createElement("div");
      missTitle.style.fontSize = "11px";
      missTitle.style.color = "#b91c1c";
      missTitle.style.marginTop = "4px";
      missTitle.textContent = "Missing items:";
      content.appendChild(missTitle);

      const ul = document.createElement("ul");
      ul.style.fontSize = "11px";
      ul.style.margin = "2px 0 4px 14px";
      standards_summary.missing_items.forEach((name) => {
        const li = document.createElement("li");
        li.textContent = name;
        ul.appendChild(li);
      });
      content.appendChild(ul);
    }
  }

  /* --- Gaps & recommendations --- */
  if (gaps && (gaps.missing || gaps.inconsistent || gaps.ambiguous)) {
    const gapsTitle = document.createElement("div");
    gapsTitle.style.fontSize = "11px";
    gapsTitle.style.fontWeight = "600";
    gapsTitle.style.margin = "8px 0 4px";
    gapsTitle.textContent = "Gaps & inconsistencies";
    content.appendChild(gapsTitle);

    const gapsList = document.createElement("div");
    gapsList.style.fontSize = "11px";
    gapsList.style.color = "#4b5563";

    function addGapBlock(label, text) {
      if (!text) return;
      const labelEl = document.createElement("div");
      labelEl.style.fontWeight = "600";
      labelEl.style.marginTop = "2px";
      labelEl.textContent = label;
      const bodyEl = document.createElement("div");
      bodyEl.textContent = text;
      gapsList.appendChild(labelEl);
      gapsList.appendChild(bodyEl);
    }

    addGapBlock("Missing:", gaps.missing);
    addGapBlock("Inconsistent / conflicting:", gaps.inconsistent);
    addGapBlock("Ambiguous:", gaps.ambiguous);

    content.appendChild(gapsList);
  }

  /* --- Full review toggle --- */
  if (filled_markdown) {
    const toggleBtn = document.createElement("button");
    toggleBtn.textContent = "View full model card review";
    toggleBtn.style.marginTop = "10px";
    toggleBtn.style.fontSize = "11px";
    toggleBtn.style.padding = "4px 8px";
    toggleBtn.style.borderRadius = "6px";
    toggleBtn.style.border = "1px solid #d1d5db";
    toggleBtn.style.background = "#f9fafb";
    toggleBtn.style.cursor = "pointer";
    toggleBtn.style.color = "#111827";

    const pre = document.createElement("pre");
    pre.textContent = filled_markdown;
    pre.style.fontSize = "11px";
    pre.style.marginTop = "6px";
    pre.style.padding = "6px";
    pre.style.background = "#f3f4f6";
    pre.style.borderRadius = "6px";
    pre.style.whiteSpace = "pre-wrap";
    pre.style.wordBreak = "break-word";
    pre.style.display = "none";

    toggleBtn.addEventListener("click", () => {
      const isVisible = pre.style.display === "block";
      pre.style.display = isVisible ? "none" : "block";
      toggleBtn.textContent = isVisible ? "View full model card review" : "Hide full model card review";
    });

    content.appendChild(toggleBtn);
    content.appendChild(pre);
  }
}

/* ---------------- Setup & grading ---------------- */

function setupEvaluationUI() {
  // Initial badge just prompts to start evaluation.
  updateBadge("Begin model card evaluation", "#22c55e");
  // Prepare panel (hidden until used)
  getOrCreatePanel();
}

async function maybeStartEvaluation() {
  // Check if we're on an active Model card tab
  if (!modelCardTabIsActive()) {
    updateBadge("Model card tab not active on this page", "#b91c1c");
    setSpinnerVisible(false);
    return;
  }

  await gradeCurrentPage();
}

async function gradeCurrentPage() {
  const url = window.location.href;
  isGrading = true;
  setSpinnerVisible(true);
  updateBadge("Grading model card…", "#fbbf24");

  try {
    const resp = await fetch("http://localhost:8000/grade", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error("Backend error:", text);
      updateBadge("Model card grade: backend error", "#b91c1c");
      return;
    }

    const data = await resp.json();
    lastGradeData = data;

    const score = data.score;
    const label = data.label || "";

    let dotColor = "#6b7280"; // default gray
    if (typeof score === "number") {
      if (score >= 85) dotColor = "#16a34a";
      else if (score >= 70) dotColor = "#f97316";
      else dotColor = "#dc2626";
    }

    let summary;
    if (typeof score === "number") {
      summary = `Model card score: ${score.toFixed(0)}`;
      if (label) summary += ` (${label})`;
      summary += " – click to open audit";
    } else {
      summary = "Model card score: N/A – click to open audit";
    }

    updateBadge(summary, dotColor);
    // After grading finishes, glow until user clicks
    startAttentionGlow();
  } catch (err) {
    console.error("Failed to grade page:", err);
    updateBadge("Model card grade: request failed", "#b91c1c");
  } finally {
    isGrading = false;
    setSpinnerVisible(false);
  }
}
