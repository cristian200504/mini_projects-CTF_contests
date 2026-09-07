const id = location.pathname.split("/").pop();
const key = location.hash.slice(1);
const doc = document.getElementById("doc");

fetch(`/api/documents/${id}?key=${encodeURIComponent(key)}&view=reader`)
  .then((res) => {
    if (!res.ok) throw new Error("unavailable");
    return res.json();
  })
  .then((data) => {
    document.title = data.title;
    doc.innerHTML = data.body;
    Prism.highlightAllUnder(doc);
    document.body.dataset.state = "loaded";
  })
  .catch(() => {
    doc.textContent = "This document needs its key.";
    document.body.dataset.state = "denied";
  });
