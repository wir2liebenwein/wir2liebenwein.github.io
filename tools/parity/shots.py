# Full-page screenshots of every built page at 1440 / 768 / 390 px.
#   python3 tools/parity/shots.py <site_dir> <out_dir> [url-substring ...]
# Serves <site_dir> itself on a free port. Motion is reduced so the shots are stable.
import asyncio, glob, os, sys
from playwright.async_api import async_playwright
from serve import serve

# Override with PARITY_WIDTHS="1440,768,600,390" (600 px covers the 480–767 band).
WIDTHS = tuple(int(w) for w in os.environ.get('PARITY_WIDTHS', '1440,768,600,390').split(','))
CONCURRENCY = 4


def page_urls(root):
    urls = set()
    for p in glob.glob(os.path.join(root, '**', '*.html'), recursive=True):
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        urls.add('/' + (rel[:-len('index.html')] if rel.endswith('index.html') else rel))
    return sorted(urls)


# Every image is switched to eager loading before the shot (no visual effect), so
# the page height never depends on how far lazy loading got.
ALL_IMAGES_LOADED = '[...document.images].every(i => i.complete)'

# Changes while something is still moving: page height, scroll-driven inline transforms.
MOTION_SIGNATURE = """[document.documentElement.scrollHeight,
  ...[...document.querySelectorAll('[style*="transform"], header, .navigation-max-width, .wrapper-image-divider')]
     .map(e => getComputedStyle(e).transform + getComputedStyle(e).opacity)].join('|')"""


async def wait_still(pg, poll=250, max_ms=5000):
    last, waited = None, 0
    while waited < max_ms:
        sig = await pg.evaluate(MOTION_SIGNATURE)
        if sig == last:
            return
        last = sig
        await pg.wait_for_timeout(poll); waited += poll


async def block_external(ctx):
    # Only the local site is loaded; the YouTube embed on /pannobile/ stays an empty frame.
    await ctx.route(lambda url: not url.startswith('http://127.0.0.1'), lambda route: route.abort())


def shot_name(url, vw):
    return (url.strip('/').replace('/', '_') or 'home') + f'@{vw}.png'


async def shoot(ctx, base, url, out, vw):
    pg = await ctx.new_page()
    await pg.goto(base + url, wait_until='networkidle')
    await pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
    try:
        await pg.wait_for_function(ALL_IMAGES_LOADED, timeout=20000)
    except Exception:
        missing = await pg.evaluate('[...document.images].filter(i => !i.complete).map(i => i.src)')
        print('WARN images not loaded on', url, vw, missing[:3])
    h = await pg.evaluate('document.documentElement.scrollHeight')
    for y in range(0, h, 800):                      # run scroll-triggered interactions once
        await pg.evaluate(f'window.scrollTo(0,{y})')
        await pg.wait_for_timeout(40)
    await pg.evaluate('window.scrollTo(0,0)')
    await pg.wait_for_timeout(700)                  # let the nav slide back in
    await wait_still(pg)
    await pg.evaluate('document.fonts.ready')
    # Chrome's full-page capture occasionally paints a band twice; keep shooting until
    # two captures in a row agree.
    prev = await pg.screenshot(full_page=True)
    for _ in range(4):
        cur = await pg.screenshot(full_page=True)
        if cur == prev:
            break
        prev = cur
    else:
        print('WARN unstable screenshot', url, vw)
    open(os.path.join(out, shot_name(url, vw)), 'wb').write(cur)
    await pg.close()


async def main(root, out, filters):
    os.makedirs(out, exist_ok=True)
    urls = [u for u in page_urls(root) if not filters or any(f in u for f in filters)]
    with serve(root) as base:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
            for vw in WIDTHS:
                ctx = await b.new_context(viewport={'width': vw, 'height': 900}, reduced_motion='reduce')
                await block_external(ctx)
                sem = asyncio.Semaphore(CONCURRENCY)

                async def one(u):
                    async with sem:
                        await shoot(ctx, base, u, out, vw)
                await asyncio.gather(*(one(u) for u in urls))
                await ctx.close()
            await b.close()
    print(f'{len(urls) * len(WIDTHS)} screenshots -> {out}')


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3:]))
