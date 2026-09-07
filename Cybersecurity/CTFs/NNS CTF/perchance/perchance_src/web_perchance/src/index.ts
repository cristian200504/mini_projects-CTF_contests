import { runBrowser } from './browser';
import homepage from './homepage.html';
import jsxss from './jsxss' with { type: 'file' };
// @ts-ignore
import perchance from './perchance.png' with { type: 'file' };
import robots from './robots.txt' with { type: 'file' };

let inUse = false;

const server = Bun.serve({
  routes: {
    '/': homepage,
    '/robots.txt': new Response(await Bun.file(robots).bytes()),
    '/jsxss.js': new Response(await Bun.file(jsxss).bytes(), {
      headers: {
        'Content-Type': 'text/javascript',
        'Access-Control-Allow-Origin': '*',
      },
    }),
    '/perchance.png': new Response(await Bun.file(perchance).bytes()),
    '/perchance': {
      async POST(req) {
        if (inUse) {
          return Response.json({ ok: false, error: 'Browser is in use' }, { status: 429 });
        }

        const form = await req.formData();
        const url = form.get('perchance')?.toString();

        if (!url || !url.startsWith('https://doc.rust-lang.org')) {
          return Response.json({ ok: false, error: 'Bad url' }, { status: 400 });
        }

        try {
          inUse = true;
          console.log(`[perchance] visiting ${url}`);
          await runBrowser(url);
          console.log(`[perchance] finished visiting ${url}`);
          inUse = false;
        } catch (e) {
          console.log(`[perchance] [ERROR]`, e);
        }
        return Response.json({
          ok: true,
        });
      },
    },
  },
});

console.log(`[perchance] listening on ${server.url}`);
