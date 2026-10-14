#!/usr/bin/env python3
"""How Long Would It Take? — ek kurgular (2026-10-14, kullanıcı: kurgular 5 katı). Her biri farklı yapı/sahne:

higherlower, countdown, distguess, speedguess, lifetime, oneday, timesaround, scalemodel, truefalse, agearrive,
yeararrive, measured, oddone, rank3, inatime, halfway  (+ howlong.py: guess, race, ladder, light = 20)

Sahne türleri: q (soru), cards (A/B kartları), opts (şıklar), big (büyük sayı), list (satırlar), tf (doğru/yanlış),
calendar (takvim yaprağı), scale (ölçekli küreler), route (rota + kronometre).
"""
import datetime
import math

from PIL import ImageDraw

import howlong as H
from howlong import (DEST, METH, ORDER, BY, hours, human, clock, compare, km, cap, font, icon, ease, wrap, big,
                     SANS, MONO, INK, SUB, BLUE, RED, GOLD, W)

LIFE = 78.4          # ABD ortalama yaşam süresi (CDC, 2023)
SIZE = {'moon': 3474.8, 'mars': 6779, 'sun': 1392700, 'saturn': 116460, 'pluto': 2376}   # çap km, NASA
EARTH_D, BALL = 12742, 0.243     # Dünya çapı (NASA); basketbol topu çapı ~24 cm
GREEN = (30, 160, 90)
SPACE = [d for d in DEST if DEST[d][5] == 'space']
EARTHLY = [d for d in DEST if DEST[d][5] != 'space']
KURGU = ['higherlower', 'countdown', 'distguess', 'speedguess', 'lifetime', 'oneday', 'timesaround', 'scalemodel',
         'truefalse', 'agearrive', 'yeararrive', 'measured', 'oddone', 'rank3', 'inatime', 'halfway']


NOUN = {'moon': 'the Moon', 'mars': 'Mars', 'sun': 'the Sun', 'saturn': 'Saturn', 'pluto': 'Pluto', 'proxima': 'Proxima Centauri',
        'center': 'the center of the Milky Way', 'iss': 'the ISS', 'karman': 'the edge of space', 'everest': 'the top of Everest',
        'trench': 'the bottom of the Mariana Trench', 'core': 'the center of the Earth', 'equator': 'one lap around the Earth',
        'pole': 'the North Pole', 'nyla': 'New York to L.A.', 'sydney': 'London to Sydney', 'tokyo': 'Tokyo to New York',
        'nile': 'the length of the Nile', 'wall': 'the whole Great Wall'}


def N(d): return NOUN[d]
def tby(m): return BY.get(m) if m in BY else f'with {METH[m][0].title()}'


def goal(d): return DEST[d][1]
def g0(d): return DEST[d][1].split(',')[0]
def by(m): return BY.get(m, f'with {METH[m][1]}')
def ok(d, m): return H.sensible(d, m)


def key_for(k, rnd):
    """Kurgu için rastgele konu anahtarı (None = uygun değil, tekrar dene)."""
    if k == 'higherlower':
        (d1, m1), (d2, m2) = [(rnd.choice(list(DEST)), rnd.choice(ORDER[:-1])) for _ in range(2)]
        if (d1, m1) == (d2, m2) or not ok(d1, m1) or not ok(d2, m2) or not (0.2 < hours(d1, m1) / hours(d2, m2) < 5): return None
        return [k, d1, m1, d2, m2]
    if k == 'countdown': return [k, rnd.choice(list(DEST))]
    if k == 'distguess': return [k, rnd.choice(list(DEST))]
    if k == 'speedguess':
        d = rnd.choice(list(DEST)); return [k, d]
    if k in ('lifetime', 'oneday', 'inatime'):
        m = rnd.choice(ORDER[:-1])
        if k == 'inatime': return [k, m, rnd.choice(['hour', 'day', 'week', 'year'])]
        dist = METH[m][2] * (LIFE * 8766 if k == 'lifetime' else 24)
        n_ok = sum(DEST[d][2] <= dist for d in DEST)
        return [k, m] if 1 <= n_ok < len(DEST) else None
    if k == 'timesaround': return [k, rnd.choice([d for d in DEST if d not in ('equator',)])]
    if k == 'scalemodel': return [k, rnd.choice(list(SIZE))]
    if k == 'truefalse':
        d, m = rnd.choice(list(DEST)), rnd.choice(ORDER[:-1])
        return [k, d, m] if ok(d, m) else None
    if k in ('agearrive', 'yeararrive'):
        d, m = rnd.choice(list(DEST)), rnd.choice(ORDER[:-1])
        y = hours(d, m) / 8766
        return [k, d, m] if ok(d, m) and (0.5 < y < 60 if k == 'agearrive' else 0.3 < y < 5000) else None
    if k == 'measured':
        d, m = rnd.choice(list(DEST)), rnd.choice(ORDER[:-1])
        return [k, d, m, rnd.choice(['heartbeats', 'breaths', 'nights', 'songs', 'movies'])] if ok(d, m) and hours(d, m) > 0.5 else None
    if k == 'oddone':
        d = rnd.choice(list(DEST)); ms = sorted(rnd.sample(ORDER[:-1], 4), key=ORDER.index)
        n_over = sum(hours(d, m) > 8766 for m in ms)
        return [k, d] + ms if all(ok(d, m) for m in ms) and n_over == 1 else None
    if k == 'rank3':
        m = rnd.choice(ORDER[3:-1]); ds = rnd.sample(list(DEST), 3)
        return [k, m] + ds if all(ok(d, m) for d in ds) else None
    if k == 'halfway':
        d, m = rnd.choice(list(DEST)), rnd.choice(ORDER[:-1])
        return [k, d, m] if ok(d, m) else None


def build(key, rnd):
    k = key[0]; B = []                      # B: [(söz, sahne)]
    src = []
    if k == 'higherlower':
        _, d1, m1, d2, m2 = key; h1, h2 = hours(d1, m1), hours(d2, m2); w = 0 if h1 > h2 else 1
        c = lambda r: [dict(ic=METH[m1][3], ic2=DEST[d1][3], t=DEST[d1][0], s=METH[m1][0], v=clock(h1) if r else '?'),
                       dict(ic=METH[m2][3], ic2=DEST[d2][3], t=DEST[d2][0], s=METH[m2][0], v=clock(h2) if r else '?')]
        B = [(rnd.choice([f'Which trip takes longer? A: {goal(d1)} {by(m1)}. B: {goal(d2)} {by(m2)}.',
                          f'Higher or lower? Trip A: {goal(d1)} {by(m1)}. Trip B: {goal(d2)} {by(m2)}.']), dict(t='cards', c=c(False))),
             ('Make your pick.', dict(t='cards', c=c(False), timer=True)),
             (f'Trip A takes {human(h1)}.', dict(t='cards', c=c(False)[:0] + [c(True)[0], c(False)[1]])),
             (f'Trip B takes {human(h2)}. So the longer one is {"A" if w == 0 else "B"}.', dict(t='cards', c=c(True), win=w)),
             (rnd.choice(['Did you get it? Comment A or B.', 'How many did you get right this week? Tell me below.']), dict(t='cards', c=c(True), win=w, cta=True))]
        title = f'Which Takes Longer? {cap(N(d1))} {tby(m1)} or {N(d2)} {tby(m2)}'
        src += [f'{DEST[d1][0].title()}: {DEST[d1][4]}; {DEST[d2][0].title()}: {DEST[d2][4]}', f'Speeds: {METH[m1][4]}; {METH[m2][4]}']
    elif k == 'countdown':
        d = key[1]; ms = [m for m in ORDER if ok(d, m)]; pick5 = [ms[int(i * (len(ms) - 1) / 4)] for i in range(5)]
        rows = [dict(ic=METH[m][3], n=METH[m][0], v=clock(hours(d, m)), r=5 - i) for i, m in enumerate(pick5)]
        B = [(f'Five speeds, one destination: {goal(d)}. Counting down from the slowest.', dict(t='list', rows=rows, n=0, head=d))]
        for i, m in enumerate(pick5):
            B.append((f'Number {5 - i}: {METH[m][1]}. {cap(human(hours(d, m)))}.', dict(t='list', rows=rows, n=i + 1, head=d)))
        B.append((rnd.choice(['Which number surprised you? Tell me below.', 'What speed should I add next time? Comment below.']), dict(t='list', rows=rows, n=5, head=d, cta=True)))
        title = f'{cap(N(d))}: 5 Speeds Counted Down'
        src += [f'Distance: {DEST[d][4]}', 'Speeds: ' + '; '.join(METH[m][4] for m in pick5)]
    elif k == 'distguess':
        d = key[1]; D = DEST[d]; opts = [D[2] * f for f in rnd.choice([(1, 3, 0.3), (1, 0.1, 10), (1, 0.5, 2)])]; rnd.shuffle(opts); r = opts.index(D[2])
        op = [f'{km(o).upper()} KM' for o in opts]
        B = [(rnd.choice([f'How far is {N(d)}? Guess first.', f'Quick question: how many kilometers is {N(d)}?']), dict(t='opts', ic=D[3], head=D[0], o=op)),
             (f'A: {km(opts[0])}. B: {km(opts[1])}. C: {km(opts[2])} kilometers.', dict(t='opts', ic=D[3], head=D[0], o=op, timer=True)),
             (f'It is {"ABC"[r]}: {km(D[2])} kilometers.', dict(t='opts', ic=D[3], head=D[0], o=op, r=r)),
             (f'By car at 100 kilometers per hour, nonstop, that is {human(hours(d, "car"))}.' if ok(d, 'car') else f'At the speed of light, that is {human(hours(d, "light"))}.',
              dict(t='big', ic=DEST[d][3], top='BY CAR, NONSTOP' if ok(d, 'car') else 'AT LIGHT SPEED', v=clock(hours(d, 'car' if ok(d, 'car') else 'light')))),
             (rnd.choice(['Were you close? Comment your guess.', 'Too high or too low? Tell me below.']), dict(t='big', ic=DEST[d][3], top='DISTANCE', v=f'{km(D[2]).upper()} KM', cta=True))]
        title = f'How Far Is {cap(N(d))}? Most People Guess Wrong'
        src += [f'Distance: {D[4]}']
    elif k == 'speedguess':
        d = key[1]; good = [m for m in ORDER[:-1] if ok(d, m) and 0.3 < hours(d, m) / 8766 < 3] or [m for m in ORDER[:-1] if ok(d, m)]
        right = good[0]; others = [m for m in ORDER if m != right and ok(d, m)]; o = [right] + rnd.sample(others, 2); rnd.shuffle(o); r = o.index(right)
        target = human(hours(d, right))
        op = [METH[m][0] for m in o]
        B = [(f'Which speed gets you to {N(d)} in about {target}?', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op)),
             (f'A: {METH[o[0]][1]}. B: {METH[o[1]][1]}. C: {METH[o[2]][1]}.', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op, timer=True)),
             (f'It is {"ABC"[r]}, {METH[right][1]}: {human(hours(d, right))}.', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op, r=r)),
             (' '.join(f'{cap(METH[m][1])}: {human(hours(d, m))}.' for m in o if m != right), dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=[f'{METH[m][0]} {clock(hours(d, m))}' for m in o], r=r)),
             ('Did you pick the right one? Comment below.', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op, r=r, cta=True))]
        title = f'Which Speed Reaches {cap(N(d))} in {target}?'
        src += [f'Distance: {DEST[d][4]}', 'Speeds: ' + '; '.join(METH[m][4] for m in o)]
    elif k == 'lifetime':
        m = key[1]; dist = METH[m][2] * LIFE * 8766
        reach = sorted([d for d in DEST if DEST[d][2] <= dist], key=lambda d: -DEST[d][2])[:4]
        miss = sorted([d for d in DEST if DEST[d][2] > dist], key=lambda d: DEST[d][2])[:1]
        rows = [dict(ic=DEST[d][3], n=DEST[d][0], v='YES', ok=True) for d in reach] + [dict(ic=DEST[d][3], n=DEST[d][0], v='NO', ok=False) for d in miss]
        B = [(f'If you traveled {by(m)} for an entire lifetime, nonstop, how far could you get?', dict(t='big', ic=METH[m][3], top='ONE LIFETIME', v=f'{LIFE} YEARS')),
             (f'The average American lives about {LIFE} years. {cap(by(m))}, that is {km(dist)} kilometers.', dict(t='big', ic=METH[m][3], top='DISTANCE', v=f'{km(dist).upper()} KM')),
             ('You could make it to:', dict(t='list', rows=rows, n=len(reach), head=None)),
             ((f'But not to {g0(miss[0]).replace("reach ", "")}. You would need {human(hours(miss[0], m))}.' if miss else 'Everything on our list!'), dict(t='list', rows=rows, n=len(rows), head=None)),
             ('What speed should I try next? Comment below.', dict(t='list', rows=rows, n=len(rows), head=None, cta=True))]
        title = f'How Far Could You Get {tby(m)} in One Lifetime?'
        src += [f'Lifetime: {LIFE} years (U.S. life expectancy, CDC 2023)', f'Speed: {METH[m][4]}']
    elif k == 'oneday':
        m = key[1]; dist = METH[m][2] * 24
        reach = sorted([d for d in DEST if DEST[d][2] <= dist], key=lambda d: -DEST[d][2])[:4]
        miss = sorted([d for d in DEST if DEST[d][2] > dist], key=lambda d: DEST[d][2])[:2]
        rows = [dict(ic=DEST[d][3], n=DEST[d][0], v='YES', ok=True) for d in reach] + [dict(ic=DEST[d][3], n=DEST[d][0], v='NO', ok=False) for d in miss]
        B = [(f'You have 24 hours, {by(m)}. Where can you get?', dict(t='big', ic=METH[m][3], top='YOU HAVE', v='24:00:00')),
             (f'In one day that is {km(dist)} kilometers.', dict(t='big', ic=METH[m][3], top='ONE DAY', v=f'{km(dist).upper()} KM')),
             ((f'You can reach: {", ".join(N(d) for d in reach)}.' if reach else 'Not even the closest place on our list.'), dict(t='list', rows=rows, n=len(reach), head=None)),
             ((f'Not in time: {", ".join(N(d) for d in miss)}.' if miss else 'Everything on our list!'), dict(t='list', rows=rows, n=len(rows), head=None)),
             ('Where would you go in 24 hours? Comment below.', dict(t='list', rows=rows, n=len(rows), head=None, cta=True))]
        title = f'Where Can You Get in 24 Hours {tby(m)}?'
        src += [f'Speed: {METH[m][4]}']
    elif k == 'timesaround':
        d = key[1]; n = DEST[d][2] / DEST['equator'][2]
        txt = (f'{n:,.1f} times around the Earth' if n >= 1 else f'{n * 100:,.1f} percent of one trip around the Earth')
        B = [(f'How many trips around the Earth equal the distance to {N(d)}?', dict(t='big', ic=DEST[d][3], top=DEST[d][0], v='? × 🌍'.replace(' 🌍', ''))),
             ('One lap around the equator is 40,075 kilometers.', dict(t='big', ic='globe', top='ONE LAP', v='40,075 KM')),
             (f'{cap(N(d))} is {km(DEST[d][2])} kilometers.', dict(t='big', ic=DEST[d][3], top=DEST[d][0], v=f'{km(DEST[d][2]).upper()} KM')),
             (f'That is {txt}.', dict(t='big', ic='globe', top='TIMES AROUND THE EARTH', v=f'{big(n).upper()}' if n >= 1000 else f'{n:,.2f}'.rstrip('0').rstrip('.'))),
             ('What distance should I measure next? Comment below.', dict(t='big', ic='globe', top='TIMES AROUND THE EARTH', v=f'{big(n).upper()}' if n >= 1000 else f'{n:,.2f}'.rstrip('0').rstrip('.'), cta=True))]
        title = f'How Many Times Around the Earth Is {cap(N(d))}?'
        src += [f'Distance: {DEST[d][4]}', 'Equator: 40,075 km (NASA)']
    elif k == 'scalemodel':
        d = key[1]; s = BALL / EARTH_D                     # metre / km
        size, dist = SIZE[d] * s, DEST[d][2] * s * 1000   # metre
        dtxt = f'{dist:,.0f} meters' if dist < 5000 else f'{dist / 1000:,.0f} kilometers'
        stxt = f'{size * 100:,.1f} centimeters' if size < 2 else f'{size:,.1f} meters'
        B = [(f'Shrink the Earth to the size of a basketball. How big is {N(d)}, and how far away?', dict(t='scale', d=d, show=0)),
             (f'The Earth is a 24 centimeter ball. {cap(N(d))} would be {stxt} across.', dict(t='scale', d=d, show=1, size=stxt)),
             (f'And it would be {dtxt} away.', dict(t='scale', d=d, show=2, size=stxt, dist=dtxt)),
             ('That is how empty space really is.' if d != 'moon' else 'About the length of a tennis court... times two and a half.' if 6 < dist < 8 else 'That is how empty space really is.', dict(t='scale', d=d, show=2, size=stxt, dist=dtxt)),
             ('Which planet should I shrink next? Comment below.', dict(t='scale', d=d, show=2, size=stxt, dist=dtxt, cta=True))]
        title = f'If Earth Were a Basketball, {cap(N(d))} Would Be Here'
        src += [f'Diameters: Earth 12,742 km, {DEST[d][0].title()} {SIZE[d]:,} km (NASA)', f'Distance: {DEST[d][4]}', 'Basketball: about 24 cm']
    elif k == 'truefalse':
        _, d, m = key; h = hours(d, m); lim = rnd.choice([(24, 'a day'), (8766, 'a year'), (LIFE * 8766, 'a human lifetime')])
        truth = h < lim[0]
        claim = f'You could {goal(d)} {by(m)} in less than {lim[1]}.'
        B = [(f'True or false? {claim}', dict(t='tf', q=claim)),
             ('Think about it.', dict(t='tf', q=claim, timer=True)),
             (f'{"True" if truth else "False"}! It takes {human(h)}.', dict(t='tf', q=claim, r=0 if truth else 1, v=clock(h))),
             (compare(h, rnd), dict(t='tf', q=claim, r=0 if truth else 1, v=clock(h))),
             ('Did you get it right? Comment true or false.', dict(t='tf', q=claim, r=0 if truth else 1, v=clock(h), cta=True))]
        title = f'True or False: {cap(N(d))} {tby(m)} in Under {lim[1].replace("a human lifetime", "a Lifetime")}?'
        src += [f'Distance: {DEST[d][4]}', f'Speed: {METH[m][4]}']
    elif k in ('agearrive', 'yeararrive'):
        _, d, m = key; h = hours(d, m); y = h / 8766
        if k == 'agearrive':
            age = rnd.choice([18, 20, 25, 30]); arr = age + y
            B = [(f'You leave today, age {age}, to {goal(d)} {by(m)}. How old are you when you arrive?', dict(t='big', ic=METH[m][3], top='DEPART AGE', v=f'{age}')),
                 (f'The trip takes {human(h)}, nonstop.', dict(t='big', ic=DEST[d][3], top=DEST[d][0], v=clock(h))),
                 (f'You arrive at age {arr:,.0f}.' + (' Happy birthday, many times over.' if y > 1 else ''), dict(t='big', ic=DEST[d][3], top='ARRIVAL AGE', v=f'{arr:,.0f}', anim=True)),
                 (compare(h, rnd), dict(t='big', ic=DEST[d][3], top='ARRIVAL AGE', v=f'{arr:,.0f}')),
                 ('What age would you arrive? Comment below.', dict(t='big', ic=DEST[d][3], top='ARRIVAL AGE', v=f'{arr:,.0f}', cta=True))]
            title = f'Leave at {age} {tby(m)}: How Old Are You at {cap(N(d))}?'
        else:
            now = datetime.date.today(); arr = now + datetime.timedelta(hours=h) if y < 7000 else None
            yr = arr.year if arr else int(now.year + y)
            B = [(f'Leave today {by(m)} to {goal(d)}. What year do you arrive?', dict(t='calendar', y=now.year, m=now.strftime('%b').upper(), lab='TODAY')),
                 (f'The trip is {human(h)} long, nonstop.', dict(t='big', ic=METH[m][3], top=DEST[d][0], v=clock(h))),
                 (f'You arrive in {arr.strftime("%B") + " " if arr else ""}{yr:,}.'.replace(',', '') if yr < 10000 else f'You arrive in the year {big(yr)}.', dict(t='calendar', y=yr, m=arr.strftime('%b').upper() if arr else '', lab='ARRIVAL', anim=True)),
                 (compare(h, rnd), dict(t='calendar', y=yr, m=arr.strftime('%b').upper() if arr else '', lab='ARRIVAL')),
                 ('Would you go? Tell me below.', dict(t='calendar', y=yr, m=arr.strftime('%b').upper() if arr else '', lab='ARRIVAL', cta=True))]
            title = f'Leave Today {tby(m)}: You Reach {cap(N(d))} in {yr if yr < 10000 else big(yr)}'
        src += [f'Distance: {DEST[d][4]}', f'Speed: {METH[m][4]}']
    elif k == 'measured':
        _, d, m, unit = key; h = hours(d, m)
        per = {'heartbeats': (70 * 60, '70 beats a minute, a typical resting heart rate'), 'breaths': (15 * 60, '15 breaths a minute at rest'),
               'nights': (1 / 24, 'one night per day'), 'songs': (60 / 3.5, 'a 3.5 minute song'), 'movies': (0.5, 'a 2 hour movie')}[unit]
        n = h * per[0]
        B = [(f'Let us measure a trip in {unit}. {cap(goal(d))} {by(m)}.', dict(t='route', d=d, m=m, p=0.0)),
             (f'The trip takes {human(h)}.', dict(t='route', d=d, m=m, p=1.0, clock=True, anim=True)),
             (f'At {per[1]}, that is about {big(n) if n >= 1e6 else f"{n:,.0f}"} {unit}.', dict(t='big', ic=METH[m][3], top=unit.upper(), v=big(n).upper() if n >= 1e6 else f'{n:,.0f}', anim=True)),
             ('What else should I count? Comment below.', dict(t='big', ic=METH[m][3], top=unit.upper(), v=big(n).upper() if n >= 1e6 else f'{n:,.0f}', cta=True))]
        title = f'{cap(N(d))} {tby(m)}, Measured in {unit.title()}'
        src += [f'Distance: {DEST[d][4]}', f'Speed: {METH[m][4]}', f'Rate: {per[1]}']
    elif k == 'oddone':
        d = key[1]; ms = key[2:]; hs = [hours(d, m) for m in ms]; r = [i for i, x in enumerate(hs) if x > 8766][0]
        op = [METH[m][0] for m in ms]
        B = [(f'{cap(goal(d))}. Only one of these takes more than a year. Which one?', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op)),
             ('A, B, C or D?', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op, timer=True)),
             (f'It is {"ABCD"[r]}, {METH[ms[r]][1]}: {human(hs[r])}.', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op, r=r)),
             (' '.join(f'{cap(METH[m][1])}: {human(x)}.' for i, (m, x) in enumerate(zip(ms, hs)) if i != r), dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=[f'{METH[m][0]} {clock(x)}' for m, x in zip(ms, hs)], r=r)),
             ('Did you spot it? Comment below.', dict(t='opts', ic=DEST[d][3], head=DEST[d][0], o=op, r=r, cta=True))]
        title = f'{cap(N(d))}: Only One of These Takes Over a Year'
        src += [f'Distance: {DEST[d][4]}', 'Speeds: ' + '; '.join(METH[m][4] for m in ms)]
    elif k == 'rank3':
        m, ds = key[1], key[2:]; order = sorted(ds, key=lambda d: hours(d, m))
        rows = lambda n: [dict(ic=DEST[d][3], n=DEST[d][0], v=clock(hours(d, m)), r=i + 1) for i, d in enumerate(order[:n])]
        B = [(f'Rank these three trips {by(m)}, from fastest to slowest: ' + ', '.join(g0(d).replace('reach ', '') for d in ds) + '.', dict(t='list', rows=[dict(ic=DEST[d][3], n=DEST[d][0], v='?') for d in ds], n=3, head=None)),
             ('Lock in your order.', dict(t='list', rows=[dict(ic=DEST[d][3], n=DEST[d][0], v='?') for d in ds], n=3, head=None, timer=True))] + \
            [(f'Number {i + 1}: {N(d)}, {human(hours(d, m))}.', dict(t='list', rows=rows(i + 1), n=i + 1, head=None)) for i, d in enumerate(order)] + \
            [('How did you rank them? Comment below.', dict(t='list', rows=rows(3), n=3, head=None, cta=True))]
        title = f'Rank These 3 Trips {tby(m)}'
        src += ['Distances: ' + '; '.join(f'{DEST[d][0].title()}: {DEST[d][4]}' for d in ds), f'Speed: {METH[m][4]}']
    elif k == 'inatime':
        _, m, per = key; hh = {'hour': 1, 'day': 24, 'week': 168, 'year': 8766}[per]; dist = METH[m][2] * hh
        near = min(DEST, key=lambda d: abs(math.log(DEST[d][2] / dist)))
        B = [(f'How far do you get in one {per} {by(m)}?', dict(t='big', ic=METH[m][3], top=f'ONE {per.upper()}', v='? KM')),
             (f'{km(dist)} kilometers, nonstop.', dict(t='big', ic=METH[m][3], top=f'ONE {per.upper()}', v=f'{km(dist).upper()} KM', anim=True)),
             (f'For comparison, {N(near)} is {km(DEST[near][2])} kilometers.', dict(t='big', ic=DEST[near][3], top=DEST[near][0], v=f'{km(DEST[near][2]).upper()} KM')),
             (f'So you would need {human(hours(near, m))} to {g0(near)}.', dict(t='route', d=near, m=m, p=1.0, clock=True)),
             ('What speed should I check next? Comment below.', dict(t='route', d=near, m=m, p=1.0, clock=True, cta=True))]
        title = f'How Far Can You Go in One {per.title()} {tby(m)}?'
        src += [f'Speed: {METH[m][4]}', f'{DEST[near][0].title()}: {DEST[near][4]}']
    else:                                           # halfway
        _, d, m = key; h = hours(d, m)
        B = [(f'Halfway check. You are traveling {by(m)} to {N(d)}. When do you reach the halfway point?', dict(t='route', d=d, m=m, p=0.0)),
             (f'Halfway is {km(DEST[d][2] / 2)} kilometers.', dict(t='route', d=d, m=m, p=0.5, clock=True, half=True, anim=True)),
             (f'You get there after {human(h / 2)}.', dict(t='route', d=d, m=m, p=0.5, clock=True, half=True)),
             (f'And the full trip takes {human(h)}. ' + compare(h, rnd), dict(t='route', d=d, m=m, p=1.0, clock=True, anim=True)),
             ('Would you keep going after halfway? Comment below.', dict(t='route', d=d, m=m, p=1.0, clock=True, cta=True))]
        title = f'Halfway to {cap(N(d))} {tby(m)}: How Long?'
        src += [f'Distance: {DEST[d][4]}', f'Speed: {METH[m][4]}']
    title = H.tcase(title)[:95]
    desc = (title + '\n\n' + '\n'.join(s + '.' for s in src) + '\nTime = distance ÷ speed, nonstop, in a straight line where there is no road. A thought experiment, not a travel plan.'
            + '\n\nEmoji art: Microsoft Fluent Emoji (MIT).\n\n#howlong #science #space #shorts')
    return dict(key=key, kurgu=k, beats=[b for b, _ in B], scenes=[s for _, s in B], title=title, desc=desc,
                tags=['how long would it take', 'science', 'space', 'quiz', 'distance', 'shorts'])


# ---------------------------------------------------------------- sahneler
def pill(d, box, txt, on=False, good=None, f=None):
    fill = (BLUE if on else (255, 255, 255)) if good is None else (GREEN if good else (255, 255, 255))
    d.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill, outline=INK, width=4)
    d.text(((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), txt, font=f or font(MONO, 46), fill=(255, 255, 255) if (on or good) else INK, anchor='mm')


def frame(base, v, bi, t, dur):
    img = base.copy(); d = ImageDraw.Draw(img); sc = v['scenes'][bi]; T = sc['t']; a = ease(t / 0.7) if sc.get('anim') else 1.0
    d.text((W // 2, 150), 'HOW LONG WOULD IT TAKE?', font=font(SANS, 62), fill=INK, anchor='mm')
    d.rectangle([W // 2 - 220, 196, W // 2 + 220, 204], fill=BLUE)
    if T == 'cards':
        for i, c in enumerate(sc['c']):
            x = 70 + i * 480; win = sc.get('win') == i
            d.rounded_rectangle([x, 300, x + 460, 1150], radius=36, fill=(255, 255, 255), outline=BLUE if win else INK, width=10 if win else 4)
            d.text((x + 230, 350), 'AB'[i], font=font(SANS, 70), fill=BLUE, anchor='mm')
            ic = icon(c['ic'], 170); img.paste(ic, (x + 145, 420), ic)
            ic2 = icon(c['ic2'], 130); img.paste(ic2, (x + 165, 620), ic2)
            for j, l in enumerate(wrap(d, c['t'], font(SANS, 38), 420)[:2]):
                d.text((x + 230, 790 + j * 46), l, font=font(SANS, 38), fill=INK, anchor='mm')
            d.text((x + 230, 900), c['s'], font=font(SANS, 34, 500), fill=SUB, anchor='mm')
            d.text((x + 230, 1040), c['v'], font=font(MONO, 64 if len(c['v']) < 12 else 46), fill=RED if win else BLUE, anchor='mm')
        if sc.get('timer'): d.text((W // 2, 1260), f'{max(0, 3 - int(t * 1.2))}', font=font(MONO, 120), fill=RED, anchor='mm')
    elif T == 'opts':
        ic = icon(sc['ic'], 220); img.paste(ic, (W // 2 - 110, 260), ic)
        d.text((W // 2, 520), sc['head'], font=font(SANS, 54), fill=INK, anchor='mm')
        n = len(sc['o'])
        for i, o in enumerate(sc['o']):
            y = 610 + i * (150 if n <= 3 else 120)
            pill(d, [120, y, 960, y + (118 if n <= 3 else 100)], f'{"ABCD"[i]}   {o}', on=(sc.get('r') == i), f=font(MONO, 44 if len(o) < 22 else 34))
        if sc.get('timer'): d.text((W // 2, 1290), f'{max(0, 3 - int(t * 1.2))}', font=font(MONO, 110), fill=RED, anchor='mm')
    elif T == 'big':
        ic = icon(sc['ic'], 260); img.paste(ic, (W // 2 - 130, 300), ic)
        d.text((W // 2, 650), sc['top'], font=font(SANS, 56), fill=SUB, anchor='mm')
        val = sc['v']; fs = 170 if len(val) <= 6 else 120 if len(val) <= 10 else 84
        d.text((W // 2, 840), val, font=font(MONO, int(fs * (0.6 + 0.4 * a))), fill=BLUE, anchor='mm')
    elif T == 'list':
        if sc.get('head'):
            hi = icon(DEST[sc['head']][3], 150); img.paste(hi, (W // 2 - 75, 250), hi)
            d.text((W // 2, 430), DEST[sc['head']][0], font=font(SANS, 50), fill=INK, anchor='mm')
        y0 = 500 if sc.get('head') else 320
        for i, r in enumerate(sc['rows'][:sc['n']]):
            y = y0 + i * 190; ic = icon(r['ic'], 120); img.paste(ic, (110, y), ic)
            if 'r' in r: d.text((80, y + 60), f"{r['r']}", font=font(SANS, 54), fill=GOLD, anchor='rm')
            d.text((260, y + 30), r['n'], font=font(SANS, 40), fill=INK, anchor='lm')
            col = GREEN if r.get('ok') is True else RED if r.get('ok') is False else BLUE
            d.text((260, y + 95), r['v'], font=font(MONO, 66 if len(r['v']) < 16 else 48), fill=col, anchor='lm')
        if sc.get('timer'): d.text((W // 2, 1300), f'{max(0, 3 - int(t * 1.2))}', font=font(MONO, 110), fill=RED, anchor='mm')
    elif T == 'tf':
        for j, l in enumerate(wrap(d, sc['q'], font(SANS, 58), 900)[:4]):
            d.text((W // 2, 420 + j * 72), l, font=font(SANS, 58), fill=INK, anchor='mm')
        pill(d, [110, 760, 520, 900], 'TRUE', good=(sc.get('r') == 0) if 'r' in sc else None, f=font(SANS, 60))
        pill(d, [560, 760, 970, 900], 'FALSE', good=(sc.get('r') == 1) if 'r' in sc else None, f=font(SANS, 60))
        if 'v' in sc: d.text((W // 2, 1080), sc['v'], font=font(MONO, 110 if len(sc['v']) < 12 else 80), fill=BLUE, anchor='mm')
        if sc.get('timer'): d.text((W // 2, 1080), f'{max(0, 3 - int(t * 1.2))}', font=font(MONO, 110), fill=RED, anchor='mm')
    elif T == 'calendar':
        d.rounded_rectangle([240, 320, 840, 1060], radius=40, fill=(255, 255, 255), outline=INK, width=6)
        d.rounded_rectangle([240, 320, 840, 470], radius=40, fill=RED); d.rectangle([240, 420, 840, 470], fill=RED)
        d.text((W // 2, 395), sc['lab'], font=font(SANS, 56), fill=(255, 255, 255), anchor='mm')
        d.text((W // 2, 600), sc['m'], font=font(SANS, 80), fill=SUB, anchor='mm')
        yr = sc['y']; ys = f'{yr}' if yr < 1e5 else big(yr).upper()
        if sc.get('anim'): ys = f'{int(datetime.date.today().year + (yr - datetime.date.today().year) * a)}' if yr < 1e5 else ys
        d.text((W // 2, 830), ys, font=font(MONO, 210 if len(ys) <= 4 else 150 if len(ys) <= 6 else 90), fill=INK, anchor='mm')
    elif T == 'scale':
        dd = sc['d']; earth = icon('globe', 200); img.paste(earth, (120, 480), earth)
        d.text((220, 720), 'EARTH = 24 CM BALL', font=font(SANS, 30), fill=SUB, anchor='mm')
        if sc['show'] >= 1:
            ps = int(max(40, min(320, 200 * SIZE[dd] / EARTH_D)))
            ob = icon(DEST[dd][3], ps); img.paste(ob, (840 - ps // 2, 580 - ps // 2), ob)
            d.text((840, 600 + max(ps // 2, 100)), sc.get('size', ''), font=font(MONO, 40), fill=BLUE, anchor='mm')
        if sc['show'] >= 2:
            d.line([(220, 900), (840, 900)], fill=BLUE, width=8)
            d.text((W // 2, 980), sc.get('dist', '').upper(), font=font(MONO, 72), fill=RED, anchor='mm')
    elif T == 'route':
        p = sc['p'] * (a if sc.get('anim') else 1.0) if sc['p'] > 0 else 0.0
        H.route(img, d, 620, p, METH[sc['m']][3], DEST[sc['d']][3], DEST[sc['d']][0])
        if sc.get('half'): d.line([(540, 560), (540, 680)], fill=GOLD, width=6)
        if sc.get('clock'):
            ct = clock(hours(sc['d'], sc['m']), p); d.text((W // 2, 900), ct, font=font(MONO, 140 if len(ct) <= 10 else 96 if len(ct) <= 14 else 72), fill=BLUE, anchor='mm')
    if sc.get('cta'):
        d.rounded_rectangle([170, 1560, 910, 1680], radius=60, fill=BLUE)
        d.text((W // 2, 1620), 'COMMENT YOUR ANSWER!', font=font(SANS, 50), fill=(255, 255, 255), anchor='mm')
    else:
        f = font(SANS, 42, 500); ls = wrap(d, v['beats'][bi], f, 920)
        groups = [ls[i:i + 3] for i in range(0, len(ls), 3)] or [[]]
        for j, l in enumerate(groups[min(len(groups) - 1, int(t / max(dur, 0.1) * len(groups)))]):
            d.text((W // 2, 1590 + j * 56), l, font=f, fill=INK, anchor='mm')
    return img


def render(v, mp4):
    tmp = mp4.with_suffix(''); tmp.mkdir(parents=True, exist_ok=True)
    durs = H.voice(v['beats'], tmp, min_d=lambda i: 3.0 if v['scenes'][i].get('timer') else None)
    base = H.background()
    H.encode(lambda i, t, dd: frame(base, v, i, t, dd), durs, tmp / 'voice.wav', mp4, H.W, H.H, lambda i, dd: 99)
    return mp4
