"""Bölüm üretici (kanal: de-en — Almanca konuşanlara İngilizce). İçerik content/course.json'dan gelir.

Formatlar (slot sırasıyla):
  sahne  ünitenin diyaloğunu Max ve Lily İngilizce canlandırır (Almanca altyazı), sonda bir soru
  kelime 5 kelime kartı (emoji + İngilizce + Almanca)
  quiz   3 soru (İngilizce → Almanca anlam / Almanca → İngilizce karşılık), 3 sn geri sayım, cevap
  av     harf tablosunda 5 saklı İngilizce kelime, 10 sn geri sayım

Her şey içerikten türetilir; kelime/cümle uydurulmaz. Aynı içerik kısa sürede tekrar etmez (history.json).
"""
import json
import os
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = json.loads((ROOT / 'content' / 'course.json').read_text(encoding='utf-8'))
SRC, TGT = 'de', 'en'  # anlatım dili (Almanca), öğretilen dil (İngilizce)
NAMES = {'emre': 'MAX', 'lena': 'LILY'}   # öğrenen (Almanca konuşan) ve yerli (İngilizce konuşan)
LEVEL_WEIGHT = {'A1': 5, 'A2': 4, 'B1': 3, 'B2': 2, 'C1': 1, 'C2': 1}
SLOT_FORMATS = ['sahne', 'kelime', 'quiz', 'kelime', 'sahne', 'av']
LEVELS = [l.strip() for l in (os.environ.get('LEVELS') or 'A1,A2,B1').split(',')]

HOOKS = {
    'sahne': ['So spricht man Englisch!', 'Hör zu und sprich nach!', 'Diesen Dialog musst du kennen!'],
    'kelime': ['Fünf englische Wörter. Bist du bereit?', 'Fünf Wörter, dreißig Sekunden!'],
    'quiz': ['Drei Fragen, drei Sekunden. Bereit?', 'Teste dich! Drei Fragen.'],
    'av': ['In dieser Tabelle verstecken sich fünf englische Wörter. Du hast zehn Sekunden!',
           'Fünf Wörter sind versteckt. Wie viele findest du?'],
}
SITE_CTAS = ['Die ganze Lektion gibt es gratis auf der Seite. Link im Profil!']
FOLLOW_CTAS = ['Folge für jeden Tag neues Englisch!', 'Wie viele wusstest du? Schreib es in die Kommentare!',
               'Speicher das und wiederhole es morgen!', 'Morgen kommen neue Wörter. Folge jetzt!']
BRAND = bool((os.environ.get('SITE_URL') or '').strip())
CTAS = SITE_CTAS + FOLLOW_CTAS if BRAND else FOLLOW_CTAS
ASK_MEAN = 'Was heißt das?'
ASK_REV = 'Wie heißt das auf Englisch?'
UI = {'mean': 'was heißt das?', 'rev': 'auf Englisch?', 'follow': '🔔 FOLGEN', 'daily': 'Jeden Tag neues Englisch!',
      'free': 'kostenlose Lektion', 'start': 'START', 'stats': '35 Lektionen · 10 Sprachen · gratis',
      'link': '👉 Link im Profil'}


def pick_least_used(items, key, used, rng, weight=lambda x: 1):
    """En az kullanılan (ve en eskide kullanılan) öğeyi seç; seviye ağırlığıyla."""
    counts = {}
    for i, u in enumerate(used):
        counts[u] = (counts.get(u, (0, -1))[0] + 1, i)
    def score(x):
        c, last = counts.get(key(x), (0, -1))
        return (c, last, -weight(x) * rng.random())
    pool = sorted(items, key=score)
    best = [x for x in pool if score(x)[:2] == score(pool[0])[:2]]
    return rng.choices(best, weights=[weight(x) for x in best])[0]


def beat(who, lang, text, sub='', **st):
    return {'who': who, 'lang': lang, 'text': text, 'sub': sub, 'st': st}


def pause(sec, **st):
    return {'who': None, 'lang': None, 'text': '', 'silence': sec, 'st': st}


def up(s):
    return s.upper().replace('ß', 'SS')


def lower_first(s):
    return s[:1].lower() + s[1:] if s else s


def distractors(w, pool, key, rng, k=2):
    same = [x for x in pool if x is not w and x[key] != w[key]]
    return rng.sample(same, min(k, len(same)))


def rev_q(w, pool, rng):
    """Almanca kelime gösterilir, 3 İngilizce seçenek."""
    opts = [w[TGT]] + [x[TGT] for x in distractors(w, pool, TGT, rng)]
    rng.shuffle(opts)
    return {'type': 'quiz', 'kind': 'rev', 'emoji': w['emoji'], 'word': w[SRC], 'opts': opts, 'answer': w[TGT],
            'tr': w[SRC], 'ask': UI['rev']}


def mean_q(w, pool, rng):
    """İngilizce kelime gösterilir, 3 Almanca seçenek."""
    opts = [w[SRC]] + [x[SRC] for x in distractors(w, pool, SRC, rng)]
    rng.shuffle(opts)
    return {'type': 'quiz', 'kind': 'mean', 'emoji': '❓', 'word': w[TGT], 'opts': opts, 'answer': w[SRC], 'tr': w[SRC],
            'ask': UI['mean']}


# ------------------------------------------------------------------ formatlar

def ep_sahne(unit, rng):
    t = unit['title'][SRC]
    beats = [beat('fenek', SRC, rng.choice(HOOKS['sahne']), phase='hook', fenek=True)]
    roles = {'A': 'lena', 'B': 'emre'}
    for i, ln in enumerate(unit['lines'][:8]):
        beats.append(beat(roles[ln['who']], TGT, ln[TGT], ln[SRC], phase='dialog', mood={'emre': 'happy' if i == 7 else 'neutral'}))
    if len(unit['words']) >= 3:
        w = rng.choice(unit['words'])
        q = rev_q(w, unit['words'], rng)
        beats += [beat('fenek', SRC, ASK_REV, overlay=q, key='q', fenek=True),
                  pause(3.0, overlay=q, key='q', countdown=3, fenek=True),
                  beat('lena', TGT, w[TGT], w[SRC], overlay={**q, 'reveal': True}, key='q', sfx='ding', fenek=True, mood={'emre': 'happy'})]
    beats.append(beat('fenek', SRC, rng.choice([c for c in CTAS if 'Wie viele' not in c]), overlay={'type': 'cta', 'unit': t, 'emoji': unit['emoji'], 'cefr': unit['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    title = rng.choice([f"{t}: Englisch Dialog {unit['emoji']} | {unit['cefr']} #englisch",
                        f"So spricht man auf Englisch: {t} {unit['emoji']} | {unit['cefr']}",
                        f"Verstehst du dieses Gespräch? {t} {unit['emoji']} #englischlernen",
                        f"Englisch im Alltag: {t} {unit['emoji']} {unit['cefr']}",
                        f"{t} auf Englisch 🇬🇧 Dialog mit Untertitel {unit['emoji']}"])
    return dict(caption=[up(t), "ENGLISCH DIALOG " + unit['emoji']], tag=f"{unit['cefr']} · LEKTION", title=title,
                topic=unit['id'], theme=unit['id'], poster={'emoji': unit['emoji'], 'label': unit['title'][TGT].upper()[:18]}, beats=beats,
                desc=f"Englischer Dialog aus der Lektion {t} ({unit['cefr']}). Mit deutschen Untertiteln und Audio.")


def ep_kelime(pack, rng):
    t = pack['title'][SRC]
    words = rng.sample(pack['words'], min(5, len(pack['words'])))
    beats = [beat('fenek', SRC, rng.choice(HOOKS['kelime']), phase='hook', fenek=True)]
    for i, w in enumerate(words):
        card = {'type': 'card', 'emoji': w['emoji'], 'de': w[TGT], 'art': None, 'noun': None, 'tr': w[SRC], 'i': i + 1, 'n': len(words)}
        who = 'lena' if i % 2 == 0 else 'emre'
        beats += [beat(who, TGT, w[TGT], '', overlay=card, key=f'c{i}', sfx_before='whoosh', nosub=True),
                  beat('fenek', SRC, w[SRC], '', overlay=card, key=f'c{i}', fenek=True, nosub=True)]
    beats.append(beat('fenek', SRC, rng.choice(CTAS), overlay={'type': 'cta', 'unit': t, 'emoji': pack['emoji'], 'cefr': pack['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    return dict(caption=["5 ENGLISCHE WÖRTER", f"{up(t)} {pack['emoji']}"], tag=f"{pack['cefr']} · WÖRTER", topic=pack['id'], theme='study', poster={'emoji': pack['emoji'], 'label': pack['title'][TGT].upper()[:18]},
                title=rng.choice([f"5 englische Wörter: {t} {pack['emoji']} | {pack['cefr']} #englisch",
                                  f"{t} auf Englisch {pack['emoji']} | {pack['cefr']}",
                                  f"Kennst du diese 5 Wörter? {t} {pack['emoji']} #englischlernen",
                                  f"{t}: die 5 wichtigsten englischen Wörter {pack['emoji']}",
                                  f"Englisch Vokabeln: {t} {pack['emoji']} Niveau {pack['cefr']}"]), beats=beats,
                desc=f"5 englische Wörter zum Thema {t} ({pack['cefr']}). Mit Aussprache und deutscher Bedeutung.")


def ep_quiz(pack, rng):
    t = pack['title'][SRC]
    pool = pack['words'][:]
    rng.shuffle(pool)
    kinds = ['mean', 'rev', 'mean'] if rng.random() < 0.5 else ['rev', 'mean', 'rev']
    qs = [{'w': w, 'q': (mean_q if k == 'mean' else rev_q)(w, pack['words'], rng)} for w, k in zip(pool[:3], kinds)]
    beats = [beat('fenek', SRC, rng.choice(HOOKS['quiz']), phase='hook', fenek=True)]
    for i, item in enumerate(qs):
        q, w = dict(item['q'], i=i + 1, n=len(qs)), item['w']
        if q['kind'] == 'mean':
            beats += [beat('fenek', SRC, ASK_MEAN, overlay=q, key=f'q{i}', fenek=True, sfx_before='whoosh', nosub=True),
                      beat('lena', TGT, w[TGT], '', overlay=q, key=f'q{i}', fenek=True, nosub=True),
                      pause(3.0, overlay=q, key=f'q{i}', countdown=3, fenek=True),
                      beat('fenek', SRC, f"Antwort: {w[SRC]}!", '', overlay={**q, 'reveal': True}, key=f'q{i}', sfx='ding', fenek=True, nosub=True, mood={'emre': 'happy'})]
        else:
            beats += [beat('fenek', SRC, ASK_REV, overlay=q, key=f'q{i}', fenek=True, sfx_before='whoosh', nosub=True),
                      pause(3.0, overlay=q, key=f'q{i}', countdown=3, fenek=True),
                      beat('lena', TGT, w[TGT], w[SRC], overlay={**q, 'reveal': True}, key=f'q{i}', sfx='ding', fenek=True, mood={'emre': 'happy'})]
    beats.append(beat('fenek', SRC, rng.choice(CTAS), overlay={'type': 'cta', 'unit': t, 'emoji': pack['emoji'], 'cefr': pack['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    return dict(caption=['ENGLISCH QUIZ 🤔', up(t)], tag=f"{pack['cefr']} · QUIZ", topic=pack['id'], theme='study', poster={'emoji': pack['emoji'], 'label': pack['title'][TGT].upper()[:18]},
                title=rng.choice([f"Englisch Quiz: {t} 🤔 Teste dich in 3 Fragen! | {pack['cefr']}",
                                  f"Wie gut ist dein Englisch? {t} 🤔 {pack['cefr']}",
                                  f"3 Fragen, 1 Thema: {t} 🧠 #englisch",
                                  f"Alles richtig? Dann bist du {pack['cefr']}: {t} 🤔",
                                  f"Englisch Test: {t} ✍️ Wie viele schaffst du?"]), beats=beats,
                desc=f"Englisch Quiz mit 3 Fragen zum Thema {t} ({pack['cefr']}). Wie viele hattest du richtig? Schreib es in die Kommentare!")


HUNT_FILL = 'ABCDEFGHIJKLMNOPRSTUVWY'


def hunt_word(w):
    s = re.sub(r'^(the|a|an|to) ', '', w[TGT].lower())
    return re.sub(r'[^A-Z]', '', s.upper())


def make_grid(words, rng, size=8):
    grid = [[''] * size for _ in range(size)]
    placed = []
    dirs = [(0, 1), (1, 0), (1, 1)]
    for wd in words:
        for _ in range(300):
            dr, dc = rng.choice(dirs)
            r = rng.randrange(size - (len(wd) - 1) * dr)
            c = rng.randrange(size - (len(wd) - 1) * dc)
            cells = [(r + k * dr, c + k * dc) for k in range(len(wd))]
            if all(grid[a][b] in ('', wd[k]) for k, (a, b) in enumerate(cells)):
                for k, (a, b) in enumerate(cells):
                    grid[a][b] = wd[k]
                placed.append(cells)
                break
        else:
            return None
    for a in range(size):
        for b in range(size):
            grid[a][b] = grid[a][b] or rng.choice(HUNT_FILL)
    return [''.join(r) for r in grid], placed


def ep_av(pack, rng):
    t = pack['title'][SRC]
    cands = [w for w in pack['words'] if 3 <= len(hunt_word(w)) <= 8 and ' ' not in w[TGT].strip()]
    if len(cands) < 5:
        cands = [w for w in pack['words'] if 3 <= len(hunt_word(w)) <= 8]
    for _ in range(40):
        ws = rng.sample(cands, min(5, len(cands)))
        g = make_grid([hunt_word(w) for w in ws], rng)
        if g:
            break
    else:
        raise RuntimeError(f'grid failed for {pack["id"]}')
    grid, cells = g
    words = [{'w': hunt_word(w), 'de': w[TGT], 'tr': w[SRC], 'emoji': w['emoji'], 'cells': c} for w, c in zip(ws, cells)]
    base = {'type': 'grid', 'grid': grid, 'words': words}
    beats = [beat('fenek', SRC, rng.choice(HOOKS['av']), overlay={**base, 'found': 0}, key='g', fenek=True),
             pause(10.0, overlay={**base, 'found': 0}, key='g', countdown=10, fenek=False)]
    for i, w in enumerate(words):
        who = 'lena' if i % 2 == 0 else 'emre'
        beats.append(beat(who, TGT, w['de'], w['tr'], overlay={**base, 'found': i + 1}, key='g', sfx_before='pop'))
    beats.append(beat('fenek', SRC, 'Wie viele hast du gefunden? Schreib es in die Kommentare!', overlay={**base, 'found': len(words)}, key='g', fenek=True))
    beats.append(beat('fenek', SRC, rng.choice([c for c in CTAS if 'Kommentare' not in c]), overlay={'type': 'cta', 'unit': t, 'emoji': pack['emoji'], 'cefr': pack['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    return dict(caption=['5 WÖRTER VERSTECKT 🔍', 'DU HAST 10 SEKUNDEN!'], tag=f"{pack['cefr']} · WORTSUCHE", topic=pack['id'], theme='study', poster={'emoji': pack['emoji'], 'label': pack['title'][TGT].upper()[:18]},
                title=rng.choice([f"5 englische Wörter versteckt 🔍 Findest du sie? | {t}",
                                  f"Wortsuche: {t} 🔍 Finde sie in 10 Sekunden!",
                                  f"{t}: 5 englische Wörter im Buchstabensalat 👀",
                                  f"Hast du gute Augen? 🔍 {t} Wortsuche",
                                  f"10 Sekunden, 5 Wörter: {t} 🔎 #englisch"]), beats=beats,
                desc=f"Wortsuche: {t} ({pack['cefr']}). Finde die 5 versteckten englischen Wörter in 10 Sekunden!")


# ------------------------------------------------------------------ seçim

def make_episode(slot, hist, seed):
    rng = random.Random(seed)
    used = [h['topic'] for h in hist.get('recent', []) if h.get('topic')]
    fmt = SLOT_FORMATS[slot % len(SLOT_FORMATS)]
    lw = lambda x: LEVEL_WEIGHT.get(x['cefr'], 1)
    if fmt == 'sahne':
        unit = pick_least_used([u for u in COURSE['units'] if u['cefr'] in LEVELS], lambda u: u['id'], used, rng, lw)
        ep = ep_sahne(unit, rng)
    else:
        packs = [p for p in COURSE['packs'] if len(p['words']) >= 8 and p['cefr'] in LEVELS]
        pack = pick_least_used(packs, lambda p: p['id'], used, rng, lw)
        ep = {'kelime': ep_kelime, 'quiz': ep_quiz, 'av': ep_av}[fmt](pack, rng)
    ep['format'] = fmt
    ep['names'] = NAMES
    ep['tgt'] = TGT
    ep['ui'] = UI
    return ep
