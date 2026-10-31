# Functional checks of the interactions in site.js (keyboard, focus, Esc, wrap-around).
#   python3 tools/parity/behaviour.py <site_dir>
import asyncio, sys
from playwright.async_api import async_playwright
from serve import serve
from shots import block_external

results = []
def check(name, ok, detail=''):
    results.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f'  ({detail})' if detail else ''))

async def main(root):
    with serve(root) as base:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
            ctx = lambda w: b.new_context(viewport={'width': w, 'height': 800})
            # skip link
            c = await ctx(1440); await block_external(c); pg = await c.new_page()
            await pg.goto(base + '/bottleshop/', wait_until='networkidle')
            await pg.keyboard.press('Tab'); await pg.keyboard.press('Enter'); await pg.keyboard.press('Tab')
            inside = await pg.evaluate("!!document.activeElement.closest('main')")
            check('skip link moves focus into <main>', inside, await pg.evaluate('document.activeElement.outerHTML.slice(0,60)'))
            await c.close()
            # burger menu
            c = await ctx(768); await block_external(c); pg = await c.new_page()
            await pg.goto(base + '/', wait_until='networkidle')
            btn = pg.locator('.nav-toggle')
            await btn.focus(); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
            check('menu opens with Enter', await btn.get_attribute('aria-expanded') == 'true' and await pg.locator('.nav-menu').is_visible())
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
            check('Esc closes menu and returns focus', await btn.get_attribute('aria-expanded') == 'false'
                  and not await pg.locator('.nav-menu').is_visible()
                  and await pg.evaluate("document.activeElement.classList.contains('nav-toggle')"))
            await btn.click(); await pg.wait_for_timeout(500); await btn.click(); await pg.wait_for_timeout(500)
            check('second click closes menu', not await pg.locator('.nav-menu').is_visible())
            await c.close()
            # nav hide/show
            c = await ctx(1440); await block_external(c); pg = await c.new_page()
            await pg.goto(base + '/bottleshop/', wait_until='networkidle')
            await pg.mouse.wheel(0, 600); await pg.wait_for_timeout(600)
            down = await pg.evaluate("getComputedStyle(document.querySelector('.navigation-max-width')).transform")
            await pg.mouse.wheel(0, -200); await pg.wait_for_timeout(600)
            up = await pg.evaluate("getComputedStyle(document.querySelector('.navigation-max-width')).transform")
            check('nav hides on scroll down, returns on scroll up', '-72' in down and up in ('none', 'matrix(1, 0, 0, 1, 0, 0)'), f'{down} / {up}')
            await c.close()
            # artist dialog
            c = await ctx(1440); await block_external(c); pg = await c.new_page()
            await pg.goto(base + '/winzer/beck/', wait_until='networkidle')
            opener = pg.locator('[data-dialog-open]')
            await opener.focus(); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(700)
            check('dialog opens from keyboard, focus inside', await pg.evaluate("document.querySelector('#kuenstler').open && !!document.activeElement.closest('#kuenstler')"))
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(700)
            check('Esc closes dialog and focus returns to the link', await pg.evaluate("!document.querySelector('#kuenstler').open && document.activeElement.hasAttribute('data-dialog-open')"))
            await opener.click(); await pg.wait_for_timeout(700)
            await pg.locator('.div-schliessen').click(); await pg.wait_for_timeout(700)
            check('"schliessen" closes dialog', await pg.evaluate("!document.querySelector('#kuenstler').open"))
            await c.close()
            # slider
            c = await ctx(1440); await block_external(c); pg = await c.new_page()
            await pg.goto(base + '/neues/', wait_until='networkidle')
            s = pg.locator('.w-slider').first
            n = await s.locator('.w-slide').count()
            active = lambda: s.evaluate("e => [...e.querySelectorAll('.w-slider-dot')].findIndex(d => d.classList.contains('w-active'))")
            await s.locator('.w-slider-arrow-left').click(); await pg.wait_for_timeout(700)
            check('slider wraps backwards to the last image', await active() == n - 1, f'{n} slides')
            await s.locator('.w-slider-arrow-right').click(); await pg.wait_for_timeout(700)
            check('slider wraps forwards to the first image', await active() == 0)
            await s.locator('.w-slider-dot').nth(2).click(); await pg.wait_for_timeout(700)
            x = await s.evaluate("e => e.querySelectorAll('.w-slide')[2].getBoundingClientRect().x - e.getBoundingClientRect().x")
            check('dot 3 shows image 3 in place', await active() == 2 and abs(x) < 1, f'offset {x}')
            await c.close()
            # lightbox, multi-image group
            c = await ctx(1440); await block_external(c); pg = await c.new_page()
            found = None
            for page in ['/neues/'] + [f'/neues/{i}/' for i in range(2, 15)]:
                await pg.goto(base + page, wait_until='networkidle')
                if await pg.locator('.lightbox-link').count():
                    found = page; break
            t = pg.locator('.blog-einzelbild').filter(has=pg.locator('xpath=..')).first
            grp = await pg.locator('.lightbox-link').first.get_attribute('data-lightbox')
            first = pg.locator(f'.blog-einzelbild[data-lightbox="{grp}"]')
            await first.scroll_into_view_if_needed(); await first.click(); await pg.wait_for_timeout(800)
            items = await pg.locator('.w-lightbox-strip .w-lightbox-item').count()
            check('lightbox opens with thumbnail strip for a group', items >= 2, f'{found}, {items} images')
            await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(500)
            check('arrow key shows next image', await pg.evaluate("document.querySelectorAll('.w-lightbox-item')[1].classList.contains('w-lightbox-active')"))
            await pg.screenshot(path='/home/claude/parity/report/schritt6-lightbox-gruppe-neu.png')
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(600)
            check('Esc closes lightbox and unlocks scrolling', await pg.evaluate("!document.querySelector('dialog.w-lightbox-backdrop').open && !document.body.classList.contains('w-lightbox-noscroll')"))
            await c.close()
            await b.close()
    print(f'{sum(results)}/{len(results)} passed')
    return all(results)

if __name__ == '__main__':
    sys.exit(0 if asyncio.run(main(sys.argv[1])) else 1)
