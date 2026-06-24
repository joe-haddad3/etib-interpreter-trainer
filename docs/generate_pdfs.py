"""
Generate ETIB documentation PDFs.
Run: python docs/generate_pdfs.py
Output: docs/ETIB_User_Guide.pdf  and  docs/ETIB_Technical_Documentation.pdf
"""
from fpdf import FPDF
from datetime import date

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY   = (27,  58, 107)   # primary brand blue
STEEL  = (60,  90, 140)   # section header
ACCENT = (220, 160,  30)  # gold accent line
LIGHT  = (240, 244, 251)  # row fill
GRAY   = (110, 110, 110)  # body secondary
BLACK  = (30,  30,  30)


# ── Base PDF class ────────────────────────────────────────────────────────────
FONT_DIR = r'C:\Windows\Fonts'

class EtibPDF(FPDF):
    def __init__(self, title, subtitle):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.doc_title = title
        self.doc_subtitle = subtitle
        self.set_auto_page_break(auto=True, margin=22)
        self.set_margins(20, 20, 20)
        # Register Calibri as the Unicode font family
        self.add_font('Cal',  '',  f'{FONT_DIR}\\calibri.ttf')
        self.add_font('Cal',  'B', f'{FONT_DIR}\\calibrib.ttf')
        self.add_font('Cal',  'I', f'{FONT_DIR}\\calibrii.ttf')
        self.add_font('Cal',  'BI',f'{FONT_DIR}\\calibriz.ttf')
        # Register Consolas for code blocks (Unicode monospace)
        self.add_font('Mono', '',  f'{FONT_DIR}\\consola.ttf')
        self.add_font('Mono', 'B', f'{FONT_DIR}\\consolab.ttf')

    # ---------- Header / footer ----------

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font('Cal', 'B', 8)
        self.set_text_color(*NAVY)
        self.cell(0, 6, 'ETIB Interpreter Self-Training Platform', align='L')
        self.set_font('Cal', '', 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, self.doc_title, align='R', new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*NAVY)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-16)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(2)
        self.set_font('Cal', '', 8)
        self.set_text_color(*GRAY)
        self.cell(0, 5, f'Page {self.page_no() - 1}', align='C')

    # ---------- Cover page ----------

    def cover(self):
        self.add_page()
        # Top colour band
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 60, 'F')
        # Accent stripe
        self.set_fill_color(*ACCENT)
        self.rect(0, 60, 210, 3, 'F')

        # Logo text block
        self.set_y(14)
        self.set_font('Cal', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'ETIB', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Cal', '', 11)
        self.set_text_color(190, 210, 240)
        self.cell(0, 7, 'Interpreter Self-Training Platform', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Cal', '', 9)
        self.cell(0, 6, 'Ecole de Traducteurs et d\'Interpretes de Beyrouth  |  USJ Beirut',
                  align='C', new_x='LMARGIN', new_y='NEXT')

        # Document title
        self.set_y(82)
        self.set_font('Cal', 'B', 20)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 11, self.doc_title, align='C')
        self.ln(4)
        self.set_font('Cal', '', 12)
        self.set_text_color(*STEEL)
        self.multi_cell(0, 7, self.doc_subtitle, align='C')

        # Divider
        self.ln(14)
        self.set_draw_color(*ACCENT)
        self.set_line_width(1)
        self.line(55, self.get_y(), 155, self.get_y())

        # Working languages
        self.ln(12)
        self.set_font('Cal', 'B', 10)
        self.set_text_color(*GRAY)
        self.cell(0, 6, 'Working languages:  Arabic  |  French  |  English', align='C',
                  new_x='LMARGIN', new_y='NEXT')

        # Bottom info box
        self.set_y(230)
        self.set_fill_color(*LIGHT)
        self.set_draw_color(*STEEL)
        self.set_line_width(0.3)
        self.rect(20, self.get_y(), 170, 38, 'DF')
        self.set_y(self.get_y() + 5)
        self.set_font('Cal', 'B', 9)
        self.set_text_color(*NAVY)
        self.cell(0, 5, 'Final Year Project  -  ESIB, Universite Saint-Joseph', align='C',
                  new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        self.set_font('Cal', '', 9)
        self.set_text_color(*GRAY)
        self.cell(0, 5, 'Supervised by Prof. Lina Sader Feghali and Prof. Wadad Wazen Gergy',
                  align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        self.cell(0, 5, f'Generated  {date.today().strftime("%B %d, %Y")}', align='C')

    # ---------- Typography helpers ----------

    def h1(self, text):
        """Top-level section heading with coloured background."""
        self.ln(6)
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_font('Cal', 'B', 13)
        self.cell(0, 9, f'  {text}', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        self.set_text_color(*BLACK)

    def h2(self, text):
        """Sub-section heading."""
        self.ln(4)
        self.set_font('Cal', 'B', 11)
        self.set_text_color(*STEEL)
        self.cell(0, 7, text, new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 100, self.get_y())
        self.ln(3)
        self.set_text_color(*BLACK)

    def h3(self, text):
        """Third-level heading."""
        self.ln(3)
        self.set_font('Cal', 'B', 10)
        self.set_text_color(*NAVY)
        self.cell(0, 6, text, new_x='LMARGIN', new_y='NEXT')
        self.ln(1)
        self.set_text_color(*BLACK)

    def body(self, text, indent=0):
        """Normal paragraph text."""
        self.set_font('Cal', '', 10)
        self.set_text_color(*BLACK)
        self.set_x(20 + indent)
        self.multi_cell(170 - indent, 5.5, text)
        self.ln(1)

    def bullet(self, text, indent=4):
        """Bullet point."""
        self.set_font('Cal', '', 10)
        self.set_text_color(*BLACK)
        # Bullet symbol
        self.set_x(20 + indent)
        self.set_font('Cal', 'B', 12)
        self.set_text_color(*ACCENT)
        self.cell(5, 5.5, '•')   # bullet char
        self.set_font('Cal', '', 10)
        self.set_text_color(*BLACK)
        self.multi_cell(165 - indent, 5.5, text)

    def sub_bullet(self, text, indent=10):
        """Second-level bullet."""
        self.set_font('Cal', '', 9.5)
        self.set_text_color(*GRAY)
        self.set_x(20 + indent)
        self.cell(5, 5, '-')
        self.multi_cell(160 - indent, 5, text)

    def note(self, text):
        """Highlighted note box."""
        self.ln(2)
        self.set_fill_color(*LIGHT)
        self.set_draw_color(*STEEL)
        self.set_line_width(0.3)
        y = self.get_y()
        # Draw background
        self.set_font('Cal', 'I', 9.5)
        self.set_text_color(*STEEL)
        # Left accent bar
        self.set_fill_color(*NAVY)
        self.rect(20, y, 2, 12, 'F')
        self.set_fill_color(*LIGHT)
        self.rect(22, y, 168, 12, 'F')
        self.set_xy(25, y + 2)
        self.multi_cell(163, 5, text)
        self.ln(2)
        self.set_text_color(*BLACK)

    def code(self, text):
        """Monospace code block."""
        self.ln(1)
        self.set_fill_color(245, 245, 245)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.set_font('Mono', '', 8.5)
        self.set_text_color(50, 50, 50)
        lines = text.strip().split('\n')
        h = len(lines) * 4.8 + 4
        self.rect(20, self.get_y(), 170, h, 'DF')
        self.set_x(23)
        self.set_y(self.get_y() + 2)
        for line in lines:
            self.set_x(23)
            self.cell(165, 4.8, line, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        self.set_text_color(*BLACK)

    def table(self, headers, rows, col_widths=None):
        """Render a simple table."""
        self.ln(2)
        n = len(headers)
        if col_widths is None:
            col_widths = [170 // n] * n

        # Header row
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_font('Cal', 'B', 9)
        self.set_x(20)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, f' {h}', border=0, fill=True)
        self.ln()

        # Data rows
        self.set_font('Cal', '', 9)
        for r_idx, row in enumerate(rows):
            # alternate row fill
            if r_idx % 2 == 0:
                self.set_fill_color(*LIGHT)
            else:
                self.set_fill_color(255, 255, 255)
            self.set_text_color(*BLACK)
            self.set_x(20)
            # calculate row height based on longest cell
            max_lines = 1
            for i, cell in enumerate(row):
                words = str(cell).split()
                chars = 0
                lines = 1
                for w in words:
                    chars += len(w) + 1
                    if chars * 2.2 > col_widths[i] - 2:
                        lines += 1
                        chars = len(w)
                max_lines = max(max_lines, lines)
            row_h = max(6, max_lines * 5)

            for i, cell in enumerate(row):
                x = self.get_x()
                y = self.get_y()
                self.rect(x, y, col_widths[i], row_h, 'F')
                self.set_xy(x + 1, y + 1)
                self.multi_cell(col_widths[i] - 2, 4.8, str(cell))
                self.set_xy(x + col_widths[i], y)
            self.ln(row_h)
        self.ln(3)

    def spacer(self, h=4):
        self.ln(h)


# ═════════════════════════════════════════════════════════════════════════════
#  USER GUIDE
# ═════════════════════════════════════════════════════════════════════════════

def build_user_guide():
    pdf = EtibPDF(
        'User Guide',
        'For Students and Instructors'
    )

    # Cover
    pdf.cover()

    # ── Section 1 ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('1. First-Time Setup — Get Your API Key')
    pdf.body(
        'The platform uses Groq to generate speeches and evaluate your performance. '
        'Groq is free — you just need your own personal key.'
    )

    pdf.h2('Step 1 — Create a free Groq account')
    pdf.bullet('Go to console.groq.com')
    pdf.bullet('Sign up with your email address (free, no credit card needed)')
    pdf.bullet('Once logged in, click API Keys in the left menu')
    pdf.bullet('Click Create API key, give it a name (e.g. "ETIB"), and copy the key')
    pdf.spacer(2)
    pdf.note('Your key starts with gsk_   Keep it private — do not share it with anyone. '
             'If it leaks, delete it on console.groq.com and create a new one.')

    pdf.h2('Step 2 — Save your key in the platform')
    pdf.bullet('Open the ETIB platform and log in to your account')
    pdf.bullet('Click the  gear icon (Settings)  in the top navigation bar')
    pdf.bullet('Paste your key in the field that shows  gsk_...')
    pdf.bullet('Click  Test key  — you should see "Key is valid and working"')
    pdf.bullet('Click  Save key')
    pdf.spacer(2)
    pdf.note(
        'Your key is saved in your browser only. No other student or the server can see it. '
        'Each student uses their own quota from their own free Groq account.'
    )

    # ── Section 2 ────────────────────────────────────────────────────────────
    pdf.h1('2. Create an Account and Log In')
    pdf.bullet('Open the platform in your browser')
    pdf.bullet('Click  Create an account')
    pdf.bullet('Enter your full name, email, and a password (at least 8 characters)')
    pdf.bullet('Select your role: Student, Instructor, or Coordinator')
    pdf.bullet('Click  Create account  — you are logged in automatically')
    pdf.spacer(2)
    pdf.body('Next time, use  Sign in  with your email and password.')

    # ── Section 3 ────────────────────────────────────────────────────────────
    pdf.h1('3. Module A — Generate a Training Speech')
    pdf.body(
        'This is where you create the speech you will interpret. '
        'Click Generate speech in the navigation bar.'
    )

    pdf.h2('Basic generation (topic-only)')
    pdf.bullet('Choose the Speech language (the language the speaker will use: AR, FR, or EN)')
    pdf.bullet('Choose the Target language (the language you will interpret into)')
    pdf.bullet('Type a Topic  (e.g. "climate change", "digital health", "water scarcity")')
    pdf.bullet('Choose a Domain')
    pdf.spacer(2)

    pdf.table(
        ['Setting', 'What it does'],
        [
            ['Speech length', 'Short (~150 words), Medium (~250), Long (~350)'],
            ['Difficulty', 'Beginner, Intermediate, Advanced, Expert'],
            ['Discourse structure', 'Argumentative, Narrative, Descriptive, Mixed'],
            ['Interpretation mode', 'Consecutive, Simultaneous, Sight translation'],
            ['Number density', 'Controls how many figures and statistics appear'],
            ['Hesitations', 'Adds natural fillers (euh, um, ah) to the speech'],
            ['Pressure mode', 'Speed pressure, topic shifts, cognitive load'],
        ],
        col_widths=[55, 115]
    )

    pdf.bullet('Click  Generate speech')
    pdf.body('The speech appears below. A note tells you whether it was grounded in a real UN document.')

    pdf.h2('Document-grounded generation')
    pdf.body(
        'Upload a PDF, Word, or text file as the source. The platform extracts key content '
        'using AI (RAG — Retrieval-Augmented Generation) and builds the speech around it.'
    )
    pdf.bullet('Expand the  Document grounding  section')
    pdf.bullet('Click  Choose file  and upload your document')
    pdf.bullet('Adjust settings as usual, then click  Generate from document')
    pdf.spacer(2)
    pdf.note('Click  Preview retrieved context  to see exactly which passages the AI used from your document before generating.')

    pdf.h2('UN Library')
    pdf.body(
        'Click  UN Library  to search real United Nations speeches and documents. '
        'When you select one, the generated speech will be grounded in actual UN content '
        'and factually verified.'
    )

    # ── Section 4 ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('4. Module B — Listen and Study')
    pdf.body('After generating a speech in Module A, click  Audio & materials  in the navigation bar.')

    pdf.h2('Audio playback')
    pdf.bullet('Choose a  voice accent  (Lebanese Arabic, Gulf Arabic, Parisian French, etc.)')
    pdf.bullet('Adjust the  speech rate  if you want it slower or faster for practice')
    pdf.bullet('Click  Generate audio  — the audio player appears')
    pdf.bullet('Listen to the speech as you would in a booth')

    pdf.h2('Pedagogical materials')
    pdf.body('Click  Generate materials  to get:')
    pdf.table(
        ['Material', 'Description'],
        [
            ['Key terms', '5 important domain-specific terms from the speech'],
            ['Thematic summary', 'A visual tree structure of the main ideas'],
            ['MCQ', '2-3 multiple-choice comprehension questions with answers'],
            ['Open questions', 'Discussion questions about the speech content'],
            ['Trilingual glossary', 'AR / FR / EN equivalents for the key terms'],
        ],
        col_widths=[50, 120]
    )
    pdf.bullet('Click  Download glossary (DOCX)  to save as a Word file you can edit and study offline')

    # ── Section 5 ────────────────────────────────────────────────────────────
    pdf.h1('5. Module C — Record Your Interpretation')
    pdf.bullet('Click  Record & transcribe  in the navigation bar')
    pdf.bullet('Select the language of your interpretation (not the source — the language you are speaking)')
    pdf.bullet('Click the record button and start interpreting')
    pdf.bullet('Click  Stop  when you are done')
    pdf.bullet('Click  Transcribe  — takes 5-15 sec with Groq, up to 2 min with the local fallback')
    pdf.spacer(2)
    pdf.body(
        'The transcript appears with timestamps. For Arabic, the system adds tashkeel '
        '(vowel diacritics) reflecting what you actually pronounced — including case-ending errors. '
        'Low-confidence words are highlighted and may indicate pronunciation issues.'
    )

    # ── Section 6 ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('6. Module D — Get Your Evaluation')
    pdf.body(
        'Click  Evaluation  in the navigation bar. This module compares your recorded '
        'interpretation against the original speech.'
    )

    pdf.h2('Scores (0-100)')
    pdf.table(
        ['Score', 'What it measures'],
        [
            ['Overall', 'Combined performance score'],
            ['Fluency', 'Smooth delivery — fewer hesitations = higher score'],
            ['Coverage', 'How much of the source content you conveyed'],
            ['Numbers', 'Accuracy of numbers, dates, and statistics'],
        ],
        col_widths=[45, 125]
    )

    pdf.h2('Error breakdown')
    pdf.bullet('Hesitations detected (euh, um, ah, ...) — count and positions')
    pdf.bullet('Omissions — content from the source you missed')
    pdf.bullet('Number errors — figures you got wrong or skipped entirely')
    pdf.bullet('Terminology issues — key terms not used in your interpretation')
    pdf.spacer(2)
    pdf.body('You also receive an AI feedback paragraph and, for Arabic, a pronunciation report showing word-by-word confidence scores.')

    pdf.h2('Adaptive recommendations')
    pdf.body(
        'After completing a session, the platform analyses your recent history and recommends '
        'a speech difficulty level, length, and domain suited to your current level. '
        'Go to Module E and click  Apply these settings  to use them next time.'
    )

    # ── Section 7 ────────────────────────────────────────────────────────────
    pdf.h1('7. Module E — Track Your Progress')
    pdf.body('Click  Progress  in the navigation bar to see:')
    pdf.bullet('Latest session — your most recent scores at a glance')
    pdf.bullet('Score trend — chart of your last 10 sessions showing improvement or decline')
    pdf.bullet('Focus areas — skills declining or stable that you should prioritise')
    pdf.bullet('Strengths — areas where you are consistently performing well')
    pdf.bullet('Specific errors — your most frequent recurring mistakes')
    pdf.bullet('Recommendations — difficulty and domain suggestions from the AI')
    pdf.spacer(2)
    pdf.note('Progress is tracked automatically every time you complete a full evaluation in Module D. You do not need to do anything extra.')

    # ── Section 8 ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('8. Tips for Effective Practice')

    pdf.h2('Module A — Speech generation')
    pdf.bullet('Move to  Advanced  difficulty once you consistently score above 75 on Intermediate')
    pdf.bullet('Turn on  Hesitations  to simulate real speaker conditions')
    pdf.bullet('Use  Number density: High  if you struggle with figures — a common weak point')
    pdf.bullet('Try the  UN Library  for authentic content on real UN topics')

    pdf.h2('Module B — Study materials')
    pdf.bullet('Study the key terms before listening — it reduces cognitive load during interpretation')
    pdf.bullet('Read the thematic summary to build a mental map of the speech')
    pdf.bullet('Download and review the glossary the evening before a practice session')

    pdf.h2('Module C — Recording')
    pdf.bullet('For simultaneous: start recording as soon as you hear the first sentence')
    pdf.bullet('For consecutive: take the speech segment by segment if you prefer')
    pdf.bullet('Speak clearly — the ASR model works better with clear articulation')

    pdf.h2('Module D — Evaluation')
    pdf.bullet('Always use full evaluation (with audio) — it gives you the complete picture')
    pdf.bullet('Focus on one score at a time — if fluency is low, prioritise reducing hesitations')
    pdf.bullet('Read the AI feedback paragraph carefully — it identifies patterns across sessions')

    pdf.h2('General')
    pdf.bullet('Practice every day for 20-30 minutes rather than once a week for 2 hours')
    pdf.bullet('After each session, check Focus areas in Module E and choose your next topic accordingly')
    pdf.bullet('The platform tracks everything automatically')

    # ── Section 9 ────────────────────────────────────────────────────────────
    pdf.h1('9. Troubleshooting')

    pdf.h3('"No Groq API key found" error')
    pdf.body('You have not saved your personal API key. Go to the gear icon (Settings), paste your key (gsk_...), test it, and save it. See Section 1.')

    pdf.h3('"Invalid API key" when testing')
    pdf.bullet('Make sure you copied the full key starting with gsk_')
    pdf.bullet('Keys expire if deleted on console.groq.com — create a new one if needed')
    pdf.bullet('Do not add spaces before or after the key')

    pdf.h3('Speech generation is slow')
    pdf.body('Normal generation takes 5-15 seconds. If longer than 30 seconds, your Groq free-tier rate limit may have been reached. Wait 1 minute and try again.')

    pdf.h3('Transcription is very slow (2+ minutes)')
    pdf.body('Your key may have reached the audio limit (2 000 seconds/day). The platform falls back to a local model automatically. Wait until the next day to use Groq Whisper again.')

    pdf.h3('The recording button does not appear')
    pdf.body('Your browser needs microphone permission. Click the microphone icon in the address bar and allow access, then reload the page.')

    pdf.h3('Scores seem too low')
    pdf.body('The platform is calibrated for conference interpreter training standards. A score of 60-70 is solid for a first attempt. Focus on consistency across sessions rather than a single high score.')

    pdf.h3('"No matching UN document was found"')
    pdf.body('The UN Library did not find a document matching your topic. The speech is generated without grounding but includes factual accuracy guidelines. Try a more specific topic or a different language.')

    # ── Quick reference ───────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('Quick Reference')
    pdf.table(
        ['Action', 'Where'],
        [
            ['Add / change your Groq API key', 'Gear icon (Settings) in the navigation bar'],
            ['Generate a speech', 'Module A — Generate speech'],
            ['Listen to the speech', 'Module B — Audio & materials'],
            ['Download the glossary', 'Module B > Generate materials > Download glossary'],
            ['Record your interpretation', 'Module C — Record & transcribe'],
            ['Get your score and feedback', 'Module D — Evaluation'],
            ['See your history and trends', 'Module E — Progress'],
            ['Apply AI-recommended settings', 'Module E > Apply these settings'],
        ],
        col_widths=[90, 80]
    )

    pdf.output('docs/ETIB_User_Guide.pdf')
    print('  Created: docs/ETIB_User_Guide.pdf')


# ═════════════════════════════════════════════════════════════════════════════
#  TECHNICAL DOCUMENTATION
# ═════════════════════════════════════════════════════════════════════════════

def build_technical_doc():
    pdf = EtibPDF(
        'Technical Documentation',
        'Developer Reference — Architecture, Setup, API'
    )

    pdf.cover()

    # ── Overview ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('Project Overview')
    pdf.body(
        'The ETIB Interpreter Self-Training Platform is an AI-powered web application '
        'that lets trainee conference interpreters practice independently. Students generate '
        'realistic training speeches, listen to them via text-to-speech, record their own '
        'interpretation, and receive instant automated feedback — all in one browser session.'
    )

    pdf.table(
        ['Module', 'What it produces'],
        [
            ['A  Speech Generation',
             'Configurable training speech (topic, domain, length, difficulty, hesitations, '
             'number density, discourse structure) grounded in real UN documents when available'],
            ['B  Audio & Materials',
             'Edge-TTS audio with accent/speed control + key terms, thematic summary, MCQ, '
             'comprehension questions, trilingual glossary (AR/FR/EN), downloadable DOCX'],
            ['C  Transcription',
             'Groq Whisper-large-v3 ASR (falls back to local faster-whisper) + '
             'Arabic tashkeel of what the student actually said'],
            ['D  Evaluation',
             'Hesitation count, omission detection, number errors, terminology coverage, '
             'pronunciation alignment, LLM feedback paragraph, adaptive difficulty recommendations'],
            ['E  Progress',
             'Session history, score trend (last 10 sessions), focus areas, strengths, '
             'specific recurring errors'],
        ],
        col_widths=[42, 128]
    )

    # ── Architecture ──────────────────────────────────────────────────────────
    pdf.h1('Architecture')
    pdf.code(
        'Browser (React + Vite)\n'
        '  | fetch() with X-Groq-Api-Key header\n'
        '  v\n'
        'Flask backend  (Python 3.11)\n'
        '  +-- before_request  ->  flask.g.groq_api_key\n'
        '  +-- /api/module-a   ->  LLM speech generation   (llm_service.py -> Groq)\n'
        '  +-- /api/module-b   ->  TTS (edge-tts) + materials (Groq)\n'
        '  +-- /api/module-c   ->  ASR transcription (Groq Whisper / faster-whisper)\n'
        '  +-- /api/module-d   ->  Evaluation + feedback (Groq) + sessions (MongoDB)\n'
        '  +-- /api/library    ->  UN Digital Library search + PDF download\n'
        '  +-- /api/auth       ->  Login / signup / validate-groq-key'
    )
    pdf.note(
        'No server-side Groq key — each student supplies their own free key via the '
        'Settings modal. The key lives only in their browser (localStorage) and is '
        'sent per-request as the X-Groq-Api-Key HTTP header.'
    )

    # ── Tech stack ────────────────────────────────────────────────────────────
    pdf.h1('Tech Stack')
    pdf.table(
        ['Layer', 'Technology'],
        [
            ['Frontend', 'React 18, Vite, plain CSS (no framework)'],
            ['Backend', 'Flask 3, Python 3.11'],
            ['LLM', 'Groq API  —  llama-3.3-70b-versatile  (speech gen, eval, feedback)'],
            ['ASR', 'Groq hosted whisper-large-v3  ->  local faster-whisper fallback'],
            ['TTS', 'edge-tts (Microsoft Azure Neural voices, free)'],
            ['Embeddings', 'paraphrase-multilingual-MiniLM-L12-v2 (sentence-transformers) for RAG'],
            ['Database', 'MongoDB (local) with in-memory fallback for dev'],
            ['UN Library', 'UN Digital Library MARCXML API + curl PDF download'],
        ],
        col_widths=[35, 135]
    )

    # ── Local setup ───────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('Local Setup')

    pdf.h2('Prerequisites')
    pdf.bullet('Python 3.10+')
    pdf.bullet('Node.js 18+')
    pdf.bullet('ffmpeg  (winget install ffmpeg  /  brew install ffmpeg  /  sudo apt install ffmpeg)')
    pdf.bullet('MongoDB  (optional — app runs without it, sessions stored in memory)')

    pdf.h2('1 — Clone and configure')
    pdf.code(
        'git clone https://github.com/chrisswhb/ETIB-Interpreter-Trainer.git\n'
        'cd ETIB-Interpreter-Trainer\n'
        'git checkout joe-main'
    )
    pdf.body('Create  backend/.env :')
    pdf.code(
        'LLM_PROVIDER=groq\n'
        'FLASK_SECRET_KEY=change-me-in-production\n'
        'FLASK_DEBUG=true\n'
        'UPLOAD_FOLDER=./uploads\n'
        'AUDIO_OUTPUT_FOLDER=./audio_outputs\n'
        '# GROQ_API_KEY intentionally omitted — students supply their own key'
    )

    pdf.h2('2 — Backend')
    pdf.code(
        'cd backend\n'
        'python -m venv venv\n'
        'venv\\Scripts\\activate        # Windows\n'
        '# source venv/bin/activate    # macOS / Linux\n'
        'pip install -r requirements.txt\n'
        'python app.py\n'
        '# -> http://127.0.0.1:5000'
    )

    pdf.h2('3 — Frontend')
    pdf.code(
        'cd Frontend\n'
        'npm install\n'
        'npm run dev\n'
        '# -> http://localhost:5173'
    )

    # ── API key model ─────────────────────────────────────────────────────────
    pdf.h1('Per-Student API Key Model')
    pdf.body('The flow for every Groq-backed request:')
    pdf.code(
        '1. Student saves their key in Settings modal\n'
        '   -> localStorage: etib_groq_api_key = "gsk_..."\n'
        '\n'
        '2. Every fetch() in api.js calls groqHeaders()\n'
        '   -> adds X-Groq-Api-Key: gsk_...  to the HTTP request\n'
        '\n'
        '3. Flask before_request hook in app.py reads the header\n'
        '   -> flask.g.groq_api_key = key\n'
        '\n'
        '4. get_groq_client() in backend/utils/groq_client.py\n'
        '   -> reads flask.g.groq_api_key\n'
        '   -> raises RuntimeError if None (no key = no generation)\n'
        '   -> creates Groq(api_key=key) and caches it per key\n'
        '\n'
        '5. Groq call is charged to the student\'s own account'
    )

    pdf.note(
        'To restore the shared server-key approach (one key for all students), '
        'switch to branch:  api-key-commun'
    )

    # ── Groq limits ───────────────────────────────────────────────────────────
    pdf.h1('Groq Free Tier Limits  (as of 2026)')
    pdf.table(
        ['Model', 'Req / min', 'Tokens / min', 'Tokens / day'],
        [
            ['llama-3.3-70b-versatile', '30', '12 000', '100 000'],
            ['whisper-large-v3', '20', '—', '2 000 audio-sec'],
        ],
        col_widths=[80, 30, 35, 25]
    )
    pdf.body(
        'A typical session (generate + transcribe + evaluate) uses approximately '
        '3 000 - 5 000 tokens. The free tier supports roughly 20-30 full sessions per day per student key.'
    )

    # ── Project structure ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('Project Structure')
    pdf.code(
        'ETIB-Interpreter-Trainer/\n'
        '|-- backend/\n'
        '|   |-- app.py                  Flask app, blueprints, CORS, before_request\n'
        '|   |-- config.py               All env vars and constants\n'
        '|   |-- requirements.txt\n'
        '|   |-- modules/\n'
        '|   |   |-- module_a.py         Speech generation (LLM + RAG + UN grounding)\n'
        '|   |   |-- module_b.py         TTS + pedagogical materials\n'
        '|   |   |-- module_c.py         ASR transcription + tashkeel\n'
        '|   |   |-- module_d.py         Evaluation, feedback, sessions, adaptive params\n'
        '|   |   |-- module_library.py   UN Digital Library search + fetch\n'
        '|   |   |-- alignment.py        WhisperX forced alignment + LLM analysis\n'
        '|   |   `-- auth.py             Login, signup, validate-groq-key\n'
        '|   |-- services/\n'
        '|   |   `-- llm_service.py      LLM provider abstraction (Groq / Gemini / local)\n'
        '|   `-- utils/\n'
        '|       `-- groq_client.py      Per-request Groq client factory\n'
        '|-- Frontend/\n'
        '|   |-- src/\n'
        '|   |   |-- App.jsx             All React components + UI strings (EN/AR/FR)\n'
        '|   |   `-- api.js              All fetch helpers with groqHeaders()\n'
        '|   |-- styles/\n'
        '|   |   |-- main.css\n'
        '|   |   `-- rtl.css\n'
        '|   `-- index.html\n'
        '`-- docs/\n'
        '    |-- USER_GUIDE.md\n'
        '    `-- ETIB_User_Guide.pdf'
    )

    # ── Branches ──────────────────────────────────────────────────────────────
    pdf.h1('Branches')
    pdf.table(
        ['Branch', 'Purpose'],
        [
            ['joe-main', 'Main development branch — all features, per-student key'],
            ['api-key-commun', 'Backup: shared server-key approach (one key for all students)'],
            ['kevin-main', "Kevin's contributions (merged into joe-main)"],
        ],
        col_widths=[55, 115]
    )

    # ── Module A technical ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1('Module A — Speech Generation (Technical Notes)')

    pdf.h2('RAG pipeline')
    pdf.body('Used when a source document or UN PDF is provided:')
    pdf.bullet('Source document chunked: 1 800 characters per chunk, 250-character overlap')
    pdf.bullet('Each chunk embedded with  paraphrase-multilingual-MiniLM-L12-v2')
    pdf.bullet('Cosine similarity computed between query and all chunks')
    pdf.bullet('Top-4 chunks injected into the LLM prompt as context')

    pdf.h2('UN grounding')
    pdf.bullet('Searches UN Digital Library MARCXML API (tries 5 results, 3 languages: EN/FR/ES)')
    pdf.bullet('Downloads PDF using curl with browser User-Agent headers (WAF bypass)')
    pdf.bullet('20-second per-PDF timeout, 40-word minimum to count as valid')
    pdf.bullet('Falls back to ungrounded generation with factual accuracy rules if no document found')

    pdf.h2('Arabic specifics')
    pdf.bullet('All digit sequences converted to Eastern Arabic-Indic numerals (0-9 -> Eastern form)')
    pdf.bullet('Prompt instructs LLM to use correct Arabic numeral forms')

    pdf.h2('Key endpoint')
    pdf.code('POST /api/module-a/generate\nPOST /api/module-a/from-document\nPOST /api/module-a/retrieve-document-context')

    # ── Module C technical ────────────────────────────────────────────────────
    pdf.h1('Module C — ASR Transcription (Technical Notes)')
    pdf.bullet('Primary: Groq hosted whisper-large-v3 (~3 seconds per recording)')
    pdf.bullet('Fallback: local faster-whisper (medium model, ~1-3 min on CPU)')
    pdf.bullet('Disfluency priming prompts per language to preserve hesitation markers')
    pdf.bullet('Arabic tashkeel added post-transcription: reflects what student actually said, including errors')
    pdf.bullet('WhisperX forced alignment available if installed: word-level confidence scores')

    pdf.h2('Key endpoint')
    pdf.code('POST /api/module-c/transcribe\nPOST /api/module-c/align\nGET  /api/module-c/status')

    # ── Module D technical ────────────────────────────────────────────────────
    pdf.h1('Module D — Evaluation (Technical Notes)')

    pdf.h2('Error detection')
    pdf.bullet('Hesitations: regex matching per language (euh, um, ah, yani, ...)')
    pdf.bullet('Number errors: number token comparison between source and transcript')
    pdf.bullet('Omissions: silence gaps > 500 ms in audio flagged as possible omissions')
    pdf.bullet('Terminology: key terms from source checked for presence in transcript')

    pdf.h2('Adaptive parameters')
    pdf.bullet('Recomputed after each session from score history')
    pdf.bullet('Tracks problems_to_work_on and top_errors across sessions')
    pdf.bullet('Recommends difficulty / length / domain for next session')

    pdf.h2('Session storage')
    pdf.bullet('Stored in MongoDB collection: etib_interpreter_trainer.sessions')
    pdf.bullet('Falls back to in-memory dict if MongoDB is unavailable')
    pdf.bullet('Sessions keyed by user_id (or "anonymous" if not authenticated)')

    pdf.h2('Key endpoints')
    pdf.code(
        'POST /api/module-d/full-evaluation\n'
        'POST /api/module-d/evaluate\n'
        'POST /api/module-d/feedback\n'
        'GET  /api/module-d/sessions\n'
        'GET  /api/module-d/adaptive-params'
    )

    # ── Auth endpoints ────────────────────────────────────────────────────────
    pdf.h1('Authentication Endpoints')
    pdf.table(
        ['Endpoint', 'Method', 'Description'],
        [
            ['POST /api/auth/signup', 'POST', 'Create a new account'],
            ['POST /api/auth/login', 'POST', 'Log in with email + password'],
            ['GET  /api/auth/me', 'GET', 'Check current session'],
            ['POST /api/auth/logout', 'POST', 'End the session'],
            ['POST /api/auth/validate-groq-key', 'POST', 'Test a Groq API key (live call)'],
        ],
        col_widths=[75, 20, 75]
    )
    pdf.note(
        'Session uses Flask server-side sessions (cookie). '
        'MongoDB stores user accounts when available; in-memory dict otherwise.'
    )

    pdf.output('docs/ETIB_Technical_Documentation.pdf')
    print('  Created: docs/ETIB_Technical_Documentation.pdf')


if __name__ == '__main__':
    print('Generating PDFs...')
    build_user_guide()
    build_technical_doc()
    print('Done.')
