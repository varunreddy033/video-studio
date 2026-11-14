"""Premium blocks 1-7 (measured from ex01..ex07; numbers in ../SPECS.md)."""
from .core import esc, stage, out, loop_js, spans


# ------------------------------------------------------------------------------------------- 1 glass_quote
def glass_quote(P, ctx):
    """Frosted-glass testimonial that lands out of a zoom. ctx: quote, name, role, label, image (path/url, optional)."""
    w, h, period = 1022, 640, 4.40
    loops = ctx.get("loops", 1)
    quote = ctx.get("quote", "“These templates save us hours and make every campaign feel personal. Highly recommend!”")
    name, role = ctx.get("name", "John Doe,"), ctx.get("role", "CEO of Acme")
    img = ctx.get("image")
    photo = (f'background:url({esc(img)}) center/cover no-repeat;' if img else
             'background:radial-gradient(60% 80% at 62% 30%,#f0a845 0,#d07f25 38%,#a85a16 70%,#6b360c 100%);')
    deco = "" if img else (
        '<div style="position:absolute;left:0;top:0;width:150px;height:640px;background:linear-gradient(90deg,#17130f,#3a2a1a)"></div>'
        '<div style="position:absolute;left:150px;top:0;width:26px;height:640px;background:#0f0c09"></div>'
        '<div style="position:absolute;left:560px;top:250px;width:340px;height:210px;border-radius:18px;background:#8a8f93;transform:rotate(-14deg);box-shadow:0 30px 60px rgba(0,0,0,.35)"></div>'
        '<div style="position:absolute;left:430px;top:430px;width:560px;height:260px;border-radius:60px;background:#b9a07a"></div>'
        '<div style="position:absolute;left:300px;top:545px;width:110px;height:120px;border-radius:14px;background:#1d3557"></div>')
    qh, _ = spans(P, quote, "w")
    nh = "".join(f'<span class="{P}n" style="display:inline-block;white-space:pre">{esc(x)} </span>' for x in name.split(" "))
    rh = "".join(f'<span class="{P}n" style="display:inline-block;white-space:pre">{esc(x)} </span>' for x in role.split(" "))
    heart = ('M12 21s-7.5-4.6-10-9.3C.3 8.2 2.2 4.5 5.8 4.5c2 0 3.4 1 4.2 2.3h4C14.8 5.5 16.2 4.5 18.2 4.5c3.6 0 5.5 3.7 3.8 7.2'
             'C19.5 16.4 12 21 12 21z')
    inner = f"""
<div id="{P}-ph" style="position:absolute;inset:0;transform-origin:50% 50%;{photo}">{deco}</div>
<div style="position:absolute;right:34px;top:20px;font:500 10px Inter;color:rgba(255,255,255,.85)">{esc(ctx.get("label", "yourbrand.co"))}</div>
<div style="position:absolute;left:24px;top:18px;font:700 11px Inter;color:#fff">● studio</div>
<div id="{P}-card">
  <div id="{P}-in">
    <div style="position:absolute;left:24px;top:26px;width:306px;font:500 15.5px/1.32 Inter;color:rgba(255,255,255,.96);letter-spacing:-.005em">{qh}</div>
    <div id="{P}-av" style="position:absolute;left:24px;top:134px;width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#1c1c1e,#4a4a4f)"></div>
    <div style="position:absolute;left:70px;top:133px;font:400 13.5px/1.3 Inter;color:rgba(255,255,255,.74)">{nh}<br>{rh}</div>
    <svg id="{P}-ht" viewBox="0 0 24 24" style="position:absolute;right:26px;top:141px;width:19px;height:19px"><path d="{heart}" fill="none" stroke="#fff" stroke-width="1.6"/></svg>
    <svg id="{P}-hf" viewBox="0 0 24 24" style="position:absolute;right:26px;top:141px;width:19px;height:19px"><path d="{heart}" fill="#fff"/></svg>
  </div>
</div>"""
    css = f"""
#{P}-card {{ position:absolute; left:518px; top:321px; width:576px; height:446px; transform:translate(-50%,-50%);
  border-radius:34px; background:rgba(176,150,122,.34); border:1px solid rgba(255,255,255,.16);
  -webkit-backdrop-filter:blur(26px) saturate(1.1); backdrop-filter:blur(26px) saturate(1.1); overflow:hidden;
  box-shadow:0 18px 50px rgba(40,20,0,.18); }}
#{P}-in {{ position:absolute; left:50%; top:50%; width:350px; height:207px; margin:-103.5px 0 0 -175px; }}
.{P}w {{ transform-origin:0% 100%; }}
"""
    one = """
tl.set("#@P-card", {width: 576, height: 446}, @o);
tl.set("#@P-ph", {scale: 1.488}, @o);
tl.set(".@Pw, .@Pn, #@P-ht, #@P-hf", {autoAlpha: 0}, @o);
tl.set("#@P-av", {scale: 0}, @o);
tl.fromTo("#@P-card", {width: 576, height: 446}, {width: 350, height: 207, duration: 1.113, ease: PMX.cb(0.61, 0, 0.15, 1.02), immediateRender: false}, @o + 0.0);
tl.fromTo("#@P-ph", {scale: 1.488}, {scale: 1, duration: 1.267, ease: PMX.cb(0.38, 0.01, 0.02, 0.98), immediateRender: false}, @o + 0.117);
tl.fromTo(".@Pw", {autoAlpha: 0, scale: 0.3}, {autoAlpha: 1, scale: 1, duration: 0.22, ease: "power2.out", stagger: 0.052, immediateRender: false}, @o + 0.69);
tl.fromTo("#@P-ht", {autoAlpha: 0}, {autoAlpha: 0.45, duration: 0.2, immediateRender: false}, @o + 1.40);
tl.fromTo("#@P-av", {scale: 0}, {scale: 1, duration: 0.2, ease: "back.out(1.6)", immediateRender: false}, @o + 1.42);
tl.fromTo(".@Pn", {autoAlpha: 0, y: 6}, {autoAlpha: 1, y: 0, duration: 0.2, ease: "power2.out", stagger: 0.08, immediateRender: false}, @o + 1.67);
tl.fromTo("#@P-hf", {autoAlpha: 0, scale: 0.4}, {autoAlpha: 1, scale: 1, duration: 0.22, ease: "back.out(2.2)", transformOrigin: "50% 50%", immediateRender: false}, @o + 2.42);
"""
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.1, "whoosh"), (0.7, "keyboard"), (1.42, "pop"), (2.42, "pop"))]
    return out(P, stage(P, ctx, w, h, "#3a2410", inner), css, loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 2 card_pops
CARD_ART = [
    "background:radial-gradient(60% 9% at 50% 55%,#ff5be0 0,#ff1fc4 45%,rgba(255,31,196,0) 100%),radial-gradient(70% 45% at 50% 62%,#a3127f 0,#4a0a3c 55%,#1b0617 100%)",
    "background:linear-gradient(160deg,#b7a1ff 0,#dccfff 48%,#a58cf6 100%)",
    "background:radial-gradient(circle at 50% 78%,rgba(0,0,0,0) 33%,#ff4d1c 34%,#ff8a1f 41%,#ffc233 47%,rgba(0,0,0,0) 48%),#171717",
    "background:linear-gradient(180deg,#a9c2ba,#8fa9a2)",
    "background:repeating-linear-gradient(45deg,#4a2e1b 0 8px,#2b190d 8px 16px)",
    "background:radial-gradient(circle at 28% 82%,#27d23c 0,#f6ea3a 22%,#ff7b2e 40%,#c9a0ff 66%,#cfeaf3 100%)",
    "background:linear-gradient(170deg,#21514f,#0b2123)",
    "background:linear-gradient(150deg,#b4b2ff,#9d9bf7)",
]
CARD_EXTRA = [
    "", '<div style="position:absolute;left:34%;top:30%;width:32%;height:36%;border-radius:10px;background:linear-gradient(160deg,rgba(255,255,255,.55),rgba(160,130,255,.5));transform:skewY(-18deg)"></div>',
    "", '<div style="position:absolute;left:22%;top:14%;width:56%;height:62%;background:#f4efe6;box-shadow:0 8px 18px rgba(0,0,0,.25)"><div style="position:absolute;inset:10%;background:radial-gradient(circle at 50% 38%,#ff7a3d 0 24%,rgba(0,0,0,0) 25%),radial-gradient(circle at 50% 72%,#ffb089 0 20%,rgba(0,0,0,0) 21%),#cfe3dc"></div></div>',
    '<div style="position:absolute;left:14%;top:26%;width:72%;height:50%;border-radius:10px;background:#9db0a6;border:5px solid #1c1c1c;transform:rotate(6deg)"><div style="position:absolute;left:14%;top:26%;width:34%;height:52%;border-radius:50%;background:#18201c"></div></div>',
    "", "", '<div style="position:absolute;left:30%;top:22%;width:44%;height:70%;border-radius:22px;border:7px solid #1b1d3a"></div>',
]


def card_pops(P, ctx):
    """Square picture cards pop in a ring around stacked headline lines, weaving in front of / behind the words.
    ctx: lines (3 strings), top, bottom, images (list of up to 8 paths/urls, optional), loops."""
    w, h, period = 1028, 1030, 1.20
    loops = ctx.get("loops", 2)
    lines = ctx.get("lines", ["SHARE", "YOUR", "WORK"])
    imgs = ctx.get("images") or []
    pos = [(311, 366, 3), (493, 300, -6), (648, 341, 8), (765, 507, 6), (657, 633, -8), (493, 696, 7), (324, 639, 10), (189, 504, -8)]
    zc = [11, 9, 8, 7, 5, 3, 2, 1]                # z of card 1..8 ; lines: SHARE 10, YOUR 6, WORK 4
    zl = [10, 6, 4]
    S = 330
    hs = [f'<div style="position:absolute;left:0;top:58px;width:{w}px;text-align:center;font:700 12px Inter;letter-spacing:.02em;color:#fff">{esc(ctx.get("top", "YOUR STUDIO"))}</div>',
          f'<div style="position:absolute;left:0;top:938px;width:{w}px;text-align:center;font:700 12px Inter;letter-spacing:.02em;color:#fff">{esc(ctx.get("bottom", "PORTFOLIO"))}</div>']
    for i, (cx, cy, rot) in enumerate(pos):
        art = (f"background:url({esc(imgs[i])}) center/cover" if i < len(imgs) else CARD_ART[i])
        extra = "" if i < len(imgs) else CARD_EXTRA[i]
        hs.append(f'<div style="position:absolute;left:{cx - S / 2}px;top:{cy - S / 2}px;width:{S}px;height:{S}px;z-index:{zc[i]};transform:rotate({rot}deg)">'
                  f'<div id="{P}-c{i}" style="position:absolute;inset:0;overflow:hidden;visibility:hidden;opacity:0;{art}">{extra}</div></div>')
    for j, t in enumerate(lines[:3]):
        hs.append(f'<div style="position:absolute;left:-10px;top:{308 + 128 * j}px;width:{w}px;height:128px;z-index:{zl[j]};text-align:center;'
                  f'font:800 150px/128px Inter;letter-spacing:-.045em;color:#fff">{esc(t)}</div>')
    js, cues, total = [], [], period * loops
    for k in range(-1, loops):
        for i in range(8):
            t0 = k * period + i * 0.15
            t1 = t0 + 0.45
            if t1 <= 0:
                continue
            if t0 < 0:
                js.append(f'tl.set("#{P}-c{i}", {{autoAlpha: 1, scale: 1}}, 0);')
            else:
                js.append(f'tl.set("#{P}-c{i}", {{autoAlpha: 1}}, {t0:.3f});')
                js.append(f'tl.fromTo("#{P}-c{i}", {{scale: 0.55}}, {{scale: 1, duration: 0.35, ease: "power3.out", immediateRender: false}}, {t0:.3f});')
                if t0 < total:
                    cues.append((t0, "pop"))
            if t1 < total:
                js.append(f'tl.set("#{P}-c{i}", {{autoAlpha: 0}}, {t1:.3f});')
    return out(P, stage(P, ctx, w, h, "#000", "".join(hs)), "", js, cues, total, (w, h), loops)


# ------------------------------------------------------------------------------------------- 3 card_wheel
def card_wheel(P, ctx):
    """Tall cards fanned on a big wheel; the wheel turns one card and back. ctx: words (marquee), tokens, images {index: path}."""
    w, h, period = 1012, 768, 5.30
    loops = ctx.get("loops", 1)
    words = ctx.get("words", ["BOLD", "WORK", "2026", "NOW"])
    tokens = ctx.get("tokens", ["USD", "EUR", "INR", "GBP"])
    imgs = ctx.get("images") or {}
    R, CW, CH = 873, 248, 400
    marq = "".join(f"<div>{esc(x)}</div>" for x in (words * 8))
    faces = {
        -3: 'background:linear-gradient(160deg,#2a2a2c,#0c0c0d)',
        -2: 'background:linear-gradient(120deg,#fdfdfd,#c9cace)',
        -1: 'background:radial-gradient(120% 90% at 0% 100%,#3d3d40 0,#0a0a0b 62%),#0a0a0b',
        0: 'background:linear-gradient(100deg,#8d8f93 0,#e9e9eb 55%,#c7c8cc 100%)',
        1: 'background:linear-gradient(180deg,#c3c4c9,#a9abb1)',
        2: 'background:#050505',
        3: 'background:#f2b705',
        4: 'background:#2f5fb3',
    }
    inner_of = {
        -2: (f'<div id="{P}-coin" style="position:absolute;left:-46px;top:150px;width:150px;height:150px;border-radius:50%;border:5px solid #9a9ca3;box-shadow:inset 0 0 0 9px rgba(255,255,255,.7)">'
             + "".join(f'<div class="{P}tk" id="{P}-tk{i}" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:500 42px Inter;color:#1b1b1d;letter-spacing:-.03em;opacity:{1 if i == 0 else 0}">{esc(t)}</div>' for i, t in enumerate(tokens))
             + '</div>'),
        -1: '<div style="position:absolute;left:138px;top:196px;width:58px;height:58px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#7a7a7e,#1c1c1e 70%)"></div>'
            '<div style="position:absolute;left:-60px;top:120px;width:420px;height:420px;border-radius:50%;border-top:1px solid rgba(255,255,255,.18)"></div>',
        0: '<div style="position:absolute;left:38px;top:36px;width:190px;height:230px;border-radius:48% 52% 46% 54%;background:radial-gradient(circle at 62% 30%,#5b5b5e,#101011 70%)"></div>'
           '<div style="position:absolute;left:-10px;top:268px;width:230px;height:170px;border-radius:50% 50% 0 0;background:linear-gradient(180deg,#2c2c2e,#0e0e0f)"></div>',
        1: f'<div id="{P}-mq" style="position:absolute;left:0;top:0;width:{CW}px;text-align:center;font:800 62px/59px Inter;letter-spacing:-.03em;color:#0b0b0c">{marq}</div>',
        2: f'<div id="{P}-mk" style="position:absolute;left:92px;top:184px;width:66px;height:14px;border-radius:14px 2px 14px 2px;background:#fff;transform:rotate(-14deg)"></div>',
        3: '<div style="position:absolute;left:30px;top:120px;font:800 110px/1 Inter;color:#0b0b0c;transform:rotate(90deg);transform-origin:0 0;margin-left:120px;letter-spacing:-.04em">Play</div>',
    }
    cards = []
    for i in range(-3, 5):
        face = f"background:url({esc(imgs[i])}) center/cover" if i in imgs else faces[i]
        body = "" if i in imgs else inner_of.get(i, "")
        cards.append(f'<div style="position:absolute;left:{-CW / 2}px;top:{-(R + CH / 2)}px;width:{CW}px;height:{CH}px;border-radius:14px;overflow:hidden;'
                     f'z-index:{i + 5};transform-origin:{CW / 2}px {R + CH / 2}px;transform:rotate({15 * i}deg);{face};box-shadow:-10px 0 30px rgba(0,0,0,.18)">{body}</div>')
    foot = "".join(f'<div style="position:absolute;left:{x}px;top:728px;font:500 10px SpaceMono,monospace;color:#fff;opacity:.9">{esc(t)}</div>'
                   for x, t in ((30, "studio"), (482, "Orbit"), (678, "S-01 (LITE)"), (910, "YOUR.SITE")))
    inner = (f'<div id="{P}-wh" style="position:absolute;left:505px;top:1258px;width:0;height:0">{"".join(cards)}</div>'
             f'<div style="position:absolute;left:{505 - 760}px;top:585px;width:1520px;height:1520px;border-radius:50%;z-index:20;background:linear-gradient(180deg,#b3b5ba 0,#77797e 12%,#5d5f63 30%)"></div>'
             f'<div style="position:absolute;inset:0;z-index:30">{foot}</div>')
    one = """
tl.fromTo("#@P-wh", {rotation: -15}, {rotation: 0, duration: 1.6, ease: PMX.cb(0.77, 0.06, 0.19, 0.98), immediateRender: false}, @o + 0.05);
tl.fromTo("#@P-wh", {rotation: 0}, {rotation: -15, duration: 1.6, ease: PMX.cb(0.77, 0.06, 0.19, 0.98), immediateRender: false}, @o + 3.05);
"""
    total = period * loops
    js = [f'tl.set("#{P}-wh", {{rotation: -15}}, 0);', loop_js(one, period, loops, P),
          f'tl.fromTo("#{P}-mq", {{y: 0}}, {{y: {-110 * total:.0f}, duration: {total:.3f}, ease: "none"}}, 0);']
    n, t = 0, 0.55
    while t < total - 0.3:
        a, b = n % len(tokens), (n + 1) % len(tokens)
        js.append(f'tl.to("#{P}-coin", {{scaleX: 0.04, duration: 0.12, ease: "power1.in"}}, {t:.2f});')
        js.append(f'tl.set("#{P}-tk{a}", {{opacity: 0}}, {t + 0.12:.2f}); tl.set("#{P}-tk{b}", {{opacity: 1}}, {t + 0.12:.2f});')
        js.append(f'tl.to("#{P}-coin", {{scaleX: 1, duration: 0.12, ease: "power1.out"}}, {t + 0.12:.2f});')
        n, t = n + 1, t + 0.75
    t = 0.9
    while t < total - 0.3:
        js.append(f'tl.set("#{P}-mk", {{x: 7, opacity: 0.55, scaleX: 0.8}}, {t:.2f}); tl.set("#{P}-mk", {{x: -5, opacity: 1, scaleX: 1.1}}, {t + 0.05:.2f}); tl.set("#{P}-mk", {{x: 0, scaleX: 1}}, {t + 0.1:.2f});')
        t += 1.25
    cues = [(k * period + t, "whoosh") for k in range(loops) for t in (0.6, 3.6)]
    return out(P, stage(P, ctx, w, h, "linear-gradient(180deg,#e1e2e6,#d6d7db)", inner), "", js, cues, total, (w, h), loops)


# ------------------------------------------------------------------------------------------- 4 morph_word
def morph_word(P, ctx):
    """A word whose letters swell into fat blobs one by one (grotesque -> blob font, melted together with a goo
    filter), then the word stretches to fill the frame. ctx: word (short, caps), color, bg, blob (font family), loops."""
    w, h, period = 1016, 626, 2.217
    loops = ctx.get("loops", 2)
    word = ctx.get("word", "MORPH")
    col, bg = ctx.get("color", "#00b2ff"), ctx.get("bg", "#11112a")
    blob = ctx.get("blob", "Modak")
    big, bsz, sy, sx = ctx.get("fat_px", 140), ctx.get("blob_em", 1.0), ctx.get("blob_sy", 1.62), ctx.get("blob_sx", 1.16)
    letters = "".join(f'<span class="{P}L" style="display:inline-block;position:relative;font-size:71.5px"><span class="{P}A" style="display:inline-block">{esc(c)}</span>'
                      f'<span class="{P}B" style="position:absolute;left:50%;top:50%;font-family:{blob};font-weight:400;font-size:{bsz}em;line-height:1;opacity:0;transform-origin:50% 50%">{esc(c)}</span></span>'
                      for c in word)
    inner = (f'<div style="position:absolute;inset:0;isolation:isolate">'
             f'<div id="{P}-gb" style="position:absolute;inset:-40px;background:#000;display:flex;align-items:center;justify-content:center;filter:blur(0px) contrast(40)">'
             f'<div id="{P}-wd" style="display:flex;align-items:center;white-space:nowrap;font-family:Inter;font-weight:800;color:#fff;letter-spacing:-.01em;transform-origin:50% 50%">{letters}</div></div>'
             f'<div style="position:absolute;inset:0;background:{col};mix-blend-mode:multiply"></div>'
             f'<div style="position:absolute;inset:0;background:{bg};mix-blend-mode:lighten"></div></div>')
    n = len(word)
    starts = [0.23 + (0.47 / max(1, n - 1)) * i for i in range(n)]
    one = ['tl.set(".@PL", {fontSize: 71.5}, @o); tl.set(".@PA", {opacity: 1}, @o); tl.set(".@PB", {xPercent: -50, yPercent: -50, opacity: 0, scaleX: 0.55, scaleY: 0.5}, @o);',
           'tl.set("#@P-wd", {scaleX: 1, scaleY: 1}, @o); tl.set("#@P-gb", {filter: "blur(0px) contrast(40)"}, @o);',
           'tl.fromTo("#@P-gb", {filter: "blur(0px) contrast(40)"}, {filter: "blur(4px) contrast(40)", duration: 0.2, ease: "none", immediateRender: false}, @o + 0.23);',
           'tl.fromTo("#@P-gb", {filter: "blur(4px) contrast(40)"}, {filter: "blur(9px) contrast(40)", duration: 0.6, ease: "none", immediateRender: false}, @o + 1.40);']
    for i, t in enumerate(starts):
        L = f'.@PL:nth-child({i + 1})'
        one.append(f'tl.fromTo("{L}", {{fontSize: 71.5}}, {{fontSize: {big}, duration: 0.42, ease: "back.out(1.5)", immediateRender: false}}, @o + {t:.3f});')
        one.append(f'tl.fromTo("{L} .@PA", {{opacity: 1}}, {{opacity: 0, duration: 0.16, ease: "none", immediateRender: false}}, @o + {t + 0.03:.3f});')
        one.append(f'tl.fromTo("{L} .@PB", {{opacity: 0}}, {{opacity: 1, duration: 0.14, ease: "none", immediateRender: false}}, @o + {t:.3f});')
        one.append(f'tl.fromTo("{L} .@PB", {{scaleX: 0.55, scaleY: 0.5}}, {{scaleX: {sx}, scaleY: {sy}, duration: 0.5, ease: "back.out(3.0)", immediateRender: false}}, @o + {t:.3f});')
    one.append('tl.fromTo("#@P-wd", {scaleX: 1, scaleY: 1}, {scaleX: %s, scaleY: %s, duration: 0.75, ease: PMX.cb(0.45, 0.01, 0.0, 0.97), immediateRender: false}, @o + 1.367);' % (ctx.get("end_sx", 1.87), ctx.get("end_sy", 3.89)))
    cues = [(k * period + t, s) for k in range(loops) for t, s in ([(x, "pop") for x in starts] + [(1.4, "whoosh")])]
    return out(P, stage(P, ctx, w, h, bg, inner), "", loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 5 pill_split
def pill_split(P, ctx):
    """A pill button collapses into its icon and reveals two round buttons beside it; then merges back.
    ctx: label, count, colors (pill, left, right), loops."""
    w, h, period = 1008, 770, 6.30
    loops = ctx.get("loops", 1)
    label, count = ctx.get("label", "View cart"), ctx.get("count", "3")
    cp, cl, cr = ctx.get("colors", ["#ffd60a", "#000000", "#6c35de"])
    cart = ('<svg viewBox="3 5 40 38" width="59" height="59" fill="none" stroke="#111" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M5 8h6l5 22h20l4-15H14"/><circle cx="19" cy="38" r="3"/><circle cx="34" cy="38" r="3"/></svg>')
    card = ('<svg viewBox="6 10 36 28" width="68" height="68" fill="none" stroke="#fff" stroke-width="2.0" stroke-linecap="round">'
            '<rect x="8" y="13" width="32" height="22" rx="5"/><path d="M8 20h32M14 28h6"/></svg>')
    inner = f"""
<div id="{P}-k" class="{P}c" style="left:{357 - 62}px;background:{cl}">{card}</div>
<div id="{P}-p" class="{P}c" style="left:{657 - 62}px;background:{cr};font:500 50px Poppins;color:#fff">{esc(count)}</div>
<div id="{P}-pill" style="position:absolute;left:505.5px;top:323px;width:468px;height:124px;transform:translateX(-50%);border-radius:62px;background:{cp};overflow:hidden;box-shadow:0 16px 34px rgba(255,214,10,.22)">
  <div id="{P}-ic" style="position:absolute;left:70px;top:32.5px;width:59px;height:59px">{cart}</div>
  <div id="{P}-tx" style="position:absolute;left:153px;top:0;height:124px;line-height:124px;white-space:nowrap;font:400 51px/124px Poppins;color:#111;letter-spacing:-.012em">{esc(label)}</div>
</div>"""
    css = f".{P}c {{ position:absolute; top:323px; width:124px; height:124px; border-radius:50%; display:flex; align-items:center; justify-content:center; }}"
    one = """
tl.set("#@P-pill", {width: 468}, @o); tl.set("#@P-ic", {left: 70}, @o); tl.set("#@P-tx", {autoAlpha: 1}, @o); tl.set("#@P-k, #@P-p", {x: 0}, @o);
tl.fromTo("#@P-pill", {width: 468}, {width: 536, duration: 0.15, ease: "power2.out", immediateRender: false}, @o + 0.0);
tl.fromTo("#@P-ic", {left: 70}, {left: 84, duration: 0.15, ease: "power2.out", immediateRender: false}, @o + 0.0);
tl.fromTo("#@P-tx", {autoAlpha: 1}, {autoAlpha: 0, duration: 0.07, ease: "none", immediateRender: false}, @o + 0.15);
tl.fromTo("#@P-pill", {width: 536}, {width: 124, duration: 0.967, ease: PMX.cb(0.41, 0.07, 0.0, 1.03), immediateRender: false}, @o + 0.20);
tl.fromTo("#@P-ic", {left: 84}, {left: 32.5, duration: 0.967, ease: PMX.cb(0.41, 0.07, 0.0, 1.03), immediateRender: false}, @o + 0.20);
tl.fromTo("#@P-k", {x: 5}, {x: 0, duration: 0.5, ease: "back.out(4)", immediateRender: false}, @o + 0.42);
tl.fromTo("#@P-p", {x: -5}, {x: 0, duration: 0.5, ease: "back.out(4)", immediateRender: false}, @o + 0.42);
tl.fromTo("#@P-k", {x: 0}, {x: -30, duration: 0.17, ease: "power2.out", immediateRender: false}, @o + 3.717);
tl.fromTo("#@P-p", {x: 0}, {x: 30, duration: 0.17, ease: "power2.out", immediateRender: false}, @o + 3.717);
tl.fromTo("#@P-k", {x: -30}, {x: 0, duration: 0.15, ease: "power2.in", immediateRender: false}, @o + 3.887);
tl.fromTo("#@P-p", {x: 30}, {x: 0, duration: 0.15, ease: "power2.in", immediateRender: false}, @o + 3.887);
tl.fromTo("#@P-pill", {width: 124}, {width: 510, duration: 0.40, ease: PMX.tab([124, 188, 266, 326, 370, 406, 436, 458, 478, 490, 502, 508, 510]), immediateRender: false}, @o + 3.883);
tl.fromTo("#@P-ic", {left: 32.5}, {left: 78, duration: 0.40, ease: "power2.out", immediateRender: false}, @o + 3.883);
tl.fromTo("#@P-tx", {autoAlpha: 0}, {autoAlpha: 1, duration: 0.12, ease: "none", immediateRender: false}, @o + 4.097);
tl.fromTo("#@P-pill", {width: 510}, {width: 468, duration: 0.62, ease: "sine.inOut", immediateRender: false}, @o + 4.30);
tl.fromTo("#@P-ic", {left: 78}, {left: 70, duration: 0.62, ease: "sine.inOut", immediateRender: false}, @o + 4.30);
"""
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.0, "click"), (0.45, "pop"), (3.72, "click"), (3.95, "swoosh-up"))]
    return out(P, stage(P, ctx, w, h, "#f7f7f7", inner), css, loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 6 card_flip
def card_flip(P, ctx):
    """A payment-style card spins 360 around Y, then 360 around X, with a light sweep. ctx: word, back, color, loops."""
    w, h, period = 806, 1012, 4.0
    loops = ctx.get("loops", 1)
    col = ctx.get("color", "#6a11ff")
    icons = ('<svg viewBox="0 0 60 130" width="100" height="216" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="2.4" style="position:absolute;right:38px;top:44px">'
             '<circle cx="30" cy="28" r="22"/><ellipse cx="30" cy="28" rx="9" ry="22"/><path d="M8 28h44M11 16h38M11 40h38"/>'
             '<rect x="10" y="74" width="40" height="50" rx="9"/><path d="M10 92h12v14H10M50 92H38v14h12M22 74v18M38 74v18M22 106v18M38 106v18"/></svg>')
    inner = f"""
<div style="position:absolute;left:153px;top:192px;width:500px;height:610px;perspective:1500px">
  <div id="{P}-cd" style="position:absolute;inset:0;transform-style:preserve-3d">
    <div style="position:absolute;inset:0;border-radius:62px;background:linear-gradient(120deg,#7d33ff 0,{col} 42%);backface-visibility:hidden;-webkit-backface-visibility:hidden;overflow:hidden">
      {icons}
      <div style="position:absolute;left:36px;bottom:34px;font:800 128px/1 Inter;letter-spacing:-.05em;color:#fff">{esc(ctx.get("word", "Pay"))}</div>
      <div id="{P}-sh" style="position:absolute;top:0;left:0;width:60%;height:100%;background:linear-gradient(100deg,rgba(255,255,255,0) 0,rgba(255,255,255,.26) 50%,rgba(255,255,255,0) 100%)"></div>
    </div>
    <div id="{P}-bk" style="position:absolute;inset:0;border-radius:62px;background:#2a2a2e;backface-visibility:hidden;-webkit-backface-visibility:hidden;display:flex;align-items:center;justify-content:center;font:600 46px Inter;color:#b9b9bd;letter-spacing:-.02em">{esc(ctx.get("back", "Studio"))}
      <div style="position:absolute;left:70px;right:70px;bottom:70px;height:26px;background:repeating-linear-gradient(180deg,rgba(255,255,255,.22) 0 2px,rgba(0,0,0,0) 2px 9px)"></div>
    </div>
  </div>
</div>"""
    one = """
tl.set("#@P-cd", {rotationY: 0, rotationX: 0}, @o); tl.set("#@P-bk", {rotationY: 180, rotationX: 0}, @o); tl.set("#@P-sh", {xPercent: -120}, @o);
tl.fromTo("#@P-cd", {rotationY: 0}, {rotationY: 360, duration: 1.60, ease: PMX.tab([0, 0, 0, 0.022, 0.032, 0.083, 0.108, 0.157, 0.203, 0.247, 0.324, 0.402, 0.479, 0.556, 0.634, 0.711, 0.769, 0.802, 0.83, 0.853, 0.874, 0.892, 0.907, 0.92, 0.933, 0.943, 0.953, 0.96, 0.966, 0.973, 0.98, 0.987, 0.994, 1]), immediateRender: false}, @o + 0.0);
tl.fromTo("#@P-sh", {xPercent: -120}, {xPercent: 190, duration: 0.5, ease: "power1.inOut", immediateRender: false}, @o + 0.0);
tl.set("#@P-cd", {rotationY: 0, rotationX: 0}, @o + 1.97); tl.set("#@P-bk", {rotationY: 0, rotationX: 180}, @o + 1.97);
tl.fromTo("#@P-cd", {rotationX: 0}, {rotationX: 360, duration: 1.60, ease: PMX.tab([0, 0, 0, 0.022, 0.032, 0.083, 0.108, 0.157, 0.203, 0.247, 0.324, 0.402, 0.479, 0.556, 0.634, 0.711, 0.769, 0.802, 0.83, 0.853, 0.874, 0.892, 0.907, 0.92, 0.933, 0.943, 0.953, 0.96, 0.966, 0.973, 0.98, 0.987, 0.994, 1]), immediateRender: false}, @o + 2.0);
tl.fromTo("#@P-sh", {xPercent: -120}, {xPercent: 190, duration: 0.5, ease: "power1.inOut", immediateRender: false}, @o + 2.0);
"""
    cues = [(k * period + t, "whoosh") for k in range(loops) for t in (0.2, 2.2)]
    return out(P, stage(P, ctx, w, h, "#090909", inner), "", loop_js(one, period, loops, P), cues, period * loops, (w, h), loops)


# ------------------------------------------------------------------------------------------- 7 word_slide
SLIDE_IN = [410, 255, 151, 82, 35, 2, -19, -31, -35, -34, -29, -23, -17, -13, -9, -6, -4, -2, -1, 0, 0]      # px, 50 ms steps
SLIDE_OUT = [0, 17, 30, 38, 40, 35, 24, 6, -22, -70, -150, -270, -430]                                       # px, 50 ms steps


def word_slide(P, ctx):
    """Words hard-appear and slide in from the right with a soft overshoot, one after another; they leave to the left
    after a small wind-up. ctx: blocks = [[line, line], [line, line]] (words split on spaces), loops."""
    w, h, period = 824, 846, 2.483
    loops = ctx.get("loops", 2)
    blocks = ctx.get("blocks", [["All Eyes on", "Independents"], ["January", "19 - 21"]])
    tops = [[51, 139], [427, 515]]
    words = []                                   # (text, block, line, index in block)
    for b, lines in enumerate(blocks[:2]):
        k = 0
        for l, line in enumerate(lines[:2]):
            for wd in line.split(" "):
                words.append((wd, b, l, k))
                k += 1
    hs = []
    for b, lines in enumerate(blocks[:2]):
        for l, line in enumerate(lines[:2]):
            sp = "".join(f'<span class="{P}w {P}b{b}" style="display:inline-block;white-space:pre;visibility:hidden">{esc(x)}</span>'
                         + '<span style="display:inline-block;width:.30em"></span>' for x in line.split(" "))
            hs.append(f'<div style="position:absolute;left:47px;top:{tops[b][l]}px;white-space:nowrap;font:600 93px/88px Inter;letter-spacing:-.03em;color:#fff">{sp}</div>')
    one = []
    for b in range(2):
        nb = sum(1 for x in words if x[1] == b)
        for k in range(nb):
            sel = f'gsap.utils.toArray(".@Pb{b}")[{k}]'
            tin = 0.10 * k + (0.10 if b == 1 else 0.0)
            tout = 1.653 + 0.05 * k + (0.10 if b == 1 else 0.0)
            one.append(f'tl.set({sel}, {{autoAlpha: 0, x: 410}}, @o);')
            one.append(f'tl.set({sel}, {{autoAlpha: 1}}, @o + {tin + 0.03:.3f});')
            one.append(f'tl.fromTo({sel}, {{x: 410}}, {{x: 0, duration: 1.0, ease: PMX.tab({SLIDE_IN}), immediateRender: false}}, @o + {tin:.3f});')
            one.append(f'tl.fromTo({sel}, {{x: 0}}, {{x: -430, duration: 0.6, ease: PMX.tab({SLIDE_OUT}), immediateRender: false}}, @o + {tout:.3f});')
            one.append(f'tl.set({sel}, {{autoAlpha: 0}}, @o + {min(tout + 0.6, period - 0.001):.3f});')
    cues = [(k * period + t, s) for k in range(loops) for t, s in ((0.05, "whoosh"), (1.7, "swipe"))]
    return out(P, stage(P, ctx, w, h, "#000", "".join(hs)), "", loop_js("\n".join(one), period, loops, P), cues, period * loops, (w, h), loops)
