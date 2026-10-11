// Tiny lightbox shared by the website2 designs.
// Any element with data-lb="<src>" opens it. Optional:
//   data-lb-type="video"   play a video instead of showing an image
//   data-lb-type="youtube" data-lb is a YouTube URL (watch?v=, youtu.be/, shorts/) or bare video id
//   data-lb-cap="..."      caption
//   data-lb-group="name"   arrow keys / buttons step through the group
// Look is controlled by the page with .lbx / .lbx-* selectors; sensible defaults below.
(function () {
  var css =
    '.lbx{position:fixed;inset:0;z-index:999;display:none;align-items:center;justify-content:center;background:rgba(10,10,14,.92);padding:24px}' +
    '.lbx.open{display:flex}' +
    '.lbx-stage{max-width:min(94vw,1200px);max-height:86vh;display:flex;flex-direction:column;align-items:center;gap:14px}' +
    '.lbx-stage img,.lbx-stage video{max-width:100%;max-height:76vh;display:block;object-fit:contain}' +
    '.lbx-cap{color:#fff;font-size:14px;text-align:center}' +
    '.lbx-btn{position:absolute;width:52px;height:52px;border-radius:50%;border:0;cursor:pointer;font-size:24px;line-height:1;display:flex;align-items:center;justify-content:center;background:var(--lbx-accent,#fff);color:var(--lbx-on-accent,#000)}' +
    '.lbx-close{top:18px;right:18px}.lbx-prev{left:18px;top:50%;transform:translateY(-50%)}.lbx-next{right:18px;top:50%;transform:translateY(-50%)}' +
    '@media(max-width:640px){.lbx-prev,.lbx-next{top:auto;bottom:18px;transform:none}}';
  var st = document.createElement('style');
  st.textContent = css;
  document.head.insertBefore(st, document.head.firstChild);

  var box = document.createElement('div');
  box.className = 'lbx';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.innerHTML =
    '<button class="lbx-btn lbx-close" aria-label="閉じる">&times;</button>' +
    '<button class="lbx-btn lbx-prev" aria-label="前へ">&#8249;</button>' +
    '<div class="lbx-stage"></div>' +
    '<button class="lbx-btn lbx-next" aria-label="次へ">&#8250;</button>';
  document.body.appendChild(box);
  var stage = box.querySelector('.lbx-stage');
  var prev = box.querySelector('.lbx-prev'), next = box.querySelector('.lbx-next');
  var items = [], idx = 0, opener = null;

  function render() {
    var el = items[idx], src = el.getAttribute('data-lb'), cap = el.getAttribute('data-lb-cap') || '';
    stage.innerHTML = '';
    var media, type = el.getAttribute('data-lb-type');
    if (type === 'youtube') {
      var m = src.match(/(?:youtu\.be\/|v=|shorts\/|embed\/)([\w-]{11})/);
      media = document.createElement('iframe');
      media.src = 'https://www.youtube-nocookie.com/embed/' + (m ? m[1] : src) + '?autoplay=1&rel=0&playsinline=1';
      media.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      media.allowFullscreen = true;
      media.title = cap;
      media.style.cssText = 'width:min(94vw,1200px);aspect-ratio:16/9;max-height:76vh;border:0;background:#000';
    } else if (type === 'video') {
      media = document.createElement('video');
      media.src = src; media.controls = true; media.autoplay = true; media.playsInline = true;
    } else {
      media = document.createElement('img');
      media.src = src; media.alt = cap;
    }
    stage.appendChild(media);
    var c = document.createElement('div');
    c.className = 'lbx-cap';
    c.textContent = cap + (items.length > 1 ? '  (' + (idx + 1) + '/' + items.length + ')' : '');
    stage.appendChild(c);
    prev.style.display = next.style.display = items.length > 1 ? '' : 'none';
  }
  function open(el) {
    var g = el.getAttribute('data-lb-group');
    items = g ? Array.prototype.slice.call(document.querySelectorAll('[data-lb-group="' + g + '"]')) : [el];
    // de-duplicate identical sources inside a group
    var seen = {};
    items = items.filter(function (x) { var k = x.getAttribute('data-lb'); return seen[k] ? false : (seen[k] = 1); });
    idx = Math.max(0, items.findIndex(function (x) { return x.getAttribute('data-lb') === el.getAttribute('data-lb'); }));
    opener = el;
    render();
    box.classList.add('open');
    document.documentElement.style.overflow = 'hidden';
    box.querySelector('.lbx-close').focus();
  }
  function close() {
    box.classList.remove('open');
    stage.innerHTML = '';
    document.documentElement.style.overflow = '';
    if (opener) opener.focus();
  }
  function step(d) { idx = (idx + d + items.length) % items.length; render(); }

  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-lb]');
    if (el) { e.preventDefault(); open(el); }
  });
  box.addEventListener('click', function (e) { if (e.target === box) close(); });
  box.querySelector('.lbx-close').addEventListener('click', close);
  prev.addEventListener('click', function () { step(-1); });
  next.addEventListener('click', function () { step(1); });
  document.addEventListener('keydown', function (e) {
    if (!box.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') step(-1);
    if (e.key === 'ArrowRight') step(1);
  });
})();
