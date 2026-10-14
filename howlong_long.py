#!/usr/bin/env python3
"""How Long Would It Take? — uzun video (16:9): 'all' = bir hedefe salyangozdan ışığa bütün hızlar;
'tour' = tek hız ile bütün hedefler (yakından uzağa). Konu kimliği hll:... howlong_published.csv'de; tekrar edilmez."""
import random
from PIL import ImageDraw

import howlong as H
from howlong import DEST, METH, ORDER, BY, hours, human, clock, compare, km, cap, font, icon, ease, wrap, SANS, MONO, INK, SUB, BLUE, RED

W, Hh = 1920, 1080


def pick(rnd):
    seen, _ = H.done()
    opts = [['all', d] for d in DEST] + [['tour', m] for m in ORDER if m not in ('snail', 'light')]
    rnd.shuffle(opts)
    for key in opts:
        tid = 'hll:' + ':'.join(key)
        if tid not in seen:
            return key, tid
    raise RuntimeError('yeni uzun konu kalmadı')


def build(key, rnd):
    k, x = key
    if k == 'all':
        D = DEST[x]; rows = [(m, hours(x, m)) for m in ORDER if H.sensible(x, m)]
        rows.sort(key=lambda r: -r[1])
        items = [dict(ic=METH[m][3], name=METH[m][0], h=h, src=METH[m][4],
                      say=f"{cap(BY.get(m, 'with ' + METH[m][1]))}: {human(h)}. " + compare(h, rnd)) for m, h in rows]
        head, head_ic = D[0], D[3]
        intro = rnd.choice([f"How long would it take to {D[1]}? Today we try every speed, from a garden snail all the way to the speed of light.",
                            f"{cap(D[1])}. {len(items)} different speeds, from the slowest to the fastest. Let us time every one."])
        context = f"The distance is {km(D[2])} kilometers. Source: {D[4]}. Every trip is nonstop, in a straight line, with no breaks."
        title = rnd.choice([f"How Long to {D[1].split(',')[0]}? Every Speed From Snail to Light", f"{cap(D[1].split(',')[0])}: {len(items)} Speeds Compared"])
        src = [f"Distance: {D[4]}."] + [f"{METH[m][0].title()}: {METH[m][4]}." for m, _ in rows]
    else:
        M = METH[x]; rows = [(d, hours(d, x)) for d in DEST if H.sensible(d, x)]
        rows.sort(key=lambda r: r[1])
        items = [dict(ic=DEST[d][3], name=DEST[d][0], h=h, src=DEST[d][4],
                      say=f"{cap(DEST[d][1].split(',')[0])}: {km(DEST[d][2])} kilometers, so {human(h)}. " + compare(h, rnd)) for d, h in rows]
        head, head_ic = M[0], M[3]
        intro = rnd.choice([f"What if you could only travel {BY.get(x, 'with ' + M[1])}? Here is how long it would take to reach {len(items)} places, from close to impossibly far.",
                            f"One speed, {len(items)} destinations. Let us see how far {M[1]} can really go."])
        context = f"The speed: about {M[2]:,.4g} kilometers per hour. Source: {M[4]}. Every trip is nonstop, in a straight line."
        title = rnd.choice([f"How Far Can {M[1].split(',')[0]} Go? {len(items)} Destinations Timed", f"Everywhere {BY.get(x, 'with ' + M[1])}: How Long Would It Take?"])
        src = [f"Speed: {M[4]}."] + [f"{DEST[d][0].title()}: {DEST[d][4]}." for d, _ in rows]
    fast, slow = min(items, key=lambda i: i['h']), max(items, key=lambda i: i['h'])
    summary = f"From {human(fast['h'])} to {human(slow['h'])}. The slowest takes {km(slow['h'] / fast['h'])} times longer than the fastest."
    outro = rnd.choice(["Which one surprised you most? And what should I time next? Tell me in the comments.",
                        "Give me a place and a speed in the comments, and I will time it."])
    title = H.tcase(title)
    desc = (title + '\n\n' + '\n'.join(f"{i['name'].title()}: {human(i['h'])}" for i in items) + '\n\nSources and assumptions:\n' + '\n'.join(src)
            + '\nTime = distance ÷ speed, nonstop, in a straight line where there is no road. A thought experiment, not a travel plan.'
            + '\n\nEmoji art: Microsoft Fluent Emoji (MIT).\n\n#howlong #science #space')
    return dict(key=key, head=head, head_ic=head_ic, items=items, beats=[intro, context] + [i['say'] for i in items] + [summary, outro],
                title=title[:95], desc=desc, tags=['how long would it take', 'science', 'space', 'speed', 'distance', 'education'])


def frame(base, v, bi, t, dur):
    img = base.copy(); d = ImageDraw.Draw(img); its = v['items']; n = len(its)
    hi = icon(v['head_ic'], 220); img.paste(hi, (120, 200), hi)
    d.text((230, 470), v['head'], font=font(SANS, 52), fill=INK, anchor='mm')
    d.text((230, 120), 'HOW LONG?', font=font(SANS, 60), fill=BLUE, anchor='mm')
    cur = bi - 2; rh = min(84, 860 // max(n, 1))
    for i, it in enumerate(its):
        if i > cur: break
        y = 50 + i * rh; act = (i == cur)
        ic = icon(it['ic'], rh - 8); img.paste(ic, (480, y + 2), ic)
        d.text((480 + rh + 14, y + rh // 2), it['name'], font=font(SANS, int(rh * 0.5)), fill=INK if act else SUB, anchor='lm')
        kk = ease(t / 1.2) if act else 1.0
        d.text((1840, y + rh // 2), clock(it['h'], kk), font=font(MONO, int(rh * 0.72)), fill=RED if act else BLUE, anchor='rm')
    if bi < 2:
        d.text((1180, 500), 'SLOW' if v['key'][0] == 'all' else 'NEAR', font=font(SANS, 120), fill=INK, anchor='mm')
        d.text((1180, 640), '→ FAST' if v['key'][0] == 'all' else '→ FAR', font=font(SANS, 120), fill=BLUE, anchor='mm')
    f = font(SANS, 36, 500); allx = wrap(d, v['beats'][bi], f, 1700)
    groups = [allx[i:i + 2] for i in range(0, len(allx), 2)] or [[]]
    ls = groups[min(len(groups) - 1, int(t / max(dur, 0.1) * len(groups)))]
    d.rectangle([0, 950, W, Hh], fill=(255, 255, 255))
    for j, l in enumerate(ls):
        d.text((W // 2, 990 + j * 46), l, font=f, fill=INK, anchor='mm')
    return img


def render(v, mp4):
    tmp = mp4.with_suffix(''); tmp.mkdir(parents=True, exist_ok=True)
    durs = H.voice(v['beats'], tmp, pad=0.6)
    base = H.background(W, Hh)
    H.encode(lambda i, t, dd: frame(base, v, i, t, dd), durs, tmp / 'voice.wav', mp4, W, Hh, lambda i, dd: 99)   # altyazı parçası değişir: önbellek yok
    return mp4
