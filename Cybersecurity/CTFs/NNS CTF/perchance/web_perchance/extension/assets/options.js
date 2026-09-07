async function updateConfig(new_url) {
  if (!new_url.match(/^https?:\/\//)) {
    return;
  }

  let u;
  try {
    u = new URL(new_url);
  } catch {
    document.querySelector('#err').textContent = 'Unable to parse URL';
    return;
  }
  if (!u.href.includes('https://doc.rust-lang.org/')) {
    document.querySelector('#err').textContent = 'URL must be doc.rust-lang.org.';
    return;
  }

  await browser.storage.local.set({
    activateOn: u.origin,
  });
  document.querySelector('#err').textContent = 'Saved.';
}

document.querySelector('form').addEventListener('submit', (e) => {
  e.preventDefault();
  updateConfig(document.querySelector('#x').value);
});

window.addEventListener(
  'message',
  function (e) {
    let str_data = e.data;
    if (str_data.match(/^https?/)) {
      updateConfig(str_data);
    }
  },
  false,
);
