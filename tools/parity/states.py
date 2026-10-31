# Viewport screenshots of the interactive states, with motion ON.
#   python3 tools/parity/states.py <site_dir> <out_dir>
# Each state lists several selectors: the Webflow markup first, then the rebuilt
# markup, so the same script works on the baseline and on every later step.
import asyncio, os, sys
from playwright.async_api import async_playwright
from serve import serve
from shots import block_external

MENU = '.w-nav-button, .nav-toggle'
MODAL_OPEN = '[data-ix="modal-window-open"], [data-dialog-open]'
SLIDER_NEXT = '.w-slider-arrow-right, .slider__next'
LIGHTBOX = '.blog-einzelbild'
THUMB = '.post-thumb-image'


async def first(pg, sel):
    loc = pg.locator(sel).first
    await loc.wait_for(state='attached', timeout=5000)
    return loc


async def settle(pg, ms=1200):
    await pg.wait_for_timeout(ms)
    await pg.evaluate('document.fonts.ready')


async def run(b, base, out):
    async def ctx(vw, h=900):
        c = await b.new_context(viewport={'width': vw, 'height': h})
        await block_external(c)
        return c, await c.new_page()

    async def go(pg, url):
        await pg.goto(base + url, wait_until='networkidle')
        await settle(pg, 600)

    async def save(pg, name, **kw):
        await pg.screenshot(path=os.path.join(out, name + '.png'), **kw)

    # 1 Burger menu open (tablet + phone)
    for vw in (768, 390):
        c, pg = await ctx(vw)
        await go(pg, '/')
        await (await first(pg, MENU)).click()
        await settle(pg)
        await save(pg, f'state-menu-open@{vw}')
        await c.close()

    # 2 Nav hidden after scrolling down, shown again after scrolling up
    c, pg = await ctx(1440)
    await go(pg, '/bottleshop/')
    await pg.mouse.wheel(0, 900); await settle(pg)
    await save(pg, 'state-nav-scrolled-down@1440')
    await pg.mouse.wheel(0, -300); await settle(pg)
    await save(pg, 'state-nav-scrolled-up@1440')
    await c.close()

    # 3 Thumbnail hover zoom
    c, pg = await ctx(1440)
    await go(pg, '/')
    t = await first(pg, THUMB)
    await t.scroll_into_view_if_needed(); await settle(pg, 900)
    box = await t.bounding_box()
    await pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    await settle(pg, 600)
    await save(pg, 'state-thumb-hover@1440', clip={'x': box['x'] - 20, 'y': box['y'] - 20,
                                                    'width': box['width'] + 40, 'height': box['height'] + 40})
    await c.close()

    # 4 Parallax on the homepage bar photo at three scroll positions
    c, pg = await ctx(1440)
    await go(pg, '/')
    top = await pg.evaluate("(() => { const e = document.querySelector('.wrapper-image-divider, .parallax');"
                            " return e ? e.parentElement.getBoundingClientRect().top + scrollY : 0 })()")
    for i, dy in enumerate((-700, -300, 100)):
        await pg.evaluate(f'window.scrollTo(0, {max(0, top + dy)})')
        await settle(pg, 1500)
        await save(pg, f'state-parallax-{i + 1}@1440')
    await c.close()

    # 5 Artist modal open
    for vw in (1440, 390):
        c, pg = await ctx(vw)
        await go(pg, '/winzer/beck/')
        o = await first(pg, MODAL_OPEN)
        await o.scroll_into_view_if_needed(); await settle(pg, 600)
        await o.click(); await settle(pg)
        await save(pg, f'state-modal-open@{vw}')
        await c.close()

    # 6 Slider on slide 2
    c, pg = await ctx(1440)
    await go(pg, '/neues/')
    nxt = await first(pg, SLIDER_NEXT)
    await nxt.scroll_into_view_if_needed(); await settle(pg, 600)
    await save(pg, 'state-slider-1@1440')
    await nxt.click(); await settle(pg)
    await save(pg, 'state-slider-2@1440')
    await c.close()

    # 7 Lightbox open
    for vw in (1440, 390):
        c, pg = await ctx(vw)
        await go(pg, '/neues/')
        lb = await first(pg, LIGHTBOX)
        await lb.scroll_into_view_if_needed(); await settle(pg, 600)
        await lb.click(); await settle(pg)
        await save(pg, f'state-lightbox-open@{vw}')
        await c.close()


async def main(root, out):
    os.makedirs(out, exist_ok=True)
    with serve(root) as base:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
            await run(b, base, out)
            await b.close()
    print('states ->', out)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], sys.argv[2]))
