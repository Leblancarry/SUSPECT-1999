import json
import os
import random
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nanqiao-402-1997-donottellit")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ─── 证据触发规则 ─────────────────────────────────────────────────────────────
# type: "chat"  → 聊天中匹配角色+关键词触发
# type: "page"  → 访问/点击页面元素触发（前端调 /api/page_trigger）
# type: "auto"  → 满足条件自动触发（在代码里判断）

EVIDENCE_TRIGGERS = {
    "E01": {"type": "page",  "trigger_id": "case_visit",    "hint": "在案件资料页查找"},
    "E02": {"type": "page",  "trigger_id": "index_photo",   "hint": "仔细看首页的照片"},
    "E03": {"type": "chat",  "characters": ["xu_yan"],
            "keywords": ["作业", "书包", "学校", "语文", "读书", "上学"],
            "hint": "和许延谈谈顾小满的学校生活"},
    "E04": {"type": "chat",  "characters": ["xu_yan"],
            "keywords": ["照片", "家人", "父母", "合照", "妈妈", "爸爸", "家庭"],
            "hint": "问问许延有没有家庭合照"},
    "E05": {"type": "chat",  "characters": ["master_ma"],
            "keywords": ["电话", "拨号", "通话", "打电话", "座机", "铃声"],
            "hint": "马师傅去402那天，有没有听到电话声"},
    "E06": {"type": "chat",  "characters": ["master_ma"],
            "keywords": ["电视", "维修", "修", "那天", "信号", "频道"],
            "hint": "问马师傅当年的维修细节"},
    "E07": {"type": "chat",  "characters": ["liu_ayi"],
            "keywords": ["小满", "孩子", "身高", "长高", "小孩", "个子"],
            "hint": "刘姨认识顾小满吗"},
    "E08": {"type": "page",  "trigger_id": "index_slippers","hint": "首页有个细节值得点一下"},
    "E09": {"type": "chat",  "characters": ["liu_ayi"],
            "keywords": ["楼道", "声音", "哭", "夜里", "晚上", "噪音", "叫"],
            "hint": "问问刘姨楼道里的事"},
    "E10": {"type": "chat",  "characters": ["xiaoman", "liu_ayi", "master_ma", "xu_yan", "admin"],
            "keywords": ["衣柜", "划痕", "柜子", "消失", "衣橱"],
            "hint": "和任何人谈谈402室的衣柜"},
    "E11": {"type": "page",  "trigger_id": "case_visit",    "hint": "在案件资料页查找"},
    "E12": {"type": "auto",  "hint": "收集所有其他证据后解锁"},
}

# 证据图片映射（有图的才填）
EVIDENCE_IMAGES = {
    "E01": "E01.png",
    "E03": "E03.png",
    "E04": "xiaoman_photo.png",
    "E08": "E08.png",
    "E10": "room_402.png",
    "E11": "E11.png",
}


def try_unlock_evidence(evidence_id: str, state: dict) -> list:
    """尝试解锁一条证据，返回实际解锁的ID列表（含自动触发的E12）"""
    newly = []
    collected = state.setdefault("evidence_collected", [])
    ev_data = load_json("evidence.json")
    valid_ids = [e["id"] for e in ev_data["evidence"]]
    if evidence_id in valid_ids and evidence_id not in collected:
        collected.append(evidence_id)
        newly.append(evidence_id)
    # 检查E12是否可以自动解锁
    non_e12 = [e for e in collected if e != "E12"]
    if len(non_e12) >= 11 and "E12" not in collected:
        collected.append("E12")
        newly.append("E12")
        state["ending_unlocked"] = True
    return newly


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def save_game_state(state):
    with open(os.path.join(DATA_DIR, "game_state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_game_state():
    if "game_state" not in session:
        session["game_state"] = load_json("game_state.json")
    return session["game_state"]


# ─── DeepSeek API ─────────────────────────────────────────────────────────────

def _build_state_context(game_state: dict) -> str:
    """把游戏状态转成给角色的背景提示，让角色知道玩家目前了解多少。"""
    collected = len(game_state.get("evidence_collected", []))
    lines = [
        "\n\n【当前游戏状态（仅你可见，不要直接告诉玩家）】",
        f"玩家已收集证据：{collected} 条",
        f"玩家已知19:20规则：{'是' if game_state.get('knows_1920_rule') else '否'}",
        f"玩家已知名字规则：{'是' if game_state.get('knows_name_rule') else '否'}",
        f"玩家已知402可迁移：{'是' if game_state.get('knows_402_can_migrate') else '否'}",
        f"玩家是否已注册名字：{'是，名字是' + game_state.get('visitor_name','') if game_state.get('visitor_registered') else '否'}",
        "\n根据以上状态，决定透露多少信息。证据越少、规则越不了解，越应该保持神秘和片段感。",
    ]
    return "\n".join(lines)


def _mock_reply(character_id: str, user_message: str) -> str:
    """没有 API key 时的 fallback 回复。"""
    characters = load_json("characters.json")
    if character_id not in characters:
        return "……"
    char = characters[character_id]
    replies = char.get("mock_replies", ["……"])

    if "名字" in user_message or "你叫" in user_message:
        contextual = {
            "xiaoman": "别问名字。我的意思是，别让它知道你的名字。",
            "liu_ayi": "名字的事你别多问，问多了它就记住你了。",
            "master_ma": "名字不能乱给。修电视我都不留名。",
            "xu_yan": "……不要告诉它任何名字。任何一个字都不行。",
            "admin": "检测到访客主动提及「名字」。建议立即设置昵称。",
        }
        return contextual.get(character_id, random.choice(replies))
    if "顾小满" in user_message or "小满" in user_message:
        contextual = {
            "xiaoman": "他……他存在过。你要记住这件事。",
            "liu_ayi": "那孩子挺好的，就是后来……大家好像都忘了他。我没忘。",
            "master_ma": "去修电视那天见过他，小孩，穿绿色拖鞋。后来就没了。",
            "xu_yan": "他是我表弟。他存在过。不管谁说什么，他存在过。",
            "admin": "搜索「顾小满」：未找到匹配记录。建议重新输入。",
        }
        return contextual.get(character_id, random.choice(replies))
    if "402" in user_message:
        contextual = {
            "xiaoman": "402不是地址。你来了就知道了。",
            "liu_ayi": "那间房子……你别往那边想，往那边想它就往你这边看。",
            "master_ma": "402我进去过一次，出来之后邻居说没见我进去。",
            "xu_yan": "我建这个网站是为了证明他存在。没想到网站本身也变成402了。",
            "admin": "房间编号402当前状态：迁移就绪。等待目标命名。",
        }
        return contextual.get(character_id, random.choice(replies))
    if "19:20" in user_message or "1920" in user_message:
        contextual = {
            "xiaoman": "19:20不要接电话。记住。",
            "liu_ayi": "19:20那个时间点，手机也不要接，不只是座机。",
            "master_ma": "我去402修电视，到的时间是19:15，出来的时候表显示是19:20，但外面天都黑了。",
            "xu_yan": "小满失踪是19:20。我建站上线也是19:20。我不是故意的。",
            "admin": "当前时间：19:20。建议访客检查周围环境。",
        }
        return contextual.get(character_id, random.choice(replies))
    return random.choice(replies)


def get_character_reply(character_id: str, user_message: str, game_state: dict,
                        api_key_override: str = "") -> str:
    # 优先级：玩家自带 key → 服务器环境变量 → mock 回复
    api_key = api_key_override.strip() or os.getenv("DEEPSEEK_API_KEY", "").strip()

    if not api_key:
        return _mock_reply(character_id, user_message)

    characters = load_json("characters.json")
    if character_id not in characters:
        return "……"
    char = characters[character_id]

    # 格式约束前缀：防止 AI 输出动作描写/剧本格式
    FORMAT_RULES = (
        "【发消息格式，绝对禁止违反】\n"
        "你在QQ聊天窗口里打字，不是在写小说、剧本或角色扮演。\n"
        "以下内容一律禁止出现，无论什么情况：\n"
        "- 全角括号里的动作/神态：（停顿）（忽然停住）（沉默）（叹气）（皱眉）（犹豫）（转移话题）等任何此类\n"
        "- 半角括号里的动作：(沉默)(停顿) 等\n"
        "- 星号包裹的动作：*叹气* *停顿* 等\n"
        "- 方括号动作：【皱眉】【沉默】 等\n"
        "- 书名号动作：「沉默」「停顿」 等\n"
        "- 任何描述肢体、表情、情绪状态的词，哪怕只有两个字\n"
        "你只能输出纯文字，就像在手机上给朋友发短消息。\n"
        "每条消息1到3句，简短自然。禁止markdown、禁止分段编号、禁止重复自己名字。\n\n"
    )
    # System prompt = 格式规则 + 角色设定 + 当前游戏状态
    system_content = FORMAT_RULES + char["system_prompt"] + _build_state_context(game_state)

    # 带入本角色最近 6 轮对话历史，给 AI 上下文
    history = game_state.get("chat_history", [])
    char_history = [h for h in history if h["character"] == character_id][-6:]

    messages = [{"role": "system", "content": system_content}]
    for h in char_history:
        messages.append({"role": "user",      "content": h["user"]})
        messages.append({"role": "assistant", "content": h["reply"]})
    messages.append({"role": "user", "content": user_message})

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=messages,
            max_tokens=120,
            temperature=0.85,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DeepSeek ERROR] {e}", flush=True)
        return _mock_reply(character_id, user_message)


# ─── Page routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    state = get_game_state()
    return render_template("index.html", state=state)


@app.route("/case")
def case():
    state = get_game_state()
    return render_template("case.html", state=state)


@app.route("/chat")
def chat():
    state = get_game_state()
    characters = load_json("characters.json")
    return render_template("chat.html", state=state, characters=characters)


@app.route("/evidence")
def evidence():
    state = get_game_state()
    evidence_data = load_json("evidence.json")
    collected = state.get("evidence_collected", [])
    hints = {eid: t.get("hint", "") for eid, t in EVIDENCE_TRIGGERS.items()}
    images = EVIDENCE_IMAGES
    return render_template("evidence.html", state=state,
                           evidence=evidence_data["evidence"],
                           collected=collected, hints=hints, images=images)


@app.route("/ending")
def ending():
    state = get_game_state()
    ending_unlocked = state.get("ending_unlocked", False)
    collected_count = len(state.get("evidence_collected", []))
    return render_template("ending.html", state=state,
                           ending_unlocked=ending_unlocked,
                           collected_count=collected_count)


# ─── API routes ───────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    character_id = data.get("character_id", "admin")
    message = data.get("message", "")
    state = get_game_state()

    if not message.strip():
        return jsonify({"reply": "……", "state_updates": {}})

    # 玩家自带 key（存于 session）
    user_apikey = session.get("user_apikey", "")
    reply = get_character_reply(character_id, message, state, api_key_override=user_apikey)

    # Track chat history
    state.setdefault("chat_history", []).append({
        "character": character_id,
        "user": message,
        "reply": reply,
        "timestamp": datetime.now().strftime("%H:%M"),
    })

    # State updates based on conversation content
    state_updates = {}
    if "19:20" in reply or "19:20" in message:
        state["knows_1920_rule"] = True
        state_updates["knows_1920_rule"] = True
    if "名字" in reply:
        state["knows_name_rule"] = True
        state_updates["knows_name_rule"] = True

    # 聊天触发证据解锁
    newly_unlocked = []
    combined = message + " " + reply
    for eid, trigger in EVIDENCE_TRIGGERS.items():
        if trigger["type"] != "chat":
            continue
        if character_id not in trigger["characters"]:
            continue
        if eid in state.get("evidence_collected", []):
            continue
        if any(kw in combined for kw in trigger["keywords"]):
            newly_unlocked.extend(try_unlock_evidence(eid, state))
    if newly_unlocked:
        state_updates["newly_unlocked"] = newly_unlocked

    session["game_state"] = state
    return jsonify({"reply": reply, "state_updates": state_updates})


@app.route("/api/collect_evidence", methods=["POST"])
def api_collect_evidence():
    data = request.get_json()
    evidence_id = data.get("evidence_id", "")
    state = get_game_state()

    evidence_data = load_json("evidence.json")
    valid_ids = [e["id"] for e in evidence_data["evidence"] if not e.get("locked")]

    if evidence_id not in valid_ids:
        return jsonify({"success": False, "message": "无效证据ID或证据已锁定"})

    collected = state.setdefault("evidence_collected", [])
    if evidence_id not in collected:
        collected.append(evidence_id)

    if len(collected) >= 5:
        state["knows_guxiaoman_exists"] = True
    if len(collected) >= 8:
        state["knows_402_can_migrate"] = True

    session["game_state"] = state
    return jsonify({"success": True, "evidence_collected": collected})


@app.route("/api/page_trigger", methods=["POST"])
def api_page_trigger():
    data = request.get_json()
    trigger_id = data.get("trigger_id", "")
    state = get_game_state()

    # 找出所有匹配此 trigger_id 的证据
    newly_unlocked = []
    for eid, trigger in EVIDENCE_TRIGGERS.items():
        if trigger.get("trigger_id") == trigger_id:
            newly_unlocked.extend(try_unlock_evidence(eid, state))

    # 更新知识状态
    collected = state.get("evidence_collected", [])
    if len(collected) >= 5:
        state["knows_guxiaoman_exists"] = True
    if len(collected) >= 8:
        state["knows_402_can_migrate"] = True

    session["game_state"] = state
    return jsonify({
        "newly_unlocked": newly_unlocked,
        "evidence_collected": collected
    })


@app.route("/api/save_filename", methods=["POST"])
def api_save_filename():
    """第一步：保存文件名，返回「成功」，引导玩家进入第二步"""
    data = request.get_json()
    filename = data.get("filename", "").strip()
    if not filename:
        return jsonify({"error": "文件名不能为空"}), 400
    safe = filename.replace("/", "").replace("\\", "").replace("..", "")[:32]
    state = get_game_state()
    state["pending_filename"] = safe
    session["game_state"] = state
    return jsonify({"filename": safe, "ok": True})


@app.route("/api/save_replay", methods=["POST"])
def api_save_replay():
    """第二步：输入调查人员姓名 → 触发恐怖反转"""
    data = request.get_json()
    investigator = data.get("investigator", "").strip()
    if not investigator:
        return jsonify({"error": "请填写调查人员姓名"}), 400

    safe_name = investigator.replace("/", "").replace("\\", "").replace("..", "")[:32]
    state = get_game_state()
    filename = state.get("pending_filename", "report")
    state["player_saved_replay"] = True
    state["visitor_name"] = safe_name
    state["visitor_registered"] = True
    session["game_state"] = state

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        # ── 表面正常：归档流程 ──────────────────────
        "归档确认中……",
        f"文件：{filename}.html",
        f"调查人员：{safe_name}",
        f"时间：{now}",
        "",
        # ── 假装关闭 ────────────────────────────────
        "正在关闭402档案……",
        "正在关闭402档案……",
        "正在关闭402档案……",
        "",
        "ERROR：402不是一个可以关闭的档案。",
        "402是一个可以迁移的空间。",
        "",
        # ── 规则回调：玩家早就被警告过 ──────────────
        "检测到访客已阅读【已知规则 / 许延整理】。",
        "第二条：不要在本站任何输入框填写真实姓名。",
        "你选择了填写。",
        "",
        # ── 重新解析 ────────────────────────────────
        "重新解析输入信息……",
        f"文件名：{filename}  →  已废弃",
        f"调查人员：{safe_name}  →  正在识别……",
        "",
        # ── 名字定性 ────────────────────────────────
        f"「{safe_name}」不是调查人员的名字。",
        f"「{safe_name}」是你的名字。",
        "",
        # ── 坐标定位：更亲密、更侵入 ────────────────
        "正在通过名称定位坐标……",
        "已找到：一台运行中的设备",
        "已找到：当前打开的浏览器窗口",
        "已找到：坐在屏幕前的人",
        f"已找到：{safe_name}",
        "",
        "坐标锁定完成。",
        "",
        # ── 指控：有重量，逐行落下 ──────────────────
        f"{safe_name}，你看过规则的。",
        "你还是填了。",
        "",
        # ── 合同揭示 ────────────────────────────────
        "你签的不是调查档案。",
        "你签的是入住协议。",
        "",
        # ── 最终结果 ────────────────────────────────
        "402.html 迁移完成。",
        f"新站长：{safe_name}",
        f"原站长：许延  ·  状态：已离开",
    ]

    return jsonify({"accepted_name": safe_name, "filename": filename, "lines": lines})


@app.route("/api/set_apikey", methods=["POST"])
def api_set_apikey():
    """玩家提交自己的 DeepSeek API Key，存入 session（不持久化，关闭浏览器即失效）"""
    data = request.get_json()
    key = data.get("apikey", "").strip()
    if key:
        session["user_apikey"] = key
    else:
        session.pop("user_apikey", None)
    has_key = bool(key or os.getenv("DEEPSEEK_API_KEY", "").strip())
    return jsonify({"ok": True, "has_key": has_key, "source": "player" if key else ("server" if os.getenv("DEEPSEEK_API_KEY") else "none")})


@app.route("/api/apikey_status", methods=["GET"])
def api_apikey_status():
    """返回当前 AI 模式状态，不暴露 key 本身"""
    player_key = session.get("user_apikey", "")
    server_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if player_key:
        source = "player"
    elif server_key:
        source = "server"
    else:
        source = "none"
    return jsonify({"has_key": bool(player_key or server_key), "source": source})


@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(get_game_state())


@app.route("/api/contamination", methods=["GET"])
def api_contamination():
    """返回当前污染等级（0-4），供前端 contamination.js 控制视觉效果强度。"""
    state = get_game_state()
    count = len(state.get("evidence_collected", []))
    if   count == 0: lv = 0
    elif count <= 3: lv = 1
    elif count <= 6: lv = 2
    elif count <= 9: lv = 3
    else:            lv = 4
    return jsonify({"level": lv, "evidence_count": count})


@app.route("/reset")
def reset():
    """清空游戏进度，重新开始——仅供开发/测试使用，不出现在游戏 UI 中"""
    session.clear()
    from flask import redirect
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
