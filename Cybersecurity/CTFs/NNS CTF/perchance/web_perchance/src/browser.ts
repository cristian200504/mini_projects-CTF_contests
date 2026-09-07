import { firefox } from 'playwright';
import { withExtension } from 'playwright-webextext';

export async function runBrowser(target: string) {
  const browserTypeWithExtension = withExtension(firefox, '/app/extension');
  const browser = await browserTypeWithExtension.launch({
    headless: true,
    firefoxUserPrefs: {
      'extensions.webextensions.uuids': JSON.stringify({
        'perchance@2026.nnsc.tf': '09a6c422-a354-447d-b4ea-185cb10be869',
      }),
    },
  });
  try {
    const context = await browser.newContext();
    await context.addCookies([
      {
        name: 'flag',
        value: process.env.FLAG ?? 'NNS{example_flag}',
        domain: 'doc.rust-lang.org',
        path: '/stable/std/',
        httpOnly: false,
        sameSite: 'Strict',
      },
    ]);

    const page = await context.newPage();
    await page.goto(target);
    await Bun.sleep(1000 * 40); // 40s
    await context.close();
  } finally {
    await browser.close();
  }
}
