"""Kanalı özelleştir (bir kez, GitHub Actions'tan): açıklama, anahtar kelimeler, ülke, dil ve kapak görseli.
Profil resmi YouTube API ile değiştirilemez: Studio → Özelleştirme → Markalama'dan channel/profil_fenek_1080.png yüklenir.
    python tools/channel_setup.py
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
DESC = ("Learn German with short videos every day! 🇩🇪\n"
        "Vocabulary, real-life dialogues, der/die/das quizzes and word searches — all explained in English.\n"
        "From A1 to B1: for beginners, travellers, students and anyone moving to Germany.\n"
        "Learn a few minutes of German every day with Tom, Lena and our fox. Follow now! 🔔")
KEYWORDS = ('"learn german" german "german lesson" "german for beginners" "german vocabulary" "der die das" '
            '"german a1" "german a2" "german b1" "speak german" deutsch')


def main():
    creds = Credentials(None, refresh_token=os.environ['YT_REFRESH_TOKEN'], client_id=os.environ['YT_CLIENT_ID'],
                        client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)
    ch = yt.channels().list(part='id,snippet,brandingSettings', mine=True).execute()['items'][0]
    print(f"Kanal: {ch['snippet']['title']} ({ch['id']})", flush=True)

    banner = ROOT / 'channel' / 'kapak_fenek_2560x1440.png'
    res = yt.channelBanners().insert(media_body=MediaFileUpload(str(banner), mimetype='image/png')).execute()
    print('kapak yüklendi', flush=True)

    bs = ch.get('brandingSettings', {})
    bs.setdefault('channel', {}).update({'description': DESC, 'keywords': KEYWORDS, 'country': 'TR', 'defaultLanguage': 'tr'})
    bs.setdefault('image', {})['bannerExternalUrl'] = res['url']
    yt.channels().update(part='brandingSettings', body={'id': ch['id'], 'brandingSettings': bs}).execute()
    print('açıklama, anahtar kelimeler, ülke (TR), dil (tr) ve kapak ayarlandı ✓', flush=True)
    print('Profil resmi: YouTube Studio → Özelleştirme → Markalama → channel/profil_fenek_1080.png (API ile değiştirilemiyor)')


if __name__ == '__main__':
    sys.exit(main())
