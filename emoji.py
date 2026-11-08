"""Emoji bulmaca Shorts'ları (2026-11-05, How Long Would It Take? kanalının yeni konsepti).

Trend taraması (tools/trend_scan.py, son 30 gün): "find the odd emoji" medyan 246K (23 kanal 100K+),
"spot the difference" 246K (36 kanal), "guess the emoji" 1.1M → tek kanalın tekelinde değil, kodla üretilebilir.

Kurgular:
  odd   — FIND THE ODD EMOJI: 3 seviye (kolay/orta/zor), her seviyede aynı emojilerin arasında 1 farklı; sayaç, sonra cevap
  spot  — SPOT THE DIFFERENCE: üst ve alt ızgara, 3 fark; sayaç, sonra daireler
Ses: tik-tak, ding, hafif müzik (kodla üretilir, seslendirme yok). Emoji: Google Noto Color Emoji (SIL OFL, fonts/emoji).

    python emoji.py --dry-run [--kurgu odd|spot]     # sadece render
    python emoji.py --auto                           # günlük sayı dolana kadar 1 Short üret + yükle (emoji.yml)
"""
import csv
import math
import os
import random
import re
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / 'out' / 'emoji'
LOG = HERE / 'emoji_published.csv'
EMOJI_FONT = HERE / 'fonts' / 'emoji' / 'NotoColorEmoji.ttf'
TEXT_FONT = HERE / 'fonts' / 'emoji' / 'LuckiestGuy-Regular.ttf'   # Apache 2.0 (Google Fonts)
DRY = '--dry-run' in sys.argv
W, H, FPS, SR = 1080, 1920, 30, 44100

BG1, BG2 = (255, 214, 64), (255, 160, 40)          # sıcak sarı (kanalın rengi; diğer kanallara benzemesin)
INK, WHITE, RED, GREEN = (34, 24, 60), (255, 255, 255), (235, 50, 70), (40, 190, 110)

# ---------------------------------------------------------------- içerik
# (A, B): A ızgarayı doldurur, B tek farklı olan. Sadece varyasyon seçicisiz (FE0F'siz) emojiler → her yerde aynı çizilir.
ODD = {
    'easy': [('🍎', '🍅'), ('🐶', '🐱'), ('⚽', '🏀'), ('🌞', '🌝'), ('🍊', '🍑'), ('🐸', '🐢'), ('🚗', '🚕'), ('🍩', '🥯'),
             ('🐝', '🐞'), ('🌲', '🌳'), ('🍇', '🫐'), ('🐧', '🐦'), ('🍓', '🍒'), ('🎃', '🍊'), ('💙', '💜'), ('🍔', '🍪'),
             ('🐼', '🐨'), ('🦊', '🐯'), ('🍋', '🍌'), ('🚀', '✈'), ('🌵', '🌴'), ('🐙', '🦑'), ('🎈', '🎀'), ('🧁', '🍰')],
    'medium': [('😀', '😃'), ('😁', '😆'), ('🙂', '🙃'), ('😐', '😑'), ('😮', '😯'), ('😢', '😥'), ('🐵', '🙈'), ('🌕', '🌖'),
               ('🍏', '🍐'), ('🐻', '🐨'), ('🐮', '🐷'), ('📕', '📙'), ('🔴', '🟠'), ('🟦', '🟪'), ('🐟', '🐠'), ('🦁', '🐯'),
               ('😺', '😸'), ('🐭', '🐹'), ('🥝', '🥑'), ('🌸', '🌺'), ('🍑', '🥭'), ('😴', '😪'), ('🤠', '🥳'), ('🍫', '🍪')],
    'hard': [('😀', '😄'), ('😃', '😄'), ('😗', '😙'), ('😙', '😚'), ('😶', '😐'), ('😔', '😞'), ('😟', '🙁'), ('😤', '😠'),
             ('🕐', '🕑'), ('🕒', '🕓'), ('🌑', '🌚'), ('✋', '🤚'), ('🎵', '🎶'), ('⭐', '🌟'), ('💛', '🧡'), ('😊', '😌'),
             ('😕', '🫤'), ('😲', '😮'), ('🥲', '😢'), ('😸', '😹'), ('🐈', '🐆'), ('🔵', '🫐'), ('🟡', '🌕'), ('😓', '😥')],
}
LEVELS = [('EASY', 'easy', (6, 8)), ('MEDIUM', 'medium', (7, 10)), ('HARD', 'hard', (8, 11))]
SPOT_POOL = list('🍎🍌🍇🍓🍒🍑🍍🥝🥕🌽🍄🌵🌻🌈⭐🌙⚽🏀🎈🎁🎃🐶🐱🐸🐵🐔🐧🐙🦋🐞🍩🍪🍰🧁🍿🚗🚀⛵🎸🎲🔑💎👑🎩🧸')

# 2026-11-07 'guess' (trend: "guess the emoji" medyan 1.1M, 19 kanal): emoji ipuçlarından kelime/ülke. FE0F'siz, tek satır.
GUESS = {
    'WORD': [('🌞🌻', 'SUNFLOWER'), ('🐱🐟', 'CATFISH'), ('⭐🐟', 'STARFISH'), ('🐶🏠', 'DOGHOUSE'), ('🔥🚒', 'FIRE TRUCK'),
             ('🍯🌙', 'HONEYMOON'), ('🧈🪰', 'BUTTERFLY'), ('🌞👓', 'SUNGLASSES'), ('🍳🎂', 'PANCAKE'), ('💥🌽', 'POPCORN'),
             ('☕🎂', 'CUPCAKE'), ('🔥🐶', 'HOT DOG'), ('📚🐛', 'BOOKWORM'), ('🌲🍎', 'PINEAPPLE'), ('💧🍈', 'WATERMELON'),
             ('🚗🐶', 'CARPET'), ('✋👜', 'HANDBAG'), ('🌊🐴', 'SEAHORSE'), ('🌙🚶', 'MOONWALK'), ('☔🧥', 'RAINCOAT'),
             ('🐉🪰', 'DRAGONFLY'), ('🐴👟', 'HORSESHOE'), ('🔵🍓', 'BLUEBERRY'), ('🥇🐟', 'GOLDFISH'), ('🌍💥', 'EARTHQUAKE'),
             ('🦶🏈', 'FOOTBALL'), ('🌙💡', 'MOONLIGHT'), ('🥜🧈', 'PEANUT BUTTER'), ('🍯🐝', 'HONEYBEE'), ('🧀🍔', 'CHEESEBURGER')],
    'COUNTRY': [('🍕🍝', 'ITALY'), ('🌮🌵', 'MEXICO'), ('🥐🗼', 'FRANCE'), ('🍣🗻', 'JAPAN'), ('🦘🐨', 'AUSTRALIA'),
                ('🍁🦫', 'CANADA'), ('🐼🥟', 'CHINA'), ('🍔🗽', 'USA'), ('🌷🧀🚲', 'NETHERLANDS'), ('🧇🍫', 'BELGIUM'),
                ('🥨🍺', 'GERMANY'), ('🐫🔺', 'EGYPT'), ('⚽☕🦜', 'BRAZIL'), ('🐘🍛', 'INDIA'), ('🦁🦒', 'KENYA'),
                ('🫖💂', 'UK'), ('🥘💃', 'SPAIN'), ('🍫⌚🧀', 'SWITZERLAND'), ('🥝🐑', 'NEW ZEALAND'), ('🍜🛵', 'VIETNAM')],
}
GUESS_N, GUESS_T, GUESS_R = 5, 4.0, 1.6

TITLES = {
    'odd': ['Find the Odd Emoji: {a} vs {b} 👀 Can You Find All 3?', 'Find the Different Emoji 🔍 {a} {b} (Easy to Hard)',
            'Odd One Out: {a} or {b}? 😳 3 Levels', 'Can You Spot the Odd Emoji? {a} {b} 🧐', 'Emoji Challenge: Find the {b} 👀'],
    'guess': ['Guess the {cat} From Emojis: {a} 🤔 5 Puzzles', 'Emoji Quiz: Can You Guess All 5? {a}', 'Guess the Emoji {cat}: {a} = ? 🧠',
              'Only Emojis: Guess the {cat} 🤔 {a}'],
    'spot': ['Spot the Difference: 3 Emoji Changes 🔍 {a}', 'Find 3 Differences in 10 Seconds 👀 {a}{b}',
             'Emoji Spot the Difference 🧐 {a} Edition', 'Can You Find All 3 Differences? {a}{b} 🔍'],
}


@lru_cache(None)
def emoji_img(ch, size):
    """Emojiyi Noto'dan (109 px bitmap) çizip size'a ölçekler; RGBA."""
    f = ImageFont.truetype(str(EMOJI_FONT), 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor='mm')
    bb = im.getbbox()
    if not bb:
        raise ValueError(f'emoji çizilemedi: {ch!r}')
    im = im.crop(bb)
    s = size / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


@lru_cache(None)
def font(sz):
    return ImageFont.truetype(str(TEXT_FONT), sz)


def text(d, xy, s, sz, fill=WHITE, stroke=INK, sw=None, anchor='mm'):
    d.text(xy, s, font=font(sz), fill=fill, anchor=anchor, stroke_width=sw if sw is not None else max(3, sz // 12),
           stroke_fill=stroke)


# ---------------------------------------------------------------- plan
def make_plan(kurgu, rnd):
    if kurgu == 'odd':
        levels = []
        for name, diff, (cols, rows) in LEVELS:
            a, b = rnd.choice(ODD[diff])
            if rnd.random() < 0.5: a, b = b, a
            levels.append(dict(name=name, a=a, b=b, cols=cols, rows=rows, pos=rnd.randrange(cols * rows)))
        return dict(kurgu='odd', levels=levels, seed=rnd.randrange(10 ** 6))
    if kurgu == 'guess':
        cat = rnd.choice(list(GUESS))
        return dict(kurgu='guess', cat=cat, items=rnd.sample(GUESS[cat], GUESS_N), seed=rnd.randrange(10 ** 6))
    cols, rows = 5, 5
    grid = [rnd.choice(SPOT_POOL) for _ in range(cols * rows)]
    diffs = rnd.sample(range(cols * rows), 3)
    alt = list(grid)
    for i in diffs:
        alt[i] = rnd.choice([e for e in SPOT_POOL if e != grid[i]])
    return dict(kurgu='spot', cols=cols, rows=rows, grid=grid, alt=alt, diffs=diffs, seed=rnd.randrange(10 ** 6))


def plan_key(p):
    if p['kurgu'] == 'odd':
        return 'em:odd:' + '|'.join(f"{L['a']}{L['b']}" for L in p['levels'])
    if p['kurgu'] == 'guess':
        return 'em:guess:' + p['cat'] + ':' + '|'.join(e for e, _ in p['items'])
    return 'em:spot:' + ''.join(p['grid']) + ':' + ','.join(map(str, sorted(p['diffs'])))


# ---------------------------------------------------------------- zaman çizelgesi
INTRO, SEARCH, REVEAL, OUTRO = 1.4, 5.0, 1.6, 2.6


def timeline(p):
    if p['kurgu'] == 'odd':
        segs, t = [], INTRO
        for i in range(len(p['levels'])):
            segs.append((t, t + SEARCH, t + SEARCH + REVEAL, i)); t += SEARCH + REVEAL
        return segs, t + OUTRO
    if p['kurgu'] == 'guess':
        segs, t = [], INTRO
        for i in range(len(p['items'])):
            segs.append((t, t + GUESS_T, t + GUESS_T + GUESS_R, i)); t += GUESS_T + GUESS_R
        return segs, t + OUTRO
    t0 = INTRO
    return [(t0, t0 + 9.0, t0 + 9.0 + 2.2, 0)], t0 + 9.0 + 2.2 + OUTRO


# ---------------------------------------------------------------- çizim
@lru_cache(4)
def background():
    a = np.linspace(0, 1, H)[:, None, None]
    g = (np.array(BG1) * (1 - a) + np.array(BG2) * a) * np.ones((1, W, 1))
    im = Image.fromarray(g.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    for k in range(-H, W, 90):   # çapraz şeritler
        d.line([(k, 0), (k + H, H)], fill=(255, 255, 255, 18), width=26)
    return im


def ease(u): return 1 - (1 - max(0.0, min(1.0, u))) ** 3


def grid_rect(cols, rows, top, bottom):
    cell = min((W - 80) / cols, (bottom - top) / rows)
    gw, gh = cell * cols, cell * rows
    return (W - gw) / 2, top + (bottom - top - gh) / 2, cell


def draw_grid(img, items, cols, rows, top, bottom, scale=1.0, card=True):
    x0, y0, cell = grid_rect(cols, rows, top, bottom)
    d = ImageDraw.Draw(img)
    if card:
        d.rounded_rectangle([x0 - 24, y0 - 24, x0 + cell * cols + 24, y0 + cell * rows + 24], radius=36, fill=(255, 255, 255, 235))
    size = int(cell * 0.82 * scale)
    for i, ch in enumerate(items):
        if size < 4: break
        e = emoji_img(ch, size)
        cx, cy = x0 + (i % cols + 0.5) * cell, y0 + (i // cols + 0.5) * cell
        img.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
    return x0, y0, cell


def ring(img, cx, cy, r, u, col=RED):
    d = ImageDraw.Draw(img)
    r2 = r * (1.6 - 0.6 * ease(u))
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=col + (255,), width=12)


def timer_bar(img, frac, label):
    d = ImageDraw.Draw(img)
    x0, x1, y = 90, W - 90, 1760
    d.rounded_rectangle([x0, y, x1, y + 46], radius=23, fill=(255, 255, 255, 200))
    col = GREEN if frac > 0.5 else ((250, 170, 30) if frac > 0.25 else RED)
    d.rounded_rectangle([x0, y, x0 + max(46, (x1 - x0) * frac), y + 46], radius=23, fill=col)
    text(d, (W / 2, y + 100), label, 64)


def frame(p, T):
    img = background().copy()
    d = ImageDraw.Draw(img)
    segs, total = timeline(p)
    head = {'odd': 'FIND THE ODD EMOJI', 'spot': 'SPOT 3 DIFFERENCES', 'guess': f"GUESS THE {p.get('cat', '')}"}[p['kurgu']]
    d.rectangle([0, 0, W, 300], fill=INK + (235,))
    text(d, (W / 2, 120), head, 86, fill=(255, 220, 60))
    if T < INTRO:   # kanca
        u = ease(T / 0.5)
        n = len(p['items']) if p['kurgu'] == 'guess' else 3
        text(d, (W / 2, 820), {'odd': 'CAN YOU FIND', 'spot': 'CAN YOU SPOT', 'guess': 'CAN YOU GUESS'}[p['kurgu']], int(110 * u) + 1)
        text(d, (W / 2, 960), f'ALL {n}?', int(150 * u) + 1, fill=(255, 235, 80))
        return img
    if T >= segs[-1][2]:   # kapanış: yorum çağrısı
        u = ease((T - segs[-1][2]) / 0.5)
        text(d, (W / 2, 760), 'HOW MANY DID', int(100 * u) + 1)
        text(d, (W / 2, 880), 'YOU GET?', int(120 * u) + 1, fill=(255, 235, 80))
        text(d, (W / 2, 1060), 'COMMENT YOUR SCORE' if p['kurgu'] == 'guess' else 'COMMENT 0, 1, 2 OR 3', int(70 * u) + 1)
        if p.get('n'): text(d, (W / 2, 1420), f"NEXT: CHALLENGE #{p['n'] + 1}", int(60 * u) + 1, fill=(255, 235, 80))
        e = emoji_img('👇', 150); img.alpha_composite(e, (int(W / 2 - 75), 1150))
        return img
    s0, s1, s2, i = next(s for s in segs if s[0] <= T < s[2])
    if p['kurgu'] == 'guess':
        em, ans = p['items'][i]
        text(d, (W / 2, 230), f"PUZZLE {i + 1} OF {len(p['items'])}", 60)
        d.rounded_rectangle([90, 560, W - 90, 1260], radius=48, fill=(255, 255, 255, 235))
        e = emoji_img(em, 330 if len(em) <= 2 else 260)
        pop = ease((T - s0) / 0.35)
        if pop > 0.02:
            e2 = e.resize((max(1, int(e.width * pop)), max(1, int(e.height * pop))))
            img.alpha_composite(e2, (int(W / 2 - e2.width / 2), int(910 - e2.height / 2)))
        if T < s1:
            left = s1 - T; timer_bar(img, left / GUESS_T, f'{math.ceil(left)}')
        else:
            u = ease((T - s1) / 0.3)
            text(d, (W / 2, 1420), ans, int((96 if len(ans) < 12 else 76) * u) + 1, fill=(255, 235, 80))
        return img
    if p['kurgu'] == 'odd':
        L = p['levels'][i]
        items = [L['a']] * (L['cols'] * L['rows']); items[L['pos']] = L['b']
        pop = ease((T - s0) / 0.35)
        text(d, (W / 2, 230), f"LEVEL {i + 1}: {L['name']}", 60, fill=WHITE)
        x0, y0, cell = draw_grid(img, items, L['cols'], L['rows'], 360, 1560, scale=pop)
        if T < s1:
            left = s1 - T
            timer_bar(img, left / SEARCH, f'{math.ceil(left)}')
        else:
            cx, cy = x0 + (L['pos'] % L['cols'] + 0.5) * cell, y0 + (L['pos'] // L['cols'] + 0.5) * cell
            ring(img, cx, cy, cell * 0.6, (T - s1) / 0.35)
            text(d, (W / 2, 1720), 'HERE IT IS!', 80, fill=(255, 235, 80))
        return img
    # spot
    text(d, (W / 2, 230), 'TOP vs BOTTOM', 60)
    pop = ease((T - s0) / 0.35)
    xa, ya, cell = draw_grid(img, p['grid'], p['cols'], p['rows'], 340, 930, scale=pop)
    xb, yb, _ = draw_grid(img, p['alt'], p['cols'], p['rows'], 1000, 1590, scale=pop)
    if T < s1:
        left = s1 - T
        timer_bar(img, left / (s1 - s0), f'{math.ceil(left)}')
    else:
        for k, j in enumerate(sorted(p['diffs'])):
            u = (T - s1 - 0.35 * k) / 0.35
            if u > 0:
                ring(img, xb + (j % p['cols'] + 0.5) * cell, yb + (j // p['cols'] + 0.5) * cell, cell * 0.58, u)
        text(d, (W / 2, 1760), '3 DIFFERENCES!', 80, fill=(255, 235, 80))
    return img


# ---------------------------------------------------------------- ses (kodla)
def tone(f, dur, amp=0.3, decay=6.0):
    t = np.arange(int(SR * dur)) / SR
    return amp * np.sin(2 * np.pi * f * t) * np.exp(-decay * t)


def build_audio(p, path):
    segs, total = timeline(p)
    n = int(SR * total); mix = np.zeros(n)
    rnd = np.random.default_rng(p['seed'])
    def place(x, t0):
        i0 = int(t0 * SR); mix[i0:i0 + len(x)] += x[:max(0, n - i0)]
    # hafif müzik: pentatonik arpej
    notes = [523.25, 587.33, 659.25, 783.99, 880.0]
    beat = 0.25
    for k in range(int(total / beat)):
        place(tone(notes[rnd.integers(len(notes))] / 2, 0.24, 0.05, 9), k * beat)
    for s0, s1, s2, _ in segs:
        place(tone(220, 0.25, 0.25, 14) + tone(330, 0.25, 0.15, 14), s0)      # yeni seviye
        for t in np.arange(s0 + 1.0, s1, 1.0):                                 # tik-tak
            place(tone(1800, 0.04, 0.22, 60), t)
        place(tone(880, 0.6, 0.35, 5) + tone(1320, 0.6, 0.25, 5), s1)          # ding
    place(tone(660, 0.5, 0.3, 4) + tone(990, 0.5, 0.2, 4), segs[-1][2])
    mix = np.clip(mix / max(1.0, np.abs(mix).max() / 0.8), -1, 1)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return total


def ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe: return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render(p, mp4):
    mp4 = Path(mp4); mp4.parent.mkdir(parents=True, exist_ok=True)
    wav = mp4.with_suffix('.wav')
    total = build_audio(p, wav)
    nf = int(total * FPS)
    cmd = [ffmpeg(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', str(wav), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '160k',
           '-shortest', '-movflags', '+faststart', str(mp4)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last = None
    for i in range(nf):
        T = i / FPS
        f = frame(p, T)
        if T > total - 0.4 and last is None:   # kesintisiz döngü: son 0.4 sn ilk kareye karışır
            last = frame(p, 0.0)
        if last is not None:
            f = Image.blend(f, last, min(1.0, (T - (total - 0.4)) / 0.4))
        pr.stdin.write(f.convert('RGB').tobytes())
    pr.stdin.close(); pr.wait()
    wav.unlink(missing_ok=True)
    if pr.returncode: raise RuntimeError('ffmpeg hata')
    return mp4


# ---------------------------------------------------------------- başlık / kayıt / yükleme
def tkey(t):
    """Başlık anahtarı: metin + içindeki emojiler (farklı emoji çifti = farklı başlık)."""
    t = re.sub(r'#\w+', ' ', t.lower())
    return ' '.join(re.sub(r'[^\w ]', ' ', t).split()) + '|' + ''.join(ch for ch in t if ord(ch) > 0x2100)


def done():
    if not LOG.exists(): return set(), []
    rows = list(csv.DictReader(LOG.open(encoding='utf-8')))
    return {r['topic_id'] for r in rows}, rows


def metadata(p, rnd, seen_titles):
    if p['kurgu'] == 'odd':
        L = p['levels'][-1]; a, b = L['a'], L['b']
    elif p['kurgu'] == 'guess':
        a, b = p['items'][0][0], p['items'][1][0]
    else:
        a, b = p['grid'][0], p['grid'][1]
    n = len(done()[1]) + 1   # 2026-11-08: seri numarası (#N) → "devamı yarın" hissi, abone dönüşümü
    p['n'] = n
    opts = [t.format(a=a, b=b, cat=p.get('cat', '').title()) + f' #{n}' for t in TITLES[p['kurgu']]]; rnd.shuffle(opts)
    # emojiler tkey'de silinir → anahtara emojiyi de kat ki farklı çiftler farklı başlık sayılsın
    title = next((o for o in opts if tkey(o) not in seen_titles), None)
    if p['kurgu'] == 'odd':
        desc = ('Find the odd emoji in 3 levels: easy, medium and hard. Pause if you need more time!\n\n'
                + '\n'.join(f"Level {i + 1}: {L['a']} vs {L['b']}" for i, L in enumerate(p['levels'])))
    elif p['kurgu'] == 'guess':
        desc = (f"Guess the {p['cat'].lower()} from the emojis before the timer runs out!\n\n"
                + '\n'.join(f'{i + 1}. {e} = {a_}' for i, (e, a_) in enumerate(p['items'])))
    else:
        desc = 'Spot the 3 differences between the top and bottom emoji grids before the timer runs out!'
    desc += ('\n\nHow many did you get? Comment below 👇 New emoji puzzles every day.\n\n'
             'Emoji: Noto Color Emoji by Google (SIL Open Font License).\n\n#shorts #emoji #emojichallenge #puzzle #brainteaser')
    tags = ['emoji', 'emoji challenge', 'find the odd emoji', 'odd one out', 'spot the difference', 'emoji quiz',
            'brain teaser', 'puzzle', 'find the difference', 'shorts']
    return title, desc, tags


def record(tid, vid, title, publish_at):
    new = not LOG.exists()
    with LOG.open('a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['topic_id', 'date_utc', 'quota_day', 'video_id', 'kind', 'title', 'publish_at'])
        if new: w.writeheader()
        w.writerow(dict(topic_id=tid, date_utc=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'), quota_day=quota_day(),
                        video_id=vid, kind='short', title=title, publish_at=publish_at))


def quota_day(now=None):
    now = now or datetime.now(timezone.utc)
    return (now - timedelta(hours=7)).strftime('%Y-%m-%d')   # YouTube kota günü ≈ 07:00 UTC


def publish_at(n_today):
    slots = ['15:00', '18:00', '20:30']   # ABD öğleden sonra/akşam (UTC)
    hh, mm = map(int, slots[min(n_today, len(slots) - 1)].split(':'))
    now = datetime.now(timezone.utc); t = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if t < now + timedelta(minutes=30): t = now + timedelta(minutes=40)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def log(m): print(m, flush=True)


def main():
    a = sys.argv[1:]
    kurgu = a[a.index('--kurgu') + 1] if '--kurgu' in a else None
    n_today = 0
    if '--auto' in a:
        _, rows = done(); q = quota_day()
        n_today = sum(r['quota_day'] == q for r in rows)
        if n_today >= int(os.environ.get('SHORTS_PER_DAY') or 3):
            log(f'kota günü {q}: {n_today} Short yüklendi, iş yok'); return
    seen, rows = done()
    seen_titles = {tkey(r['title']) for r in rows}
    rnd = random.Random()
    recent = [r['topic_id'].split(':')[1] for r in rows[-2:]]
    for _ in range(200):
        k = kurgu or rnd.choices(['odd', 'spot', 'guess'], weights=[1 if recent.count('odd') == 2 else 3, 1, 2])[0]
        p = make_plan(k, rnd)
        tid = plan_key(p)
        title, desc, tags = metadata(p, rnd, seen_titles)
        if tid not in seen and title:
            break
    else:
        raise SystemExit('yeni bulmaca/başlık bulunamadı')
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    log(f'[emoji] {tid} → {title}')
    mp4 = render(p, OUT / f'short_{stamp}.mp4')
    if DRY:
        log(f'  [dry-run] {mp4}\n{desc}'); return
    import upload
    log(f'kanal: {upload.check_channel()}')
    pa = publish_at(n_today)
    yt = upload.client()
    body = {'snippet': {'title': upload.clean(title + ' #shorts')[:100], 'description': upload.clean(desc)[:4900], 'tags': tags,
                        'categoryId': '24', 'defaultLanguage': 'en', 'defaultAudioLanguage': 'en'},
            'status': {'privacyStatus': 'private', 'publishAt': pa, 'selfDeclaredMadeForKids': False}}
    from googleapiclient.http import MediaFileUpload
    vid = yt.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(str(mp4), resumable=True)).execute()['id']
    record(tid, vid, title, pa)
    log(f'  ✓ https://youtu.be/{vid} (yayın {pa})')


if __name__ == '__main__':
    main()
