"""
Module B — TTS + Pedagogical Materials
========================================
Source: Cahier des charges, Section B — Production automatique associée au discours

Responsible: Person 4

For every generated speech, this module produces:
  B1  Audio (TTS) with configurable voice and rate
  B2  Accent variability (AR: Lebanese, Gulf, Egyptian; FR: Paris, Canadian; EN: US, UK, AU)
  B3  Full text script
  B4  Key terms list
  B5  Preparatory context / mind map (text-based)
  B6  Comprehension questions
  B7  Flashcards (term → definition, term → equivalent)
  B8  Thematic summary
  B9  MCQ (multiple-choice questions)
  B10 Key concepts identification
  B11 Editable trilingual glossary AR-FR-EN (downloadable)
  B12 Sight translation scroller interface (served by frontend)

Endpoints:
  POST /api/module-b/tts             — convert text to speech audio
  POST /api/module-b/materials       — generate all pedagogical materials for a speech
  GET  /api/module-b/audio/<filename> — serve generated audio file
"""
import os
import asyncio
import uuid
import json
import re
import io
from flask import Blueprint, request, jsonify, send_file
from config import TTS_VOICES, DEFAULT_VOICE, AUDIO_OUTPUT_FOLDER, PRIMARY_LLM_MODEL

module_b_bp = Blueprint('module_b', __name__)


# ── TTS ─────────────────────────────────────────────────────────────────────

def get_voice(language: str, accent: str = None) -> str:
    """Return the edge-tts voice name for a given language and accent."""
    lang_voices = TTS_VOICES.get(language, TTS_VOICES['en'])
    if accent and accent in lang_voices:
        return lang_voices[accent]
    return DEFAULT_VOICE.get(language, DEFAULT_VOICE['en'])

async def _tts_async(text: str, voice: str, output_path: str, rate: str = '+0%'):
    """Internal async TTS call using edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


_AR_D = r'[0-9٠-٩]'   # Western + Eastern Arabic-Indic digits


def _prepare_arabic_tts_text(text: str) -> str:
    """
    Make numbers read correctly by the Arabic TTS voice (student feedback,
    18 July): edge-tts reads "٨٫٢" / "8.2" as "eight two" — the decimal
    separator must be spoken as the word فاصلة so the listener hears
    "eight POINT two". Thousands separators are removed so grouped numbers
    ("١٬٤٠٠") are read as one value.
    """
    text = str(text or '')
    # Arabic thousands separator ٬ (U+066C) between digits → drop
    text = re.sub(rf'({_AR_D})٬(?={_AR_D})', r'\1', text)
    # Comma/dot as thousands group (separator + exactly 3 digits) → drop separator
    text = re.sub(rf'({_AR_D})[.,](?={_AR_D}{{3}}(?!{_AR_D}))', r'\1', text)
    # Remaining decimal separators (٫ U+066B, Arabic comma ،, dot, comma)
    # between digits → the spoken word فاصلة
    text = re.sub(rf'({_AR_D})\s*[٫،.,]\s*(?={_AR_D})', r'\1 فاصلة ', text)
    return text


def run_tts(text: str, language: str, accent: str = None,
            rate_adjustment: int = 0) -> str:
    """
    Convert text to speech. Returns path to the generated MP3 file.
    rate_adjustment: percentage change from normal speed (-50 to +50)
    """
    if language == 'ar':
        text = _prepare_arabic_tts_text(text)
    voice = get_voice(language, accent)
    rate_str = f'{rate_adjustment:+d}%' if rate_adjustment != 0 else '+0%'
    filename = f'speech_{uuid.uuid4().hex[:8]}.mp3'
    output_path = os.path.join(AUDIO_OUTPUT_FOLDER, filename)
    asyncio.run(_tts_async(text, voice, output_path, rate_str))
    return output_path, filename


@module_b_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Convert a speech script to audio.

    Request body (JSON):
      text             str   the speech text                  required
      language         str   'ar' | 'fr' | 'en'              required
      accent           str   e.g. 'LB', 'EG', 'US', 'GB'    optional
      rate_adjustment  int   -50 (slower) to +50 (faster)    default 0

    Response (JSON):
      audio_url   str   URL to retrieve the audio file
      filename    str   filename for reference
      voice_used  str   the edge-tts voice name
    """
    params = request.get_json()
    if not params or not params.get('text'):
        return jsonify({'error': 'text is required'}), 400

    try:
        path, filename = run_tts(
            text=params['text'],
            language=params.get('language', 'ar'),
            accent=params.get('accent'),
            rate_adjustment=params.get('rate_adjustment', 0)
        )
        return jsonify({
            'audio_url': f'/api/module-b/audio/{filename}',
            'filename': filename,
            'voice_used': get_voice(params.get('language', 'ar'), params.get('accent'))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_b_bp.route('/audio/<filename>')
def serve_audio(filename: str):
    """Serve a generated audio file (basename only — no path traversal)."""
    safe_name = os.path.basename(filename)
    if not safe_name.endswith('.mp3'):
        return jsonify({'error': 'File not found'}), 404
    path = os.path.join(AUDIO_OUTPUT_FOLDER, safe_name)
    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(path, mimetype='audio/mpeg')


# ── Pedagogical materials ────────────────────────────────────────────────────

MATERIALS_PROMPT = """You are a pedagogical materials developer for ETIB (École de Traducteurs et d'Interprètes de Beyrouth, USJ Beirut).

Given the following {lang_name} conference speech on the topic of "{domain}", generate training materials for interpreter trainees.

SPEECH:
{script}

Return ONLY a valid JSON object — no markdown, no code fences, no explanation. Use this exact structure:

{{
  "key_terms": ["term1", "term2", "term3", "term4", "term5"],
  "summary": "[Main Theme]\\n└── Context: brief background\\n└── Pillar 1\\n    ├── Sub-point A\\n    └── Key data point\\n└── Pillar 2\\n    └── Sub-point B",
  "mcq": [
    {{"question": "Question text?", "options": ["A. option1", "B. option2", "C. option3", "D. option4"], "answer": "A"}},
    {{"question": "Question text?", "options": ["A. option1", "B. option2", "C. option3", "D. option4"], "answer": "C"}}
  ],
  "comprehension": ["Open question 1?", "Open question 2?"],
  "glossary": [
    {{"ar": "Arabic term", "fr": "French term", "en": "English term"}},
    {{"ar": "Arabic term", "fr": "French term", "en": "English term"}},
    {{"ar": "Arabic term", "fr": "French term", "en": "English term"}},
    {{"ar": "Arabic term", "fr": "French term", "en": "English term"}},
    {{"ar": "Arabic term", "fr": "French term", "en": "English term"}}
  ]
}}

Rules:
- key_terms: exactly 5 important domain-specific terms from the speech (in the speech language)
- summary: visual text tree — keep it concise, max 10 lines
- mcq: 2 to 3 questions with 4 options each, mark the correct answer letter
- glossary: exactly 5 entries, every entry must have Arabic, French AND English
"""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, stripping markdown code fences if present."""
    text = text.strip()
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence:
        text = fence.group(1).strip()
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > start:
        text = text[start:end]
    return json.loads(text)


@module_b_bp.route('/materials', methods=['POST'])
def generate_materials():
    """
    Generate all pedagogical materials for a given speech script.

    Request body (JSON):
      script     str   the speech text                  required
      language   str   'ar' | 'fr' | 'en'              default 'ar'
      domain     str   speech domain                    default 'general'

    Response (JSON):
      key_terms       list[str]
      summary         str   (mind-map formatted text)
      mcq             list[{question, options, answer}]
      comprehension   list[str]
      glossary        list[{ar, fr, en}]
    """
    data = request.get_json()
    if not data or not data.get('script'):
        return jsonify({'error': 'script is required'}), 400

    script   = data['script']
    language = data.get('language', 'ar')
    domain   = data.get('domain', 'general')

    lang_names = {'ar': 'Arabic', 'fr': 'French', 'en': 'English'}

    try:
        from utils.groq_client import get_groq_client
        client = get_groq_client()

        prompt = MATERIALS_PROMPT.format(
            lang_name=lang_names.get(language, 'English'),
            domain=domain,
            script=script
        )

        response = client.chat.completions.create(
            model=PRIMARY_LLM_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a pedagogical materials developer for interpreter training. '
                        'You always return valid JSON only — no markdown, no extra text.'
                    )
                },
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )

        content = response.choices[0].message.content
        materials = _extract_json(content)
        return jsonify(materials)

    except json.JSONDecodeError as e:
        return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_b_bp.route('/glossary/download', methods=['POST'])
def download_glossary():
    """
    Export a trilingual glossary as a downloadable DOCX file.
    Requirement: Cahier des charges B11 — editable and downloadable.

    Request body (JSON):
      glossary   list[{ar, fr, en}]   required
      domain     str                  used in filename
    """
    data = request.get_json()
    if not data or not data.get('glossary'):
        return jsonify({'error': 'glossary is required'}), 400

    glossary = data['glossary']
    domain   = data.get('domain', 'General')

    try:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        section = doc.sections[0]
        section.left_margin  = Inches(1)
        section.right_margin = Inches(1)

        title = doc.add_heading('ETIB — Trilingual Glossary', level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        sub = doc.add_paragraph(f'Domain: {domain}')
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub.runs[0].italic = True

        doc.add_paragraph()

        table = doc.add_table(rows=1, cols=3)
        table.style = 'Table Grid'

        hdr = table.rows[0].cells
        for cell, label in zip(hdr, ['العربية / Arabic', 'Français / French', 'English']):
            cell.text = label
            run = cell.paragraphs[0].runs[0]
            run.bold = True
            run.font.size = Pt(11)

        for entry in glossary:
            row = table.add_row().cells
            row[0].text = entry.get('ar', '')
            row[1].text = entry.get('fr', '')
            row[2].text = entry.get('en', '')

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', domain)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'glossary_{safe_name}.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Glossary upload / import ─────────────────────────────────────────────────
# Professor bilan (23 July): "Glossaire à éditer avec possibilité de le
# téléverser dans la plateforme pour qu'il soit pris en compte dans la phase
# d'évaluation." The student uploads their own trilingual glossary; it is parsed
# into the standard {term, arabic, french, english, definition} shape and merged
# into the in-app glossary, which already flows into Module D as approved
# terminology.

_GLOSSARY_COLUMN_ALIASES = {
    'term':       ('term', 'terme', 'مصطلح', 'key term', 'source term', 'concept'),
    'arabic':     ('arabic', 'arabe', 'العربية', 'عربي', 'ar', 'arabic term', 'المقابل العربي'),
    'french':     ('french', 'français', 'francais', 'fr', 'الفرنسية', 'terme français'),
    'english':    ('english', 'anglais', 'en', 'الإنجليزية', 'english term'),
    'definition': ('definition', 'définition', 'definitions', 'meaning', 'تعريف', 'def'),
}


def _glossary_field_for_header(header: str) -> str | None:
    """Map an arbitrary column header to a canonical glossary field name."""
    key = str(header or '').strip().casefold()
    for field, aliases in _GLOSSARY_COLUMN_ALIASES.items():
        if key in aliases:
            return field
    return None


def _normalize_uploaded_glossary_rows(rows: list[dict]) -> list[dict]:
    """Keep only real glossary fields; drop rows that carry no content."""
    cleaned = []
    for row in rows:
        entry = {k: str(row.get(k, '') or '').strip() for k in
                 ('term', 'arabic', 'french', 'english', 'definition')}
        # A row needs at least one language equivalent or a term to be useful.
        if entry['term'] or entry['arabic'] or entry['french'] or entry['english']:
            cleaned.append(entry)
    return cleaned


def _parse_glossary_json(data: bytes) -> list[dict]:
    parsed = json.loads(data.decode('utf-8-sig'))
    if isinstance(parsed, dict):
        parsed = parsed.get('glossary', [])
    if not isinstance(parsed, list):
        return []
    rows = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        row = {}
        for header, value in item.items():
            field = _glossary_field_for_header(header)
            if field:
                row[field] = value
        rows.append(row)
    return _normalize_uploaded_glossary_rows(rows)


def _parse_glossary_csv(data: bytes) -> list[dict]:
    import csv
    text = data.decode('utf-8-sig', errors='replace')
    # Sniff the delimiter (comma / semicolon / tab) from the first line.
    first_line = text.splitlines()[0] if text.strip() else ''
    delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
    if '\t' in first_line and first_line.count('\t') >= first_line.count(delimiter):
        delimiter = '\t'
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    table = [r for r in reader if any(cell.strip() for cell in r)]
    if not table:
        return []
    header_map = {i: _glossary_field_for_header(h) for i, h in enumerate(table[0])}
    has_header = any(field for field in header_map.values())
    rows = []
    if has_header:
        for raw in table[1:]:
            row = {}
            for i, cell in enumerate(raw):
                field = header_map.get(i)
                if field:
                    row[field] = cell
            rows.append(row)
    else:
        # No recognizable header — assume columns: term, arabic, french, english, definition
        order = ('term', 'arabic', 'french', 'english', 'definition')
        for raw in table:
            rows.append({order[i]: cell for i, cell in enumerate(raw) if i < len(order)})
    return _normalize_uploaded_glossary_rows(rows)


def _parse_glossary_docx(data: bytes) -> list[dict]:
    from docx import Document
    doc = Document(io.BytesIO(data))
    rows = []
    for table in doc.tables:
        if not table.rows:
            continue
        header_cells = [c.text for c in table.rows[0].cells]
        header_map = {i: _glossary_field_for_header(h) for i, h in enumerate(header_cells)}
        has_header = any(field for field in header_map.values())
        body_rows = table.rows[1:] if has_header else table.rows
        order = ('arabic', 'french', 'english')   # matches the DOCX export column order
        for trow in body_rows:
            cells = [c.text for c in trow.cells]
            row = {}
            if has_header:
                for i, cell in enumerate(cells):
                    field = header_map.get(i)
                    if field:
                        row[field] = cell
            else:
                for i, cell in enumerate(cells):
                    if i < len(order):
                        row[order[i]] = cell
            rows.append(row)
    return _normalize_uploaded_glossary_rows(rows)


def _parse_glossary_txt(data: bytes) -> list[dict]:
    text = data.decode('utf-8-sig', errors='replace')
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        # Accept "term | arabic | french | english | definition" or tab-separated.
        parts = re.split(r'\s*\|\s*|\t', line.strip())
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            continue
        order = ('term', 'arabic', 'french', 'english', 'definition')
        rows.append({order[i]: parts[i] for i in range(min(len(parts), len(order)))})
    return _normalize_uploaded_glossary_rows(rows)


@module_b_bp.route('/glossary/upload', methods=['POST'])
def upload_glossary():
    """
    Parse an uploaded glossary file (CSV, TSV, TXT, DOCX, or JSON) into the
    standard trilingual glossary shape so it can be merged into the in-app
    glossary and used by the evaluation phase. Returns {'glossary': [...]}.
    """
    file = request.files.get('glossary') or request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No glossary file provided'}), 400

    filename = file.filename.lower()
    raw = file.read()
    if not raw:
        return jsonify({'error': 'The uploaded file is empty'}), 400
    if len(raw) > 2 * 1024 * 1024:
        return jsonify({'error': 'Glossary file too large (max 2 MB)'}), 400

    try:
        if filename.endswith('.json'):
            entries = _parse_glossary_json(raw)
        elif filename.endswith(('.csv', '.tsv')):
            entries = _parse_glossary_csv(raw)
        elif filename.endswith('.docx'):
            entries = _parse_glossary_docx(raw)
        elif filename.endswith(('.txt', '.md')):
            entries = _parse_glossary_txt(raw)
        else:
            return jsonify({'error': 'Unsupported file type. Use CSV, TSV, TXT, DOCX, or JSON.'}), 400
    except Exception as e:
        return jsonify({'error': f'Could not read the glossary file: {e}'}), 400

    if not entries:
        return jsonify({'error': 'No glossary terms could be read from the file. '
                                 'Expected columns like Term / Arabic / French / English.'}), 400

    return jsonify({'glossary': entries[:200]})
