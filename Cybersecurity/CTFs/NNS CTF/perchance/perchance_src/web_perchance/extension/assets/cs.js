(async () => {
  const prev = (await browser.storage.local.get('previous')).previous;
  const elm = document.createElement('p');
  elm.innerHTML = `Previous: ${prev}`;
  document.body.appendChild(elm);

  // do not load dependencies in trusted context of the extension
  const nonce = 'a' + crypto.randomUUID().replaceAll('-', '');
  const scr = document.createElement('script');
  scr.type = 'module';
  scr.textContent = `import ${nonce} from 'http://localhost:3000/jsxss.js';
window['${nonce}']=${nonce}`;
  document.body.appendChild(scr);

  function r() {
    if (!window.wrappedJSObject[nonce]) {
      setTimeout(r, 1);
    } else {
      browser.runtime.sendMessage({
        message: {
          type: 'updateLastUrl',
          lastPage: window.wrappedJSObject[nonce](location.href),
        },
      });
    }
  }
  r();
})();
