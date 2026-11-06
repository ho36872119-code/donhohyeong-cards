#!/usr/bin/env python3
"""돈되는 호형 카드뉴스 렌더러: cards.json -> 1080x1350 PNG (인스타 4:5), 마지막에 로고 장 자동 추가
"emoji": 3D 이모지(내용 카드 오른쪽 위, 표지 오른쪽 아래) / "photo": 제목 아래 사진 칸 / type "chart": 지수 꺾은선
사용법: python3 make_cards.py cards.json out_dir
설치: npm install pretendard@1.3.9 @lobehub/fluent-emoji-3d@1.1.0 (실행 폴더에 node_modules 생성)
"""
import html, json, re, sys, os, glob, base64
from playwright.sync_api import sync_playwright

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))


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
.art{position:absolute;right:0;top:calc(30px*var(--s));width:calc(220px*var(--s));height:calc(220px*var(--s));padding:14px}
.art img{width:100%;height:100%;display:block;object-fit:contain;filter:drop-shadow(0 14px 18px rgba(23,32,74,.18))}
.has-art h1{padding-right:calc(232px*var(--s))}
.cover{background:var(--marker)}
.cover .foot{border-top-color:rgba(23,32,74,.18);color:var(--ink)}
.cover .date{font-size:34px;font-weight:700;color:var(--ink);margin-top:110px}
.cover h1{font-size:calc(116px*var(--s));line-height:1.13;letter-spacing:-0.045em;margin-top:36px;position:relative;z-index:1}
.cover.has-art h1{padding-right:0}
.cover .art{top:auto;bottom:24px;right:-14px;width:280px;height:280px;transform:rotate(8deg)}
.cover.has-art .sub{max-width:590px}
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
.photo{position:relative;margin-top:calc(30px*var(--s));height:calc(320px*var(--s));border-radius:28px;overflow:hidden;flex-shrink:0;background:#dde}
.photo img{width:100%;height:100%;object-fit:cover;display:block}
.photo .cr{position:absolute;right:14px;bottom:12px;font-size:18px;color:#fff;background:rgba(0,0,0,.45);padding:4px 10px;border-radius:8px}
.chart{margin-top:calc(30px*var(--s))}
.chart svg{width:100%;height:auto;display:block}
.outro{background:var(--marker);align-items:center;justify-content:center;padding:0}
.outro .big{width:560px;height:560px;border-radius:50%;background:var(--ink);color:var(--marker);display:flex;align-items:center;justify-content:center;font-size:300px;font-weight:900;position:relative}
.outro .big:before{content:'';position:absolute;inset:38px;border-radius:50%;border:13px dashed rgba(255,225,79,.55)}
.outro .name{margin-top:60px;font-size:100px;font-weight:900;color:var(--ink);letter-spacing:-0.04em}
.outro .line{margin-top:20px;font-size:40px;font-weight:600;color:var(--ink)}
"""

PHOTO_CACHE = {}


def photo_uri(path):
    if path not in PHOTO_CACHE:
        from PIL import Image
        import io
        im = Image.open(path).convert("RGB")
        if im.width > 1400:
            im = im.resize((1400, int(im.height * 1400 / im.width)))
        b = io.BytesIO(); im.save(b, "JPEG", quality=86)
        PHOTO_CACHE[path] = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    return PHOTO_CACHE[path]


def photo_html(c):
    if not c.get("photo"):
        return ""
    pos = c.get("photo_pos", "center")
    cr = f'<div class="cr">{fmt(c.get("photo_credit", ""))}</div>' if c.get("photo_credit") else ""
    return f'<div class="photo"><img src="{photo_uri(c["photo"])}" style="object-position:{pos}" alt="">{cr}</div>'


def chart_html(c):
    pts = c["points"]; W_, H_ = 896, 545
    vals = [p["value"] for p in pts]; lo, hi = min(vals), max(vals); pad = (hi - lo) * 0.18
    lo -= pad; hi += pad
    x0, x1, y0, y1 = 70, W_ - 70, 60, H_ - 150
    xs = [x0 + (x1 - x0) * i / (len(pts) - 1) for i in range(len(pts))]
    ys = [y1 - (v - lo) / (hi - lo) * (y1 - y0) for v in vals]
    g = [f'<svg viewBox="0 0 {W_} {H_}" xmlns="http://www.w3.org/2000/svg" font-family="P">']
    g.append(f'<line x1="20" y1="{y1+40}" x2="{W_-20}" y2="{y1+40}" stroke="#DCE0E8" stroke-width="3"/>')
    area = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    g.append(f'<polygon points="{xs[0]:.1f},{y1+40} {area} {xs[-1]:.1f},{y1+40}" fill="#FFE14F" opacity=".35"/>')
    g.append(f'<polyline points="{area}" fill="none" stroke="#17204A" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>')
    for x, y, p in zip(xs, ys, pts):
        col = {"up": "#E2302A", "down": "#1E5CE0"}.get(p.get("dir"), "#17204A")
        arrow = {"up": "▲", "down": "▼"}.get(p.get("dir"), "")
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="{col}" stroke="#fff" stroke-width="5"/>')
        g.append(f'<text x="{x:.1f}" y="{y-30:.1f}" text-anchor="middle" font-size="27" font-weight="800" fill="#17204A">{html.escape(p["label_value"])}</text>')
        g.append(f'<text x="{x:.1f}" y="{y1+85}" text-anchor="middle" font-size="28" font-weight="700" fill="#6E7488">{html.escape(p["day"])}</text>')
        g.append(f'<text x="{x:.1f}" y="{y1+122}" text-anchor="middle" font-size="27" font-weight="800" fill="{col}">{arrow}{html.escape(p["change"])}</text>')
    g.append("</svg>")
    return '<div class="chart">' + "".join(g) + "</div>"


def art_html(c):
    if c.get("photo"):
        return ""
    if not c.get("emoji"):
        return ""
    em = emoji_img(c["emoji"])
    if not em:
        MISSING.append(c["emoji"])
        return ""
    return f'<div class="art"><img src="{em}" alt=""></div>'


def render_body(c):
    t = c["type"]
    h = [art_html(c)]
    if t == "cover":
        h.append(f'<div class="date">{fmt(c.get("date",""))}</div>')
        h.append(f'<h1>{fmt(c["title"])}</h1>')
        h.append(f'<div class="sub">{fmt(c.get("subtitle",""))}</div>')
        return "".join(h)
    if c.get("tag"):
        h.append(f'<div class="tag">{fmt(c["tag"])}</div>')
    h.append(f'<h1>{fmt(c["title"])}</h1>')
    h.append(photo_html(c))
    if t == "chart":
        h.append(chart_html(c))
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
<div class="line">팔로우하고 매일 아침 돈되는 상식 받아보세요</div><div id="b" style="display:none"></div></div></body></html>"""


def page(c, i, n, brand, fd, mark):
    cls = "card cover" if c["type"] == "cover" else "card"
    if c.get("emoji") and not c.get("photo") and emoji_img(c["emoji"]):
        cls += " has-art"
    if c["type"] == "cover":
        foot_l = '<div class="swipe"><span></span>넘겨서 보기</div>'
    else:
        foot_l = f'<div class="src">{"출처: " + fmt(c["source"]) if c.get("source") else ""}</div>'
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS.replace('{fd}', fd)}</style></head>
<body><div class="{cls}"><div class="top"><div class="brand"><span class="coin">{fmt(mark)}</span>{fmt(brand)}</div><div class="page">{i} / {n}</div></div>
<div class="body" id="b">{render_body(c)}</div><div class="foot">{foot_l}<div></div></div></div></body></html>"""


FIT_JS = """() => { const b=document.getElementById('b'); const r=document.documentElement;
 let s=1; const fits=()=>b.scrollHeight<=b.clientHeight+1;
 while(!fits() && s>0.72){ s-=0.02; r.style.setProperty('--s', s.toFixed(2)); }
 return {scale:s, overflow:!fits()}; }"""


def main(src, out):
    data = json.load(open(src, encoding="utf-8"))
    cards, brand, mark = data["cards"], data.get("brand", "돈되는 호형"), data.get("mark", "호")
    if not EMOJI_DIRS:
        print("경고: 3D 이모지 패키지가 없습니다: npm install @lobehub/fluent-emoji-3d@1.1.0")
    os.makedirs(out, exist_ok=True)
    fd = "file://" + font_dir()
    exe = "/opt/pw-browsers/chromium" if os.path.isfile("/opt/pw-browsers/chromium") else None
    warn = []
    for c in cards:
        if c.get("photo") and not os.path.exists(c["photo"]):
            sys.exit(f"사진 파일이 없습니다: {c['photo']}")
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pages = [page(c, i, len(cards), brand, fd, mark) for i, c in enumerate(cards, 1)] + [outro(brand, fd, mark)]
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
    if MISSING:
        warn.append("3D 이모지 파일이 없어 그림이 빠진 이모지: " + " ".join(sorted(set(MISSING))) + " — 다른 이모지로 바꾸세요")
    print("\n".join(warn) if warn else "모든 카드 정상")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
