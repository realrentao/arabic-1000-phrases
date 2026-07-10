/* ============================================================
   阿拉伯语常用语1000句 · 渲染 + 发音逻辑
   依赖：js/data.js (DATA)  js/audio.js (AUDIO_MAP)
   ============================================================ */
(function () {
  "use strict";

  // audio.js 顶层用 const 声明，不会挂到 window；这里直接引用全局词法绑定并兜底
  var AUDIO = (typeof AUDIO_MAP !== "undefined") ? AUDIO_MAP : {};

  var DIAL_ORDER = ["msa", "egyptian", "levantine", "maghreb"];
  var DIAL_META = {
    msa:       { tag: "① 标准语", short: "标准语" },
    egyptian:  { tag: "② 埃及",   short: "埃及" },
    levantine: { tag: "③ 黎凡特/海湾", short: "海湾" },
    maghreb:   { tag: "④ 马格里布", short: "马格里布" }
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function md(s) {
    return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  }
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }

  // 解析“最通用”列，找出推荐方言标记 ①②③④
  function commonKey(common) {
    if (!common) return null;
    var m = common.match(/[①②③④]/);
    if (!m) return null;
    var map = { "①": "msa", "②": "egyptian", "③": "levantine", "④": "maghreb" };
    return map[m[0]] || null;
  }

  function cellLabel(el) {
    var tag = el.querySelector(".tag");
    if (!tag) return "";
    return tag.textContent.replace("★", "").replace(/[①-④]/g, "").trim();
  }

  /* ---------------- 渲染 ---------------- */
  function renderIntro() {
    var el = $("#intro");
    if (!DATA.intro || !DATA.intro.length) { el.style.display = "none"; return; }
    var html = '<h2>使用说明 · دليل</h2><ul>';
    DATA.intro.forEach(function (b) { if (b) html += "<li>" + md(b) + "</li>"; });
    html += "</ul>";
    el.innerHTML = html;
    if (window.twemoji) window.twemoji.parse(el);
  }

  function renderLegend() {
    if (!DATA.legend) return;
    var parts = DATA.legend.split("📌");
    var row = parts[0] ? '<div class="legend-row">' + esc(parts[0].trim()) + "</div>" : "";
    var tip = parts[1]
      ? '<div class="legend-tip"><span class="tip-ico">📌</span><span>' + esc(parts[1].trim()) + "</span></div>"
      : "";
    $("#legend").innerHTML = row + tip;
  }

  function renderToc() {
    var nav = $("#toc-list");
    var html = "";
    DATA.sections.forEach(function (s, i) {
      html += '<a href="#sec-' + i + '" data-sec="' + i + '">' +
                '<span class="bullet"></span>' + esc(s.title) + "</a>";
    });
    nav.innerHTML = html;
  }

  function dialectCell(row, key, isCommon) {
    var d = row.dialects[key];
    if (!d || !d.ar) return "";
    var src = (AUDIO && AUDIO[d.ar]) ? AUDIO[d.ar] : "";
    var cls = "dial" + (isCommon ? " is-common" : "");
    var star = isCommon ? '<span class="star">★</span>' : "";
    var noteBadge = d.note
      ? '<span class="note-badge" title="合成/借词标注（' + esc(d.note) + '），原文建议使用前核对">' + esc(d.note) + "</span>"
      : "";
    return '<div class="' + cls + '" data-ar="' + esc(d.ar) + '" data-src="' + esc(src) + '">' +
             '<div class="tag">' + star + esc(DIAL_META[key].tag) + noteBadge + "</div>" +
             '<div class="ar">' + esc(d.ar) + "</div>" +
             (d.rom ? '<div class="rom">' + esc(d.rom) + "</div>" : "") +
           "</div>";
  }

  // 全局检索：中文 / 阿拉伯文 / 罗马音
  function rowMatches(r, filter) {
    if (!filter) return true;
    var f = filter.toLowerCase();
    if (r.cn && r.cn.toLowerCase().indexOf(f) >= 0) return true;
    if (r.common && r.common.toLowerCase().indexOf(f) >= 0) return true;
    for (var k in r.dialects) {
      var d = r.dialects[k];
      if (d.ar && d.ar.indexOf(filter) >= 0) return true;   // 阿拉伯文不区分大小写
      if (d.rom && d.rom.toLowerCase().indexOf(f) >= 0) return true;
    }
    return false;
  }

  // 单章 HTML（filter 为空表示不过滤，载入该章全部行）
  function sectionHTML(i, filter) {
    var s = DATA.sections[i];
    var rows = s.rows.filter(function (r) { return rowMatches(r, filter); });
    if (filter && rows.length === 0) return "";
    var html = '<section class="chapter" id="sec-' + i + '">';
    html += '<div class="chapter-head"><span class="ch-no">' + (i + 1) + "</span>" +
            '<span class="ch-title">' + esc(s.title) + "</span>" +
            '<span class="ch-count">' + rows.length + " 句</span>" +
            '<button class="play-sec" data-sec="' + i + '">▶ 连播本节</button>' +
            '<button class="back-toc" data-sec="' + i + '" title="返回目录">↥ 目录</button></div>';
    html += '<div class="cards">';
    rows.forEach(function (r) {
      var ck = commonKey(r.common);
      html += '<div class="card">';
      html += '<button class="back-toc card-toc" title="返回目录" aria-label="返回目录">↥</button>';
      html += '<div class="row-top"><span class="num">' + esc(r.num) + "</span>" +
              '<span class="cn">' + esc(r.cn) + "</span>";
      if (r.common) html += '<span class="common">' + esc(r.common) + "</span>";
      html += "</div>";
      html += '<div class="dialects">';
      DIAL_ORDER.forEach(function (k) { html += dialectCell(r, k, k === ck); });
      html += "</div></div>";
    });
    html += "</div></section>";
    return html;
  }

  // 搜索模式：一次性渲染全部匹配结果
  function renderAll(filter) {
    var main = $("#sections");
    var out = "";
    if (filter) {
      var total = 0;
      DATA.sections.forEach(function (s) {
        s.rows.forEach(function (r) { if (rowMatches(r, filter)) total++; });
      });
      out += '<div class="search-banner">🔍 搜索 “<b>' + esc(filter) + '</b>” — 共 <b>' +
             total + '</b> 条 <button id="clear-search" class="banner-clear">✕ 清除</button></div>';
    }
    DATA.sections.forEach(function (s, i) { out += sectionHTML(i, filter); });
    main.innerHTML = out;
    var hasResults = main.querySelector("section.chapter") !== null;
    $("#empty").style.display = hasResults ? "none" : "block";
    observeAllSections();
  }

  /* ---------------- 音频播放 ---------------- */
  var audio = new Audio();
  var current = null; // {el, src}
  var np = $("#now-playing");

  function showNowPlaying(label, ar) {
    $("#np-label").textContent = label || "正在播放";
    $("#np-ar").textContent = ar;
    np.classList.add("show");
  }
  function hideNowPlaying() { np.classList.remove("show"); }

  function setPlaying(el, on) {
    if (el) el.classList.toggle("playing", on);
  }

  function playEl(el) {
    var src = el.getAttribute("data-src");
    var ar = el.getAttribute("data-ar");
    if (!src) { return; }
    if (current && current.el === el) {
      if (!audio.paused) { audio.pause(); return; }
    } else {
      if (current) { audio.pause(); setPlaying(current.el, false); }
      audio.src = src;
      current = { el: el, src: src };
    }
    setPlaying(el, true);
    showNowPlaying(cellLabel(el), ar);
    audio.play().catch(function () {});
  }

  audio.addEventListener("timeupdate", function () {
    if (audio.duration) {
      var p = (audio.currentTime / audio.duration) * 100;
      $("#np-fill").style.width = p + "%";
    }
  });
  audio.addEventListener("ended", function () {
    if (current) setPlaying(current.el, false);
    if (queue.length) { playNextInQueue(); }
    else { hideNowPlaying(); current = null; }
  });

  /* 章节连播队列 */
  var queue = [];
  function playNextInQueue() {
    if (!queue.length) { hideNowPlaying(); current = null; return; }
    var el = queue.shift();
    if (!el || !el.getAttribute("data-src")) { playNextInQueue(); return; }
    current = { el: el, src: el.getAttribute("data-src") };
    setPlaying(el, true);
    showNowPlaying(cellLabel(el), el.getAttribute("data-ar"));
    audio.src = current.src;
    audio.play().catch(function () { playNextInQueue(); });
  }

  /* ---------------- 事件 ---------------- */
  document.addEventListener("click", function (e) {
    // 返回目录
    var tocBtn = e.target.closest ? e.target.closest(".back-toc") : null;
    if (tocBtn) {
      var toc = document.querySelector("nav.toc");
      if (toc) toc.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    // 搜索结果条上的“清除”
    if (e.target.id === "clear-search") {
      var box = $("#search");
      if (box) { box.value = ""; renderSections(""); box.focus(); }
      return;
    }
    // 点击任意句子 -> 立即中断连播，改播所选句子
    var cell = e.target.closest ? e.target.closest(".dial") : null;
    if (cell && cell.getAttribute("data-src")) {
      queue = [];          // 中断连播队列，避免后续自动播放
      playEl(cell);
      return;
    }
    // 连播本节
    var secBtn = e.target.closest ? e.target.closest(".play-sec") : null;
    if (secBtn) {
      var idx = secBtn.getAttribute("data-sec");
      var sec = document.getElementById("sec-" + idx);
      if (!sec) return;
      var cells = sec.querySelectorAll(".dial.is-common");
      if (!cells.length) cells = sec.querySelectorAll(".dial");
      queue = [];
      for (var i = 0; i < cells.length; i++) {
        if (cells[i].getAttribute("data-src")) queue.push(cells[i]);
      }
      if (queue.length) {
        if (current) { audio.pause(); setPlaying(current.el, false); }
        playNextInQueue();
      }
    }
  });

  // 搜索（对全部 1020 句全局检索）
  var searchTimer;
  var searchBox = $("#search");
  if (searchBox) {
    searchBox.addEventListener("input", function (e) {
      clearTimeout(searchTimer);
      var v = e.target.value.trim();
      searchTimer = setTimeout(function () { renderSections(v); }, 150);
    });
    searchBox.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { searchBox.value = ""; renderSections(""); }
    });
  }
  var searchClear = $("#search-clear");
  if (searchClear) {
    searchClear.addEventListener("click", function () {
      if (searchBox) { searchBox.value = ""; renderSections(""); searchBox.focus(); }
    });
  }

  // 滚动高亮 TOC（逐章观察，兼容懒加载）
  var tocLinks = {};
  var tocObserver = null;
  function setupTocSpy() {
    var links = document.querySelectorAll("#toc-list a");
    links.forEach(function (a) { tocLinks[a.getAttribute("data-sec")] = a; });
    if (tocObserver) tocObserver.disconnect();
    tocObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          var id = en.target.id.replace("sec-", "");
          for (var k in tocLinks) tocLinks[k].classList.remove("active");
          if (tocLinks[id]) tocLinks[id].classList.add("active");
        }
      });
    }, { rootMargin: "-10% 0px -80% 0px" });
    observeAllSections();
  }
  function observeSection(i) {
    var sec = document.getElementById("sec-" + i);
    if (sec && tocObserver) tocObserver.observe(sec);
  }
  function observeAllSections() {
    if (!tocObserver) return;
    document.querySelectorAll("section.chapter").forEach(function (s) { tocObserver.observe(s); });
  }

  /* ---------------- 懒加载：首屏只渲染前几章，滚动时续载 ---------------- */
  var RENDER_BATCH = 3;
  var lazy = { active: false, upTo: 0, sentinel: null, rafId: 0 };

  function renderNextBatch() {
    var main = $("#sections");
    var start = lazy.upTo;
    var end = Math.min(start + RENDER_BATCH, DATA.sections.length);
    var html = "";
    for (var i = start; i < end; i++) { html += sectionHTML(i, ""); }
    lazy.upTo = end;
    if (lazy.sentinel) {
      var tmp = document.createElement("div");
      tmp.innerHTML = html;
      while (tmp.firstChild) main.insertBefore(tmp.firstChild, lazy.sentinel);
    } else {
      main.insertAdjacentHTML("beforeend", html);
    }
    // 插入 DOM 之后再观察，否则 getElementById 拿不到节点
    for (var j = start; j < end; j++) observeSection(j);
    if (lazy.upTo >= DATA.sections.length && lazy.sentinel) {
      lazy.sentinel.remove(); lazy.sentinel = null;
    }
  }

  function ensureRendered(index) {
    if (!lazy.active) return;
    while (lazy.upTo <= index) renderNextBatch();
  }

  function pump() {
    lazy.rafId = 0;
    if (!lazy.active || lazy.upTo >= DATA.sections.length || !lazy.sentinel) return;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var r = lazy.sentinel.getBoundingClientRect();
    if (r.top <= vh + 600) { renderNextBatch(); lazy.rafId = requestAnimationFrame(pump); }
  }

  function onScroll() {
    if (lazy.rafId) return;
    lazy.rafId = requestAnimationFrame(pump);
  }

  function initLazy() {
    lazy.active = true;
    lazy.upTo = 0;
    var main = $("#sections");
    main.innerHTML = "";
    if (!lazy.sentinel) {
      lazy.sentinel = document.createElement("div");
      lazy.sentinel.id = "lazy-sentinel";
      lazy.sentinel.style.height = "1px";
      main.appendChild(lazy.sentinel);
    }
    renderNextBatch();
    requestAnimationFrame(pump);
  }

  function renderSections(filter) {
    if (filter) {
      lazy.active = false;
      if (lazy.sentinel) { lazy.sentinel.remove(); lazy.sentinel = null; }
      renderAll(filter);
    } else {
      initLazy();
    }
  }

  /* ---------------- 初始化 ---------------- */
  function init() {
    if (!DATA) { document.body.innerHTML = "<p style='color:#fff;padding:40px'>数据未加载 (data.js)</p>"; return; }
    if (DATA.title) document.getElementById("page-title").textContent = DATA.title;
    renderLegend();
    renderIntro();
    renderToc();
    setupTocSpy();
    renderSections("");
    // TOC 点击：目标章节尚未渲染时先渲染再跳转
    var tocList = $("#toc-list");
    if (tocList) {
      tocList.addEventListener("click", function (e) {
        var a = e.target.closest ? e.target.closest("a[data-sec]") : null;
        if (!a) return;
        e.preventDefault();
        var idx = parseInt(a.getAttribute("data-sec"), 10);
        ensureRendered(idx);
        var sec = document.getElementById("sec-" + idx);
        if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
