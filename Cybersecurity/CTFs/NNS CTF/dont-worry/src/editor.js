const id = location.pathname.split("/").pop();
const key = location.hash.slice(1);
const title = document.getElementById("title");
const source = document.getElementById("source");
const language = document.getElementById("language");
const raw = document.getElementById("raw");
const save = document.getElementById("save");
const status = document.getElementById("status");

fetch(`/api/documents/${id}?key=${encodeURIComponent(key)}&view=editor`)
  .then((res) => {
    if (!res.ok) throw new Error("unavailable");
    return res.json();
  })
  .then((data) => {
    title.value = data.title;
    source.value = data.body;
    language.value = data.language;
    title.disabled = false;
    source.disabled = false;
    language.disabled = false;
    save.disabled = false;
    document.getElementById("share").textContent =
      `${location.origin}/d/${id}#${key}`;
    raw.href = `/raw/${id}?key=${encodeURIComponent(key)}`;
    document.body.dataset.state = "loaded";
  })
  .catch(() => {
    status.textContent = "This document needs its key.";
    document.body.dataset.state = "denied";
  });

save.addEventListener("click", async () => {
  save.disabled = true;
  const res = await fetch(
    `/api/documents/${id}?key=${encodeURIComponent(key)}`,
    {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        title: title.value,
        body: source.value,
        language: language.value,
      }),
    },
  );
  status.textContent = res.ok ? "Saved." : "Could not save.";
  save.disabled = false;
});
