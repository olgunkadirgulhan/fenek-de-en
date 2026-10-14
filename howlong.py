#!/usr/bin/env python3
"""How Long Would It Take? — "X ile Y'ye gitmek ne kadar sürer" (2026-10-14, German with Fenek kanalının yeni konsepti).

Mesafeler NASA/NOAA/ölçüm kaynaklarından, hızlar kaynaklı ya da açıkça varsayım (ör. yürüme 5 km/sa, durmadan);
süre = mesafe / hız. Her açıklamada kaynak + varsayım yazar. Kurgular (Short): guess (3 şıklı tahmin), race (iki yöntem
yarışı), ladder (bir hedef, 4 yöntem), light (ışığın yaşı). Uzun (16:9): howlong_long.py.
Görsel kimlik (diğer kanallara benzemesin): kırık beyaz zemin, kronometre rakamları (Share Tech Mono), mavi rota,
Fluent 3D emojiler (MIT), İngiliz kadın anlatıcı (en-GB-SoniaNeural).

  python howlong.py --dry-run [--kurgu guess|race|ladder|light]
  python howlong.py --auto      # zamanlanmış: kota gününün sonunda 3 Short + 2 uzun, publishAt ile ABD saatine
"""
import asyncio
import csv
import json
import math
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FD = HERE / 'fonts' / 'howlong'
OUT = HERE / 'out' / 'howlong'
LOG = HERE / 'howlong_published.csv'
W, H, FPS = 1080, 1920, 30
BG, GRID, INK, SUB, BLUE, RED, GOLD = (244, 241, 234), (230, 226, 216), (20, 22, 28), (110, 112, 120), (31, 91, 255), (230, 60, 50), (240, 170, 20)
MONO, SANS = str(FD / 'ShareTechMono-Regular.ttf'), str(FD / 'SpaceGrotesk.ttf')
VOICE = os.environ.get('HL_VOICE', 'en-GB-SoniaNeural')
DRY = '--dry-run' in sys.argv
LY = 9.4607e12

# id: (ekran adı, konuşma adı, km, ikon, kaynak, tür)
DEST = {
    'moon': ('THE MOON', 'reach the Moon', 384400, 'moon', 'average Earth-Moon distance, NASA', 'space'),
    'mars': ('MARS', 'reach Mars', 225e6, 'red', 'average distance from Earth, about 225 million km, NASA', 'space'),
    'sun': ('THE SUN', 'reach the Sun', 149.6e6, 'sun', '1 astronomical unit, NASA', 'space'),
    'saturn': ('SATURN', 'reach Saturn', 1.43e9, 'saturn', 'about 1.43 billion km on average, NASA', 'space'),
    'pluto': ('PLUTO', 'reach Pluto', 5.9e9, 'blue', 'about 5.9 billion km on average, NASA', 'space'),
    'proxima': ('PROXIMA CENTAURI', 'reach Proxima Centauri, the nearest star', 4.24 * LY, 'star', '4.24 light-years, NASA', 'space'),
    'center': ('MILKY WAY CENTER', 'reach the center of the Milky Way', 26000 * LY, 'galaxy', 'about 26,000 light-years, NASA', 'space'),
    'iss': ('THE ISS', 'reach the International Space Station', 400, 'probe', 'about 400 km altitude, NASA', 'up'),
    'karman': ('EDGE OF SPACE', 'reach the edge of space', 100, 'comet', 'Karman line, 100 km', 'up'),
    'everest': ('TOP OF EVEREST', 'climb to the top of Mount Everest', 8.849, 'mountain', '8,849 m (2020 China-Nepal survey), straight up from sea level', 'up'),
    'trench': ('MARIANA TRENCH', 'reach the bottom of the Mariana Trench', 10.935, 'wave', 'Challenger Deep, about 10,935 m, NOAA', 'down'),
    'core': ('EARTH\'S CENTER', 'reach the center of the Earth', 6371, 'volcano', 'mean Earth radius 6,371 km, NASA', 'down'),
    'equator': ('AROUND THE EARTH', 'go all the way around the Earth', 40075, 'globe', 'equator 40,075 km, NASA', 'earth'),
    'pole': ('THE NORTH POLE', 'go from the equator to the North Pole', 10002, 'iceberg', 'equator to pole about 10,002 km', 'earth'),
    'nyla': ('NEW YORK → L.A.', 'go from New York to Los Angeles', 3940, 'liberty', 'about 3,940 km in a straight line', 'earth'),
    'sydney': ('LONDON → SYDNEY', 'go from London to Sydney', 17000, 'kangaroo', 'about 17,000 km in a straight line', 'earth'),
    'tokyo': ('TOKYO → NEW YORK', 'go from Tokyo to New York', 10850, 'tokyo', 'about 10,850 km in a straight line', 'earth'),
    'nile': ('THE NILE', 'travel the full length of the Nile', 6650, 'crocodile', 'about 6,650 km long', 'earth'),
    'wall': ('THE GREAT WALL', 'cover the whole Great Wall of China', 21196, 'brick', 'all sections 21,196 km, 2012 Chinese survey', 'earth'),
}
# id: (ekran adı, konuşma adı (fiil öbeği), km/sa, ikon, kaynak/varsayım)
METH = {
    'snail': ('SNAIL', 'a garden snail', 0.048, 'snail', 'garden snail about 0.048 km/h'),
    'sloth': ('SLOTH', 'a sloth', 0.24, 'sloth', 'sloth about 0.24 km/h on the ground'),
    'tortoise': ('TORTOISE', 'a giant tortoise', 0.3, 'turtle', 'giant tortoise about 0.3 km/h'),
    'walk': ('WALKING', 'walking', 5, 'walk', 'walking 5 km/h, nonstop'),
    'run': ('RUNNING', 'jogging', 10, 'run', 'jogging 10 km/h, nonstop'),
    'bike': ('BIKE', 'a bike', 20, 'bike', 'cycling 20 km/h, nonstop'),
    'horse': ('HORSE', 'a horse at a steady trot', 25, 'horse', 'horse trotting about 25 km/h, nonstop'),
    'bolt': ('USAIN BOLT', 'Usain Bolt at top speed', 44.72, 'run', 'Usain Bolt top speed 44.72 km/h (2009 world record race)'),
    'car': ('CAR', 'a car', 100, 'car', 'car at 100 km/h, nonstop'),
    'train': ('BULLET TRAIN', 'a bullet train', 320, 'train', 'bullet train 320 km/h (Shinkansen top operating speed)'),
    'plane': ('JET PLANE', 'a jet plane', 900, 'plane', 'jet cruising about 900 km/h'),
    'sound': ('SPEED OF SOUND', 'the speed of sound', 1235, 'sound', 'speed of sound about 1,235 km/h (343 m/s at 20°C)'),
    'rocket': ('APOLLO 10', 'Apollo 10, the fastest crewed spacecraft', 39897, 'rocket', 'Apollo 10 39,897 km/h, fastest humans (Guinness)'),
    'probe': ('PARKER PROBE', 'the Parker Solar Probe, the fastest human-made object', 692000, 'probe', 'Parker Solar Probe about 692,000 km/h (NASA, 2024)'),
    'light': ('LIGHT', 'light', 1079252849, 'light', 'speed of light 1,079,252,849 km/h'),
}
ORDER = list(METH)
BY = {'walk': 'on foot', 'run': 'jogging', 'bike': 'by bike', 'car': 'by car', 'train': 'by bullet train', 'plane': 'by jet plane',
      'horse': 'on a trotting horse', 'sound': 'at the speed of sound', 'light': 'at the speed of light',
      'snail': 'at the speed of a garden snail', 'sloth': 'at the speed of a sloth', 'tortoise': 'at the speed of a giant tortoise',
      'bolt': 'at Usain Bolt\'s top speed'}
SMALL = {'of', 'the', 'to', 'vs', 'and', 'by', 'a', 'in', 'from', 'it', 'is', 'as', 'at', 'on', 'with'}


def tcase(t):
    w = t.split(' ')
    return ' '.join(x.lower() if (i and x.lower() in SMALL) else (x[0].upper() + x[1:].lower() if x.isupper() and len(x) > 2 else x[:1].upper() + x[1:])
                    for i, x in enumerate(w)).replace('L.a.', 'L.A.').replace('Iss', 'ISS').replace(' vs ', ' vs ')


def log(m): print(m, flush=True)


# ---------------------------------------------------------------- süre
def hours(dest, meth): return DEST[dest][2] / METH[meth][2]


def big(n):
    for v, w in ((1e18, 'quintillion'), (1e15, 'quadrillion'), (1e12, 'trillion'), (1e9, 'billion'), (1e6, 'million'), (1e3, 'thousand')):
        if n >= v:
            x = n / v
            return f'{x:,.0f} {w}' if x >= 10 else f'{x:.1f} {w}'.replace('.0 ', ' ')
    return f'{n:,.0f}'


def km(n):
    return big(n) if n >= 1e6 else f'{n:,.0f}' if n >= 100 else f'{n:,.3g}'


def spd(v):
    return f'{v:,.0f}' if v >= 10 else f'{v:g}'


def cap(x): return x[0].upper() + x[1:]


def noun(goal):
    return goal.replace('reach ', '').replace('climb to ', '').split(',')[0]


def human(h):
    """Konuşma/başlık için insan dili."""
    s = h * 3600
    if s < 1: return f'{s * 1000:,.1f} milliseconds' if s >= 0.001 else f'{s * 1e6:,.1f} microseconds'
    if s < 90: return f'{s:,.1f} seconds'.replace('.0 ', ' ')
    if h < 2: return f'{s / 60:,.0f} minutes'
    if h < 72: return f'{h:,.1f} hours'.replace('.0 ', ' ')
    d = h / 24
    if d < 730: return f'{d:,.0f} days'
    y = d / 365.25
    return f'{y:,.0f} years' if y < 1e4 else f'{big(y)} years'


def clock(h, k=1.0):
    """Ekrandaki kronometre: k (0→1) ilerleme."""
    s = h * 3600 * k
    if h * 3600 < 1: return f'{s * 1000:,.1f} MS'
    if h < 72:
        hh, r = divmod(int(s), 3600); mm, ss = divmod(r, 60)
        return f'{hh:02d}:{mm:02d}:{ss:02d}'
    d = s / 86400
    if h / 24 < 730: return f'{d:,.0f} DAYS'
    y = d / 365.25
    return f'{y:,.0f} YEARS' if h / 8766 < 1e7 else f'{big(y).upper()} YRS'


def compare(h, rnd):
    s, y = h * 3600, h / 8766
    if s < 0.3: return rnd.choice(['That is faster than a blink.', 'You could not even blink in that time.'])
    if s < 600: return rnd.choice([f'That is shorter than most songs.', 'Over before you finish a snack.'])
    if h < 48: return rnd.choice([f'That is about {h / 2:,.0f} movies back to back.', f'That is about {h / 8:,.1f} full work days.'.replace('.0 ', ' ')])
    if h < 24 * 21: return rnd.choice([f'That is {h / 24:,.0f} days and nights without stopping.', f'No sleep, no breaks, for {h / 24:,.0f} days straight.'])
    if y < 2: return rnd.choice([f'That is about {h / 168:,.0f} weeks.', f'That is about {h / 730:,.0f} months without a single break.'])
    if y < 70: return rnd.choice([f'That is about {y / 78.4 * 100:,.0f} percent of an average human life.', f'Leave at 20, and you arrive at about {20 + y:,.0f}.'])
    if y < 400: return rnd.choice([f'That is about {y / 78.4:,.1f} human lifetimes.'.replace('.0 ', ' '), f'Someone who left the day you were born would still be going at age {min(y, 78):,.0f}.' if y > 78 else f'That is about {y / 78.4 * 100:,.0f} percent of an average human life.'])
    if y < 1e6: return rnd.choice([f'That is about {y / 4500:,.1f} times longer than the pyramids of Giza have existed.'.replace('.0 ', ' '), f'That is roughly {y / 78.4:,.0f} human lifetimes.'])
    return rnd.choice([f'That is {y / 13.8e9:,.2f} times the age of the universe.' if y > 1e9 else f'That is about {y / 66e6:,.2f} times as long ago as the dinosaurs died out.',
                       f'That is about {big(y / 78.4)} human lifetimes.'])


# ---------------------------------------------------------------- konu
def done():
    if not LOG.exists(): return set(), []
    with LOG.open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return {r['topic_id'] for r in rows}, rows


def sensible(dest, meth):
    h = hours(dest, meth)
    return 1e-7 < h * 3600 < 3e19 * 3600 and not (DEST[dest][5] in ('up', 'down') and meth in ('plane', 'train', 'sound', 'probe', 'rocket') and DEST[dest][2] < 50)


def pick(rnd, kurgu=None):
    seen, rows = done(); recent = [r['topic_id'].split(':')[2] for r in rows[-4:] if r['topic_id'].count(':') >= 2]
    for _ in range(2000):
        k = kurgu or rnd.choice(['guess', 'guess', 'race', 'ladder', 'light'])
        if k == 'light':
            d = rnd.choice([x for x in DEST if DEST[x][5] == 'space']); key = ['light', d]
        else:
            d = rnd.choice(list(DEST))
            if d in recent: continue
            if k == 'guess':
                m = rnd.choice(ORDER); key = ['guess', d, m]
                if m == 'light' or not sensible(d, m): continue
            elif k == 'race':
                a, b = sorted(rnd.sample(ORDER[:-1], 2), key=ORDER.index); key = ['race', d, a, b]
                if not (sensible(d, a) and sensible(d, b)) or hours(d, a) / hours(d, b) < 2.5: continue
            else:
                ms = sorted(rnd.sample(ORDER, 4), key=ORDER.index); key = ['ladder', d] + ms
                if not all(sensible(d, m) for m in ms): continue
        tid = 'hl:' + ':'.join(key)
        if tid not in seen:
            return key, tid
    raise RuntimeError('yeni konu kalmadı')


def build(key, rnd):
    k = key[0]; d = key[1]; D = DEST[d]
    src = [f'Distance: {D[4]}.']
    if k == 'guess':
        m = key[2]; M = METH[m]; h = hours(d, m)
        wrong = [h * f for f in rnd.choice([(0.1, 10), (0.25, 4), (0.05, 20), (0.3, 3)])]
        opts = [h] + wrong; rnd.shuffle(opts); letter = 'ABC'[opts.index(h)]
        v = dict(icons=[M[3]], dest=d, h=[h], opts=[human(o) for o in opts], right=opts.index(h))
        say_opts = ', '.join(f'{"ABC"[i]}: {human(o)}' for i, o in enumerate(opts))
        by = BY.get(m, f'with {M[1]}')
        beats = [rnd.choice([f'How long would it take to {D[1]} {by}?', f'{cap(D[1])} {by}. How long would that take?',
                             f'Imagine you {D[1]} {by}. Guess the time.']),
                 f'Is it {say_opts}? Pick one.',
                 rnd.choice([f'The distance is {km(D[2])} kilometers.', f'That is {km(D[2])} kilometers.'])
                 + f' The speed: about {spd(M[2])} kilometers per hour, nonstop, no breaks.',
                 rnd.choice(['Let us go.', 'Starting the clock.', 'Here we go.']),
                 rnd.choice([f'The answer is {letter}: {human(h)}.', f'It takes {human(h)}. Answer {letter}.']),
                 compare(h, rnd),
                 rnd.choice(['Did you guess right? Tell me below.', 'What should I time next? Comment below.', 'Was your guess too high or too low? Comment below.'])]
        title = rnd.choice([f'How Long to {D[1]} {by}?', f'{cap(D[1])} {by}: How Long Would It Take?']).split(',')[0].rstrip('?') + '?'
        src.append(f'Speed: {M[4]}.')
        show = ['hook', 'opts', 'facts', 'run', 'answer', 'compare', 'cta']
    elif k == 'race':
        a, b = key[2], key[3]; A, B = METH[a], METH[b]; ha, hb = hours(d, a), hours(d, b)
        v = dict(icons=[A[3], B[3]], dest=d, h=[ha, hb])
        beats = [rnd.choice([f'Race time! {cap(D[1])}: {A[1]} against {B[1]}.', f'{cap(A[1])} or {B[1]}: who would {D[1]} first, and by how much?']),
                 f'The distance: {km(D[2])} kilometers.',
                 rnd.choice(['Go!', 'Three, two, one, go.']),
                 f'{cap(B[1])} arrives in {human(hb)}.',
                 f'{cap(A[1])} needs {human(ha)}. That is {km(ha / hb)} times longer.',
                 rnd.choice(['Which matchup should I race next? Comment below.', 'Did you expect that gap? Tell me below.'])]
        title = rnd.choice([f'{A[0]} vs {B[0]}: Who Would {D[1].split(",")[0]} First?', f'{cap(D[1].split(",")[0])}: {A[0]} vs {B[0]}'])
        src += [f'Speeds: {A[4]}; {B[4]}.']
        show = ['hook', 'facts', 'run', 'finish_b', 'finish_a', 'cta']
    elif k == 'ladder':
        ms = key[2:]; hs = [hours(d, m) for m in ms]
        v = dict(icons=[METH[m][3] for m in ms], dest=d, h=hs, names=[METH[m][0] for m in ms])
        beats = [rnd.choice([f'Four ways to {D[1]}, from slowest to fastest.', f'How long would it take to {D[1]}? Four speeds.']),
                 f'The distance is {km(D[2])} kilometers.'] + \
                [f'{cap(METH[m][1])}: {human(h)}.' for m, h in zip(ms, hs)] + \
                [rnd.choice(['Which one surprised you? Tell me below.', 'What should I add next time? Comment below.'])]
        title = rnd.choice([f'How Long to {D[1].split(",")[0]}? 4 Speeds Compared', f'{cap(D[1].split(",")[0])}: {METH[ms[0]][0]} vs {METH[ms[-1]][0]} and More'])
        src += ['Speeds: ' + '; '.join(METH[m][4] for m in ms) + '.']
        show = ['hook', 'facts'] + [f'row{i}' for i in range(4)] + ['cta']
    else:
        h = hours(d, 'light')
        v = dict(icons=['light'], dest=d, h=[h])
        nn = noun(D[1])
        beats = [rnd.choice([f'When you look at {nn}, you are looking into the past. Here is how far.', f'How old is the light you see from {nn}?']),
                 f'{cap(nn)} is {km(D[2])} kilometers away, and light travels about 300 thousand kilometers every second.',
                 'Starting the clock.',
                 f'The light takes {human(h)} to reach us.',
                 f'So you see {nn} as it was {human(h)} ago.',
                 rnd.choice(['Which object should I check next? Comment below.', 'Did you know this? Tell me below.'])]
        title = rnd.choice([f'How Old Is the Light From {nn}?', f'You See {nn} as It Was {human(h)} Ago'])
        src.append('Speed of light: 299,792 km/s.')
        show = ['hook', 'facts', 'run', 'answer', 'compare', 'cta']
    title = tcase(title)
    v.update(key=key, kurgu=k, beats=beats, show=show, title=title[:90],
             desc=(title + '\n\n' + '\n'.join(src) + '\nTime = distance ÷ speed, nonstop, in a straight line where there is no road. A fun thought experiment, not a travel plan.'
                   + '\n\nEmoji art: Microsoft Fluent Emoji (MIT).\n\n#howlong #science #space #maths #shorts'))
    v['tags'] = ['how long would it take', 'how long', 'science', 'space', 'speed', 'distance', 'shorts']
    return v


# ---------------------------------------------------------------- çizim
_FC, _IC = {}, {}


def font(path, sz, w=700):
    k = (path, sz, w)
    if k not in _FC:
        f = ImageFont.truetype(path, sz)
        if path == SANS:
            try: f.set_variation_by_axes([w])
            except Exception: pass
        _FC[k] = f
    return _FC[k]


def icon(name, sz):
    k = (name, sz)
    if k not in _IC:
        _IC[k] = Image.open(FD / 'emoji' / f'{name}.png').convert('RGBA').resize((sz, sz), Image.LANCZOS)
    return _IC[k]


def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def background(w=W, h=H):
    img = Image.new('RGB', (w, h), BG); d = ImageDraw.Draw(img)
    for x in range(0, w, 54): d.line([(x, 0), (x, h)], fill=GRID)
    for y in range(0, h, 54): d.line([(0, y), (w, y)], fill=GRID)
    return img


def route(img, d, y, prog, ic, dest_ic, label, x0=120, x1=960, sz=150):
    for x in range(x0, x1, 28): d.line([(x, y), (x + 14, y)], fill=SUB, width=5)
    d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=BLUE, width=9)
    di = icon(dest_ic, sz); img.paste(di, (x1 - sz // 2, y - sz // 2 - 4), di)
    mi = icon(ic, int(sz * 0.8)); img.paste(mi, (int(x0 + (x1 - x0) * prog) - mi.width // 2, y - mi.height - 18), mi)
    if label:
        lf = font(SANS, 34); lw = d.textlength(label, font=lf)
        d.text((min(x1, W - 30 - lw / 2), y + sz // 2 + 18), label, font=lf, fill=INK, anchor='mt')


def wrap(d, text, f, maxw):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    return lines + [cur] if cur else lines


def frame(base, v, bi, t, dur):
    img = base.copy(); d = ImageDraw.Draw(img); st = v['show'][bi]; D = DEST[v['dest']]
    d.text((W // 2, 150), 'HOW LONG WOULD IT TAKE?', font=font(SANS, 62), fill=INK, anchor='mm')
    d.rectangle([W // 2 - 220, 196, W // 2 + 220, 204], fill=BLUE)
    step = v['show'].index(st)
    run_i = v['show'].index('run') if 'run' in v['show'] else None
    k_run = 0.0 if run_i is None or step < run_i else (ease(t / max(1.0, dur - 0.3)) if step == run_i else 1.0)
    if v['kurgu'] in ('guess', 'light'):
        route(img, d, 620, k_run, v['icons'][0], D[3], D[0])
        hint = METH['light'][0] if v['kurgu'] == 'light' else METH[v['key'][2]][0]
        d.text((120, 720), hint, font=font(SANS, 34), fill=SUB)
        d.text((W // 2, 900), clock(v['h'][0], k_run), font=font(MONO, 150), fill=BLUE if k_run < 1 else RED, anchor='mm')
        if v['kurgu'] == 'guess' and step >= 1:
            for i, o in enumerate(v['opts']):
                y = 1070 + i * 130; right = (i == v['right']) and step >= v['show'].index('answer')
                d.rounded_rectangle([140, y, 940, y + 105], radius=52, fill=(BLUE if right else (255, 255, 255)), outline=INK, width=4)
                d.text((190, y + 52), 'ABC'[i], font=font(SANS, 52), fill=(255, 255, 255) if right else BLUE, anchor='lm')
                d.text((560, y + 52), o.upper(), font=font(MONO, 50), fill=(255, 255, 255) if right else INK, anchor='mm')
    elif v['kurgu'] == 'race':
        ha, hb = v['h']; fa = v['show'].index('finish_a')
        for j, (ic, y) in enumerate(((v['icons'][0], 560), (v['icons'][1], 860))):
            if j == 1: p = k_run
            else:
                p = max(0.02 if k_run > 0 else 0.0, k_run * hb / ha)
                if step == fa: p = p + (1 - p) * ease(t / 2.0)
                elif step > fa: p = 1.0
            route(img, d, y, p, ic, D[3], D[0] if j == 1 else None, sz=130)
            d.text((120, y + 50), METH[v['key'][2 + j]][0], font=font(SANS, 32), fill=SUB)
        d.text((W // 2, 1100), clock(hb, 1.0) if step >= v['show'].index('finish_b') else '', font=font(MONO, 92), fill=BLUE, anchor='mm')
        if step >= v['show'].index('finish_a'):
            d.text((W // 2, 1220), clock(ha, 1.0), font=font(MONO, 92), fill=RED, anchor='mm')
    else:                                                              # ladder
        di = icon(D[3], 170); img.paste(di, (W // 2 - 85, 240), di)
        d.text((W // 2, 440), D[0], font=font(SANS, 52), fill=INK, anchor='mm')
        for i in range(4):
            if step < 2 + i: break
            y = 540 + i * 200; mi = icon(v['icons'][i], 120); img.paste(mi, (110, y), mi)
            d.text((260, y + 30), v['names'][i], font=font(SANS, 38), fill=SUB, anchor='lm')
            kk = ease(t / 0.8) if step == 2 + i else 1.0
            d.text((260, y + 92), clock(v['h'][i], kk), font=font(MONO, 72), fill=BLUE, anchor='lm')
    if step >= 1 and v['kurgu'] != 'ladder':
        d.text((W // 2, 1480 if v['kurgu'] == 'guess' else 1420), f'{km(D[2]).upper()} KM', font=font(MONO, 44), fill=SUB, anchor='mm')
    if st == 'cta':
        d.rounded_rectangle([170, 1560, 910, 1680], radius=60, fill=BLUE)
        d.text((W // 2, 1620), 'WHAT NEXT? COMMENT!', font=font(SANS, 52), fill=(255, 255, 255), anchor='mm')
    else:
        f = font(SANS, 42, 500); ls = wrap(d, v['beats'][bi], f, 920)[:3]
        for j, l in enumerate(ls):
            d.text((W // 2, 1590 + j * 56), l, font=f, fill=INK, anchor='mm')
    return img


# ---------------------------------------------------------------- ses + video
def tts(text, path):
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, VOICE, rate='+4%').save(str(path))
    for i in range(3):
        try:
            asyncio.run(go())
            if path.exists() and path.stat().st_size > 1000: return
        except Exception as e:
            log(f'  tts deneme {i + 1}: {e}')
    raise RuntimeError('edge-tts çalışmadı')


def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def voice(beats, tmp, pad=0.3, min_d=None):
    auds, durs = [], []
    for i, b in enumerate(beats):
        a = tmp / f'a{i}.mp3'; tts(b, a); w = tmp / f'w{i}.wav'
        af = f'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur={pad}'
        if min_d and min_d(i): af += f',apad=whole_dur={min_d(i)}'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(a), '-af', af, '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', str(w)], check=True)
        auds.append(w); durs.append(dur(w))
    lst = tmp / 'a.txt'; lst.write_text(''.join(f"file '{a}'\n" for a in auds))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-ar', '44100', '-ac', '2', str(tmp / 'voice.wav')], check=True)
    return durs


def encode(frames_fn, durs, wav, mp4, w, h, settle_fn):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                          '-i', str(wav), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(mp4)], stdin=subprocess.PIPE)
    for i, dd in enumerate(durs):
        last = None; settle = settle_fn(i, dd)
        for k in range(int(dd * FPS)):
            t = k / FPS
            if t > settle and last is not None: p.stdin.write(last); continue
            fr = frames_fn(i, t, dd).tobytes()
            if t > settle - 0.04: last = fr
            p.stdin.write(fr)
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError('ffmpeg hata')


def render(v, mp4):
    tmp = mp4.with_suffix(''); tmp.mkdir(parents=True, exist_ok=True)
    run_i = v['show'].index('run') if 'run' in v['show'] else -1
    durs = voice(v['beats'], tmp, min_d=lambda i: 3.2 if i == run_i else None)
    base = background()
    encode(lambda i, t, dd: frame(base, v, i, t, dd), durs, tmp / 'voice.wav', mp4, W, H,
           lambda i, dd: dd if (i == run_i or (v['kurgu'] == 'race' and i == v['show'].index('finish_a'))) else 1.0)
    return mp4


# ---------------------------------------------------------------- yükleme + akış
def quota_day(now=None):
    now = now or datetime.now(timezone.utc)
    return (now - timedelta(hours=7)).strftime('%Y-%m-%d')            # YouTube kota günü: Pasifik gece yarısı ≈ 07:00 UTC


def record(tid, vid, kind, title, publish_at):
    new = not LOG.exists()
    with LOG.open('a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['topic_id', 'date_utc', 'quota_day', 'video_id', 'kind', 'title', 'publish_at'])
        if new: w.writeheader()
        w.writerow(dict(topic_id=tid, date_utc=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'), quota_day=quota_day(),
                        video_id=vid, kind=kind, title=title, publish_at=publish_at))


def publish_at(kind, n_today):
    """Kota gününün sonunda yüklenir, ABD izlenme saatinde yayınlanır (aynı UTC günü)."""
    slots = {'short': ['14:00', '17:30', '21:00'], 'long': ['15:30', '23:00']}[kind]
    hh, mm = map(int, slots[min(n_today, len(slots) - 1)].split(':'))
    now = datetime.now(timezone.utc); t = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if t < now + timedelta(minutes=30): t = now + timedelta(minutes=40)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    a = sys.argv[1:]
    kurgu = a[a.index('--kurgu') + 1] if '--kurgu' in a else None
    kind = 'short'
    if '--auto' in a:
        _, rows = done(); q = quota_day()
        today = [r for r in rows if r['quota_day'] == q]
        ns, nl = sum(r['kind'] == 'short' for r in today), sum(r['kind'] == 'long' for r in today)
        want_s, want_l = int(os.environ.get('SHORTS_PER_DAY') or 3), int(os.environ.get('LONGS_PER_DAY') or 2)
        if ns < want_s: kind = 'short'
        elif nl < want_l: kind = 'long'
        else:
            log(f'kota günü {q}: {ns} short + {nl} uzun yüklendi, iş yok'); return
        log(f'kota günü {q}: {ns} short, {nl} uzun → şimdi {kind}')
        n_today = ns if kind == 'short' else nl
    else:
        n_today = 0
        if '--long' in a: kind = 'long'
    rnd = random.Random(); OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')
    if kind == 'long':
        import howlong_long as L
        key, tid = L.pick(rnd); v = L.build(key, rnd); log(f'[howlong-long] {tid} → {v["title"]}')
        mp4 = L.render(v, OUT / f'long_{stamp}.mp4')
    else:
        key, tid = pick(rnd, kurgu); v = build(key, rnd); log(f'[howlong] {tid} → {v["title"]}')
        mp4 = render(v, OUT / f'short_{stamp}.mp4')
    if DRY:
        log(f'  [dry-run] {mp4}\n{v["desc"]}'); return
    import upload
    log(f'kanal: {upload.check_channel()}')
    pa = publish_at(kind, n_today)
    yt = upload.client()
    body = {'snippet': {'title': upload.clean(v['title'] + (' #shorts' if kind == 'short' else ''))[:100], 'description': upload.clean(v['desc'])[:4900],
                        'tags': v['tags'], 'categoryId': '28', 'defaultLanguage': 'en', 'defaultAudioLanguage': 'en-GB'},
            'status': {'privacyStatus': 'private', 'publishAt': pa, 'selfDeclaredMadeForKids': False}}
    from googleapiclient.http import MediaFileUpload
    vid = yt.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(str(mp4), resumable=True)).execute()['id']
    record(tid, vid, kind, v['title'], pa)
    log(f'  ✓ https://youtu.be/{vid} (yayın {pa})')


if __name__ == '__main__':
    main()
