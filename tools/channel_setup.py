"""Kanal kurulumu (tekrar çalıştırılabilir; Actions 'channel-setup'): açıklama, anahtar kelimeler, ülke, dil (en),
banner, filigran, çocuklara yönelik değil, format oynatma listeleri ve ana sayfa bölümleri.
Profil resmi ve @handle API ile değiştirilemez: channel/profile_1080.png → Studio → Özelleştirme.
    python tools/channel_setup.py
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / 'channel'
PLAYLISTS_FILE = ROOT / 'playlists.json'

DESC = """Learn German with short videos every day! 🇩🇪

Real-life dialogues, 5-word vocabulary packs, der/die/das quizzes and word searches — all explained in English.
From A1 to B1: for beginners, travellers, students and anyone moving to Germany.

📚 Every lesson comes from a structured A1–B1 course (35 units, 3000 words), so you learn in the right order.
🦊 Learn with Tom, Lena and Fenek the fox — one minute a day is enough to start speaking.

New Shorts every day. Subscribe and turn on notifications 🔔
Tell us in the comments which topic you want next!"""

KEYWORDS = ('"learn german" german "german lesson" "german for beginners" "german vocabulary" "der die das" '
            '"german a1" "german a2" "german b1" "speak german" "german grammar" "german conversation" deutsch '
            '"german with fenek"')

# format anahtarı (fenek/episodes.py ep['format']) -> (liste adı, açıklama)
PLAYLISTS = {
    'sahne': ('German Conversations 🗣️ (A1–B1)', 'Short real-life German dialogues with English subtitles.'),
    'kelime': ('German Vocabulary: 5 Words a Day 📚', 'Five useful German words per video, grouped by topic.'),
    'quiz': ('German Quiz: Der, Die or Das? 🧠', 'Test yourself: articles and vocabulary in 3 quick questions.'),
    'av': ('German Word Search 🔍', 'Find 5 hidden German words in 10 seconds.'),
    'hata': ('Common German Mistakes ⚠️', 'Typical mistakes English speakers make in German, and how to fix them.'),
}
SECTIONS = ['kelime', 'sahne', 'quiz', 'av']


def step(name, fn):
    try:
        fn(); print(f'✓ {name}', flush=True)
    except Exception as e:  # noqa: BLE001 — bir adım düşerse diğerleri devam etsin
        print(f'✗ {name}: {str(e)[:300]}', flush=True)


def main():
    creds = Credentials(None, refresh_token=os.environ['YT_REFRESH_TOKEN'], client_id=os.environ['YT_CLIENT_ID'],
                        client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)
    ch = yt.channels().list(part='id,snippet,brandingSettings', mine=True).execute()['items'][0]
    cid = ch['id']
    print(f"Kanal: {ch['snippet']['title']} ({cid})", flush=True)

    def branding():
        res = yt.channelBanners().insert(
            media_body=MediaFileUpload(str(CH / 'banner_2560x1440.png'), mimetype='image/png')).execute()
        bs = ch.get('brandingSettings', {})
        bs.setdefault('channel', {}).update({'description': DESC, 'keywords': KEYWORDS, 'country': 'TR',
                                             'defaultLanguage': 'en'})
        bs.setdefault('image', {})['bannerExternalUrl'] = res['url']
        yt.channels().update(part='brandingSettings', body={'id': cid, 'brandingSettings': bs}).execute()
    step('açıklama, anahtar kelimeler, dil (en), banner', branding)
    step('çocuklara yönelik değil', lambda: yt.channels().update(part='status', body={
        'id': cid, 'status': {'selfDeclaredMadeForKids': False}}).execute())

    def watermark():
        b = 'fenekBoundary'
        meta = json.dumps({'timing': {'type': 'offsetFromStart', 'offsetMs': 0},
                           'position': {'type': 'corner', 'cornerPosition': 'topRight'}})
        data = (f'--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n--{b}\r\n'
                'Content-Type: image/png\r\n\r\n').encode() + (CH / 'watermark_150.png').read_bytes() + f'\r\n--{b}--\r\n'.encode()
        r = AuthorizedSession(creds).post(
            f'https://www.googleapis.com/upload/youtube/v3/watermarks/set?channelId={cid}&uploadType=multipart',
            data=data, headers={'Content-Type': f'multipart/related; boundary={b}'})
        if r.status_code >= 300:
            raise RuntimeError(f'{r.status_code} {r.text[:200]}')
    step('filigran (abone ol)', watermark)

    existing = {p['snippet']['title']: p['id'] for p in
                yt.playlists().list(part='snippet', mine=True, maxResults=50).execute().get('items', [])}
    ids = json.loads(PLAYLISTS_FILE.read_text()) if PLAYLISTS_FILE.exists() else {}
    for key, (title, desc) in PLAYLISTS.items():
        if key in ids:
            continue
        if title in existing:
            ids[key] = existing[title]; continue
        p = yt.playlists().insert(part='snippet,status', body={
            'snippet': {'title': title, 'description': desc + '\n\nNew German Shorts every day. #learngerman',
                        'defaultLanguage': 'en'}, 'status': {'privacyStatus': 'public'}}).execute()
        ids[key] = p['id']; print(f'✓ oynatma listesi: {title}', flush=True)
    PLAYLISTS_FILE.write_text(json.dumps(ids, indent=2) + '\n')

    if not ids.get('_sections_done'):
        wanted = [('recentUploads', ())] + [('singlePlaylist', (ids[k],)) for k in SECTIONS if k in ids]
        for pos, (stype, pls) in enumerate(wanted):
            body = {'snippet': {'type': stype, 'position': pos}}
            if pls:
                body['contentDetails'] = {'playlists': list(pls)}
            step(f'ana sayfa bölümü {stype}', lambda: yt.channelSections().insert(
                part='snippet,contentDetails', body=body).execute())
        ids['_sections_done'] = True
        PLAYLISTS_FILE.write_text(json.dumps(ids, indent=2) + '\n')
    print('Profil resmi: Studio → Özelleştirme → Marka → channel/profile_1080.png (API ile değiştirilemiyor)')


if __name__ == '__main__':
    sys.exit(main())
