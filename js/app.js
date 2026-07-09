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

  function renderSections(filter) {
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

    DATA.sections.forEach(function (s, i) {
      var rows = s.rows.filter(function (r) { return rowMatches(r, filter); });
      if (filter && rows.length === 0) return;

      out += '<section class="chapter" id="sec-' + i + '">';
      out += '<div class="chapter-head"><span class="ch-no">' + (i + 1) + "</span>" +
             '<span class="ch-title">' + esc(s.title) + "</span>" +
             '<span class="ch-count">' + rows.length + " 句</span>" +
             '<button class="play-sec" data-sec="' + i + '">▶ 连播本节</button>' +
             '<button class="back-toc" data-sec="' + i + '" title="返回目录">↥ 目录</button></div>';
      out += '<div class="cards">';
      rows.forEach(function (r) {
        var ck = commonKey(r.common);
        out += '<div class="card">';
        out += '<button class="back-toc card-toc" title="返回目录" aria-label="返回目录">↥</button>';
        out += '<div class="row-top"><span class="num">' + esc(r.num) + "</span>" +
               '<span class="cn">' + esc(r.cn) + "</span>";
        if (r.common) out += '<span class="common">' + esc(r.common) + "</span>";
        out += "</div>";
        out += '<div class="dialects">';
        DIAL_ORDER.forEach(function (k) { out += dialectCell(r, k, k === ck); });
        out += "</div></div>";
      });
      out += "</div></section>";
    });
    main.innerHTML = out;

    if (filter) {
      var hasResults = out.indexOf('class="chapter"') >= 0;
      $("#empty").style.display = hasResults ? "none" : "block";
    }
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

  // 滚动高亮 TOC
  var tocLinks = {};
  function setupTocSpy() {
    var links = document.querySelectorAll("#toc-list a");
    links.forEach(function (a) { tocLinks[a.getAttribute("data-sec")] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          var id = en.target.id.replace("sec-", "");
          for (var k in tocLinks) tocLinks[k].classList.remove("active");
          if (tocLinks[id]) tocLinks[id].classList.add("active");
        }
      });
    }, { rootMargin: "-10% 0px -80% 0px" });
    document.querySelectorAll("section.chapter").forEach(function (s) { obs.observe(s); });
  }

  /* ---------------- 初始化 ---------------- */
  function init() {
    if (!DATA) { document.body.innerHTML = "<p style='color:#fff;padding:40px'>数据未加载 (data.js)</p>"; return; }
    renderLegend();
    renderIntro();
    renderToc();
    renderSections("");
    setupTocSpy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
