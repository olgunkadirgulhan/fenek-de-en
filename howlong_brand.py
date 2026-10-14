#!/usr/bin/env python3
"""How Long Would It Take? kanal kimliği: banner, profil, açıklama; --hide-old eski Almanca Short'ları gizler (silmez).
    python howlong_brand.py --make | --apply [--hide-old]"""
import csv, json, sys
from pathlib import Path
from PIL import Image, ImageDraw
import howlong as H

A = H.FD
DESCRIPTION = """How long would it take to walk to the Moon? To reach Mars at the speed of a snail? To see light from the nearest star?

Every video times one journey with real distances from NASA, NOAA and official surveys, and real or clearly stated speeds, from a garden snail to the speed of light. Guess first, then watch the clock run.

Shorts every day, plus longer videos that time every speed or every destination.

Sources and assumptions are in every description. Time = distance ÷ speed, nonstop: a thought experiment, not a travel plan."""
KEYWORDS = ['how long would it take', 'how long', 'space', 'science', 'speed of light', 'distance', 'moon', 'mars',
            'education', 'math', 'thought experiment', 'universe', 'scale']


def banner():
    W, Hh = 2560, 1440
    img = H.background(W, Hh); d = ImageDraw.Draw(img); cy = Hh // 2
    H.route(img, d, cy + 60, 0.55, 'snail', 'moon', None, x0=W // 2 - 700, x1=W // 2 + 700, sz=170)
    d.text((W // 2, cy - 230), 'HOW LONG WOULD IT TAKE?', font=H.font(H.SANS, 110), fill=H.INK, anchor='mm')
    d.text((W // 2, cy + 200), '914 YEARS', font=H.font(H.MONO, 90), fill=H.BLUE, anchor='mm')
    img.save(A / 'hl_banner_2560x1440.png')


def profile():
    img = H.background(800, 800); d = ImageDraw.Draw(img)
    sw = H.icon('stopwatch', 520); img.paste(sw, (140, 110), sw)
    d.text((400, 700), 'HOW LONG?', font=H.font(H.SANS, 92), fill=H.BLUE, anchor='mm')
    img.convert('RGB').save(A / 'hl_profile_800x800.png')


def apply(hide_old):
    import upload
    from googleapiclient.http import MediaFileUpload
    yt = upload.client()
    ch = yt.channels().list(part='snippet,brandingSettings', mine=True).execute()['items'][0]
    print('kanal:', ch['snippet']['title'])
    url = yt.channelBanners().insert(media_body=MediaFileUpload(str(A / 'hl_banner_2560x1440.png'), mimetype='image/png')).execute()['url']
    b = ch.get('brandingSettings', {}); b.setdefault('channel', {})
    b['channel']['description'] = DESCRIPTION
    b['channel']['keywords'] = ' '.join(f'"{k}"' if ' ' in k else k for k in KEYWORDS)
    b['channel'].pop('unsubscribedTrailer', None); b['channel']['defaultLanguage'] = 'en'
    b.setdefault('image', {})['bannerExternalUrl'] = url; b.pop('hints', None)
    yt.channels().update(part='brandingSettings', body={'id': ch['id'], 'brandingSettings': b}).execute()
    print('✓ banner + açıklama')
    if not hide_old: return
    with open('published.csv', encoding='utf-8') as f:
        old = [r['video_id'] for r in csv.DictReader(f) if r.get('video_id')]
    hf = Path('hidden_old.json'); hidden = json.loads(hf.read_text()) if hf.exists() else []
    for i in range(0, len(old), 50):
        for v in yt.videos().list(part='status,snippet', id=','.join(old[i:i + 50])).execute().get('items', []):
            if v['status']['privacyStatus'] == 'private': continue
            st = v['status']; was = st['privacyStatus']; st['privacyStatus'] = 'private'; st.pop('publishAt', None)
            yt.videos().update(part='status', body={'id': v['id'], 'status': st}).execute()
            hidden.append({'id': v['id'], 'was': was, 'title': v['snippet']['title']})
    hf.write_text(json.dumps(hidden, indent=1, ensure_ascii=False))
    print(f'✓ {len(hidden)} eski video gizli (hidden_old.json)')


if __name__ == '__main__':
    if '--make' in sys.argv or not (A / 'hl_banner_2560x1440.png').exists():
        banner(); profile(); print('✓ görseller')
    if '--apply' in sys.argv: apply('--hide-old' in sys.argv)
