#!/usr/bin/env python3
"""돈되는 호형 이슈 카드뉴스 렌더러 (아침 카드뉴스와 같은 디자인 + 3D 이모지 그림 + 짤 장)
cards.json -> 1080x1350 PNG, 마지막에 로고 장 자동 추가
사용법: python3 make_issue_cards.py cards.json out_dir
"""
import html, json, re, sys, os, glob, base64
from playwright.sync_api import sync_playwright

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
NV, YL, RD, BL, WH = "#17204A", "#FFE14F", "#E2302A", "#1E5CE0", "#FFFFFF"


def font_dir():
    for c in glob.glob(os.path.join(HERE, "node_modules/pretendard/dist/web/static/woff2")) + \
             glob.glob(os.path.join(os.getcwd(), "node_modules/pretendard/dist/web/static/woff2")):
        return c
    sys.exit("Pretendard 폰트가 없습니다: npm install pretendard@1.3.9")


EMOJI_DIRS = glob.glob(os.path.join(HERE, "node_modules/@lobehub/fluent-emoji-3d/assets")) + \
    glob.glob(os.path.join(os.getcwd(), "node_modules/@lobehub/fluent-emoji-3d/assets"))
MISSING = []


def emoji_img(e):
    cps = [f"{ord(ch):x}" for ch in e]
    for name in ("-".join(cps), "-".join(x for x in cps if x != "fe0f")):
        for d in EMOJI_DIRS:
            f = os.path.join(d, name + ".webp")
            if os.path.exists(f):
                return "data:image/webp;base64," + base64.b64encode(open(f, "rb").read()).decode()
    return None


def fmt(s):
    s = html.escape(str(s))
    s = re.sub(r"==(.+?)==", r"<mark>\1</mark>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("\n", "<br>")


ART = {}

CSS = """
@font-face{font-family:P;src:url('{fd}/Pretendard-Regular.woff2');font-weight:400}
@font-face{font-family:P;src:url('{fd}/Pretendard-Medium.woff2');font-weight:500}
@font-face{font-family:P;src:url('{fd}/Pretendard-SemiBold.woff2');font-weight:600}
@font-face{font-family:P;src:url('{fd}/Pretendard-Bold.woff2');font-weight:700}
@font-face{font-family:P;src:url('{fd}/Pretendard-ExtraBold.woff2');font-weight:800}
@font-face{font-family:P;src:url('{fd}/Pretendard-Black.woff2');font-weight:900}
:root{--ink:#17204A;--body:#2E3550;--muted:#6E7488;--paper:#F5F6F9;--line:#DCE0E8;
--marker:#FFE14F;--up:#E2302A;--down:#1E5CE0;--panel:#FFFFFF;--s:1}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden}
body{font-family:P,sans-serif;color:var(--body);background:var(--paper);word-break:keep-all;
-webkit-font-smoothing:antialiased;font-feature-settings:'tnum' 1}
.card{position:relative;width:1080px;height:1350px;padding:84px 92px 0;display:flex;flex-direction:column}
.top{display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:700;color:var(--ink);height:48px}
.top .page{font-weight:600;color:var(--muted);font-size:26px}
.brand{display:flex;align-items:center;gap:14px}
.brand{font-size:30px;font-weight:900;letter-spacing:-0.03em}
.coin{display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:50%;background:var(--ink);color:var(--marker);font-size:25px;font-weight:900;position:relative;letter-spacing:0}
.coin:before{content:'';position:absolute;inset:4px;border-radius:50%;border:2px dashed rgba(255,225,79,.55)}
.body{flex:1;overflow:hidden;padding-top:calc(52px*var(--s));display:flex;flex-direction:column;position:relative}
.foot{height:100px;display:flex;align-items:center;justify-content:space-between;font-size:22px;color:var(--muted);border-top:2px solid var(--line);margin-top:24px}
.foot .src{max-width:760px;line-height:1.4}
mark{background:linear-gradient(transparent 52%,var(--marker) 52%,var(--marker) 92%,transparent 92%);color:inherit;padding:0 4px}
b{font-weight:800;color:var(--ink)}
h1{font-size:calc(70px*var(--s));line-height:1.22;font-weight:900;color:var(--ink);letter-spacing:-0.035em}
.tag{display:inline-block;align-self:flex-start;font-size:calc(28px*var(--s));font-weight:700;color:var(--ink);background:var(--marker);padding:8px 18px;border-radius:999px;margin-bottom:calc(28px*var(--s))}
p{font-size:calc(37px*var(--s));line-height:1.62;letter-spacing:-0.015em;margin-top:calc(30px*var(--s))}
.lead{margin-top:calc(34px*var(--s))}
.art{position:absolute;right:0;top:calc(30px*var(--s));width:calc(220px*var(--s));height:calc(220px*var(--s))}
.art svg{width:100%;height:100%;display:block}
.art.emo{padding:14px}
.art.emo img{width:100%;height:100%;display:block;object-fit:contain;filter:drop-shadow(0 14px 18px rgba(23,32,74,.18))}
.dark .art.emo{padding:58px}
.has-art h1{padding-right:calc(232px*var(--s))}
.cover .art{top:430px;right:0;width:360px;height:360px}
.cover.has-art h1{padding-right:0}
.cover{background:var(--marker)}
.cover .foot{border-top-color:rgba(23,32,74,.18);color:var(--ink)}
.cover .date{font-size:34px;font-weight:700;color:var(--ink);margin-top:110px}
.cover h1{font-size:calc(116px*var(--s));line-height:1.13;letter-spacing:-0.045em;margin-top:36px;position:relative;z-index:1}
.cover .sub{font-size:calc(40px*var(--s));line-height:1.5;font-weight:500;color:var(--ink);margin-top:auto;margin-bottom:48px;max-width:820px}
.cover mark{background:none;color:var(--up)}
.swipe{display:flex;align-items:center;gap:16px;font-weight:700;font-size:26px;color:var(--ink)}
.swipe span{display:block;width:56px;height:56px;border-radius:50%;background:var(--ink);position:relative}
.swipe span:after{content:'';position:absolute;left:19px;top:20px;width:14px;height:14px;border-top:4px solid var(--marker);border-right:4px solid var(--marker);transform:rotate(45deg)}
.stats{margin-top:calc(26px*var(--s));display:flex;flex-direction:column}
.stat{padding:calc(30px*var(--s)) 0;border-bottom:2px solid var(--line);display:grid;grid-template-columns:1fr;row-gap:6px}
.stat:last-child{border-bottom:none}
.stat .lab{font-size:calc(30px*var(--s));font-weight:600;color:var(--muted)}
.stat .val{font-size:calc(82px*var(--s));font-weight:800;letter-spacing:-0.035em;color:var(--ink);line-height:1.1;display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}
.stat .chg{font-size:calc(36px*var(--s));font-weight:700}
.up .val,.up .chg{color:var(--up)} .down .val,.down .chg{color:var(--down)}
.stat .note{font-size:calc(28px*var(--s));color:var(--body);line-height:1.45}
.steps{margin-top:calc(40px*var(--s));position:relative}
.step{display:grid;grid-template-columns:64px 1fr;column-gap:28px;position:relative;padding-bottom:calc(30px*var(--s))}
.step:not(:last-child):before{content:'';position:absolute;left:30px;top:64px;bottom:0;width:4px;background:var(--line)}
.step .n{width:64px;height:64px;border-radius:50%;background:var(--ink);color:#fff;font-weight:800;font-size:30px;display:flex;align-items:center;justify-content:center}
.step:last-child .n{background:var(--marker);color:var(--ink)}
.step .t{font-size:calc(38px*var(--s));font-weight:800;color:var(--ink);line-height:1.3;padding-top:10px}
.step .d{font-size:calc(31px*var(--s));line-height:1.5;margin-top:6px}
.panel{background:var(--panel);border-radius:28px;padding:calc(38px*var(--s)) calc(44px*var(--s));margin-top:calc(40px*var(--s));border:2px solid var(--line)}
.panel .pt{font-size:calc(30px*var(--s));font-weight:800;color:var(--ink)}
.panel .pd{font-size:calc(33px*var(--s));line-height:1.55;margin-top:12px}
.list{margin-top:calc(30px*var(--s))}
.li{display:grid;grid-template-columns:230px 1fr;column-gap:30px;padding:calc(30px*var(--s)) 0;border-bottom:2px solid var(--line)}
.li:last-child{border-bottom:none}
.li .k{font-size:calc(36px*var(--s));font-weight:800;color:var(--ink);line-height:1.3}
.li .v{font-size:calc(33px*var(--s));line-height:1.5}
.li .v b{display:block;font-size:calc(36px*var(--s));margin-bottom:6px}
.points{margin-top:calc(40px*var(--s));counter-reset:pt}
.pt-i{font-size:calc(38px*var(--s));line-height:1.55;padding:calc(28px*var(--s)) 0 calc(28px*var(--s)) 76px;position:relative;border-bottom:2px solid var(--line);counter-increment:pt}
.pt-i:before{content:counter(pt);position:absolute;left:0;top:calc(28px*var(--s));width:52px;height:52px;border-radius:50%;background:var(--marker);color:var(--ink);font-weight:800;font-size:28px;display:flex;align-items:center;justify-content:center}
.cta{margin-top:auto;margin-bottom:12px;background:var(--ink);color:#fff;border-radius:28px;padding:36px 44px;font-size:calc(34px*var(--s));line-height:1.5;font-weight:600}
.cta b{color:var(--marker)}
.disc{font-size:22px;color:var(--muted);margin-top:18px;line-height:1.45}
.series{display:inline-block;align-self:flex-start;background:var(--marker);color:var(--ink);font-size:32px;font-weight:800;padding:12px 26px;border-radius:999px;margin-top:70px;letter-spacing:-0.02em}
.dark{background:var(--ink)}
.dark .top{color:#fff} .dark .top .page{color:#AEB3C6}
.dark .coin{background:var(--marker);color:var(--ink)} .dark .coin:before{border-color:rgba(23,32,74,.45)}
.dark.cover .date{color:#C9CDDB;margin-top:28px;font-size:30px;font-weight:600}
.dark.cover h1{color:#fff}
.dark.cover mark{color:var(--marker)}
.dark.cover .sub{color:#E3E6EF}
.dark.cover .foot{border-top-color:rgba(255,255,255,.18);color:#fff}
.dark .swipe{color:#fff} .dark .swipe span{background:var(--marker)}
.dark .swipe span:after{border-color:var(--ink)}
.dark .art{background:#F5F6F9;border-radius:50%;padding:46px}
.cover .kicker{font-size:50px;font-weight:800;color:rgba(255,255,255,.88);margin-top:56px;line-height:1.3;letter-spacing:-0.03em}
.cover .big{font-weight:900;color:var(--marker);line-height:1;letter-spacing:-0.05em;margin-top:18px;white-space:nowrap}
.cover.st-number h1{font-size:calc(96px*var(--s));margin-top:22px}
.cover.st-versus h1,.cover.st-quiz h1{font-size:calc(100px*var(--s))}
.cover.st-number .art,.cover.st-versus .art,.cover.st-quiz .art{top:30px;width:250px;height:250px;padding:36px}
.vs{display:flex;align-items:stretch;gap:20px;margin-top:56px}
.vs .box{flex:1;border-radius:32px;padding:34px 30px;background:rgba(255,255,255,.08);border:3px solid rgba(255,255,255,.28)}
.vs .box.after{background:var(--marker);border-color:var(--marker)}
.vs .lab{font-size:34px;font-weight:700;color:rgba(255,255,255,.75)}
.vs .after .lab{color:var(--ink)}
.vs .val{font-weight:900;color:#fff;letter-spacing:-0.04em;margin-top:12px;line-height:1.1;white-space:nowrap}
.vs .after .val{color:var(--ink)}
.vs .arr{align-self:center;font-size:70px;color:var(--marker);font-weight:900}
.quiz-q{font-size:56px;font-weight:900;color:var(--marker);margin-top:56px;line-height:1}
.cover.st-quiz h1{margin-top:18px}
.ox{display:flex;gap:26px;margin-top:52px}
.ox div{flex:1;height:150px;border-radius:30px;display:flex;align-items:center;justify-content:center;font-weight:900;color:var(--ink);letter-spacing:-0.03em}
.ox .o{background:var(--marker)} .ox .x{background:#fff}
.hint{font-size:32px;font-weight:700;color:rgba(255,255,255,.75);margin-top:24px}
.sticker{position:absolute;left:-40px;top:-30px;width:180px;height:180px;border-radius:50%;background:var(--up);color:#fff;font-size:38px;font-weight:900;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.15;transform:rotate(-12deg);box-shadow:0 8px 0 rgba(0,0,0,.2);z-index:3;letter-spacing:-0.03em;padding:14px}
.st-number .sticker,.st-versus .sticker,.st-quiz .sticker{width:140px;height:140px;font-size:30px;left:-70px;top:-14px}
.sticker.solo{left:auto;right:0;top:40px}
.dark.bg-red{background:var(--up)} .dark.bg-blue{background:var(--down)}
.bg-red .sticker{background:var(--marker);color:var(--ink)}
.dark.bg-red.cover .date,.dark.bg-blue.cover .date{color:rgba(255,255,255,.8)}
.dark.bg-red .top .page,.dark.bg-blue .top .page{color:rgba(255,255,255,.75)}
.meme .body{padding-top:calc(36px*var(--s))}
.mbox{position:relative;width:100%;height:calc(700px*var(--s));border-radius:32px;overflow:hidden;background:var(--mbg,#FFE14F);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.mbox img.ph{width:100%;height:100%;object-fit:cover;display:block}
.mbox img.ph.contain{object-fit:contain;background:#fff;padding:24px}
.mbox img.em{width:62%;height:62%;object-fit:contain;filter:drop-shadow(0 22px 26px rgba(23,32,74,.28))}
.mbox .em2{position:absolute;width:30%;height:30%;object-fit:contain;right:5%;bottom:5%;filter:drop-shadow(0 14px 18px rgba(23,32,74,.3))}
.bubble{position:absolute;left:6%;top:7%;max-width:62%;background:#fff;color:var(--ink);border:5px solid var(--ink);border-radius:36px;padding:22px 32px;font-size:calc(46px*var(--s));font-weight:900;line-height:1.25;letter-spacing:-0.03em;z-index:2;box-shadow:0 8px 0 rgba(23,32,74,.18)}
.bubble:after{content:'';position:absolute;left:70px;bottom:-34px;border:18px solid transparent;border-top:26px solid var(--ink)}
.bubble.r{left:auto;right:6%}
.mtag{position:absolute;right:4%;top:5%;background:var(--up);color:#fff;font-size:30px;font-weight:900;padding:8px 18px;border-radius:12px;transform:rotate(4deg);z-index:2}
.setup{font-size:calc(42px*var(--s));line-height:1.4;color:var(--body);text-align:center;margin-top:calc(46px*var(--s));letter-spacing:-0.02em}
.punch{font-size:calc(66px*var(--s));line-height:1.22;font-weight:900;color:var(--up);text-align:center;margin-top:calc(14px*var(--s));letter-spacing:-0.04em}
.punch mark{background:none;color:var(--down)}
.credit{position:absolute;left:14px;bottom:10px;font-size:18px;color:#fff;background:rgba(0,0,0,.45);padding:3px 10px;border-radius:8px}
.outro{background:var(--marker);align-items:center;justify-content:center;padding:0}
.outro .big{width:560px;height:560px;border-radius:50%;background:var(--ink);color:var(--marker);display:flex;align-items:center;justify-content:center;font-size:300px;font-weight:900;position:relative}
.outro .big:before{content:'';position:absolute;inset:38px;border-radius:50%;border:13px dashed rgba(255,225,79,.55)}
.outro .name{margin-top:60px;font-size:100px;font-weight:900;color:var(--ink);letter-spacing:-0.04em}
.outro .line{margin-top:20px;font-size:40px;font-weight:600;color:var(--ink)}
"""


def has_art(c):
    return c.get("art") in ART or bool(c.get("emoji") and emoji_img(c["emoji"]))


def render_body(c, series=""):
    t = c["type"]
    if t == "meme":
        h = []
        bg = c.get("bg", "#FFE14F")
        inner = ""
        if c.get("photo") and os.path.exists(c["photo"]):
            ext = os.path.splitext(c["photo"])[1].lower().strip(".").replace("jpg", "jpeg")
            uri = f"data:image/{ext};base64," + base64.b64encode(open(c["photo"], "rb").read()).decode()
            fit = " contain" if c.get("fit") == "contain" else ""
            inner += f'<img class="ph{fit}" src="{uri}" alt="">'
        elif c.get("emoji"):
            e1 = emoji_img(c["emoji"])
            if e1:
                inner += f'<img class="em" src="{e1}" alt="">'
            else:
                MISSING.append(c["emoji"])
        if c.get("emoji2"):
            e2 = emoji_img(c["emoji2"])
            if e2:
                inner += f'<img class="em2" src="{e2}" alt="">'
            else:
                MISSING.append(c["emoji2"])
        if c.get("bubble"):
            inner += f'<div class="bubble{" r" if c.get("bubble_side") == "right" else ""}">{fmt(c["bubble"])}</div>'
        if c.get("label"):
            inner += f'<div class="mtag">{fmt(c["label"])}</div>'
        if c.get("credit"):
            inner += f'<div class="credit">{fmt(c["credit"])}</div>'
        h.append(f'<div class="mbox" style="--mbg:{bg}">{inner}</div>')
        if c.get("setup"):
            h.append(f'<div class="setup">{fmt(c["setup"])}</div>')
        h.append(f'<div class="punch">{fmt(c.get("punch",""))}</div>')
        return "".join(h)
    h = []
    em = emoji_img(c["emoji"]) if c.get("emoji") else None
    if c.get("emoji") and not em:
        MISSING.append(c["emoji"])
    if em:
        h.append(f'<div class="art emo"><img src="{em}" alt=""></div>')
    if t == "cover":
        st = c.get("style", "classic")
        if c.get("sticker"):
            stk = f'<div class="sticker">{fmt(c["sticker"])}</div>'
            if h:
                h[0] = re.sub(r'(<div class="art[^"]*">)', lambda m: m.group(1) + stk, h[0], count=1)
            else:
                h.append(stk.replace('class="sticker"', 'class="sticker solo"'))
        if series:
            h.append(f'<div class="series">{fmt(series)}</div>')
        h.append(f'<div class="date">{fmt(c.get("date",""))}</div>')
        if st == "number":
            big = str(c.get("big", ""))
            size = min(300, int(880 / (max(len(big), 1) * 0.66)))
            if c.get("kicker"):
                h.append(f'<div class="kicker">{fmt(c["kicker"])}</div>')
            h.append(f'<div class="big" style="font-size:{size}px">{fmt(big)}</div>')
            h.append(f'<h1>{fmt(c["title"])}</h1>')
        elif st == "versus":
            h.append(f'<h1>{fmt(c["title"])}</h1>')
            v = c.get("vs", {})
            boxes = []
            for k in ("before", "after"):
                it = v.get(k, {})
                val = str(it.get("value", ""))
                size = min(88, int(330 / (max(len(val), 1) * 0.8)))
                boxes.append(f'<div class="box {k}"><div class="lab">{fmt(it.get("label",""))}</div>'
                             f'<div class="val" style="font-size:{size}px">{fmt(val)}</div></div>')
            h.append(f'<div class="vs">{boxes[0]}<div class="arr">→</div>{boxes[1]}</div>')
        elif st == "quiz":
            h.append('<div class="quiz-q">Q.</div>')
            h.append(f'<h1>{fmt(c["title"])}</h1>')
            opts = c.get("options", ["O", "X"])[:2]
            ox = "".join(f'<div class="{cl}" style="font-size:{min(64, int(340 / (max(len(str(o)), 1) * 0.95)))}px">{fmt(o)}</div>'
                         for cl, o in zip(("o", "x"), opts))
            h.append(f'<div class="ox">{ox}</div><div class="hint">정답은 넘겨서 확인해요</div>')
        else:
            h.append(f'<h1>{fmt(c["title"])}</h1>')
        h.append(f'<div class="sub">{fmt(c.get("subtitle",""))}</div>')
        return "".join(h)
    if c.get("tag"):
        h.append(f'<div class="tag">{fmt(c["tag"])}</div>')
    h.append(f'<h1>{fmt(c["title"])}</h1>')
    for i, para in enumerate(c.get("paragraphs", [])):
        h.append(f'<p class="{"lead" if i == 0 else ""}">{fmt(para)}</p>')
    if t == "stats":
        h.append('<div class="stats">')
        for it in c["items"]:
            d = it.get("dir", "flat")
            arrow = {"up": "▲ ", "down": "▼ "}.get(d, "")
            chg = f'<span class="chg">{arrow}{fmt(it["change"])}</span>' if it.get("change") else ""
            note = f'<div class="note">{fmt(it["note"])}</div>' if it.get("note") else ""
            h.append(f'<div class="stat {d}"><div class="lab">{fmt(it["label"])}</div>'
                     f'<div class="val">{fmt(it["value"])}{chg}</div>{note}</div>')
        h.append('</div>')
    if c.get("steps"):
        h.append('<div class="steps">')
        for i, s in enumerate(c["steps"], 1):
            d = f'<div class="d">{fmt(s["desc"])}</div>' if s.get("desc") else ""
            h.append(f'<div class="step"><div class="n">{i}</div><div><div class="t">{fmt(s["title"])}</div>{d}</div></div>')
        h.append('</div>')
    if t == "list":
        h.append('<div class="list">')
        for it in c["items"]:
            h.append(f'<div class="li"><div class="k">{fmt(it["key"])}</div><div class="v">{fmt(it["value"])}</div></div>')
        h.append('</div>')
    if c.get("panel"):
        p = c["panel"]
        h.append(f'<div class="panel"><div class="pt">{fmt(p["title"])}</div><div class="pd">{fmt(p["text"])}</div></div>')
    if t == "summary":
        h.append('<div class="points">' + "".join(f'<div class="pt-i">{fmt(x)}</div>' for x in c["points"]) + '</div>')
        if c.get("cta"):
            h.append(f'<div class="cta">{fmt(c["cta"])}</div>')
        h.append('<div class="disc">본 콘텐츠는 정보 제공용이며 투자 권유가 아닙니다. 투자 판단과 책임은 본인에게 있습니다.</div>')
    return "".join(h)


def outro(brand, fd, mark):
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS.replace('{fd}', fd)}</style></head>
<body><div class="card outro"><div class="big">{fmt(mark)}</div><div class="name">{fmt(brand)}</div>
<div class="line">팔로우하고 매일 돈되는 상식 받아보세요</div><div id="b" style="display:none"></div></div></body></html>"""


def page(c, i, n, brand, fd, mark, series=""):
    cls = "card cover" if c["type"] == "cover" else ("card meme" if c["type"] == "meme" else "card")
    if c["type"] == "cover" and series:
        cls += " dark"
    if c["type"] == "cover":
        cls += f' st-{c.get("style", "classic")} bg-{c.get("bg", "navy")}'
    if has_art(c) and c["type"] != "meme":
        cls += " has-art"
    if c["type"] == "cover":
        foot_l = '<div class="swipe"><span></span>넘겨서 보기</div>'
    else:
        foot_l = f'<div class="src">{"출처: " + fmt(c["source"]) if c.get("source") else ""}</div>'
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS.replace('{fd}', fd)}</style></head>
<body><div class="{cls}"><div class="top"><div class="brand"><span class="coin">{fmt(mark)}</span>{fmt(brand)}</div><div class="page">{i} / {n}</div></div>
<div class="body" id="b">{render_body(c, series)}</div><div class="foot">{foot_l}<div></div></div></div></body></html>"""


FIT_JS = """() => { const b=document.getElementById('b'); const r=document.documentElement;
 let s=1; const fits=()=>b.scrollHeight<=b.clientHeight+1;
 while(!fits() && s>0.72){ s-=0.02; r.style.setProperty('--s', s.toFixed(2)); }
 return {scale:s, overflow:!fits()}; }"""


def main(src, out):
    data = json.load(open(src, encoding="utf-8"))
    cards, brand, mark = data["cards"], data.get("brand", "돈되는 호형"), data.get("mark", "호")
    series = data.get("series", "")
    if not EMOJI_DIRS:
        print("경고: 3D 이모지 패키지가 없습니다: npm install @lobehub/fluent-emoji-3d@1.1.0")
    os.makedirs(out, exist_ok=True)
    fd = "file://" + font_dir()
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") and os.path.isfile("/opt/pw-browsers/chromium") else None
    warn = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pages = [page(c, i, len(cards), brand, fd, mark, series) for i, c in enumerate(cards, 1)] + [outro(brand, fd, mark)]
        for i, doc in enumerate(pages, 1):
            f = os.path.join(out, f"card_{i:02d}.html")
            open(f, "w", encoding="utf-8").write(doc)
            pg.goto("file://" + os.path.abspath(f))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(150)
            r = pg.evaluate(FIT_JS)
            if r["overflow"]:
                warn.append(f"card {i}: 글자가 넘칩니다 — 문장을 줄이세요")
            elif r["scale"] < 1:
                warn.append(f"card {i}: 글자 크기 {r['scale']:.2f}배로 자동 축소")
            pg.screenshot(path=os.path.join(out, f"card_{i:02d}.png"))
            os.remove(f)
        br.close()
    for c in cards:
        if c.get("photo") and not os.path.exists(c["photo"]):
            warn.append(f"사진 파일이 없습니다: {c['photo']}")
    if MISSING:
        warn.append("3D 이모지 파일이 없어 그림이 빠진 이모지: " + " ".join(sorted(set(MISSING))) + " — 다른 이모지로 바꾸세요")
    print("\n".join(warn) if warn else "모든 카드 정상")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
