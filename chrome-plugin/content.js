// Grab all visible text on the page (simple / naive approach)
const pageText = document.body.innerText || "";

// Example: do something with it -> count words
function countWords(text) {
  return text
    .split(/\s+/)
    .map(t => t.trim())
    .filter(Boolean).length;
}

const wordCount = countWords(pageText);
console.log("[Page Text Reader] Word count:", wordCount);

// Create a small floating badge in the corner
const badge = document.createElement("div");
badge.textContent = `Words on this page: ${wordCount}`;


badge.style.position = "fixed";
badge.style.bottom = "10px";
badge.style.right = "10px";
badge.style.padding = "6px 10px";
badge.style.background = "rgba(0, 0, 0, 0.8)";
badge.style.color = "white";
badge.style.fontSize = "12px";
badge.style.borderRadius = "4px";
badge.style.zIndex = "999999";
badge.style.fontFamily = "sans-serif";

document.body.appendChild(badge);
