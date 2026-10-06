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
DESC = ("Jeden Tag kurze Englisch-Videos! 🇬🇧\n"
        "Vokabeln, Alltagsdialoge, Quiz und Wortsuche — alles mit deutscher Übersetzung.\n"
        "Von A1 bis B1: für Anfänger, für die Schule, für Reisen und für den Beruf.\n"
        "Lerne mit Max, Lily und unserem Fuchs jeden Tag ein paar Minuten Englisch. Folge jetzt! 🔔")
KEYWORDS = ('englisch "englisch lernen" "englisch für anfänger" "englisch vokabeln" "learn english" '
            '"englisch a1" "englisch a2" "englisch b1" "englisch sprechen" englischkurs')


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
