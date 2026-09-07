(async () => {
  await browser.storage.local.set({
    activateOn: (await browser.storage.local.get('activateOn')).activateOn ?? 'https://doc.rust-lang.org/',
    previous: (await browser.storage.local.get('previous')).previous ?? 'perchance',
  });

  browser.runtime.onMessage.addListener(async (data, sender) => {
    if (data.message.type === 'updateLastUrl') {
      await browser.storage.local.set({
        previous: data.message.lastPage,
      });
    }
  });

  browser.webNavigation.onCompleted.addListener((e) => {
    browser.storage.local.get('activateOn').then((cfg) => {
      const activateOn = cfg.activateOn;
      if (!e.url.startsWith(activateOn) || !e.url.includes('https://doc.rust-lang.org/')) {
        return;
      }

      browser.scripting.executeScript({
        target: {
          tabId: e.tabId,
        },
        files: ['assets/cs.js'],
      });
    });
  });
})();
