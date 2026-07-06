// state.js — 本地游戏状态缓存，与后端 /api/state 同步

const GameState = (() => {
  let _state = null;

  async function load() {
    try {
      const res = await fetch('/api/state');
      _state = await res.json();
    } catch (e) {
      _state = {};
    }
    return _state;
  }

  function get(key) {
    if (!_state) return null;
    return key ? _state[key] : _state;
  }

  function set(updates) {
    if (!_state) _state = {};
    Object.assign(_state, updates);
  }

  return { load, get, set };
})();

// Load on every page
document.addEventListener('DOMContentLoaded', () => {
  GameState.load();
});
