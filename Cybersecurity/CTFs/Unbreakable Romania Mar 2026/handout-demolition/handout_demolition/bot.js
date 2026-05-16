const puppeteer = require("puppeteer");

const FIXED_FLAG =
  process.env.CHALL_DEMOLITION_FLAG ||
  "CTF{~~REDACTED~~}";

const CHALLENGE_ORIGIN =
  process.env.CHALL_DEMOLITION_URL ||  // On remote it's https://demolition.breakable.live
  process.env.CHALLENGE_ORIGIN ||
  "http://localhost:5050";

function buildLaunchOptions(browserConfig) {
  const args = [
    "--disable-dev-shm-usage",
    "--blink-settings=imagesEnabled=false",
    "--disable-popup-blocking",
  ];

  if (browserConfig.disableSandbox) {
    args.push("--no-sandbox", "--disable-setuid-sandbox");
  }

  const options = {
    headless: browserConfig.headless,
    timeout: browserConfig.launchTimeoutMs,
    args,
  };

  if (browserConfig.executablePath) {
    options.executablePath = browserConfig.executablePath;
  }

  return options;
}

module.exports = {
  name: "demolition",

  async execute(job, context) {
    const { url } = job;
    const { config, sleep } = context;
    const browser = await puppeteer.launch(buildLaunchOptions(config.browser));

    try {
      const page = await browser.newPage();

      try {
        page.setDefaultNavigationTimeout(config.browser.navigationTimeoutMs);

        await page.goto(CHALLENGE_ORIGIN, { waitUntil: "domcontentloaded" });
        await page.setCookie(
          {
            name: "FLAG",
            value: FIXED_FLAG,
            url: CHALLENGE_ORIGIN,
            httpOnly: false,
            sameSite: "Lax",
          }
        );

        await page.goto(url, { waitUntil: "domcontentloaded" });
        await sleep(5_000);
      } finally {
        await page.close().catch(() => {});
      }
    } finally {
      await browser.close().catch(() => {});
    }
  },
};
