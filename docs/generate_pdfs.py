"""
Generate ETIB documentation PDFs.
Run: python docs/generate_pdfs.py
Output: docs/ETIB_User_Guide.pdf  and  docs/ETIB_Technical_Documentation.pdf
"""
from fpdf import FPDF
from datetime import date

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY   = (27,  58, 107)
STEEL  = (60,  90, 140)
ACCENT = (220, 160,  30)
LIGHT  = (240, 244, 251)
GRAY   = (110, 110, 110)
BLACK  = (30,  30,  30)

FONT_DIR = r'C:\Windows\Fonts'
PAGE_H   = 297   # A4 height mm
MARGIN   = 20
BOTTOM   = 22    # auto-page-break margin
CONTENT_W = 170  # usable width


# ── Base PDF class ─────────────────────────────────────────────────────────────
class EtibPDF(FPDF):
    def __init__(self, title, subtitle):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.doc_title  = title
        self.doc_subtitle = subtitle
        self.set_auto_page_break(auto=True, margin=BOTTOM)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.add_font('Cal',  '',   f'{FONT_DIR}\\calibri.ttf')
        self.add_font('Cal',  'B',  f'{FONT_DIR}\\calibrib.ttf')
        self.add_font('Cal',  'I',  f'{FONT_DIR}\\calibrii.ttf')
        self.add_font('Cal',  'BI', f'{FONT_DIR}\\calibriz.ttf')
        self.add_font('Mono', '',   f'{FONT_DIR}\\consola.ttf')
        self.add_font('Mono', 'B',  f'{FONT_DIR}\\consolab.ttf')

    def _usable_bottom(self):
        return PAGE_H - BOTTOM

    def _remaining(self):
        """How many mm remain on the current page."""
        return self._usable_bottom() - self.get_y()

    # ── Header / footer ────────────────────────────────────────────────────────

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font('Cal', 'B', 8)
        self.set_text_color(*NAVY)
        self.cell(85, 6, 'ETIB Interpreter Self-Training Platform', align='L')
        self.set_font('Cal', 'I', 8)
        self.set_text_color(*GRAY)
        self.cell(85, 6, self.doc_title, align='R', new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*NAVY)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_H - MARGIN - 27, self.get_y())
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-16)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.line(MARGIN, self.get_y(), PAGE_H - MARGIN - 27, self.get_y())
        self.ln(2)
        self.set_font('Cal', '', 8)
        self.set_text_color(*GRAY)
        self.cell(0, 5, f'Page {self.page_no() - 1}', align='C')

    # ── Cover ──────────────────────────────────────────────────────────────────

    def cover(self):
        self.add_page()

        # Navy header band
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 65, 'F')
        self.set_fill_color(*ACCENT)
        self.rect(0, 65, 210, 3, 'F')

        # Header text (white on navy)
        self.set_y(16)
        self.set_font('Cal', 'B', 26)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'ETIB', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Cal', '', 13)
        self.set_text_color(190, 210, 245)
        self.cell(0, 7, 'Interpreter Self-Training Platform', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Cal', 'I', 9)
        self.cell(0, 7,
                  "Ecole de Traducteurs et d'Interpretes de Beyrouth  |  USJ Beirut",
                  align='C', new_x='LMARGIN', new_y='NEXT')

        # Document title block
        self.set_y(85)
        self.set_font('Cal', 'B', 22)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 11, self.doc_title, align='C')
        self.ln(3)
        self.set_font('Cal', 'I', 12)
        self.set_text_color(*STEEL)
        self.multi_cell(0, 7, self.doc_subtitle, align='C')

        # Gold divider
        self.ln(12)
        self.set_draw_color(*ACCENT)
        self.set_line_width(1.2)
        self.line(55, self.get_y(), 155, self.get_y())

        # Languages
        self.ln(10)
        self.set_font('Cal', 'B', 10)
        self.set_text_color(*GRAY)
        self.cell(0, 6, 'Working languages:  Arabic  |  French  |  English',
                  align='C', new_x='LMARGIN', new_y='NEXT')

        # Bottom info box
        self.set_y(236)
        self.set_fill_color(*LIGHT)
        self.set_draw_color(*STEEL)
        self.set_line_width(0.3)
        self.set_fill_color(*NAVY)
        self.rect(20, self.get_y(), 3, 40, 'F')
        self.set_fill_color(*LIGHT)
        self.rect(23, self.get_y(), 167, 40, 'F')
        self.set_y(self.get_y() + 7)
        self.set_font('Cal', 'B', 10)
        self.set_text_color(*NAVY)
        self.cell(0, 6, 'Final Year Project  -  ESIB, Universite Saint-Joseph', align='C',
                  new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        self.set_font('Cal', 'I', 9)
        self.set_text_color(*GRAY)
        self.cell(0, 5,
                  'Supervised by Prof. Lina Sader Feghali and Prof. Wadad Wazen Gergy',
                  align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        self.set_font('Cal', '', 9)
        self.cell(0, 5, f'Generated  {date.today().strftime("%B %d, %Y")}', align='C')

    # ── Typography ─────────────────────────────────────────────────────────────

    def h1(self, text):
        self.ln(5)
        if self._remaining() < 20:
            self.add_page()
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_font('Cal', 'B', 13)
        self.cell(CONTENT_W, 9, f'   {text}', fill=True,
                  new_x='LMARGIN', new_y='NEXT')
        self.ln(3)
        self.set_text_color(*BLACK)

    def h2(self, text):
        self.ln(4)
        if self._remaining() < 14:
            self.add_page()
        self.set_font('Cal', 'B', 11)
        self.set_text_color(*STEEL)
        self.cell(0, 7, text, new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.line(MARGIN, self.get_y(), MARGIN + 80, self.get_y())
        self.ln(3)
        self.set_text_color(*BLACK)

    def h3(self, text):
        self.ln(3)
        if self._remaining() < 12:
            self.add_page()
        self.set_font('Cal', 'B', 10)
        self.set_text_color(*NAVY)
        self.cell(0, 6, text, new_x='LMARGIN', new_y='NEXT')
        self.ln(1)
        self.set_text_color(*BLACK)

    def body(self, text, indent=0):
        self.set_font('Cal', '', 10)
        self.set_text_color(*BLACK)
        self.set_x(MARGIN + indent)
        self.multi_cell(CONTENT_W - indent, 5.5, text)
        self.ln(1)

    def bullet(self, text, indent=4):
        self.set_font('Cal', 'B', 11)
        self.set_text_color(*ACCENT)
        self.set_x(MARGIN + indent)
        self.cell(5, 5.5, '•')
        self.set_font('Cal', '', 10)
        self.set_text_color(*BLACK)
        self.multi_cell(CONTENT_W - indent - 5, 5.5, text)

    def sub_bullet(self, text, indent=10):
        self.set_font('Cal', '', 9.5)
        self.set_text_color(*GRAY)
        self.set_x(MARGIN + indent)
        self.cell(5, 5, '-')
        self.multi_cell(CONTENT_W - indent - 5, 5, text)

    def note(self, text):
        self.ln(2)
        # Estimate height: ~5mm per line, ~60 chars per line for 163mm width
        lines_est = max(1, len(text) // 70 + 1)
        box_h = lines_est * 5.5 + 6
        if self._remaining() < box_h + 4:
            self.add_page()
        y0 = self.get_y()
        # Left accent bar
        self.set_fill_color(*NAVY)
        self.rect(MARGIN, y0, 2.5, box_h, 'F')
        # Light background
        self.set_fill_color(*LIGHT)
        self.rect(MARGIN + 2.5, y0, CONTENT_W - 2.5, box_h, 'F')
        # Text
        self.set_xy(MARGIN + 6, y0 + 3)
        self.set_font('Cal', 'I', 9.5)
        self.set_text_color(*STEEL)
        self.multi_cell(CONTENT_W - 8, 5.5, text)
        # Ensure y is past the box
        if self.get_y() < y0 + box_h:
            self.set_y(y0 + box_h)
        self.ln(3)
        self.set_text_color(*BLACK)

    def code(self, text):
        """Monospace code block — handles page breaks by splitting lines."""
        lines = text.strip().split('\n')
        line_h = 4.8
        pad    = 3    # vertical padding inside box

        # Split into chunks that fit on a single page
        max_lines_per_page = int((self._usable_bottom() - MARGIN - 10) / line_h)
        chunks = []
        chunk  = []
        for line in lines:
            chunk.append(line)
            if len(chunk) >= max_lines_per_page:
                chunks.append(chunk)
                chunk = []
        if chunk:
            chunks.append(chunk)

        for c_idx, chunk in enumerate(chunks):
            box_h = len(chunk) * line_h + pad * 2
            if self._remaining() < box_h + 4:
                self.add_page()
            self.ln(1)
            y0 = self.get_y()
            # Background rect
            self.set_fill_color(245, 245, 245)
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.2)
            self.rect(MARGIN, y0, CONTENT_W, box_h, 'DF')
            # Left colour bar
            self.set_fill_color(*STEEL)
            self.rect(MARGIN, y0, 2.5, box_h, 'F')
            # Text
            self.set_font('Mono', '', 8.2)
            self.set_text_color(40, 40, 40)
            self.set_y(y0 + pad)
            for line in chunk:
                self.set_x(MARGIN + 5)
                self.cell(CONTENT_W - 6, line_h, line,
                          new_x='LMARGIN', new_y='NEXT')
            self.ln(2)
        self.set_text_color(*BLACK)

    def table(self, headers, rows, col_widths=None):
        """Table with page-break awareness."""
        n = len(headers)
        if col_widths is None:
            col_widths = [CONTENT_W // n] * n

        row_h = 7  # fixed row height for simplicity

        # Check space for header + at least one row
        if self._remaining() < row_h * 2 + 4:
            self.add_page()
        self.ln(2)

        # Header row
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_font('Cal', 'B', 9)
        self.set_x(MARGIN)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], row_h, f'  {h}', fill=True)
        self.ln(row_h)

        # Data rows — use multi_cell approach but keep all cells on same baseline
        self.set_font('Cal', '', 9)
        for r_idx, row in enumerate(rows):
            # Measure height needed for tallest cell
            self.set_font('Cal', '', 9)
            max_h = row_h
            for i, cell_text in enumerate(row):
                # Estimate lines: ~6 chars per 10mm at size 9
                chars_per_line = max(1, int((col_widths[i] - 4) / 1.9))
                text_lines = 1
                for part in str(cell_text).split('\n'):
                    words = part.split()
                    line_chars = 0
                    for w in words:
                        if line_chars + len(w) + 1 > chars_per_line:
                            text_lines += 1
                            line_chars = len(w)
                        else:
                            line_chars += len(w) + 1
                cell_h = text_lines * 5.2 + 3
                max_h  = max(max_h, cell_h)

            # Page break before row if needed
            if self._remaining() < max_h + 2:
                self.add_page()
                # Repeat header
                self.set_fill_color(*NAVY)
                self.set_text_color(255, 255, 255)
                self.set_font('Cal', 'B', 9)
                self.set_x(MARGIN)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], row_h, f'  {h}', fill=True)
                self.ln(row_h)
                self.set_font('Cal', '', 9)

            row_y = self.get_y()

            # Row background
            if r_idx % 2 == 0:
                self.set_fill_color(*LIGHT)
            else:
                self.set_fill_color(255, 255, 255)

            # Draw background for entire row first
            self.set_x(MARGIN)
            for i in range(n):
                self.cell(col_widths[i], max_h, '', fill=True)
            self.ln(0)

            # Write text in each cell
            self.set_text_color(*BLACK)
            for i, cell_text in enumerate(row):
                cell_x = MARGIN + sum(col_widths[:i])
                self.set_xy(cell_x + 1.5, row_y + 1)
                self.multi_cell(col_widths[i] - 3, 5.2, str(cell_text))
                # Move to next column (reset to row_y)
                self.set_xy(cell_x + col_widths[i], row_y)

            self.set_y(row_y + max_h)

        self.ln(3)

    def spacer(self, h=4):
        self.ln(h)


# ═══════════════════════════════════════════════════════════════════════════════
#  USER GUIDE
# ═══════════════════════════════════════════════════════════════════════════════

def build_user_guide():
    pdf = EtibPDF('User Guide', 'For Students and Instructors')
    pdf.cover()

    # Section 1
    pdf.add_page()
    pdf.h1('1.  First-Time Setup — Get Your API Key')
    pdf.body(
        'The platform uses Groq to generate speeches and evaluate your performance. '
        'Groq is completely free — you just need your own personal key.'
    )
    pdf.h2('Step 1 — Create a free Groq account')
    pdf.bullet('Go to  console.groq.com')
    pdf.bullet('Sign up with your email address (free, no credit card required)')
    pdf.bullet('Once logged in, click  API Keys  in the left menu')
    pdf.bullet('Click  Create API key, give it a name such as "ETIB", and copy the key — it starts with  gsk_')
    pdf.spacer(2)
    pdf.note(
        'Keep your key private — do not share it with anyone. '
        'If it leaks, delete it on console.groq.com and create a new one.'
    )
    pdf.h2('Step 2 — Save your key in the platform')
    pdf.bullet('Open the ETIB platform and log in')
    pdf.bullet('Click the gear icon (Settings) in the top navigation bar')
    pdf.bullet('Paste your key into the field that shows  gsk_...')
    pdf.bullet('Click  Test key  — you should see "Key is valid and working"')
    pdf.bullet('Click  Save key')
    pdf.spacer(2)
    pdf.note(
        'Your key is saved only in your browser. No other student or the server can see it. '
        'Each student uses their own quota from their own free Groq account.'
    )

    # Section 2
    pdf.h1('2.  Create an Account and Log In')
    pdf.bullet('Open the platform in your browser')
    pdf.bullet('Click  Create an account')
    pdf.bullet('Enter your full name, email, and a password (at least 8 characters)')
    pdf.bullet('Select your role: Student, Instructor, or Coordinator')
    pdf.bullet('Click  Create account — you are logged in automatically')
    pdf.spacer(2)
    pdf.body('Next time, use  Sign in  with your email and password.')

    # Section 3
    pdf.add_page()
    pdf.h1('3.  Module A — Generate a Training Speech')
    pdf.body('Click  Generate speech  in the navigation bar.')
    pdf.h2('Basic generation (topic-only)')
    pdf.bullet('Choose the  Speech language  (AR, FR, or EN — the speaker\'s language)')
    pdf.bullet('Choose the  Target language  (the language you will interpret into)')
    pdf.bullet('Type a  Topic  (e.g. "climate change", "digital health", "water scarcity")')
    pdf.bullet('Choose a  Domain  and adjust the settings below:')
    pdf.spacer(2)
    pdf.table(
        ['Setting', 'What it does'],
        [
            ['Speech length',       'Short (~150 words), Medium (~250), Long (~350)'],
            ['Difficulty',          'Beginner, Intermediate, Advanced, Expert'],
            ['Discourse structure', 'Argumentative, Narrative, Descriptive, Mixed'],
            ['Interpretation mode', 'Consecutive, Simultaneous, Sight translation'],
            ['Number density',      'Controls how many figures and statistics appear'],
            ['Hesitations',         'Adds natural fillers (euh, um, ah) to the speech'],
            ['Pressure mode',       'Speed pressure, topic shifts, cognitive load'],
        ],
        col_widths=[55, 115]
    )
    pdf.bullet('Click  Generate speech')
    pdf.body('The speech appears below. A note tells you whether it was grounded in a real UN document.')

    pdf.h2('Document-grounded generation')
    pdf.body(
        'Upload a PDF, Word, or text file as the source. The platform extracts key content '
        'using AI (RAG) and builds the speech around it.'
    )
    pdf.bullet('Expand  Document grounding')
    pdf.bullet('Click  Choose file  and upload your document')
    pdf.bullet('Adjust settings, then click  Generate from document')
    pdf.note('Click  Preview retrieved context  to see exactly which passages the AI used before generating.')

    pdf.h2('UN Library')
    pdf.body(
        'Click  UN Library  to search real UN speeches and documents. '
        'When you select one, the generated speech will be grounded in actual UN content.'
    )

    # Section 4
    pdf.add_page()
    pdf.h1('4.  Module B — Listen and Study')
    pdf.body('After generating a speech in Module A, click  Audio & materials  in the navigation bar.')
    pdf.h2('Audio playback')
    pdf.bullet('Choose a  voice accent  (Lebanese Arabic, Gulf Arabic, Parisian French, etc.)')
    pdf.bullet('Adjust the  speech rate  for practice pace')
    pdf.bullet('Click  Generate audio — the audio player appears')
    pdf.bullet('Listen as you would in a booth')
    pdf.h2('Pedagogical materials')
    pdf.body('Click  Generate materials  to receive:')
    pdf.table(
        ['Material', 'Description'],
        [
            ['Key terms',         '5 important domain-specific terms from the speech'],
            ['Thematic summary',  'A visual tree structure of the main ideas'],
            ['MCQ',               '2-3 multiple-choice comprehension questions with answers'],
            ['Open questions',    'Discussion questions about the speech content'],
            ['Trilingual glossary','AR / FR / EN equivalents for the key terms'],
        ],
        col_widths=[50, 120]
    )
    pdf.bullet('Click  Download glossary (DOCX)  to save the glossary as an editable Word file')

    # Section 5
    pdf.h1('5.  Module C — Record Your Interpretation')
    pdf.bullet('Click  Record & transcribe  in the navigation bar')
    pdf.bullet('Select the language of YOUR interpretation (not the source speech)')
    pdf.bullet('Click the record button and start interpreting')
    pdf.bullet('Click  Stop  when finished')
    pdf.bullet('Click  Transcribe — takes 5-15 seconds with Groq, up to 2 minutes with the local fallback')
    pdf.spacer(2)
    pdf.body(
        'The transcript appears with timestamps. For Arabic, the system adds tashkeel '
        '(vowel diacritics) reflecting what you actually pronounced, including errors. '
        'Low-confidence words are highlighted — these may indicate pronunciation issues.'
    )

    # Section 6
    pdf.add_page()
    pdf.h1('6.  Module D — Get Your Evaluation')
    pdf.body(
        'Click  Evaluation  in the navigation bar. '
        'This module compares your recorded interpretation against the original speech.'
    )
    pdf.h2('Scores  (0 - 100)')
    pdf.table(
        ['Score', 'What it measures'],
        [
            ['Overall',  'Combined performance score'],
            ['Fluency',  'Smooth delivery — fewer hesitations = higher score'],
            ['Coverage', 'How much of the source content you conveyed'],
            ['Numbers',  'Accuracy of numbers, dates, and statistics'],
        ],
        col_widths=[45, 125]
    )
    pdf.h2('Error breakdown')
    pdf.bullet('Hesitations detected  (euh, um, ah, ...) — count and positions')
    pdf.bullet('Omissions — content from the source you missed')
    pdf.bullet('Number errors — figures you got wrong or skipped entirely')
    pdf.bullet('Terminology issues — key terms not used in your interpretation')
    pdf.spacer(2)
    pdf.body(
        'You also receive an AI feedback paragraph. For Arabic, a pronunciation report '
        'shows word-by-word confidence scores and likely tashkeel errors.'
    )
    pdf.h2('Adaptive recommendations')
    pdf.body(
        'After each session the platform analyses your recent history and recommends '
        'a difficulty level, speech length, and domain. '
        'Go to Module E and click  Apply these settings  to use them next time.'
    )

    # Section 7
    pdf.h1('7.  Module E — Track Your Progress')
    pdf.body('Click  Progress  in the navigation bar to see:')
    pdf.bullet('Latest session — your most recent scores at a glance')
    pdf.bullet('Score trend — chart of your last 10 sessions')
    pdf.bullet('Focus areas — skills that are declining or stable and need priority')
    pdf.bullet('Strengths — areas where you are consistently performing well')
    pdf.bullet('Specific errors — your most frequent recurring mistakes')
    pdf.bullet('Recommendations — difficulty and domain suggestions from the AI')
    pdf.spacer(2)
    pdf.note(
        'Progress is tracked automatically every time you complete a full evaluation '
        'in Module D. You do not need to do anything extra.'
    )

    # Section 8
    pdf.add_page()
    pdf.h1('8.  Tips for Effective Practice')
    pdf.h2('Module A — Speech generation')
    pdf.bullet('Move to Advanced difficulty once you score consistently above 75 on Intermediate')
    pdf.bullet('Turn on Hesitations to simulate real speaker conditions')
    pdf.bullet('Use Number density: High if you struggle with figures — a common weak point')
    pdf.bullet('Try the UN Library for authentic content on real UN topics')
    pdf.h2('Module B — Study materials')
    pdf.bullet('Study the key terms before listening to reduce cognitive load')
    pdf.bullet('Read the thematic summary to build a mental map of the speech')
    pdf.bullet('Download the glossary and review it the evening before a practice session')
    pdf.h2('Module C — Recording')
    pdf.bullet('For simultaneous: start recording as soon as you hear the first sentence')
    pdf.bullet('For consecutive: take the speech segment by segment if you prefer')
    pdf.bullet('Speak clearly — the ASR model works better with clear articulation')
    pdf.h2('Module D — Evaluation')
    pdf.bullet('Always use full evaluation with audio — it gives the complete picture')
    pdf.bullet('Focus on one score at a time. If fluency is low, prioritise reducing hesitations')
    pdf.bullet('Read the AI feedback paragraph carefully — it identifies patterns across sessions')
    pdf.h2('General')
    pdf.bullet('Practice 20-30 minutes every day rather than once a week for 2 hours')
    pdf.bullet('After each session, check Focus areas in Module E and choose your next topic accordingly')

    # Section 9
    pdf.add_page()
    pdf.h1('9.  Troubleshooting')
    pdf.h3('"No Groq API key found" error')
    pdf.body('You have not saved your personal API key. Go to the gear icon (Settings), paste your key (gsk_...), test it, and save it. See Section 1 of this guide.')
    pdf.h3('"Invalid API key" when testing')
    pdf.bullet('Make sure you copied the full key — it must start with  gsk_')
    pdf.bullet('Keys expire if deleted on console.groq.com — create a new one if needed')
    pdf.bullet('Do not add spaces before or after the key')
    pdf.h3('Speech generation is slow')
    pdf.body('Normal generation takes 5-15 seconds. If longer than 30 seconds, you may have hit the Groq free-tier rate limit. Wait 1 minute and try again.')
    pdf.h3('Transcription takes 2+ minutes')
    pdf.body('You may have reached the audio limit (2 000 seconds per day). The platform falls back to a local model automatically. Wait until the next day to use Groq Whisper again.')
    pdf.h3('The recording button does not appear')
    pdf.body('Your browser needs microphone permission. Click the microphone icon in the address bar, allow access, then reload the page.')
    pdf.h3('Scores seem too low')
    pdf.body('The platform is calibrated for conference interpreter training standards. A score of 60-70 is solid for a first attempt. Focus on consistency across sessions.')
    pdf.h3('"No matching UN document was found"')
    pdf.body('The UN Library did not find a document matching your topic. The speech is generated without grounding but includes factual accuracy guidelines. Try a more specific topic or a different language.')

    # Quick reference
    pdf.add_page()
    pdf.h1('Quick Reference')
    pdf.table(
        ['Action', 'Where to find it'],
        [
            ['Add or change your Groq API key',  'Gear icon (Settings) in the navigation bar'],
            ['Generate a training speech',        'Module A — Generate speech'],
            ['Listen to the speech / get audio',  'Module B — Audio & materials'],
            ['Download the glossary (DOCX)',       'Module B > Generate materials > Download glossary'],
            ['Record your interpretation',         'Module C — Record & transcribe'],
            ['Get your score and AI feedback',     'Module D — Evaluation'],
            ['See your history and score trend',   'Module E — Progress'],
            ['Apply AI-recommended settings',      'Module E > Apply these settings'],
        ],
        col_widths=[90, 80]
    )

    pdf.output('docs/ETIB_User_Guide.pdf')
    print('  Created: docs/ETIB_User_Guide.pdf')


# ═══════════════════════════════════════════════════════════════════════════════
#  TECHNICAL DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

def build_technical_doc():
    pdf = EtibPDF('Technical Documentation',
                  'Developer Reference — Architecture, Setup & API')
    pdf.cover()

    # Project overview
    pdf.add_page()
    pdf.h1('Project Overview')
    pdf.body(
        'The ETIB Interpreter Self-Training Platform is an AI-powered web application '
        'that lets trainee conference interpreters practice independently. Students generate '
        'realistic training speeches, listen to them via text-to-speech, record their own '
        'interpretation, and receive instant automated feedback — all in one browser session.'
    )
    pdf.spacer(2)
    pdf.table(
        ['Module', 'What it produces'],
        [
            ['A  Speech Generation',
             'Configurable training speech (topic, domain, length, difficulty, hesitations, '
             'number density, discourse structure) grounded in real UN documents when available'],
            ['B  Audio & Materials',
             'Edge-TTS audio with accent/speed + key terms, thematic summary, MCQ, '
             'comprehension questions, trilingual glossary (AR/FR/EN), downloadable DOCX'],
            ['C  Transcription',
             'Groq Whisper-large-v3 ASR (falls back to local faster-whisper) + '
             'Arabic tashkeel reflecting what the student actually said'],
            ['D  Evaluation',
             'Hesitation count, omission detection, number errors, terminology coverage, '
             'pronunciation alignment, LLM feedback paragraph, adaptive recommendations'],
            ['E  Progress',
             'Session history, score trend (last 10 sessions), focus areas, strengths, '
             'specific recurring errors'],
        ],
        col_widths=[44, 126]
    )

    # Architecture
    pdf.add_page()
    pdf.h1('Architecture')
    pdf.code(
        'Browser (React + Vite)\n'
        '  |  fetch() with X-Groq-Api-Key header\n'
        '  v\n'
        'Flask backend  (Python 3.11)\n'
        '  +-- before_request  -->  flask.g.groq_api_key\n'
        '  +-- /api/module-a   -->  LLM speech generation  (llm_service.py -> Groq)\n'
        '  +-- /api/module-b   -->  TTS (edge-tts) + materials (Groq)\n'
        '  +-- /api/module-c   -->  ASR transcription (Groq Whisper / faster-whisper)\n'
        '  +-- /api/module-d   -->  Evaluation + feedback (Groq) + sessions (MongoDB)\n'
        '  +-- /api/library    -->  UN Digital Library search + PDF download\n'
        '  +-- /api/auth       -->  Login / signup / validate-groq-key'
    )
    pdf.spacer(2)
    pdf.note(
        'No server-side Groq key — each student supplies their own free key via the '
        'Settings modal. The key lives only in their browser (localStorage) and is '
        'sent per-request as the X-Groq-Api-Key HTTP header.'
    )

    # Tech stack
    pdf.h1('Tech Stack')
    pdf.table(
        ['Layer', 'Technology'],
        [
            ['Frontend',    'React 18, Vite, plain CSS (no UI framework)'],
            ['Backend',     'Flask 3, Python 3.11'],
            ['LLM',         'Groq API — llama-3.3-70b-versatile (speech gen, eval, feedback)'],
            ['ASR',         'Groq hosted whisper-large-v3 — falls back to local faster-whisper'],
            ['TTS',         'edge-tts (Microsoft Azure Neural voices, free)'],
            ['Embeddings',  'paraphrase-multilingual-MiniLM-L12-v2 (sentence-transformers) for RAG'],
            ['Database',    'MongoDB (local) with in-memory fallback for development'],
            ['UN Library',  'UN Digital Library MARCXML API + curl PDF download (browser UA)'],
        ],
        col_widths=[35, 135]
    )

    # Local setup
    pdf.add_page()
    pdf.h1('Local Setup')
    pdf.h2('Prerequisites')
    pdf.bullet('Python 3.10+')
    pdf.bullet('Node.js 18+')
    pdf.bullet('ffmpeg  (winget install ffmpeg  /  brew install ffmpeg  /  sudo apt install ffmpeg)')
    pdf.bullet('MongoDB — optional (app runs without it; sessions are stored in memory)')

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
        '# GROQ_API_KEY intentionally omitted -- students supply their own key'
    )

    pdf.h2('2 — Backend')
    pdf.code(
        'cd backend\n'
        'python -m venv venv\n'
        'venv\\Scripts\\activate        # Windows\n'
        '# source venv/bin/activate    # macOS / Linux\n'
        'pip install -r requirements.txt\n'
        'python app.py\n'
        '# Server starts at http://127.0.0.1:5000'
    )

    pdf.h2('3 — Frontend')
    pdf.code(
        'cd Frontend\n'
        'npm install\n'
        'npm run dev\n'
        '# Opens at http://localhost:5173'
    )

    # API key model
    pdf.add_page()
    pdf.h1('Per-Student API Key Model')
    pdf.body('Complete flow for every Groq-backed request:')
    pdf.code(
        '1. Student saves key in Settings modal\n'
        '   --> localStorage: etib_groq_api_key = "gsk_..."\n'
        '\n'
        '2. Every fetch() in api.js calls groqHeaders()\n'
        '   --> adds X-Groq-Api-Key: gsk_...  header to the HTTP request\n'
        '\n'
        '3. Flask before_request hook in app.py reads the header\n'
        '   --> flask.g.groq_api_key = key  (lives only for this request)\n'
        '\n'
        '4. get_groq_client() in backend/utils/groq_client.py\n'
        '   --> reads flask.g.groq_api_key\n'
        '   --> raises RuntimeError if None  (no key = no generation)\n'
        '   --> creates Groq(api_key=key) and caches it per key value\n'
        '\n'
        '5. Groq API call is charged to the student\'s own account'
    )
    pdf.note(
        'To restore the shared server-key approach (one key for all students), '
        'switch to the  api-key-commun  branch.'
    )

    # Groq limits
    pdf.h1('Groq Free Tier Limits  (as of 2026)')
    pdf.table(
        ['Model', 'Req / min', 'Tokens / min', 'Tokens / day'],
        [
            ['llama-3.3-70b-versatile', '30', '12 000', '100 000'],
            ['whisper-large-v3',        '20', '—',       '2 000 audio-sec'],
        ],
        col_widths=[82, 28, 35, 25]
    )
    pdf.body(
        'A typical session (generate + transcribe + evaluate) uses approximately '
        '3 000-5 000 tokens. The free tier supports roughly 20-30 full sessions '
        'per day per student key.'
    )

    # Project structure
    pdf.add_page()
    pdf.h1('Project Structure')
    pdf.code(
        'ETIB-Interpreter-Trainer/\n'
        '|-- backend/\n'
        '|   |-- app.py               Flask app, blueprints, CORS, before_request hook\n'
        '|   |-- config.py            All environment variables and constants\n'
        '|   |-- requirements.txt\n'
        '|   |-- modules/\n'
        '|   |   |-- module_a.py      Speech generation (LLM + RAG + UN grounding)\n'
        '|   |   |-- module_b.py      TTS + pedagogical materials\n'
        '|   |   |-- module_c.py      ASR transcription + tashkeel\n'
        '|   |   |-- module_d.py      Evaluation, feedback, sessions, adaptive params\n'
        '|   |   |-- module_library.py  UN Digital Library search + fetch\n'
        '|   |   |-- alignment.py     WhisperX forced alignment + LLM analysis\n'
        '|   |   `-- auth.py          Login, signup, validate-groq-key endpoint\n'
        '|   |-- services/\n'
        '|   |   `-- llm_service.py   LLM provider abstraction (Groq / Gemini / local)\n'
        '|   `-- utils/\n'
        '|       `-- groq_client.py   Per-request Groq client factory\n'
        '|-- Frontend/\n'
        '|   |-- src/\n'
        '|   |   |-- App.jsx          All React components + UI strings (EN/AR/FR)\n'
        '|   |   `-- api.js           All fetch helpers with groqHeaders()\n'
        '|   |-- styles/\n'
        '|   |   |-- main.css\n'
        '|   |   `-- rtl.css\n'
        '|   `-- index.html\n'
        '`-- docs/\n'
        '    |-- USER_GUIDE.md\n'
        '    |-- ETIB_User_Guide.pdf\n'
        '    `-- ETIB_Technical_Documentation.pdf'
    )

    # Branches
    pdf.h1('Git Branches')
    pdf.table(
        ['Branch', 'Purpose'],
        [
            ['joe-main',        'Main development branch — all features, per-student API key'],
            ['api-key-commun',  'Backup: shared server-key approach (one key for all students)'],
            ['kevin-main',      "Kevin's contributions (merged into joe-main)"],
        ],
        col_widths=[52, 118]
    )

    # Module A technical
    pdf.add_page()
    pdf.h1('Module A — Speech Generation (Technical Notes)')

    pdf.h2('RAG pipeline  (document-grounded generation)')
    pdf.bullet('Source document chunked: 1 800 characters per chunk, 250-character overlap')
    pdf.bullet('Each chunk embedded with  paraphrase-multilingual-MiniLM-L12-v2  (sentence-transformers)')
    pdf.bullet('Cosine similarity computed between topic/query and all chunks')
    pdf.bullet('Top-4 chunks injected into the LLM prompt as grounding context')

    pdf.h2('UN grounding')
    pdf.bullet('Searches UN Digital Library MARCXML API — tries up to 5 results in 3 languages (EN/FR/ES)')
    pdf.bullet('Downloads PDF using curl with browser User-Agent headers (WAF bypass)')
    pdf.bullet('20-second per-PDF timeout; minimum 40 words to count as a valid document')
    pdf.bullet('Falls back to ungrounded generation with factual accuracy rules if no document found')

    pdf.h2('Arabic specifics')
    pdf.bullet('All digit sequences converted to Eastern Arabic-Indic numerals')
    pdf.bullet('LLM prompt instructs the model to use correct Arabic numeral and grammatical forms')

    pdf.h2('Endpoints')
    pdf.code(
        'POST /api/module-a/generate\n'
        'POST /api/module-a/from-document\n'
        'POST /api/module-a/retrieve-document-context'
    )

    # Module C technical
    pdf.h1('Module C — ASR Transcription (Technical Notes)')
    pdf.bullet('Primary: Groq hosted whisper-large-v3 (~3 seconds per recording)')
    pdf.bullet('Fallback: local faster-whisper, medium model, ~1-3 minutes on CPU')
    pdf.bullet('Disfluency priming prompts per language — preserves hesitation markers (euh, um, yani)')
    pdf.bullet('Arabic tashkeel added post-transcription: reflects student pronunciation including errors')
    pdf.bullet('WhisperX forced alignment available when installed: provides word-level confidence scores')
    pdf.h2('Endpoints')
    pdf.code(
        'POST /api/module-c/transcribe\n'
        'POST /api/module-c/align\n'
        'GET  /api/module-c/status'
    )

    # Module D technical
    pdf.add_page()
    pdf.h1('Module D — Evaluation (Technical Notes)')

    pdf.h2('Error detection')
    pdf.bullet('Hesitations: regex matching per language  (euh, um, ah, yani, ...)')
    pdf.bullet('Number errors: number token comparison between source and student transcript')
    pdf.bullet('Omissions: silence gaps > 500 ms in student audio flagged as possible omissions')
    pdf.bullet('Terminology: key terms from source checked for presence in transcript')

    pdf.h2('Adaptive parameters')
    pdf.bullet('Recomputed after each session from the full score history')
    pdf.bullet('Tracks  problems_to_work_on  and  top_errors  fields across all sessions')
    pdf.bullet('Recommends difficulty, length, and domain for the next session')

    pdf.h2('Session storage')
    pdf.bullet('Stored in MongoDB collection:  etib_interpreter_trainer.sessions')
    pdf.bullet('Falls back to in-memory dict if MongoDB is unavailable (resets on server restart)')
    pdf.bullet('Sessions keyed by user_id, or "anonymous" if the user is not authenticated')

    pdf.h2('Endpoints')
    pdf.code(
        'POST /api/module-d/full-evaluation\n'
        'POST /api/module-d/evaluate\n'
        'POST /api/module-d/tashkeel-compare\n'
        'POST /api/module-d/pronunciation\n'
        'POST /api/module-d/feedback\n'
        'GET  /api/module-d/sessions\n'
        'GET  /api/module-d/adaptive-params'
    )

    # Auth endpoints
    pdf.h1('Authentication Endpoints')
    pdf.table(
        ['Endpoint', 'Method', 'Description'],
        [
            ['/api/auth/signup',             'POST', 'Create a new user account'],
            ['/api/auth/login',              'POST', 'Log in with email and password'],
            ['/api/auth/me',                 'GET',  'Check current session state'],
            ['/api/auth/logout',             'POST', 'End the session (clear cookie)'],
            ['/api/auth/validate-groq-key',  'POST', 'Test a Groq API key with a live call'],
        ],
        col_widths=[75, 20, 75]
    )
    pdf.note(
        'Sessions use Flask server-side cookies. '
        'MongoDB stores user accounts when available; an in-memory dict is used otherwise. '
        'Seed accounts (student@etib.edu, instructor@etib.edu) are created on first run.'
    )

    # Standards
    pdf.add_page()
    pdf.h1('Standards Compliance')
    pdf.table(
        ['Standard', 'How it applies'],
        [
            ['GDPR',             'User data minimised; no personal data sent to Groq beyond the speech content'],
            ['ISO/IEC 27001',    'API keys never stored server-side; session tokens use signed cookies'],
            ['IEEE 12207',       'Git version control with feature branches; modular service architecture'],
            ['ISO 9241',         'Consistent UI design; full RTL (right-to-left) support for Arabic'],
        ],
        col_widths=[45, 125]
    )

    pdf.output('docs/ETIB_Technical_Documentation.pdf')
    print('  Created: docs/ETIB_Technical_Documentation.pdf')


if __name__ == '__main__':
    print('Generating PDFs...')
    build_user_guide()
    build_technical_doc()
    print('Done.')
