"""
TTS Voice Evaluation Script — Person 4
========================================
Run this manually on Day 1. Listen to every output file.
Fill in your ratings in docs/tts_evaluation.md.

Usage:
    cd backend
    python tests/test_tts.py
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../../audio_outputs')

# Fixed test texts — same content, different languages, fair comparison
TEXTS = {
    'ar': (
        'السيدات والسادة، يسعدني أن أرحب بكم في هذا المؤتمر الدولي المعني بتغير المناخ. '
        'إن التحديات التي يواجهها عالمنا اليوم تستوجب تضافر الجهود الدولية '
        'والتزاماً جماعياً بمبادئ التنمية المستدامة. '
        'ونحن هنا اليوم لنؤكد التزامنا بهذه المبادئ.'
    ),
    'fr': (
        "Mesdames et messieurs, c'est avec un grand plaisir que je vous accueille "
        "à cette conférence internationale sur le changement climatique. "
        "Les défis auxquels notre monde fait face aujourd'hui exigent "
        "une coopération internationale renforcée et un engagement collectif."
    ),
    'en': (
        "Ladies and gentlemen, it is my honour to welcome you to this international "
        "conference on climate change. The challenges our world faces today require "
        "strengthened international cooperation and a collective commitment "
        "to the principles of sustainable development."
    )
}

VOICES_TO_TEST = [
    # (language_code, voice_name, output_filename)
    ('ar', 'ar-LB-RamiNeural',    'ar_LB_male'),
    ('ar', 'ar-LB-LaylaNeural',   'ar_LB_female'),
    ('ar', 'ar-SA-ZariyahNeural', 'ar_SA_female'),
    ('ar', 'ar-EG-SalmaNeural',   'ar_EG_female'),
    ('ar', 'ar-EG-ShakirNeural',  'ar_EG_male'),
    ('fr', 'fr-FR-DeniseNeural',  'fr_FR_female'),
    ('fr', 'fr-FR-HenriNeural',   'fr_FR_male'),
    ('en', 'en-US-JennyNeural',   'en_US_female'),
    ('en', 'en-GB-SoniaNeural',   'en_GB_female'),
]


async def generate(lang: str, voice: str, name: str):
    import edge_tts
    path = os.path.join(OUTPUT_DIR, f'tts_{name}.mp3')
    communicate = edge_tts.Communicate(TEXTS[lang], voice)
    await communicate.save(path)
    print(f'  ✓  tts_{name}.mp3')


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print('Generating TTS samples...\n')
    for lang, voice, name in VOICES_TO_TEST:
        print(f'Voice: {voice}')
        try:
            await generate(lang, voice, name)
        except Exception as e:
            print(f'  ✗  ERROR: {e}')
    print(f'\nDone. Files saved to: {OUTPUT_DIR}')
    print('Now listen to each file and fill in docs/tts_evaluation.md')


if __name__ == '__main__':
    asyncio.run(main())
