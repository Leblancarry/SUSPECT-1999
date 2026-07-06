/**
 * contamination.js
 * 402对网页的渗透效果——随玩家收集证据数量逐渐加重。
 * 共四个污染等级（1-4），等级越高效果越频繁、种类越多。
 */
(function () {
  'use strict';

  var level = 0;

  // ── 文字素材池 ────────────────────────────────────────────────

  var GHOST_POOL = [
    '……别告诉它你的名字',
    '19:20',
    '衣柜那边不对',
    '你还在吗',
    '已感知到访客',
    '别进去',
    '顾小满在哪里',
    '它知道你在这里',
    '名字一旦给出就收不回来',
    '402',
  ];

  var WB_CORRUPT = [
    '……',
    '4  0  2',
    '已感知到访客',
    '请填写名字以继续',
    '迁移准备中……',
    '检测到未命名访客 / 请登记',
  ];

  var TITLE_CORRUPT = [
    '你还在吗',
    '已检测到访客',
    '请留下来',
    '南桥小区402 — 欢迎回来',
    '别关这个页面',
  ];

  var NAV_CORRUPT = {
    '🏠 首页':    '🏠 无法离开',
    '📁 案件资料': '📁 你的资料',
    '💬 聊天室':  '💬 它在等你',
    '🔍 证据档案': '🔍 你是证据',
    '⚠ 退出':    '⚠ 你出不去',
  };

  // ── 初始化 ────────────────────────────────────────────────────

  function init() {
    fetch('/api/contamination')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        level = d.level || 0;
        if (level > 0) scheduleNext(firstDelay());
      })
      .catch(function () {});
  }

  // 等级对应的间隔范围（ms）：[level0, level1, level2, level3, level4]
  var DELAY_MIN = [0, 38000, 22000, 11000, 7000];
  var DELAY_MAX = [0, 75000, 45000, 24000, 14000];

  function firstDelay() {
    // 首次效果在 10-30s 后触发，让玩家先稳定一下
    return 10000 + Math.random() * 20000;
  }

  function nextDelay() {
    var mn = DELAY_MIN[level] || 38000;
    var mx = DELAY_MAX[level] || 75000;
    return mn + Math.random() * (mx - mn);
  }

  function scheduleNext(delay) {
    setTimeout(function () {
      triggerEffect();
      scheduleNext(nextDelay());
    }, delay);
  }

  // ── 效果选择器 ────────────────────────────────────────────────

  function triggerEffect() {
    var pool = [effectGhostText, effectWarningBar];
    if (level >= 2) {
      pool.push(effectTitleFlicker, effectCrtFlicker, effectClockGlitch);
    }
    if (level >= 3) {
      pool.push(effectFooterGlitch, effectNavGlitch, effectRedVignette);
    }
    if (level >= 4) {
      // 高等级加权，文字污染和视觉冲击更频繁
      pool.push(effectWarningBar, effectGhostText, effectRedVignette);
    }
    pick(pool)();
  }

  // ── 具体效果 ──────────────────────────────────────────────────

  /**
   * 幽灵文字：在屏幕边缘角落短暂浮现一行文字，然后消散。
   */
  function effectGhostText() {
    var msg = pick(GHOST_POOL);
    var el  = document.createElement('div');

    // 随机选上方或下方、左侧或右侧
    var top  = Math.random() > 0.5
      ? (3  + Math.random() * 10) + '%'
      : (82 + Math.random() * 10) + '%';
    var left = Math.random() > 0.5
      ? (2  + Math.random() * 14) + '%'
      : (62 + Math.random() * 26) + '%';

    el.style.cssText =
      'position:fixed;top:' + top + ';left:' + left + ';' +
      'color:rgba(170,0,0,0.6);font-size:11px;' +
      "font-family:'SimSun','宋体',serif;" +
      'z-index:8000;pointer-events:none;' +
      'opacity:0;transition:opacity 1.2s ease;' +
      'letter-spacing:0.1em;white-space:nowrap;' +
      'text-shadow:0 0 6px rgba(180,0,0,0.4);';
    el.textContent = msg;
    document.body.appendChild(el);

    setTimeout(function () { el.style.opacity = '1'; }, 40);
    var linger = 2200 + Math.random() * 1600;
    setTimeout(function () {
      el.style.transition = 'opacity 2s ease';
      el.style.opacity    = '0';
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 2100);
    }, linger);
  }

  /**
   * 顶部警告栏短暂显示污染内容。
   */
  function effectWarningBar() {
    var wb = document.getElementById('warning-bar');
    if (!wb) return;
    var orig = wb.innerHTML;
    var msg  = pick(WB_CORRUPT);
    wb.style.transition   = 'color 0.2s';
    wb.style.color        = '#ff6666';
    wb.textContent        = msg;
    var dur = 1300 + Math.random() * 700;
    setTimeout(function () {
      wb.innerHTML    = orig;
      wb.style.color  = '';
    }, dur);
  }

  /**
   * 浏览器标签页标题短暂变成污染内容。
   */
  function effectTitleFlicker() {
    var orig = document.title;
    document.title = pick(TITLE_CORRUPT);
    setTimeout(function () {
      document.title = orig;
    }, 2000 + Math.random() * 1000);
  }

  /**
   * CRT 放电：短暂亮度/对比度突变，模拟显示器不稳定。
   */
  function effectCrtFlicker() {
    var b = document.body;
    b.style.filter = 'brightness(1.4) contrast(1.18)';
    setTimeout(function () {
      b.style.filter = 'brightness(0.65)';
      setTimeout(function () {
        b.style.transition = 'filter 0.15s ease';
        b.style.filter     = '';
        setTimeout(function () {
          b.style.transition = '';
        }, 200);
      }, 100);
    }, 70);
  }

  /**
   * 19:20 时钟短暂显示乱码时间，然后恢复。
   */
  function effectClockGlitch() {
    var cl = document.getElementById('fixed-clock');
    if (!cl) return;
    var orig      = cl.textContent;
    var origColor = cl.style.color;
    cl.style.transition = 'color 0.1s';
    cl.style.color      = '#ff0000';
    cl.textContent      = '??:??';
    setTimeout(function () {
      cl.textContent = '00:00';
      setTimeout(function () {
        cl.textContent = orig;
        cl.style.color = origColor;
      }, 220);
    }, 220);
  }

  /**
   * 页脚内容短暂被污染替换。
   */
  function effectFooterGlitch() {
    var ft = document.querySelector('.page-footer');
    if (!ft) return;
    var orig = ft.innerHTML;
    ft.innerHTML =
      'Copyright &copy; 2001 南桥小区402寻人站 &nbsp;|&nbsp; ' +
      '制作：<span style="color:#cc0000;letter-spacing:0.15em;">……</span>' +
      ' &nbsp;|&nbsp; ' +
      '<span style="color:#cc0000;" class="blink-text">402已感知到访客</span>';
    setTimeout(function () { ft.innerHTML = orig; }, 1800 + Math.random() * 800);
  }

  /**
   * 导航栏某个链接短暂显示错误文字。
   */
  function effectNavGlitch() {
    var links = document.querySelectorAll('.nav-links a');
    if (!links.length) return;
    var lk   = links[Math.floor(Math.random() * links.length)];
    var orig = lk.textContent;
    var corrupt = NAV_CORRUPT[orig] || (orig + ' ——');
    lk.style.color  = '#cc0000';
    lk.textContent  = corrupt;
    setTimeout(function () {
      lk.textContent = orig;
      lk.style.color = '';
    }, 1100 + Math.random() * 500);
  }

  /**
   * 红色暗晕：屏幕边缘短暂泛出暗红色，像血迹扩散。
   */
  function effectRedVignette() {
    var el = document.createElement('div');
    el.style.cssText =
      'position:fixed;top:0;left:0;width:100%;height:100%;' +
      'background:radial-gradient(ellipse at center,' +
        'transparent 55%, rgba(110,0,0,0.22) 100%);' +
      'z-index:7998;pointer-events:none;' +
      'opacity:0;transition:opacity 0.5s ease;';
    document.body.appendChild(el);
    setTimeout(function () { el.style.opacity = '1'; }, 30);
    setTimeout(function () {
      el.style.transition = 'opacity 1.1s ease';
      el.style.opacity    = '0';
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 1200);
    }, 900 + Math.random() * 400);
  }

  // ── 工具 ─────────────────────────────────────────────────────

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  // ── 启动 ─────────────────────────────────────────────────────

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
