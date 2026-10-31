/* wir2liebenwein.de – alles, was die Seite an JavaScript braucht (ersetzt jQuery + Webflow).
   Sieben Verhalten, Zeiten und Werte 1:1 aus den Webflow-Interactions übernommen:
   1 Burger-Menü  2 Navigation beim Scrollen  3 (Hover-Zoom ist reines CSS)
   4 Parallax auf der Startseite  5 Künstler-Dialog  6 Bild-Slider  7 Lightbox */
(function () {
  'use strict';

  var desktop = window.matchMedia('(min-width: 992px)');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var afterTransition = function (el, ms, fn) {
    var done = false;
    var finish = function () { if (!done) { done = true; el.removeEventListener('transitionend', finish); fn(); } };
    el.addEventListener('transitionend', finish);
    setTimeout(finish, ms + 50);
  };

  /* 1 Burger-Menü unter 992 px: klappt in 400 ms (ease) unter der Leiste auf. */
  (function () {
    var button = $('.nav-toggle'), menu = $('.nav-menu');
    if (!button || !menu) return;
    var links = $$('a', menu);
    function setOpen(open) {
      if (open === (button.getAttribute('aria-expanded') === 'true')) return;
      button.setAttribute('aria-expanded', String(open));
      button.classList.toggle('w--open', open);
      if (open) {
        menu.setAttribute('data-nav-menu-open', '');
        links.forEach(function (a) { a.classList.add('w--nav-link-open'); });
        menu.classList.remove('is-closing');
        menu.classList.add('is-opening');
        afterTransition(menu, 400, function () { menu.classList.remove('is-opening'); });
      } else {
        menu.classList.remove('is-opening');
        menu.classList.add('is-closing');
        afterTransition(menu, 400, function () {
          if (button.getAttribute('aria-expanded') === 'true') return;
          menu.classList.remove('is-closing');
          menu.removeAttribute('data-nav-menu-open');
          links.forEach(function (a) { a.classList.remove('w--nav-link-open'); });
        });
      }
    }
    button.addEventListener('click', function () { setOpen(button.getAttribute('aria-expanded') !== 'true'); });
    links.forEach(function (a) { a.addEventListener('click', function () { setOpen(false); }); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') { setOpen(false); button.focus(); }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.navbar')) setOpen(false);
    });
    desktop.addEventListener('change', function () { if (desktop.matches) setOpen(false); });
  })();

  /* 2 Navigation: beim Runterscrollen 72 px nach oben weg, beim Hochscrollen zurück (CSS). */
  (function () {
    var bar = $('.navigation-max-width');
    if (!bar) return;
    var lastY = window.scrollY;
    window.addEventListener('scroll', function () {
      var y = window.scrollY;
      if (y > lastY) bar.classList.add('is-hidden');
      else if (y < lastY) bar.classList.remove('is-hidden');
      lastY = y;
    }, { passive: true });
    // Tastatur: ein fokussierter Menüpunkt holt die Leiste zurück
    bar.addEventListener('focusin', function () { bar.classList.remove('is-hidden'); });
  })();

  /* 4 Parallax (nur Startseite, ab 992 px): das Barfoto wandert von -22 px nach -500 px,
     von "kommt unten ins Bild" bis "oben ganz verschwunden". Wie Webflow: pro Scroll-Ereignis
     wird das Ziel aus der aktuellen (schon verschobenen) Lage berechnet und dann in
     wenigen Frames angesteuert (Glättung 50). */
  (function () {
    var photo = $('.bar-photo'), wrap = $('.wrapper-image-divider');
    if (!photo || !wrap) return;
    var FROM = -22, TO = -500, current = FROM, goal = FROM, raf = 0;
    function frame() {
      raf = 0;
      current += (goal - current) * 0.5;
      if (Math.abs(goal - current) < 0.01) current = goal;
      wrap.style.transform = 'translate3d(0, ' + current + 'px, 0)';
      if (current !== goal) raf = requestAnimationFrame(frame);
    }
    function update() {
      if (!desktop.matches || reduce.matches) {   // Q8: keine Parallaxe bei reduzierter Bewegung
        cancelAnimationFrame(raf); raf = 0; current = goal = FROM; wrap.style.transform = ''; return;
      }
      var rect = photo.getBoundingClientRect(), vh = window.innerHeight;
      var p = Math.min(1, Math.max(0, (vh - rect.top) / (vh + rect.height)));
      goal = FROM + (TO - FROM) * p;
      if (!raf) raf = requestAnimationFrame(frame);
    }
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    desktop.addEventListener('change', update);
    reduce.addEventListener('change', update);
    if (photo.complete) update(); else photo.addEventListener('load', update);
  })();

  /* 5 Künstler-Dialog: Einblenden 500 ms (Deckkraft) + 200 ms (von 65 px oberhalb),
     Ausblenden 400 ms. Esc, Fokus und Hintergrund-Sperre liefert <dialog>. */
  (function () {
    $$('[data-dialog-open]').forEach(function (opener) {
      var dialog = document.getElementById(opener.getAttribute('data-dialog-open'));
      if (!dialog || !dialog.showModal) return;
      function close() {
        if (!dialog.open || dialog.classList.contains('is-closing')) return;
        dialog.classList.remove('is-open');
        dialog.classList.add('is-closing');
        afterTransition(dialog, 400, function () {
          dialog.classList.remove('is-closing');
          dialog.close();
          opener.focus();
        });
      }
      opener.addEventListener('click', function (e) {
        e.preventDefault();
        dialog.showModal();
        requestAnimationFrame(function () { requestAnimationFrame(function () { dialog.classList.add('is-open'); }); });
      });
      dialog.addEventListener('cancel', function (e) { e.preventDefault(); close(); });
      $$('[data-dialog-close]', dialog).forEach(function (b) { b.addEventListener('click', close); });
    });
  })();

  /* 6 Slider (Beiträge mit darstellung: slider): Pfeile, Punkte, Wischen; 500 ms, endlos. */
  $$('.w-slider').forEach(function (slider, n) {
    var mask = $('.w-slider-mask', slider), slides = $$('.w-slide', mask), count = slides.length;
    var prev = $('.w-slider-arrow-left', slider), next = $('.w-slider-arrow-right', slider);
    var nav = $('.w-slider-nav', slider), live = document.createElement('div');
    var index = 0, busy = false, dots = [];
    if (count < 2) return;
    live.className = 'visually-hidden'; live.setAttribute('aria-live', 'polite'); slider.appendChild(live);
    mask.id = mask.id || 'slider-' + (n + 1);
    slides.forEach(function (s, i) {
      s.setAttribute('role', 'group'); s.setAttribute('aria-roledescription', 'Bild');
      s.setAttribute('aria-label', (i + 1) + ' von ' + count);
      var dot = document.createElement('button');
      dot.type = 'button'; dot.className = 'w-slider-dot';
      dot.setAttribute('aria-label', 'Bild ' + (i + 1) + ' von ' + count + ' zeigen');
      dot.addEventListener('click', function () { go(i); });
      nav.appendChild(dot); dots.push(dot);
    });
    function width() { return mask.getBoundingClientRect().width; }
    function place(i, x, animate) {
      var s = slides[i].style;
      s.transition = animate && !reduce.matches ? 'transform 500ms ease' : 'none';
      s.transform = 'translateX(' + x + 'px)';
    }
    function mark() {
      slides.forEach(function (s, i) { s.toggleAttribute('aria-hidden', i !== index); s.inert = i !== index; });
      dots.forEach(function (d, i) { d.classList.toggle('w-active', i === index); d.setAttribute('aria-pressed', String(i === index)); });
      live.textContent = 'Bild ' + (index + 1) + ' von ' + count;
    }
    function go(to, dir) {
      if (busy || to === index) return;
      var w = width(), from = index;
      dir = dir || (to > from ? 1 : -1);
      var wrap = (dir > 0 && to < from) || (dir < 0 && to > from);
      busy = true;
      if (wrap) {
        // wie Webflow im Endlos-Modus: Ziel-Bild erst direkt neben das aktuelle legen,
        // dann gleiten beide gemeinsam um eine Breite
        place(to, dir * w - to * w, false);
        slides[to].getBoundingClientRect();
        slides.forEach(function (s, i) { place(i, i === to ? -to * w : -from * w - dir * w, true); });
      } else {
        slides.forEach(function (s, i) { place(i, -to * w, true); });
      }
      index = to; mark();
      setTimeout(function () {
        slides.forEach(function (s, i) { place(i, -to * w, false); });
        busy = false;
      }, reduce.matches ? 0 : 510);
    }
    prev.addEventListener('click', function () { go((index - 1 + count) % count, -1); });
    next.addEventListener('click', function () { go((index + 1) % count, 1); });
    var startX = null;
    mask.addEventListener('pointerdown', function (e) { startX = e.clientX; });
    mask.addEventListener('pointerup', function (e) {
      if (startX === null) return;
      var dx = e.clientX - startX; startX = null;
      if (Math.abs(dx) > 40) (dx < 0 ? next : prev).click();
    });
    window.addEventListener('resize', function () { slides.forEach(function (s, i) { place(i, -index * width(), false); }); });
    slides.forEach(function (s, i) { place(i, 0, false); });
    mark();
  });

  /* 7 Lightbox: Bilder eines Beitrags als Gruppe, vor/zurück, Vorschaubilder, Esc. */
  (function () {
    var triggers = $$('[data-lightbox]');
    if (!triggers.length) return;
    var dialog, view, img, left, right, strip, content, items = [], index = 0;
    function build() {
      dialog = document.createElement('dialog');
      dialog.className = 'w-lightbox-backdrop';
      dialog.setAttribute('aria-label', 'Bildansicht');
      dialog.innerHTML =
        '<div class="w-lightbox-container"><div class="w-lightbox-content">' +
        '<div class="w-lightbox-view"><div class="w-lightbox-frame"><figure class="w-lightbox-figure">' +
        '<img class="w-lightbox-img w-lightbox-image" alt=""></figure></div></div>' +
        '<button type="button" class="w-lightbox-control w-lightbox-left" aria-label="Vorheriges Bild"></button>' +
        '<button type="button" class="w-lightbox-control w-lightbox-right" aria-label="Nächstes Bild"></button>' +
        '<button type="button" class="w-lightbox-control w-lightbox-close" aria-label="Schließen"></button>' +
        '</div><div class="w-lightbox-strip"></div></div>';
      document.body.appendChild(dialog);
      content = $('.w-lightbox-content', dialog); view = $('.w-lightbox-view', dialog);
      img = $('.w-lightbox-img', dialog); strip = $('.w-lightbox-strip', dialog);
      left = $('.w-lightbox-left', dialog); right = $('.w-lightbox-right', dialog);
      left.addEventListener('click', function () { show(index - 1); });
      right.addEventListener('click', function () { show(index + 1); });
      $('.w-lightbox-close', dialog).addEventListener('click', close);
      $('.w-lightbox-figure', dialog).addEventListener('click', function () { if (items.length > 1) show(index + 1); });
      dialog.addEventListener('cancel', function (e) { e.preventDefault(); close(); });
      document.addEventListener('keydown', function (e) {
        if (!dialog.open) return;
        if (e.key === 'ArrowLeft') show(index - 1);
        if (e.key === 'ArrowRight') show(index + 1);
      });
      dialog.addEventListener('click', function (e) { if (e.target === dialog || e.target.classList.contains('w-lightbox-view')) close(); });
    }
    function show(i) {
      if (i < 0 || i >= items.length) return;
      index = i;
      view.style.opacity = 0;
      img.src = items[i].src; img.alt = items[i].alt;
      var ready = function () { view.style.opacity = 1; };
      if (img.complete) ready(); else img.onload = ready;
      left.classList.toggle('w-lightbox-inactive', i === 0);
      right.classList.toggle('w-lightbox-inactive', i === items.length - 1);
      left.disabled = i === 0; right.disabled = i === items.length - 1;
      $$('.w-lightbox-item', strip).forEach(function (b, k) {
        b.classList.toggle('w-lightbox-active', k === i);
        b.setAttribute('aria-current', String(k === i));
      });
    }
    function open(group, start) {
      if (!dialog) build();
      items = triggers.filter(function (t) { return t.getAttribute('data-lightbox') === group; })
        .map(function (t) { var im = $('img', t); return { src: t.getAttribute('href'), alt: im ? im.alt : '' }; });
      content.classList.toggle('w-lightbox-group', items.length > 1);
      strip.innerHTML = '';
      if (items.length > 1) items.forEach(function (it, k) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'w-lightbox-item';
        b.setAttribute('aria-label', 'Bild ' + (k + 1) + ' von ' + items.length);
        b.innerHTML = '<div class="w-lightbox-thumbnail"><img class="w-lightbox-thumbnail-image" alt=""></div>';
        var t = $('img', b);
        t.onload = function () { t.classList.add(t.naturalWidth > t.naturalHeight ? 'w-lightbox-wide' : 'w-lightbox-tall'); };
        t.src = it.src;
        b.addEventListener('click', function () { show(k); });
        strip.appendChild(b);
      });
      document.body.classList.add('w-lightbox-noscroll');
      dialog.style.opacity = 0;
      show(start);
      dialog.showModal();
      requestAnimationFrame(function () { requestAnimationFrame(function () { dialog.style.opacity = 1; }); });
    }
    function close() {
      dialog.style.opacity = 0;
      afterTransition(dialog, 300, function () {
        dialog.close();
        document.body.classList.remove('w-lightbox-noscroll');
      });
    }
    triggers.forEach(function (t) {
      t.addEventListener('click', function (e) {
        e.preventDefault();
        var group = t.getAttribute('data-lightbox');
        var same = triggers.filter(function (x) { return x.getAttribute('data-lightbox') === group; });
        open(group, same.indexOf(t));
      });
    });
  })();
})();
