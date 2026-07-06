// main.js — 全局行为：时钟、访客计数器异常、通用效果

document.addEventListener('DOMContentLoaded', () => {
  startClock();
  scheduleCounterGlitch();
  loadMission();
});

// 固定时钟显示 19:20（永远不变）
function startClock() {
  const el = document.getElementById('fixed-clock');
  if (!el) return;
  // 始终显示 19:20，这是规则的一部分
  el.textContent = '19:20';

  // 偶尔故障闪烁
  setInterval(() => {
    if (Math.random() < 0.04) {
      el.style.color = '#ff0000';
      el.textContent = '??:??';
      setTimeout(() => {
        el.style.color = '#cc0000';
        el.textContent = '19:20';
      }, 300);
    }
  }, 3000);
}

// 根据游戏状态更新任务提示
function loadMission() {
  const el = document.getElementById('mission-text');
  if (!el) return;

  fetch('/api/state').then(r => r.json()).then(state => {
    const collected = (state.evidence_collected || []).length;
    const chatCount = (state.chat_history || []).length;
    const knows1920 = state.knows_1920_rule;
    const knowsName = state.knows_name_rule;

    let html = '';

    if (collected === 0 && chatCount === 0) {
      html = `
        <b style="color:#000080">① 了解案情</b><br>
        先阅读<a href="/case">案件资料</a>，了解顾小满失踪经过。<br><br>
        <span style="color:#888;font-size:10px;">提示：注意四条规则。</span>
      `;
    } else if (collected === 0) {
      html = `
        <b style="color:#000080">② 收集证据</b><br>
        前往<a href="/evidence">证据档案</a>，查阅顾小满存在的证明。<br><br>
        <span style="color:#888;font-size:10px;">已收集：0 / 11 条</span>
      `;
    } else if (collected < 5) {
      html = `
        <b style="color:#000080">② 继续收集证据</b><br>
        已找到 <b>${collected}</b> 条证据。<br>
        前往<a href="/chat">聊天室</a>向知情者核实。<br><br>
        <span style="color:#888;font-size:10px;">证据：${collected} / 11 条</span>
      `;
    } else if (collected < 11) {
      html = `
        <b style="color:#000080">③ 深入调查</b><br>
        已找到 <b>${collected}</b> 条证据。<br>
        继续与<a href="/chat">聊天室</a>成员交流。<br><br>
        ${knows1920 ? '✓ 已知19:20规则<br>' : ''}
        ${knowsName ? '✓ 已知名字规则<br>' : ''}
        <span style="color:#888;font-size:10px;">证据：${collected} / 11 条</span>
      `;
    } else {
      html = `
        <b style="color:#880000">⚠ 调查接近尾声</b><br>
        所有证据已收集。<br>
        前往<a href="/ending">退出页面</a>……<br><br>
        <span class="blink-text" style="font-size:10px;">注意：不要保存任何东西。</span>
      `;
    }

    el.innerHTML = html;
  });
}

// 访客计数器偶发异常
function scheduleCounterGlitch() {
  const el = document.querySelector('.counter-digits');
  if (!el) return;

  setInterval(() => {
    if (Math.random() < 0.06) {
      const glitchValues = ['000403', '000401', '??????', '000402', 'ERROR'];
      const val = glitchValues[Math.floor(Math.random() * glitchValues.length)];
      el.textContent = val;
      setTimeout(() => { el.textContent = '000402'; }, 400);
    }
  }, 5000);
}
