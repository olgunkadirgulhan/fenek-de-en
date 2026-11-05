"""Emoji bulmaca kanalı kimliği (2026-11-05): banner, profil, açıklama, anahtar kelimeler.
    python emoji_brand.py --make     # görseller (fonts/emoji/em_*.png)
    python emoji_brand.py --apply    # YouTube'a uygula (banner + açıklama). Kanal adı/profil resmi Studio'dan elle.
Not: Bu kanal YouTube kotasını Bloop ile paylaşır → eski How Long videolarını toplu gizlemek bilinçli olarak YOK.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import emoji as E

A = Path(__file__).resolve().parent / 'fonts' / 'emoji'
DESCRIPTION = """Emoji puzzles every day! 🔍

Find the odd emoji, spot the differences, test your eyes in 3 levels from easy to hard. Pause if you need more time, then tell us in the comments how many you got.

New emoji challenges every day. 👀

Emoji: Noto Color Emoji by Google (SIL Open Font License)."""
KEYWORDS = ['emoji', 'emoji challenge', 'find the odd emoji', 'odd one out', 'spot the difference', 'emoji quiz', 'emoji puzzle',
            'brain teaser', 'puzzle', 'find the difference', 'eye test', 'brain games']


def bg(w, h):
    im = E.background().resize((w, h)) if (w, h) != (E.W, E.H) else E.background().copy()
    return im


def banner():
    W, H = 2560, 1440
    im = bg(W, H); d = ImageDraw.Draw(im)
    d.rounded_rectangle([560, 470, 2000, 970], radius=60, fill=E.INK + (240,))
    d.text((W // 2, 640), 'FIND THE ODD EMOJI', font=E.font(120), fill=(255, 220, 60), anchor='mm', stroke_width=6, stroke_fill=E.INK)
    row = ['😀'] * 6; row[4] = '😃'
    for i, ch in enumerate(row):
        e = E.emoji_img(ch, 130); im.alpha_composite(e, (int(W // 2 - 3 * 160 + i * 160 + 15), 760))
    im.convert('RGB').save(A / 'em_banner_2560x1440.png')


def profile():
    S = 800
    im = bg(S, S); d = ImageDraw.Draw(im)
    d.ellipse([60, 60, 740, 740], fill=E.INK + (245,))
    e = E.emoji_img('🔍', 380); im.alpha_composite(e, ((S - e.width) // 2, 150))
    d.text((S // 2, 620), 'ODD EMOJI', font=E.font(96), fill=(255, 220, 60), anchor='mm', stroke_width=5, stroke_fill=E.INK)
    im.convert('RGB').save(A / 'em_profile_800x800.png')


def apply():
    import upload
    from googleapiclient.http import MediaFileUpload
    yt = upload.client()
    ch = yt.channels().list(part='snippet,brandingSettings', mine=True).execute()['items'][0]
    print('kanal:', ch['snippet']['title'])
    url = yt.channelBanners().insert(media_body=MediaFileUpload(str(A / 'em_banner_2560x1440.png'), mimetype='image/png')).execute()['url']
    b = ch.get('brandingSettings', {}); b.setdefault('channel', {})
    b['channel']['description'] = DESCRIPTION
    b['channel']['keywords'] = ' '.join(f'"{k}"' if ' ' in k else k for k in KEYWORDS)
    b['channel'].pop('unsubscribedTrailer', None); b['channel']['defaultLanguage'] = 'en'
    b.setdefault('image', {})['bannerExternalUrl'] = url; b.pop('hints', None)
    yt.channels().update(part='brandingSettings', body={'id': ch['id'], 'brandingSettings': b}).execute()
    print('✓ banner + açıklama')


if __name__ == '__main__':
    if '--make' in sys.argv or not (A / 'em_banner_2560x1440.png').exists():
        banner(); profile(); print('✓ görseller')
    if '--apply' in sys.argv: apply()
