// Lightbox for the shared photo sections. Every .pf-shot inside one .pf-work
// forms a group; arrows / Esc / swipe-free click navigation.
(function(){
  var lb = document.createElement('div');
  lb.className = 'lb';
  lb.setAttribute('role','dialog');
  lb.setAttribute('aria-modal','true');
  lb.innerHTML =
    '<button class="lb-close" aria-label="Close">&times;</button>' +
    '<button class="lb-prev" aria-label="Previous">&#8249;</button>' +
    '<figure><img alt=""><figcaption></figcaption></figure>' +
    '<button class="lb-next" aria-label="Next">&#8250;</button>';
  document.body.appendChild(lb);

  var img = lb.querySelector('img'), cap = lb.querySelector('figcaption');
  var prev = lb.querySelector('.lb-prev'), next = lb.querySelector('.lb-next');
  var group = [], idx = 0, lastFocus = null;

  function show(i){
    idx = (i + group.length) % group.length;
    var shot = group[idx], thumb = shot.querySelector('img');
    var work = shot.closest('.pf-work');
    var title = work ? work.querySelector('h3').textContent : '';
    img.src = shot.getAttribute('data-full') || thumb.src;
    img.alt = thumb.alt;
    cap.innerHTML = '';
    cap.appendChild(document.createTextNode(title));
    var small = document.createElement('small');
    small.textContent = thumb.alt + (group.length > 1 ? '  ·  ' + (idx + 1) + ' / ' + group.length : '');
    cap.appendChild(small);
    prev.style.display = next.style.display = group.length > 1 ? '' : 'none';
  }
  function open(shot){
    var work = shot.closest('.pf-work');
    // the main image also appears in the thumb strip; keep one entry per photo
    var seen = {};
    group = (work ? Array.prototype.slice.call(work.querySelectorAll('.pf-shot')) : [shot])
      .filter(function(s){ var k = s.getAttribute('data-full'); return seen[k] ? false : (seen[k] = true); });
    lastFocus = shot;
    var key = shot.getAttribute('data-full');
    show(group.findIndex(function(s){ return s.getAttribute('data-full') === key; }));
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
    lb.querySelector('.lb-close').focus();
  }
  function close(){
    lb.classList.remove('open');
    document.body.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }

  document.addEventListener('click', function(e){
    var shot = e.target.closest && e.target.closest('.pf-shot');
    if (shot){ e.preventDefault(); open(shot); }
  });
  lb.addEventListener('click', function(e){ if (e.target === lb) close(); });
  lb.querySelector('.lb-close').addEventListener('click', close);
  prev.addEventListener('click', function(){ show(idx - 1); });
  next.addEventListener('click', function(){ show(idx + 1); });
  document.addEventListener('keydown', function(e){
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(idx - 1);
    else if (e.key === 'ArrowRight') show(idx + 1);
  });
})();
