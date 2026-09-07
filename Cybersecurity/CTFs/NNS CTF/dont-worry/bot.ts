import { sleep } from "bun";
import { Challenge, type ChallengeContext } from "../src/types";

export const challenge = new Challenge({
  timeoutMilliseconds: 90_000,

  inputs: {
    url: {
      pattern: "^/",
    },
  },

  handler: async (ctx: ChallengeContext): Promise<void> => {
    const host = ctx.job.instancerInstances[0].host;
    const origin = `https://${host}`;

    const url = new URL(ctx.input.url!.trim(), origin);
    if (url.origin !== origin) {
      ctx.output.fatal("dont-worry", "url must be on this instance's origin", { url: url.href, origin });
      return;
    }

    const key = crypto.randomUUID();

    const editor = await ctx.browserContext.newPage();
    try {
      await editor.goto(origin, { waitUntil: "domcontentloaded" });
      const status = await editor.evaluate(async ([k, flag]: string[]) => {
        const r = await fetch(`/api/documents/welcome?key=${k}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ title: "Welcome", body: flag }),
        });
        return r.status;
      }, [key, ctx.job.flag]);
      if (status !== 200) {
        throw new Error(`put returned ${status}`);
      }
      await editor.goto(`${origin}/e/welcome#${key}`, {
        waitUntil: "domcontentloaded",
      });
      await editor.waitForFunction(
        () => document.body.dataset.state === "loaded",
        { timeout: 10_000 },
      );
    } catch (e) {
      ctx.output.fatal("dont-worry", `the document did not load: ${e}`, {});
      return;
    } finally {
      await editor.close();
    }

    await sleep(15_000);

    const page = await ctx.browserContext.newPage();
    try {
      await page.goto(url.href, { waitUntil: "domcontentloaded" });
    } catch (e) {
      ctx.output.fatal("dont-worry", `failed to visit url: ${e}`, { url: url.href });
      return;
    }

    await sleep(30_000);
    await page.close();
  },

  hooksConfig: {
    showConsoleLogs: true,
    showBrowserErrors: false,
    showNavigation: false,
    limitTabsNumber: 10,
  },

  browser: "chrome",
  browserArguments: [
    "--disable-jit",
    "--disable-wasm",
    "--disable-dev-shm-usage",
  ],
  maxLogValueChars: 4096,
  maxLogLines: 64,

  requireInstancerInstancesRunning: true,
});