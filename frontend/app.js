const form = document.querySelector("#story-form");
const statusMessage = document.querySelector("#status");
const storyCard = document.querySelector("#story-card");
const storyText = document.querySelector("#story-text");
const storyName = document.querySelector("#story-name");
const copyButton = document.querySelector("#copy-button");
const againButton = document.querySelector("#again-button");
const submitButton = form.querySelector("button[type='submit']");

let latestStory = "";

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = value;
  return element.innerHTML;
}

function renderStory(story) {
  const paragraphs = story.split("\n\n").filter(Boolean);
  storyText.innerHTML = paragraphs.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusMessage.textContent = "";

  const lambdaUrl = window.APP_CONFIG?.LAMBDA_URL;
  if (!lambdaUrl || lambdaUrl.includes("PASTE_YOUR")) {
    statusMessage.textContent = "Add your Lambda Function URL to frontend/config.js first.";
    return;
  }

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  submitButton.disabled = true;
  submitButton.querySelector(".button-label").textContent = "Gathering stardust…";

  try {
    const response = await fetch(lambdaUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The cloud could not create this tale.");

    latestStory = result.story;
    storyName.textContent = payload.name;
    renderStory(latestStory);
    storyCard.hidden = false;
    storyCard.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    statusMessage.textContent = error.message || "Something interrupted the magic. Please try again.";
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector(".button-label").textContent = "Create my tiny tale";
  }
});

copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(latestStory);
  copyButton.textContent = "Copied!";
  setTimeout(() => { copyButton.textContent = "Copy story"; }, 1600);
});

againButton.addEventListener("click", () => {
  storyCard.hidden = true;
  form.scrollIntoView({ behavior: "smooth", block: "center" });
});
