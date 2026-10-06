"""Bölüm üretici (kanal: en-de — İngilizce bilenlere Almanca): sitenin içeriğinden (content/course.json) her slot için bir Shorts senaryosu kurar.

Formatlar (günde 4 slot, sırayla):
  sahne  ünitenin diyaloğunu Emre ve Lena canlandırır, sonda artikel sorusu
  kelime 5 kelime kartı (emoji + artikel renkli Almanca + Türkçe)
  quiz   3 soru (artikel / anlam), 3 sn geri sayım, cevap
  av     harf tablosunda 5 saklı kelime, 10 sn geri sayım
  hata   bank/ klasöründeki elle yazılmış "tipik hata" skeçleri (varsa sahne yerine)

Her şey içerikten türetilir; kelime/cümle uydurulmaz. Aynı içerik kısa sürede tekrar etmez (history.json).
"""
import json
import os
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = json.loads((ROOT / 'content' / 'course.json').read_text(encoding='utf-8'))
SRC, TGT = 'en', 'de'  # anlatım dili (İngilizce), öğretilen dil (Almanca)
NAMES = {'emre': 'TOM', 'lena': 'LENA'}   # öğrenen (İngilizce konuşan) ve yerli (Almanca konuşan)
LEVEL_WEIGHT = {'A1': 5, 'A2': 4, 'B1': 3, 'B2': 2, 'C1': 1, 'C2': 1}
ART = re.compile(r'^(der|die|das) (.+)$')
ART_COLOR = {'der': '#2F6FEB', 'die': '#E5484D', 'das': '#16A37E'}
# 6'lık döngü: ilk hafta medyan izlenme kelime 743, sahne 651, quiz 200, av 76 (format başına 4-5 video);
# güçlü formatlar ikişer kez, zayıflar bir kez. Format listesi (--format) ilk geçişten okunur.
SLOT_FORMATS = ['sahne', 'kelime', 'quiz', 'kelime', 'sahne', 'av']
LEVELS = [l.strip() for l in (os.environ.get('LEVELS') or 'A1,A2,B1').split(',')]  # kanalın hedef seviyeleri

# Açılış cümleleri: konu adı söylenmez (zaten ekranın üstünde yazıyor), kısa ve doğrudan
HOOKS = {
    'sahne': ['This is how Germans really talk!', 'Learn this German dialogue!', 'Listen and repeat!'],
    'kelime': ['Five German words. Ready?', 'Five words, thirty seconds!'],
    'quiz': ['Three questions, three seconds. Ready?', 'Test yourself! Three questions.'],
    'av': ['Five German words are hidden here. You have ten seconds!', 'Five hidden words. How many can you find?'],
}
SITE_CTAS = ['The full lesson is free on the site. Link in profile!']
FOLLOW_CTAS = ['Follow for new German every day!', 'How many did you get? Tell me in the comments!',
               'Save this and review it tomorrow!', 'New words tomorrow. Follow now!']
UI = {'mean': 'what does it mean?', 'follow': '🔔 FOLLOW', 'daily': 'New German every day!', 'free': 'free lesson',
      'start': 'START', 'stats': '35 lessons · 10 languages · free', 'link': '👉 Link in profile'}
# Site açılana kadar (SITE_URL boş) siteye/markaya yönlendiren cümle kurulmaz
BRAND = bool((os.environ.get('SITE_URL') or '').strip())
CTAS = SITE_CTAS + FOLLOW_CTAS if BRAND else FOLLOW_CTAS


def noun(w):
    m = ART.match(w[TGT])
    return (m.group(1), m.group(2)) if m and not w.get('plural') else (None, None)


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
    return s.upper()


def lower_first(s):
    return s[:1].lower() + s[1:] if s else s


# ------------------------------------------------------------------ formatlar

def ep_sahne(unit, rng):
    t = unit['title'][SRC]
    lines = unit['lines']
    beats = [beat('fenek', SRC, rng.choice(HOOKS['sahne']).format(t=t, tl=lower_first(t)), phase='hook', fenek=True)]
    roles = {'A': 'lena', 'B': 'emre'}
    for i, ln in enumerate(lines[:8]):
        beats.append(beat(roles[ln['who']], TGT, ln[TGT], ln[SRC], phase='dialog', mood={'emre': 'happy' if i == 7 else 'neutral'}))
    nouns = [w for w in unit['words'] if noun(w)[0]]
    if nouns:
        w = rng.choice(nouns)
        art, n = noun(w)
        q = {'type': 'quiz', 'kind': 'art', 'emoji': w['emoji'], 'word': n, 'opts': ['der', 'die', 'das'], 'answer': art, 'tr': w[SRC]}
        beats += [beat('fenek', SRC, 'Which article is it?', overlay=q, key='q', fenek=True),
                  pause(3.0, overlay=q, key='q', countdown=3, fenek=True),
                  beat('emre', TGT, w[TGT], w[SRC], overlay={**q, 'reveal': True}, key='q', sfx='ding', fenek=True, mood={'emre': 'happy'})]
    beats.append(beat('fenek', SRC, rng.choice([c for c in CTAS if 'How many' not in c]), overlay={'type': 'cta', 'unit': t, 'emoji': unit['emoji'], 'cefr': unit['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    title = rng.choice([f"{t}: German conversation {unit['emoji']} | {unit['cefr']} #learngerman",
                        f"How Germans talk: {t} {unit['emoji']} | {unit['cefr']}",
                        f"Can you understand this German dialogue? {t} {unit['emoji']} #german",
                        f"Real-life German: {t} {unit['emoji']} {unit['cefr']}",
                        f"{t} in German 🇩🇪 Dialogue with subtitles {unit['emoji']}"])
    return dict(caption=[f"{up(t)}", "GERMAN DIALOGUE " + unit['emoji']], tag=f"{unit['cefr']} · LESSON", title=title,
                topic=unit['id'], theme=unit['id'], poster={'emoji': unit['emoji'], 'label': unit['title'][TGT].upper()[:18]}, beats=beats,
                desc=f"German dialogue from the lesson {t} ({unit['cefr']}). With English subtitles and audio.")


def ep_kelime(pack, rng):
    t = pack['title'][SRC]
    words = rng.sample(pack['words'], min(5, len(pack['words'])))
    beats = [beat('fenek', SRC, rng.choice(HOOKS['kelime']).format(t=t, tl=lower_first(t)), phase='hook', fenek=True)]
    for i, w in enumerate(words):
        art, n = noun(w)
        card = {'type': 'card', 'emoji': w['emoji'], 'de': w[TGT], 'art': art, 'noun': n, 'tr': w[SRC], 'i': i + 1, 'n': len(words)}
        who = 'lena' if i % 2 == 0 else 'emre'
        beats += [beat(who, TGT, w[TGT], '', overlay=card, key=f'c{i}', sfx_before='whoosh', nosub=True),
                  beat('fenek', SRC, w[SRC], '', overlay=card, key=f'c{i}', fenek=True, nosub=True)]
    beats.append(beat('fenek', SRC, rng.choice(CTAS), overlay={'type': 'cta', 'unit': t, 'emoji': pack['emoji'], 'cefr': pack['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    return dict(caption=["5 GERMAN WORDS", f"{up(t)} {pack['emoji']}"], tag=f"{pack['cefr']} · WORDS", topic=pack['id'], theme='study', poster={'emoji': pack['emoji'], 'label': pack['title'][TGT].upper()[:18]},
                title=rng.choice([f"5 German words: {t} {pack['emoji']} | {pack['cefr']} #learngerman", f"{t} in German {pack['emoji']} | {pack['cefr']}", f"Do you know these 5 German words? {t} {pack['emoji']} #german", f"{t}: 5 German words you need every day {pack['emoji']}", f"German vocabulary: {t} {pack['emoji']} level {pack['cefr']}"]), beats=beats,
                desc=f"5 German words about {t} ({pack['cefr']}). With der/die/das, pronunciation and English meaning.")


def ep_quiz(pack, rng):
    t = pack['title'][SRC]
    pool = pack['words'][:]
    rng.shuffle(pool)
    nouns = [w for w in pool if noun(w)[0]]
    qs = []
    for kind in ('art', 'mean', 'art' if len(nouns) > 1 else 'mean'):
        cand = [w for w in (nouns if kind == 'art' else pool) if w not in [q['w'] for q in qs]]
        if not cand:
            continue
        w = cand[0]
        if kind == 'art':
            art, n = noun(w)
            qs.append({'w': w, 'q': {'type': 'quiz', 'kind': 'art', 'emoji': w['emoji'], 'word': n, 'opts': ['der', 'die', 'das'], 'answer': art, 'tr': w[SRC]}})
        else:
            same = [x for x in pool if x is not w and x[SRC] != w[SRC] and bool(noun(x)[0]) == bool(noun(w)[0])]
            wrong = rng.sample(same if len(same) >= 2 else [x for x in pool if x is not w and x[SRC] != w[SRC]], 2)
            opts = [w[SRC]] + [x[SRC] for x in wrong]
            rng.shuffle(opts)
            qs.append({'w': w, 'q': {'type': 'quiz', 'kind': 'mean', 'emoji': '❓', 'word': w[TGT], 'opts': opts, 'answer': w[SRC], 'tr': w[SRC]}})
    beats = [beat('fenek', SRC, rng.choice(HOOKS['quiz']).format(t=t, tl=lower_first(t)), phase='hook', fenek=True)]
    for i, item in enumerate(qs):
        q, w = dict(item['q'], i=i + 1, n=len(qs)), item['w']
        ask = 'Der, die or das?' if q['kind'] == 'art' else 'What does it mean?'   # soru numarası kartta yazıyor, söylenmez
        beats += [beat('fenek', SRC, ask, overlay=q, key=f'q{i}', fenek=True, sfx_before='whoosh', nosub=True)]
        if q['kind'] == 'mean':
            beats.append(beat('lena', TGT, w[TGT], '', overlay=q, key=f'q{i}', fenek=True, nosub=True))
        beats.append(pause(3.0, overlay=q, key=f'q{i}', countdown=3, fenek=True))
        if q['kind'] == 'mean':
            # kelimeyi Lena zaten söyledi: cevabı Fenek Türkçe verir (aynı kelime iki kez duyulmasın)
            beats.append(beat('fenek', SRC, f"Answer: {w[SRC]}!", '', overlay={**q, 'reveal': True}, key=f'q{i}', sfx='ding', fenek=True, nosub=True, mood={'emre': 'happy'}))
        else:
            beats.append(beat('emre', TGT, w[TGT], w[SRC], overlay={**q, 'reveal': True}, key=f'q{i}', sfx='ding', fenek=True, mood={'emre': 'happy'}))
    beats.append(beat('fenek', SRC, rng.choice(CTAS), overlay={'type': 'cta', 'unit': t, 'emoji': pack['emoji'], 'cefr': pack['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    return dict(caption=['GERMAN QUIZ 🤔', f"{up(t)}"], tag=f"{pack['cefr']} · QUIZ", topic=pack['id'], theme='study', poster={'emoji': pack['emoji'], 'label': pack['title'][TGT].upper()[:18]},
                title=rng.choice([f"German quiz: {t} 🤔 Test yourself in 3 questions! | {pack['cefr']}", f"How good is your German? {t} 🤔 {pack['cefr']}", f"3 questions, 1 topic: {t} 🧠 #learngerman", f"Get all 3 right and you're {pack['cefr']}: {t} 🤔", f"Der, die or das? {t} ✍️ How many can you get?"]), beats=beats,
                desc=f"A 3-question German quiz about {t} ({pack['cefr']}). How many did you get right? Tell me in the comments!")


HUNT_FILL = 'ABCDEFGHIJKLMNOPRSTUVWZÄÖÜ'


def hunt_word(w):
    art, n = noun(w)
    s = (n or w[TGT]).upper()
    return re.sub(r'[^A-ZÄÖÜ]', '', s.replace('ß', 'SS'))


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
            grid[a][b] = grid[a][b] or rng.choice(HUNT_FILL[:23])
    return [''.join(r) for r in grid], placed


def ep_av(pack, rng):
    t = pack['title'][SRC]
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
    beats.append(beat('fenek', SRC, 'How many did you find? Tell me in the comments!', overlay={**base, 'found': len(words)}, key='g', fenek=True))
    beats.append(beat('fenek', SRC, rng.choice([c for c in CTAS if 'comments' not in c]), overlay={'type': 'cta', 'unit': t, 'emoji': pack['emoji'], 'cefr': pack['cefr']}, key='cta', fenek=True, sfx_before='pop'))
    return dict(caption=['5 HIDDEN WORDS 🔍', 'YOU HAVE 10 SECONDS!'], tag=f"{pack['cefr']} · WORD SEARCH", topic=pack['id'], theme='study', poster={'emoji': pack['emoji'], 'label': pack['title'][TGT].upper()[:18]},
                title=rng.choice([f"5 German words are hidden here 🔍 Can you find them? | {t}", f"Word search: {t} 🔍 Find them in 10 seconds!", f"{t}: 5 German words hidden in the letters 👀", f"Sharp eyes? 🔍 {t} German word search", f"10 seconds, 5 words: {t} 🔎 #learngerman"]), beats=beats,
                desc=f"Word search: {t} ({pack['cefr']}). Find the 5 hidden German words in 10 seconds!")


def ep_bank(item):
    return dict(item, beats=item['beats'])


# ------------------------------------------------------------------ seçim

def make_episode(slot, hist, seed):
    rng = random.Random(seed)
    used = [h['topic'] for h in hist.get('recent', []) if h.get('topic')]
    fmt = SLOT_FORMATS[slot % len(SLOT_FORMATS)]
    bank_dir = ROOT / 'bank'
    if False and fmt == 'sahne' and bank_dir.exists():  # hata skeçleri Türkçe: bu kanalda yok
        done = set(hist.get('bank_used', []))
        fresh = sorted(p for p in bank_dir.glob('*.json') if p.stem not in done)
        if fresh and rng.random() < 0.5:
            item = json.loads(fresh[0].read_text(encoding='utf-8'))
            ep = dict(item, format='hata', bank_id=fresh[0].stem)
            return ep
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
