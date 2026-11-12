// 「パブリックアートレンタル アイエル」のロゴと「戻る」ボタン：来たページ（案A／案B）の、見ていた場所に戻す
(function () {
  var from = null, direct = false;
  try {
    var u = new URL(document.referrer);
    if (u.origin === location.origin) {
      var m = u.pathname.match(/\/(01-entrance|02-workplace)\//);
      if (m) { from = m[1]; direct = true; }
    }
  } catch (e) {}
  try { if (from) sessionStorage.setItem('aile-from', from); else from = sessionStorage.getItem('aile-from'); } catch (e) {}
  document.querySelectorAll('[data-back], .wk-logo, .sw-logo').forEach(function (a) {
    if (from) a.href = a.href.replace(/01-entrance|02-workplace/, from);
    a.addEventListener('click', function (ev) {
      if (direct && history.length > 1) { ev.preventDefault(); history.back(); }
    });
  });
})();
