# SUSPECT-1999
**不要告诉它名字**

梦核 / 千禧年网页 / 90年代旧房子 / AI语音审讯风格的悬疑恐怖游戏。

玩家打开一个停留在千禧年风格的旧网页「南桥小区402寻人站」，调查1997年顾小满失踪案。

---

## 运行方法

```bash
cd SUSPECT-1999

pip install -r requirements.txt

python app.py
```

浏览器打开：**http://127.0.0.1:5000**

（建议在较暗环境下体验）

---

## 文件结构

```
SUSPECT-1999/
├── app.py                  Flask主程序，含所有路由和API
├── requirements.txt
├── .env.example            DeepSeek API配置模板
├── README.md
│
├── data/
│   ├── game_state.json     游戏状态初始值（运行时保存在session）
│   ├── characters.json     角色数据、system prompt、mock台词
│   └── evidence.json       12条证据档案内容
│
├── templates/
│   ├── base.html           基础布局（导航、时钟、计数器、CRT效果）
│   ├── index.html          首页（千禧年个人主页风格）
│   ├── case.html           案件资料页（时间线、规则、案情）
│   ├── chat.html           QQ风格聊天室
│   ├── evidence.html       证据档案页（可收集、弹窗详情）
│   └── ending.html         结局页（保存陷阱 demo）
│
└── static/
    ├── css/
    │   ├── millennium.css  千禧年旧网页全局基础样式
    │   └── style.css       各页面组件专用样式
    └── js/
        ├── state.js        游戏状态本地缓存
        ├── main.js         全局效果（时钟故障、计数器异常）
        └── chat.js         聊天室交互逻辑
```

---

## 当前阶段功能（第一阶段）

- [x] Flask 项目结构搭建完成
- [x] 千禧年旧网页风格 CSS（CRT扫描线、固定19:20时钟、访客计数器）
- [x] 首页：「南桥小区402寻人站」，闪烁文字、滚动字幕、失踪人员信息
- [x] 案件资料页：案情摘要、时间线、四条规则
- [x] QQ风格聊天室：5个角色可选，Enter发送，模拟打字延迟
- [x] 证据档案页：12条证据，可点击查看详情，收集进度追踪
- [x] 结局保存陷阱 demo：输入文件名触发恐怖反转文本逐行输出
- [x] 后端 API：`/api/chat`、`/api/collect_evidence`、`/api/save_replay`
- [x] Mock 角色回复（含关键词上下文反应）
- [x] DeepSeek API 接口预留（`get_character_reply` 函数结构）
- [x] 游戏状态 session 存储

---

## API 接口说明

| 方法 | 路由 | 说明 |
|------|------|------|
| GET  | `/` | 首页 |
| GET  | `/case` | 案件资料 |
| GET  | `/chat` | 聊天室 |
| GET  | `/evidence` | 证据档案 |
| GET  | `/ending` | 结局页 |
| POST | `/api/chat` | 角色对话 |
| POST | `/api/collect_evidence` | 收集证据 |
| POST | `/api/save_replay` | 保存结局（陷阱触发） |
| GET  | `/api/state` | 查看当前游戏状态 |

---

## 下一阶段计划

1. **接入 DeepSeek API**：替换 `get_character_reply` 中的 mock 逻辑，让每个角色根据 game_state 动态回答
2. **加入 Whisper 语音输入**：玩家可以直接对着麦克风问话
3. **加入 Edge-TTS 语音播放**：每个角色有不同音色，播放角色回复
4. **剧情状态推进**：根据收集证据数量和对话内容解锁新剧情阶段
5. **更多证据变化**：证据描述随游戏进度发生细微改变（越来越不对劲）
6. **完整真结局演出**：完整的 ending.html 叙事序列

---

## 核心恐怖规则（游戏内）

1. 不要在 **19:20** 后接电话。
2. 不要告诉网页你的**名字**。
3. 不要**保存**本页。被保存的不是网页，是房间。
4. **402** 不是地址，402是一个等待被命名的房间。
