// chat.js — QQ风格聊天室交互逻辑

let currentCharId = 'xiaoman';
let isSending = false;

const CHAR_INFO = {
  xiaoman:   { name: '小满不在家',   desc: '本站站长账号。<br>个人签名：<i>（无）</i><br>注册时间：2001-08-14<br>状态：<span class="blink-text">离线</span>' },
  liu_ayi:   { name: '隔壁刘姨',     desc: '南桥小区老居民，留言板常驻用户。<br>个人签名：邻里互助，平安是福<br>状态：<span style="color:#00aa00">在线</span>' },
  master_ma: { name: '马师傅修电视', desc: '电器维修，上门服务。<br>个人签名：（无）<br>最近登录：2001-09-03<br>状态：<span style="color:#ffaa00">离开</span>' },
  xu_yan:    { name: '许延_97',       desc: '账号创建于1997年。<br>个人签名：（已清空）<br>状态：<span style="color:#aaa">隐身</span>' },
  admin:     { name: '系统管理员',   desc: '网站系统账号。<br>负责访客登记与档案归档。<br>状态：<span style="color:#00aa00">在线</span>' },
};

function selectCharacter(charId, el) {
  currentCharId = charId;

  // Update selected UI
  document.querySelectorAll('.qq-user-item').forEach(i => i.classList.remove('qq-user-selected'));
  el.classList.add('qq-user-selected');

  // Update header indicators
  const info = CHAR_INFO[charId] || { name: charId, desc: '' };
  const nameEl = document.getElementById('current-char-name');
  const targetEl = document.getElementById('chat-target-display');
  if (nameEl) nameEl.textContent = info.name;
  if (targetEl) targetEl.textContent = info.name;

  // Update char info box
  const infoBox = document.getElementById('char-info-content');
  if (infoBox) {
    infoBox.innerHTML = `<strong>${info.name}</strong>：${info.desc}`;
  }

  // System message
  appendSysMsg(`已切换对话对象：${info.name}`);
}

function appendSysMsg(text) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;
  const div = document.createElement('div');
  div.className = 'qq-msg sys-msg';
  div.innerHTML = `<span class="sys-msg-text">[系统消息] ${text}</span>`;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function appendUserMsg(text) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;
  const div = document.createElement('div');
  div.className = 'qq-msg';
  div.innerHTML = `
    <div class="qq-msg-header">未命名访客（我）</div>
    <div class="qq-msg-bubble-user">${escapeHtml(text)}</div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function appendCharMsg(charId, text) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;
  const info = CHAR_INFO[charId] || { name: charId };
  const div = document.createElement('div');
  div.className = 'qq-msg';
  div.innerHTML = `
    <div class="qq-msg-header">${escapeHtml(info.name)}</div>
    <div class="qq-msg-bubble-char">${escapeHtml(text)}</div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function showTyping(charId) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;
  const info = CHAR_INFO[charId] || { name: charId };
  const div = document.createElement('div');
  div.className = 'qq-msg qq-typing-indicator';
  div.innerHTML = `<span class="qq-typing">${escapeHtml(info.name)} 正在输入……</span>`;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

async function sendMessage() {
  if (isSending) return;
  const input = document.getElementById('chat-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  isSending = true;
  input.value = '';

  const sendBtn = document.getElementById('send-btn');
  if (sendBtn) sendBtn.disabled = true;

  appendUserMsg(text);
  const typingEl = showTyping(currentCharId);

  // Simulate typing delay (旧网络感)
  const delay = 800 + Math.random() * 1200;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ character_id: currentCharId, message: text }),
    });
    const data = await res.json();

    await new Promise(r => setTimeout(r, delay));

    if (typingEl) typingEl.remove();
    appendCharMsg(currentCharId, data.reply);

    // Apply state updates if any
    if (data.state_updates) {
      GameState.set(data.state_updates);
      // 新证据解锁通知
      if (data.state_updates.newly_unlocked && data.state_updates.newly_unlocked.length > 0) {
        showUnlockNotify(data.state_updates.newly_unlocked);
      }
    }
  } catch (err) {
    await new Promise(r => setTimeout(r, delay));
    if (typingEl) typingEl.remove();
    appendSysMsg('连接异常。请重试。');
  } finally {
    isSending = false;
    if (sendBtn) sendBtn.disabled = false;
    input.focus();
  }
}

// Enter to send, Shift+Enter for newline
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    input.focus();
  }

  // Select first character by default
  const firstUser = document.querySelector('.qq-user-item[data-char-id]');
  if (firstUser) {
    firstUser.classList.add('qq-user-selected');
  }
});

function showUnlockNotify(ids) {
  if (ids.includes('E12')) {
    // E12 特殊通知：更长时间、不同颜色
    const div = document.createElement('div');
    div.className = 'unlock-notify unlock-notify-e12';
    div.innerHTML = '结局回放文件已解锁。<br><a href="/evidence" style="color:#ffcc00">前往证据档案 ▶</a>';
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 6000);
    const others = ids.filter(i => i !== 'E12');
    if (others.length > 0) showUnlockNotify(others);
    return;
  }
  const div = document.createElement('div');
  div.className = 'unlock-notify';
  div.textContent = '发现新档案：' + ids.join('、') + '（前往证据档案查看）';
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 4000);
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
