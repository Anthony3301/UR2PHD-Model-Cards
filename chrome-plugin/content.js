// Runs on Hugging Face pages and asks the backend to grade the current URL
if (window.location.hostname === "huggingface.co") {
  gradeCurrentPage();
}

function createBadge(text) {
  const badge = document.createElement("div");
  badge.id = "hf-modelcard-grade-badge";
  badge.textContent = text;

  badge.style.position = "fixed";
  badge.style.bottom = "12px";
  badge.style.right = "12px";
  badge.style.padding = "8px 12px";
  badge.style.background = "rgba(0, 0, 0, 0.85)";
  badge.style.color = "white";
  badge.style.fontSize = "12px";
  badge.style.borderRadius = "6px";
  badge.style.zIndex = "999999";
  badge.style.fontFamily = "system-ui, -apple-system, BlinkMacSystemFont, sans-serif";
  badge.style.boxShadow = "0 2px 6px rgba(0,0,0,0.4)";
  badge.style.maxWidth = "260px";
  badge.style.lineHeight = "1.4";
  badge.style.cursor = "default";

  document.body.appendChild(badge);
  return badge;
}

function updateBadge(text, color) {
  let badge = document.getElementById("hf-modelcard-grade-badge");
  if (!badge) {
    badge = createBadge(text);
  } else {
    badge.textContent = text;
  }
  if (color) {
    badge.style.background = color;
  }
}

async function gradeCurrentPage() {
  const url = window.location.href;

  // Optional: restrict to model pages only, if you want
  // if (!/^https:\/\/huggingface\.co\/[^\/]+\/[^\/]+\/?$/.test(url)) return;

  updateBadge("Grading model card…");

  try {
    const resp = await fetch("http://localhost:8000/grade", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error("Backend error:", text);
      updateBadge("Model card grade: backend error", "#b00020");
      return;
    }

    const data = await resp.json();
    const score = data.score;   // may be null if regex fails
    const label = data.label || "";
    const details = data.details || "";

    let bg = "#374151"; // default gray
    if (typeof score === "number") {
      if (score >= 85) bg = "#166534";      
      else if (score >= 70) bg = "#92400e"; 
      else bg = "#b91c1c";                 
    }

    let summary;
    if (typeof score === "number") {
      summary = `Model card score: ${score.toFixed(0)}`;
      if (label) summary += ` (${label})`;
    } else {
      summary = "Model card score: N/A";
    }
    if (details) summary += ` – ${details}`;

    updateBadge(summary, bg);
  } catch (err) {
    console.error("Failed to grade page:", err);
    updateBadge("Model card grade: request failed", "#b00020");
  }
}