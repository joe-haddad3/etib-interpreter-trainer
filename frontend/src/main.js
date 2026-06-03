/**
 * ETIB Interpreter Training Platform — Frontend
 * ===============================================
 * Person 3 owns this file.
 *
 * Responsibilities:
 *   - Language toggle (EN ↔ AR) with full RTL support
 *   - Module A: speech generation form + API call + result rendering
 *   - Navigation between module panels
 *   - (Future) Modules B, C, D panels
 */

const API = 'http://localhost:5000/api';
let uiLang = 'en';
let lastGeneratedScript = null;  // shared with Module B when it's built

// ── UI string translations ─────────────────────────────────────────────────
const UI = {
  en: {
    toggle: 'العربية',
    modA_title: 'Generate training speech',
    lang_label: 'Speech language',
    domain_label: 'Domain',
    words_label: 'Word count',
    diff_label: 'Difficulty',
    structure_label: 'Discourse structure',
    mode_label: 'Interpretation mode',
    numbers_label: 'Number density',
    hesitations_label: 'Simulate hesitations',
    submit: 'Generate speech',
    generating: 'Generating — please wait...',
    words_unit: 'words',
    duration_unit: 'min',
  },
  ar: {
    toggle: 'English',
    modA_title: 'توليد خطاب تدريبي',
    lang_label: 'لغة الخطاب',
    domain_label: 'المجال',
    words_label: 'عدد الكلمات',
    diff_label: 'مستوى الصعوبة',
    structure_label: 'بنية الخطاب',
    mode_label: 'نوع الترجمة الفورية',
    numbers_label: 'كثافة الأرقام',
    hesitations_label: 'محاكاة التردد',
    submit: 'توليد الخطاب',
    generating: 'جارٍ التوليد، يرجى الانتظار...',
    words_unit: 'كلمة',
    duration_unit: 'دقيقة',
  }
};

// ── Language toggle ────────────────────────────────────────────────────────
function toggleLang() {
  uiLang = uiLang === 'en' ? 'ar' : 'en';
  const htmlEl = document.getElementById('html-root');
  htmlEl.setAttribute('lang', uiLang);
  document.body.classList.toggle('rtl', uiLang === 'ar');
  document.getElementById('rtl-sheet').disabled = uiLang !== 'ar';
  document.getElementById('lang-toggle').textContent = UI[uiLang].toggle;
  renderModuleA();
}

// ── Panel navigation ───────────────────────────────────────────────────────
function showPanel(panelId, btn) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`panel-${panelId}`).classList.add('active');
  btn.classList.add('active');
}

// ── Module A ───────────────────────────────────────────────────────────────
function renderModuleA() {
  const L = UI[uiLang];
  const container = document.getElementById('module-a-content');

  container.innerHTML = `
    <div class="card">
      <h2>${L.modA_title}</h2>
      <form id="gen-form">
        <div class="form-grid">
          <div class="field">
            <label for="f-lang">${L.lang_label}</label>
            <select id="f-lang" name="language">
              <option value="ar">العربية — Arabic</option>
              <option value="fr">Français — French</option>
              <option value="en" selected>English</option>
            </select>
          </div>
          <div class="field">
            <label for="f-domain">${L.domain_label}</label>
            <select id="f-domain" name="domain">
              <option value="politics">Politics / السياسة</option>
              <option value="diplomacy">Diplomacy / الدبلوماسية</option>
              <option value="economics">Economics / الاقتصاد</option>
              <option value="climate">Climate / المناخ</option>
              <option value="health">Health / الصحة</option>
              <option value="human rights">Human rights / حقوق الإنسان</option>
              <option value="education">Education / التعليم</option>
            </select>
          </div>
          <div class="field">
            <label for="f-words">${L.words_label}</label>
            <input type="number" id="f-words" name="word_count" value="200" min="50" max="800">
          </div>
          <div class="field">
            <label for="f-diff">${L.diff_label}</label>
            <select id="f-diff" name="difficulty">
              <option value="beginner">Beginner / مبتدئ</option>
              <option value="intermediate" selected>Intermediate / متوسط</option>
              <option value="advanced">Advanced / متقدم</option>
            </select>
          </div>
          <div class="field">
            <label for="f-mode">${L.mode_label}</label>
            <select id="f-mode" name="mode">
              <option value="consecutive" selected>Consecutive / متتابعة</option>
              <option value="simultaneous">Simultaneous / فورية</option>
              <option value="sight_translation">Sight translation / ترجمة بصرية</option>
            </select>
          </div>
          <div class="field">
            <label for="f-structure">${L.structure_label}</label>
            <select id="f-structure" name="structure">
              <option value="well-organized" selected>Well organized</option>
              <option value="semi-structured">Semi-structured</option>
              <option value="deliberately disorganized">Disorganized</option>
            </select>
          </div>
          <div class="field">
            <label for="f-numbers">${L.numbers_label}</label>
            <select id="f-numbers" name="number_density">
              <option value="low" selected>Low / منخفض</option>
              <option value="medium">Medium / متوسط</option>
              <option value="high">High / مرتفع</option>
            </select>
          </div>
          <div class="field" style="justify-content: flex-end;">
            <label style="flex-direction: row; align-items: center; gap: 0.5rem; cursor:pointer;">
              <input type="checkbox" id="f-hesitations" name="include_hesitations">
              ${L.hesitations_label}
            </label>
          </div>
        </div>
        <button type="submit" class="btn-primary" id="gen-btn">${L.submit}</button>
      </form>
      <div id="gen-output"></div>
    </div>
  `;

  document.getElementById('gen-form').addEventListener('submit', handleGenerate);
}

async function handleGenerate(e) {
  e.preventDefault();
  const L = UI[uiLang];
  const form = e.target;
  const btn = document.getElementById('gen-btn');
  const output = document.getElementById('gen-output');

  const params = {
    language:           form.language.value,
    domain:             form.domain.value,
    word_count:         parseInt(form.word_count.value),
    difficulty:         form.difficulty.value,
    mode:               form.mode.value,
    structure:          form.structure.value,
    number_density:     form.number_density.value,
    include_hesitations: form.include_hesitations.checked,
  };

  btn.disabled = true;
  btn.textContent = L.generating;
  output.innerHTML = `<p class="loading">${L.generating}</p>`;

  try {
    const res = await fetch(`${API}/module-a/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });

    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    lastGeneratedScript = data;  // save for Module B to use later

    const isAr = data.language === 'ar';
    const mins = Math.floor(data.estimated_duration_seconds / 60);
    const secs = data.estimated_duration_seconds % 60;
    const duration = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;

    output.innerHTML = `
      <div class="speech-result">
        <div class="result-meta">
          <span>${data.word_count} ${L.words_unit}</span>
          <span>~${duration}</span>
          <span>${data.domain}</span>
          <span>${data.language.toUpperCase()}</span>
        </div>
        <div class="speech-text ${isAr ? 'arabic' : ''}">${escapeHtml(data.script)}</div>
      </div>
    `;
  } catch (err) {
    output.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = L.submit;
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ── Boot ───────────────────────────────────────────────────────────────────
renderModuleA();
