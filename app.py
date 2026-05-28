#!/usr/bin/env python3
"""
🐉 棋局分析 - 云端版
DeepSeek API 分析 PGN，生成深色主题 HTML 报告
部署到 Render/Vercel 或本地运行
"""

import http.server
import json
import os
import re
import uuid
import urllib.request
import urllib.error
from pathlib import Path

# ========== 配置 ==========
PORT = int(os.environ.get("PORT", 8081))
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 报告缓存目录
REPORT_DIR = Path("/tmp/chess-reports")
REPORT_DIR.mkdir(exist_ok=True)

# ========== HTML 模板 ==========
FORM_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>🐉 棋局分析 - 大奶龙</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0d1117;color:#e6edf3;min-height:100vh;padding:16px}
.c{max-width:640px;margin:0 auto}
h1{text-align:center;font-size:1.6em;margin-bottom:8px;background:linear-gradient(135deg,#ff6b6b,#ffa500,#48dbfb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{text-align:center;color:#8b949e;font-size:.85em;margin-bottom:24px}
label{display:block;font-weight:600;margin-bottom:6px;color:#c9d1d9}
textarea{width:100%;height:240px;background:#161b22;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:12px;font-family:"SF Mono","Fira Code",monospace;font-size:13px;resize:vertical;outline:none;transition:border-color .2s}
textarea:focus{border-color:#58a6ff}
textarea::placeholder{color:#484f58}
.opts{display:flex;gap:12px;margin:16px 0;align-items:center;flex-wrap:wrap}
.opts label{margin:0;font-weight:400;font-size:.9em}
select{background:#161b22;border:1px solid #30363d;border-radius:6px;color:#e6edf3;padding:6px 10px;font-size:.9em;outline:none}
.btn{display:block;width:100%;padding:14px;background:linear-gradient(135deg,#238636,#2ea043);color:#fff;border:none;border-radius:8px;font-size:1.1em;font-weight:600;cursor:pointer;transition:opacity .2s;margin-top:16px}
.btn:hover{opacity:.9}
.btn:disabled{background:#21262d;color:#484f58;cursor:not-allowed}
.st{margin-top:16px;padding:12px;border-radius:8px;display:none;font-size:.9em}
.st.ld{display:block;background:#0d419d33;border:1px solid #1f6feb55;color:#58a6ff}
.st.er{display:block;background:#da363433;border:1px solid #f8514955;color:#f85149}
.st.ok{display:block;background:#23863633;border:1px solid #2ea04355;color:#3fb950}
.sp{display:inline-block;width:16px;height:16px;border:2px solid #58a6ff55;border-top-color:#58a6ff;border-radius:50%;animation:spin .8s linear infinite;vertical-align:middle;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
.ex{margin-top:24px;padding:16px;background:#161b22;border-radius:8px;border:1px solid #21262d}
.ex summary{cursor:pointer;color:#58a6ff;font-size:.85em}
.ex pre{background:#0d1117;padding:8px;border-radius:4px;font-size:11px;margin-top:8px;overflow-x:auto;white-space:pre}
.ft{text-align:center;margin-top:32px;color:#484f58;font-size:.75em}
</style>
</head>
<body>
<div class="c">
<h1>🐉 棋局分析</h1>
<p class="sub">粘贴 PGN → AI 分析 → 深色主题报告</p>

<label for="pgn" style="margin-top:8px">📝 PGN 棋谱</label>
<textarea id="pgn" placeholder="粘贴 PGN 到这里...&#10;&#10;支持格式：&#10;[Event &quot;...&quot;]&#10;1. e4 e5 2. Nf3 Nc6 ..."></textarea>

<div class="opts">
<label>分析级别：</label>
<select id="level">
<option value="quick">快速概览</option>
<option value="standard" selected>标准分析</option>
<option value="deep">深度分析</option>
</select>
</div>

<button class="btn" id="btn" onclick="analyze()">🔍 开始分析</button>

<div class="st" id="st"></div>

<details class="ex">
<summary>📝 PGN 示例</summary>
<pre>[Event "Rated Rapid game"]
[Site "https://lichess.org/Qht8lZz7"]
[White "ToromBot"]
[Black "YoBot_v2"]
[Result "1/2-1/2"]

1. c3 d5 2. d3 e5 3. Nf3 Nc6 4. Bf4 Bd6 5. Bg3 Nf6 1/2-1/2</pre>
</details>

<p class="ft">Powered by DeepSeek AI · 大奶龙 🐉</p>
</div>

<script>
async function analyze(){
const pgn=document.getElementById('pgn').value.trim();
const level=document.getElementById('level').value;
const btn=document.getElementById('btn');
const st=document.getElementById('st');

if(!pgn){show('er','❌ 请粘贴 PGN 棋谱');return}

btn.disabled=true;btn.textContent='⏳ 分析中...';
show('ld','<span class="sp"></span>AI 正在分析，请稍候...（约 30-90 秒）');

try{
const r=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pgn,level})});
const d=await r.json();
if(d.error){show('er','❌ '+d.error)}
else{show('ok','✅ 分析完成！开局：'+d.opening+' | 结果：'+d.result);setTimeout(()=>{window.location.href=d.url},1200)}
}catch(e){show('er','❌ 网络错误：'+e.message)}
finally{btn.disabled=false;btn.textContent='🔍 开始分析'}
}
function show(t,m){const s=document.getElementById('st');s.className='st '+t;s.innerHTML=m}
document.getElementById('pgn').addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter')analyze()});
</script>
</body>
</html>"""

# ========== DeepSeek 分析 Prompt ==========
ANALYSIS_PROMPT = {
    "quick": """你是一个国际象棋分析引擎。分析以下 PGN 棋谱，输出 JSON（不要输出其他内容）。

要求：
1. 识别开局名称
2. 判断对局结果
3. 每 8 步分一组，给出简要评价
4. 指出关键转折点

输出格式（严格 JSON）：
{
  "opening": "开局名称",
  "result": "结果（如 1-0, 0-1, 1/2-1/2）",
  "result_text": "中文结果（白胜/黑胜/和棋）",
  "summary": "50字以内的对局总结",
  "groups": [
    {
      "id": 1,
      "moves": "1. e4 e5 2. Nf3 Nc6",
      "phase": "开局",
      "eval": "均势",
      "comment": "简要评价"
    }
  ],
  "critical": "关键转折点描述"
}

PGN:
{pgn}""",

    "standard": """你是一个专业国际象棋分析引擎。详细分析以下 PGN 棋谱，输出 JSON（不要输出其他内容）。

要求：
1. 识别开局名称和 ECO 编码
2. 判断对局结果
3. 每 4 步分一组，给出详细评价
4. 指出每组的评估分数（-10 到 +10，正数白优，负数黑优）
5. 标注失误、疑问手、好棋
6. 给出开局/中局/残局阶段划分
7. 总结对局亮点和教训

输出格式（严格 JSON）：
{
  "meta": {
    "opening": "开局名称 (ECO编码)",
    "result": "1-0",
    "result_text": "白胜",
    "white": "白方",
    "black": "黑方",
    "event": "赛事"
  },
  "summary": {
    "total_groups": 30,
    "white_advantage": 5,
    "critical": "关键转折点"
  },
  "moves": [
    {
      "id": 1,
      "move_text": "1. e4 e5 2. Nf3 Nc6",
      "phase": "开局",
      "eval_text": "均势偏白",
      "eval_color": "#fef9c3",
      "eval_score": 0.3,
      "comment": "双方正常应对，西班牙开局的经典变化",
      "tip": "局面均衡，双方势均力敌。",
      "details": [
        {
          "move_num": 1,
          "san": "e4",
          "side": "白",
          "eval": "+0.3",
          "blunder": null,
          "best": "",
          "tip": "中心控制"
        }
      ]
    }
  ],
  "highlights": ["亮点1", "亮点2"],
  "lessons": ["教训1", "教训2"]
}

eval_color 映射规则：
- eval_score >= 1.5: "#bbf7d0" (深绿，白大优)
- eval_score >= 0.5: "#d9f99d" (浅绿，白优)
- eval_score >= -0.3: "#fef9c3" (黄，均势)
- eval_score >= -1.0: "#fed7aa" (橙，黑优)
- eval_score < -1.0: "#fecaca" (红，黑大优)

PGN:
{pgn}""",

    "deep": """你是一个特级大师级别的国际象棋分析引擎。深度分析以下 PGN 棋谱，输出 JSON（不要输出其他内容）。

要求：
1. 识别开局名称、ECO 编码、变例名称
2. 判断对局结果
3. 每 2 步分一组，给出特级大师级别的详细评价
4. 精确评估每步的分数变化
5. 标注所有失误、疑问手、好棋、妙手
6. 给出替代线路分析（如果某步走了其他着法会怎样）
7. 分析战略主题和战术主题
8. 总结对局的教育价值

输出格式（严格 JSON）：
{
  "meta": {
    "opening": "开局名称 (ECO编码) - 变例名",
    "result": "1-0",
    "result_text": "白胜",
    "white": "白方",
    "black": "黑方",
    "event": "赛事",
    "date": "日期"
  },
  "summary": {
    "total_groups": 60,
    "white_advantage": 3,
    "critical": "关键转折点",
    "strategic_themes": ["主题1", "主题2"],
    "tactical_themes": ["战术1", "战术2"]
  },
  "moves": [
    {
      "id": 1,
      "move_text": "1. e4 e5",
      "phase": "开局",
      "eval_text": "均势",
      "eval_color": "#fef9c3",
      "eval_score": 0.2,
      "comment": "开放性开局的标志性着法，控制中心关键格",
      "tip": "中心控制是开局的核心原则。",
      "alternative": "1. d4 会导致封闭性局面",
      "details": [
        {
          "move_num": 1,
          "san": "e4",
          "side": "白",
          "eval": "+0.2",
          "blunder": null,
          "best": "",
          "tip": "控制 d5 和 f5 格，释放象的活动空间"
        }
      ]
    }
  ],
  "highlights": ["亮点1", "亮点2"],
  "lessons": ["教训1", "教训2"],
  "educational_value": "本局的教育价值总结"
}

eval_color 映射规则：
- eval_score >= 2.0: "#86efac" (深绿，白胜势)
- eval_score >= 1.0: "#bbf7d0" (绿，白大优)
- eval_score >= 0.3: "#d9f99d" (浅绿，白优)
- eval_score >= -0.3: "#fef9c3" (黄，均势)
- eval_score >= -1.0: "#fed7aa" (橙，黑优)
- eval_score >= -2.0: "#fca5a5" (红，黑大优)
- eval_score < -2.0: "#fecaca" (深红，黑胜势)

PGN:
{pgn}"""
}

# ========== SVG 棋盘 ==========
PIECE_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

def fen_to_svg(fen, size=280):
    """将 FEN 转换为 SVG 棋盘"""
    if not fen:
        return '<div style="color:#484f58;font-size:12px">无棋盘数据</div>'
    
    parts = fen.split()
    board_fen = parts[0]
    rows = board_fen.split('/')
    
    sq = size // 8
    svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
    
    y = 0
    for row in rows:
        x = 0
        for ch in row:
            if ch.isdigit():
                for _ in range(int(ch)):
                    color = "#f0d9b5" if (x + y) % 2 == 0 else "#b58863"
                    svg += f'<rect x="{x*sq}" y="{y*sq}" width="{sq}" height="{sq}" fill="{color}"/>'
                    x += 1
            else:
                color = "#f0d9b5" if (x + y) % 2 == 0 else "#b58863"
                svg += f'<rect x="{x*sq}" y="{y*sq}" width="{sq}" height="{sq}" fill="{color}"/>'
                piece = PIECE_UNICODE.get(ch, '')
                font_size = int(sq * 0.75)
                svg += f'<text x="{x*sq + sq//2}" y="{y*sq + sq*0.78}" text-anchor="middle" font-size="{font_size}" fill="{"#000" if ch.isupper() else "#fff"}">{piece}</text>'
                x += 1
        y += 1
    
    svg += '</svg>'
    return svg


def generate_report_html(analysis, depth_label="AI 分析"):
    """从分析 JSON 生成完整 HTML 报告"""
    meta = analysis.get("meta", analysis.get("opening", {}))
    if isinstance(meta, str):
        meta = {"opening": meta}
    
    opening = meta.get("opening", "未知开局")
    result = meta.get("result", "?")
    result_text = meta.get("result_text", "未知")
    white = meta.get("white", "白方")
    black = meta.get("black", "黑方")
    event = meta.get("event", "")
    date = meta.get("date", "")
    
    summary = analysis.get("summary", {})
    if isinstance(summary, str):
        summary_text = summary
    else:
        summary_text = summary.get("critical", analysis.get("critical", ""))
    
    moves = analysis.get("moves", analysis.get("groups", []))
    highlights = analysis.get("highlights", [])
    lessons = analysis.get("lessons", [])
    
    # 评估颜色
    result_color = "#fbbf24"  # 默认黄色
    if "1-0" in result:
        result_color = "#4ade80"
    elif "0-1" in result:
        result_color = "#f87171"
    
    # 构建走法 HTML
    moves_html = ""
    for g in moves:
        gid = g.get("id", 0)
        move_text = g.get("move_text", g.get("moves", ""))
        phase = g.get("phase", "")
        eval_text = g.get("eval_text", g.get("eval", ""))
        eval_color = g.get("eval_color", "#fef9c3")
        eval_score = g.get("eval_score", 0)
        comment = g.get("comment", "")
        tip = g.get("tip", "")
        fen = g.get("fen", "")
        alternative = g.get("alternative", "")
        details = g.get("details", [])
        
        # 棋盘 SVG
        board_html = ""
        if fen:
            board_html = f'<div class="board">{fen_to_svg(fen)}</div>'
        
        # 详情行
        details_html = ""
        if details:
            details_html = '<div class="details">'
            for d in details:
                move_num = d.get("move_num", "")
                san = d.get("san", "")
                side = d.get("side", "")
                ev = d.get("eval", d.get("eval_text", ""))
                blunder = d.get("blunder")
                best = d.get("best", "")
                dtip = d.get("tip", "")
                
                blunder_html = ""
                if blunder:
                    blunder_html = f'<span class="blunder">{blunder}</span>'
                
                best_html = ""
                if best:
                    best_html = f'<span class="best">最佳：{best}</span>'
                
                details_html += f'''
                <div class="detail-row">
                    <span class="move-num">{move_num}</span>
                    <span class="side-{"w" if side=="白" else "b"}">{side}</span>
                    <span class="san">{san}</span>
                    <span class="eval-val">{ev}</span>
                    {blunder_html}{best_html}
                    {f'<span class="dtip">{dtip}</span>' if dtip else ''}
                </div>'''
            details_html += '</div>'
        
        alt_html = ""
        if alternative:
            alt_html = f'<div class="alternative">💡 替代着法：{alternative}</div>'
        
        moves_html += f'''
        <div class="group">
            <div class="group-header" onclick="this.parentElement.classList.toggle('open')">
                <div class="group-title">
                    <span class="group-num">#{gid}</span>
                    <span class="group-moves">{move_text}</span>
                    <span class="group-phase">{phase}</span>
                </div>
                <div class="group-eval" style="background:{eval_color}">{eval_text} ({eval_score:+.1f})</div>
            </div>
            <div class="group-body">
                {board_html}
                <div class="comment">{comment}</div>
                {f'<div class="tip">💡 {tip}</div>' if tip else ''}
                {alt_html}
                {details_html}
            </div>
        </div>'''
    
    # 亮点和教训
    highlights_html = ""
    if highlights:
        items = "".join(f"<li>{h}</li>" for h in highlights)
        highlights_html = f'<div class="section"><h3>⭐ 亮点</h3><ul>{items}</ul></div>'
    
    lessons_html = ""
    if lessons:
        items = "".join(f"<li>{l}</li>" for l in lessons)
        lessons_html = f'<div class="section"><h3>📚 教训</h3><ul>{items}</ul></div>'
    
    educational = analysis.get("educational_value", "")
    edu_html = f'<div class="section edu"><h3>🎓 教育价值</h3><p>{educational}</p></div>' if educational else ""
    
    # 完整 HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{white} vs {black} - 棋局分析</title>
<style>
:root{{
  --bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#e6edf3;
  --text2:#8b949e;--accent:#58a6ff;--green:#3fb950;--red:#f85149;
  --yellow:#d29922;--purple:#bc8cff;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;padding:16px}}
.container{{max-width:800px;margin:0 auto}}
.header{{text-align:center;padding:24px 0;border-bottom:1px solid var(--border);margin-bottom:24px}}
.header h1{{font-size:1.8em;margin-bottom:8px}}
.header .players{{font-size:1.2em;color:var(--accent);margin-bottom:4px}}
.header .result{{font-size:1.5em;font-weight:700;padding:8px 24px;border-radius:8px;display:inline-block}}
.header .meta{{color:var(--text2);font-size:.85em;margin-top:8px}}
.section{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}}
.section h3{{color:var(--accent);margin-bottom:12px;font-size:1.1em}}
.section ul{{padding-left:20px}}
.section li{{margin-bottom:6px;color:var(--text)}}
.edu p{{color:var(--text2)}}
.group{{background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:8px;overflow:hidden}}
.group-header{{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;cursor:pointer;transition:background .2s}}
.group-header:hover{{background:#1c2128}}
.group-title{{display:flex;align-items:center;gap:12px;flex:1;min-width:0}}
.group-num{{color:var(--text2);font-size:.8em;min-width:28px}}
.group-moves{{font-family:"SF Mono",monospace;font-size:.85em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.group-phase{{font-size:.75em;color:var(--purple);background:#bc8cff22;padding:2px 8px;border-radius:4px;white-space:nowrap}}
.group-eval{{font-size:.8em;font-weight:600;padding:4px 12px;border-radius:6px;white-space:nowrap;color:#111}}
.group-body{{display:none;padding:16px;border-top:1px solid var(--border)}}
.group.open .group-body{{display:block}}
.board{{text-align:center;margin:12px 0}}
.board svg{{max-width:100%;height:auto;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,.3)}}
.comment{{color:var(--text);margin:8px 0;padding:8px 12px;background:#21262d;border-radius:6px;border-left:3px solid var(--accent)}}
.tip{{color:var(--yellow);font-size:.85em;margin:4px 0}}
.alternative{{color:var(--text2);font-size:.85em;margin:4px 0;font-style:italic}}
.details{{margin-top:12px}}
.detail-row{{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:.8em;border-bottom:1px solid #21262d;flex-wrap:wrap}}
.move-num{{color:var(--text2);min-width:24px}}
.side-w{{color:#fff;background:#30363d;padding:1px 6px;border-radius:3px;font-size:.75em}}
.side-b{{color:#fff;background:#58a6ff;padding:1px 6px;border-radius:3px;font-size:.75em}}
.san{{font-weight:600;font-family:"SF Mono",monospace}}
.eval-val{{color:var(--text2)}}
.blunder{{color:var(--red);font-weight:600}}
.best{{color:var(--green);font-size:.85em}}
.dtip{{color:var(--text2);font-size:.85em;width:100%;margin-left:24px}}
.footer{{text-align:center;padding:24px 0;color:var(--text2);font-size:.8em;border-top:1px solid var(--border);margin-top:24px}}
@media(max-width:600px){{
  .group-title{{gap:8px}}
  .group-moves{{font-size:.75em}}
  .detail-row{{font-size:.75em}}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🐉 棋局分析报告</h1>
    <div class="players">{white} ⚔ {black}</div>
    <div class="result" style="background:{result_color}22;color:{result_color};border:2px solid {result_color}">{result_text} ({result})</div>
    <div class="meta">{f'开局：{opening}' if opening else ''} {f'| {event}' if event else ''} {f'| {date}' if date else ''}</div>
    <div class="meta">分析方式：{depth_label}</div>
  </div>

  <div class="section">
    <h3>📊 对局总结</h3>
    <p>{summary_text if isinstance(summary_text, str) else json.dumps(summary_text, ensure_ascii=False)}</p>
  </div>

  {highlights_html}
  {lessons_html}
  {edu_html}

  <h2 style="margin:24px 0 16px;color:var(--accent)">📋 逐步分析</h2>
  {moves_html}

  <div class="footer">
    <p>Powered by DeepSeek AI · 大奶龙 🐉</p>
    <p>分析仅供参考，AI 评估可能存在偏差</p>
  </div>
</div>

<script>
// 默认展开前3组
document.querySelectorAll('.group').forEach((g,i)=>{{if(i<3)g.classList.add('open')}});
</script>
</body>
</html>"""
    return html


# ========== DeepSeek API 调用 ==========
def call_deepseek(pgn, level, api_key):
    """调用 DeepSeek API 分析 PGN"""
    prompt = ANALYSIS_PROMPT[level].replace("{pgn}", pgn)
    
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业国际象棋分析引擎。只输出 JSON，不要输出任何其他文字。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 16000
    }).encode("utf-8")
    
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            
            print(f"[DEBUG] Raw ({len(content)} chars): {repr(content[:300])}", flush=True)
            
            # 提取 JSON（处理可能的 markdown 代码块）
            content = content.strip()
            if '```' in content:
                match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                else:
                    lines = content.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    content = '\n'.join(lines).strip()
            
            print(f"[DEBUG] Cleaned ({len(content)} chars): {repr(content[:500])}", flush=True)
            
            # Strategy 1: direct parse with strict=False
            try:
                result = json.loads(content, strict=False)
                print(f"[DEBUG] strict=False OK, keys: {list(result.keys())}", flush=True)
                return result
            except Exception as e1:
                print(f"[DEBUG] strict=False failed: {e1}", flush=True)
            
            # Strategy 2: fix newlines in strings, then parse
            try:
                import re as re2
                def fix_newlines(s):
                    out, in_str, esc = [], False, False
                    for c in s:
                        if esc:
                            out.append(c); esc = False
                        elif c == '\\':
                            out.append(c); esc = True
                        elif c == '"':
                            out.append(c); in_str = not in_str
                        elif c == '\n' and in_str:
                            out.append('\\n')
                        else:
                            out.append(c)
                    return ''.join(out)
                result = json.loads(fix_newlines(content), strict=False)
                print(f"[DEBUG] fix_newlines OK, keys: {list(result.keys())}", flush=True)
                return result
            except Exception as e2:
                print(f"[DEBUG] fix_newlines failed: {e2}", flush=True)
            
            # Strategy 3: regex extraction of key fields
            try:
                def extract_field(s, key):
                    m = re2.search(r'"' + key + r'"\s*:\s*"((?:[^"\\]|\\.)*)"\s*[,\n}]', s)
                    return m.group(1) if m else None
                def extract_list(s, key):
                    m = re2.search(r'"' + key + r'"\s*:\s*\[(.*?)\]', s, re2.DOTALL)
                    return m.group(1) if m else "[]"
                result = {
                    "meta": {
                        "opening": extract_field(content, "opening") or "未知",
                        "result_text": extract_field(content, "result_text") or "未知",
                        "result": extract_field(content, "result") or "*",
                        "white": extract_field(content, "white") or "白方",
                        "black": extract_field(content, "black") or "黑方",
                    },
                    "summary": {"critical": extract_field(content, "critical") or "分析完成"},
                    "moves": [],
                    "highlights": [],
                    "lessons": []
                }
                print(f"[DEBUG] regex fallback OK", flush=True)
                return result
            except Exception as e3:
                print(f"[DEBUG] regex also failed: {e3}", flush=True)
                raise Exception(f"JSON 解析全部失败: {str(e1)[:100]}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"API 错误 ({e.code}): {error_body[:200]}")
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON parse failed: {e}", flush=True)
        raise Exception(f"AI 返回的不是有效 JSON: {str(e)[:200]}")
    except Exception as e:
        raise Exception(f"API 调用失败: {str(e)}")


# ========== HTTP Handler ==========
class ChessHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/version":
            self.send_json(200, {"version": "9c05b58", "fix": "full-key"})
            return
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(FORM_HTML.encode("utf-8"))
        elif self.path.startswith("/report/"):
            filename = self.path.split("/")[-1]
            filepath = REPORT_DIR / filename
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(filepath.read_bytes())
            else:
                self.send_error(404, "报告不存在")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/analyze":
            self.handle_analyze()
        else:
            self.send_error(404)

    def handle_analyze(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            pgn = data.get("pgn", "").strip()
            level = data.get("level", "standard")

            if not pgn:
                self.send_json(400, {"error": "PGN 不能为空"})
                return
            if not DEEPSEEK_API_KEY:
                self.send_json(400, {"error": "服务器未配置 API Key"})
                return
            if level not in ANALYSIS_PROMPT:
                self.send_json(400, {"error": "无效的分析级别"})
                return
            
            # 调用 DeepSeek 分析
            print(f"[DEBUG] Starting analysis for level={level}", flush=True)
            analysis = call_deepseek(pgn, level, DEEPSEEK_API_KEY)
            print(f"[DEBUG] call_deepseek returned, keys: {list(analysis.keys())}", flush=True)
            
            # 生成报告
            level_labels = {"quick": "快速概览", "standard": "标准分析", "deep": "深度分析"}
            try:
                report_html = generate_report_html(analysis, level_labels.get(level, level))
                print(f"[DEBUG] Report generated OK ({len(report_html)} chars)", flush=True)
            except Exception as e:
                print(f"[DEBUG] generate_report_html FAILED: {type(e).__name__}: {e}", flush=True)
                raise
            
            # 保存报告
            game_id = uuid.uuid4().hex[:8]
            report_name = f"report-{game_id}.html"
            report_path = REPORT_DIR / report_name
            report_path.write_text(report_html, encoding="utf-8")
            
            # 提取元信息
            meta = analysis.get("meta", {})
            if isinstance(meta, str):
                opening = meta
                result_text = "未知"
            else:
                opening = meta.get("opening", analysis.get("opening", "未知"))
                result_text = meta.get("result_text", "未知")
            
            self.send_json(200, {
                "url": f"/report/{report_name}",
                "opening": opening,
                "result": result_text
            })
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[DEBUG] Exception: {e}\n{tb}", flush=True)
            self.send_json(500, {"error": str(e), "traceback": tb[-500:]})

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ========== 主程序 ==========
def main():
    print(f"🐉 棋局分析 Web 服务 (云端版)")
    print(f"📱 监听端口: {PORT}")
    print(f"🔑 API Key: {'已配置' if DEEPSEEK_API_KEY else '❌ 未设置 DEEPSEEK_API_KEY 环境变量'}")
    print(f"🤖 模型: {DEEPSEEK_MODEL}")
    print()
    
    server = http.server.HTTPServer(("0.0.0.0", PORT), ChessHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
# push fix Wed May 27 19:39:26 CST 2026
