# axe-core (wcag2a, wcag2aa, best-practice) over every page at 1440 px.
#   python3 tools/parity/axe.py <site_dir> <path/to/axe.min.js>
import asyncio, collections, sys
from playwright.async_api import async_playwright
from serve import serve
from shots import block_external, page_urls

async def main(root, axe):
    totals, pages = collections.Counter(), collections.defaultdict(set)
    with serve(root) as base:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
            c = await b.new_context(viewport={'width': 1440, 'height': 900}); await block_external(c)
            pg = await c.new_page()
            for u in page_urls(root):
                await pg.goto(base + u, wait_until='networkidle')
                await pg.add_script_tag(path=axe)
                res = await pg.evaluate("axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'best-practice']})")
                for v in res['violations']:
                    totals[v['id']] += len(v['nodes']); pages[v['id']].add(u)
            await b.close()
    for k, n in totals.most_common():
        print(f'{k:28} {n:4} nodes on {len(pages[k]):2} pages  e.g. {sorted(pages[k])[:2]}')
    print('total nodes:', sum(totals.values()))

asyncio.run(main(sys.argv[1], sys.argv[2]))
