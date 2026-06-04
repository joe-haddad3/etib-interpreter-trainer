import React, { useEffect, useMemo, useState } from 'react';
import { generateSpeech, loginUser, logoutUser, signupUser } from './api.js';

const UI = {
  en: {
    uiLanguage: 'Interface language',
    loginTitle: 'Sign in to ETIB Trainer',
    loginSubtitle: 'Access your interpreter training workspace.',
    signupTitle: 'Create your ETIB Trainer account',
    signupSubtitle: 'Set up an account to start interpreter training.',
    name: 'Full name',
    email: 'Email',
    password: 'Password',
    showPassword: 'Show',
    hidePassword: 'Hide',
    role: 'Role',
    loginSubmit: 'Sign in',
    loginLoading: 'Signing in...',
    signupSubmit: 'Create account',
    signupLoading: 'Creating account...',
    loginNote: 'Use your account credentials, or create a new account.',
    switchToSignup: 'Create an account',
    switchToLogin: 'Already have an account? Sign in',
    student: 'Student',
    instructor: 'Instructor',
    coordinator: 'Coordinator',
    signOut: 'Sign out',
    workspaceKicker: 'Training modules',
    workspaceTitle: 'Generate speeches, prepare materials, record interpretations, and review feedback.',
    navA: 'Generate speech',
    navB: 'Audio & materials',
    navC: 'Record & transcribe',
    navD: 'Evaluation',
    moduleATitle: 'Generate training speech',
    language: 'Speech language',
    targetLanguage: 'Target language',
    topic: 'Topic',
    domain: 'Domain',
    wordCount: 'Word count',
    difficulty: 'Difficulty',
    structure: 'Discourse structure',
    mode: 'Interpretation mode',
    numbers: 'Number density',
    hesitations: 'Simulate hesitations',
    pressureMode: 'Pressure mode',
    speedPressure: 'Speed pressure',
    topicShifts: 'Topic shifts',
    contextNoise: 'Context noise',
    cognitiveLoad: 'Cognitive load',
    summary: 'Summary',
    mcq: 'MCQ',
    glossary: 'Glossary',
    submit: 'Generate speech',
    generating: 'Generating - please wait...',
    wordsUnit: 'words',
    moduleBTitle: 'Audio & Pedagogical Materials',
    moduleBBody: 'Will produce: audio playback, key terms, glossary, MCQ, and flashcards.',
    moduleCTitle: 'Record & Transcribe',
    moduleCBody: 'Will allow: in-browser recording, ASR transcription, timestamped transcript, and playback.',
    moduleDTitle: 'Performance Evaluation',
    moduleDBody: 'Will detect: hesitations, omissions, number errors, terminology issues, and recurrent weaknesses.',
    comingSoon: 'Coming soon',
    errorPrefix: 'Error'
  },
  ar: {
    uiLanguage: 'لغة الواجهة',
    loginTitle: 'تسجيل الدخول إلى منصة ETIB',
    loginSubtitle: 'ادخل إلى مساحة التدريب على الترجمة الفورية.',
    signupTitle: 'إنشاء حساب في منصة ETIB',
    signupSubtitle: 'أنشئ حساباً للبدء بالتدريب على الترجمة الفورية.',
    name: 'الاسم الكامل',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    showPassword: 'إظهار',
    hidePassword: 'إخفاء',
    role: 'الدور',
    loginSubmit: 'تسجيل الدخول',
    loginLoading: 'جارٍ تسجيل الدخول...',
    signupSubmit: 'إنشاء الحساب',
    signupLoading: 'جارٍ إنشاء الحساب...',
    loginNote: 'استخدم بيانات حسابك، أو أنشئ حساباً جديداً.',
    switchToSignup: 'إنشاء حساب',
    switchToLogin: 'لديك حساب؟ سجّل الدخول',
    student: 'طالب',
    instructor: 'مدرب',
    coordinator: 'منسق',
    signOut: 'تسجيل الخروج',
    workspaceKicker: 'وحدات التدريب',
    workspaceTitle: 'توليد الخطابات، إعداد المواد، تسجيل الأداء، ومراجعة التغذية الراجعة.',
    navA: 'توليد الخطاب',
    navB: 'الصوت والمواد',
    navC: 'التسجيل والتفريغ',
    navD: 'التقييم',
    moduleATitle: 'توليد خطاب تدريبي',
    language: 'لغة الخطاب',
    targetLanguage: 'لغة الترجمة',
    domain: 'المجال',
    wordCount: 'عدد الكلمات',
    difficulty: 'مستوى الصعوبة',
    structure: 'بنية الخطاب',
    mode: 'نوع الترجمة الفورية',
    numbers: 'كثافة الأرقام',
    hesitations: 'محاكاة التردد',
    submit: 'توليد الخطاب',
    generating: 'جارٍ التوليد، يرجى الانتظار...',
    wordsUnit: 'كلمة',
    moduleBTitle: 'الصوت والمواد التعليمية',
    moduleBBody: 'سيتم إنتاج الصوت، المصطلحات الأساسية، المسرد، الأسئلة متعددة الخيارات، والبطاقات التعليمية.',
    moduleCTitle: 'التسجيل والتفريغ',
    moduleCBody: 'سيتيح التسجيل داخل المتصفح، التفريغ الآلي، النص الزمني، وتشغيل التسجيل.',
    moduleDTitle: 'تقييم الأداء',
    moduleDBody: 'سيكشف التردد، الحذف، أخطاء الأرقام، المشاكل المصطلحية، ونقاط الضعف المتكررة.',
    comingSoon: 'قريباً',
    errorPrefix: 'خطأ'
  },
  fr: {
    uiLanguage: 'Langue de l’interface',
    loginTitle: 'Connexion à ETIB Trainer',
    loginSubtitle: 'Accédez à votre espace d’entraînement à l’interprétation.',
    signupTitle: 'Créer votre compte ETIB Trainer',
    signupSubtitle: 'Créez un compte pour commencer l’entraînement.',
    name: 'Nom complet',
    email: 'E-mail',
    password: 'Mot de passe',
    showPassword: 'Afficher',
    hidePassword: 'Masquer',
    role: 'Rôle',
    loginSubmit: 'Se connecter',
    loginLoading: 'Connexion...',
    signupSubmit: 'Créer le compte',
    signupLoading: 'Création du compte...',
    loginNote: 'Utilisez vos identifiants ou créez un nouveau compte.',
    switchToSignup: 'Créer un compte',
    switchToLogin: 'Vous avez déjà un compte ? Se connecter',
    student: 'Étudiant',
    instructor: 'Formateur',
    coordinator: 'Coordinateur',
    signOut: 'Se déconnecter',
    workspaceKicker: 'Modules d’entraînement',
    workspaceTitle: 'Générez des discours, préparez les supports, enregistrez les interprétations et consultez les retours.',
    navA: 'Générer un discours',
    navB: 'Audio et supports',
    navC: 'Enregistrer et transcrire',
    navD: 'Évaluation',
    moduleATitle: 'Générer un discours d’entraînement',
    language: 'Langue du discours',
    targetLanguage: 'Langue cible',
    domain: 'Domaine',
    wordCount: 'Nombre de mots',
    difficulty: 'Difficulté',
    structure: 'Structure du discours',
    mode: 'Mode d’interprétation',
    numbers: 'Densité des chiffres',
    hesitations: 'Simuler les hésitations',
    submit: 'Générer le discours',
    generating: 'Génération en cours...',
    wordsUnit: 'mots',
    moduleBTitle: 'Audio et supports pédagogiques',
    moduleBBody: 'Produira : lecture audio, termes clés, glossaire, QCM et flashcards.',
    moduleCTitle: 'Enregistrer et transcrire',
    moduleCBody: 'Permettra : enregistrement dans le navigateur, transcription ASR, horodatage et lecture.',
    moduleDTitle: 'Évaluation des performances',
    moduleDBody: 'Détectera : hésitations, omissions, erreurs de chiffres, problèmes terminologiques et faiblesses récurrentes.',
    comingSoon: 'Bientôt disponible',
    errorPrefix: 'Erreur'
  }
};

const NAV_ITEMS = [
  { id: 'module-a', labelKey: 'navA' },
  { id: 'module-b', labelKey: 'navB' },
  { id: 'module-c', labelKey: 'navC' },
  { id: 'module-d', labelKey: 'navD' }
];

const initialSpeechForm = {
  topic: '',
  language: 'en',
  target_language: 'fr',
  domain: 'politics',
  word_count: 200,
  difficulty: 'intermediate',
  mode: 'consecutive',
  structure: 'well-organized',
  number_density: 'low',
  include_hesitations: false,
  pressure_enabled: false,
  speed_pressure: 'normal',
  topic_shifts: 'none',
  context_noise: false,
  cognitive_load: 'medium'
};

export default function App() {
  const [uiLang, setUiLang] = useState('en');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activePanel, setActivePanel] = useState('module-a');
  const [lastGeneratedScript, setLastGeneratedScript] = useState(null);
  const L = UI[uiLang];

  useEffect(() => {
    document.documentElement.lang = uiLang;
    document.body.classList.toggle('rtl', uiLang === 'ar');
  }, [uiLang]);

  async function handleLogin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const result = await loginUser({
      email: formData.get('email'),
      password: formData.get('password'),
      role: formData.get('role')
    });
    setCurrentUser(result.user);
    setIsAuthenticated(true);
  }

  async function handleSignup(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const result = await signupUser({
      name: formData.get('name'),
      email: formData.get('email'),
      password: formData.get('password'),
      role: formData.get('role')
    });
    setCurrentUser(result.user);
    setIsAuthenticated(true);
  }

  async function handleLogout() {
    await logoutUser().catch(() => {});
    setIsAuthenticated(false);
    setCurrentUser(null);
    setActivePanel('module-a');
    setLastGeneratedScript(null);
  }

  return (
    <>
      <Header
        isAuthenticated={isAuthenticated}
        activePanel={activePanel}
        labels={L}
        onPanelChange={setActivePanel}
        uiLang={uiLang}
        onLanguageChange={setUiLang}
      />
      <main>
        {!isAuthenticated ? (
          <LoginScreen labels={L} onLogin={handleLogin} onSignup={handleSignup} />
        ) : (
          <Workspace
            labels={L}
            activePanel={activePanel}
            onLogout={handleLogout}
            onGenerated={setLastGeneratedScript}
            lastGeneratedScript={lastGeneratedScript}
            currentUser={currentUser}
          />
        )}
      </main>
    </>
  );
}

function Header({ isAuthenticated, activePanel, labels, onPanelChange, uiLang, onLanguageChange }) {
  return (
    <header>
      <div className="header-inner">
        <span className="logo">
          <span className="logo-en">ETIB Trainer</span>
          <span className="logo-sep">·</span>
          <span className="logo-ar">منصة التدريب</span>
        </span>
        {isAuthenticated && (
          <nav aria-label="Training modules">
            {NAV_ITEMS.map(item => (
              <button
                key={item.id}
                type="button"
                className={`nav-btn ${activePanel === item.id ? 'active' : ''}`}
                onClick={() => onPanelChange(item.id)}
              >
                {labels[item.labelKey]}
              </button>
            ))}
          </nav>
        )}
        <label className="language-picker">
          <span>{labels.uiLanguage}</span>
          <select value={uiLang} onChange={event => onLanguageChange(event.target.value)}>
            <option value="en">English</option>
            <option value="fr">Français</option>
            <option value="ar">العربية</option>
          </select>
        </label>
      </div>
    </header>
  );
}

function LoginScreen({ labels, onLogin, onSignup }) {
  const [mode, setMode] = useState('login');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const isSignup = mode === 'signup';

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      if (isSignup) {
        await onSignup(event);
      } else {
        await onLogin(event);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="login-shell">
      <div className="login-layout">
        <div className="login-intro">
          <p className="eyebrow">ETIB Interpreter Trainer</p>
          <h1>{isSignup ? labels.signupTitle : labels.loginTitle}</h1>
          <p>{isSignup ? labels.signupSubtitle : labels.loginSubtitle}</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {isSignup && (
            <div className="field">
              <label htmlFor="login-name">{labels.name}</label>
              <input id="login-name" name="name" type="text" autoComplete="name" required placeholder="Kevin Mansour" />
            </div>
          )}
          <div className="field">
            <label htmlFor="login-email">{labels.email}</label>
            <input id="login-email" name="email" type="email" autoComplete="email" required placeholder="name@example.com" />
          </div>
          <div className="field">
            <label htmlFor="login-password">{labels.password}</label>
            <div className="password-control">
              <input
                id="login-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                minLength="4"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(current => !current)}
                aria-pressed={showPassword}
                aria-controls="login-password"
              >
                {showPassword ? labels.hidePassword : labels.showPassword}
              </button>
            </div>
          </div>
          <div className="field">
            <label htmlFor="login-role">{labels.role}</label>
            <select id="login-role" name="role">
              <option value="student">{labels.student}</option>
              <option value="instructor">{labels.instructor}</option>
              <option value="coordinator">{labels.coordinator}</option>
            </select>
          </div>
          {error && <div className="error-msg">{labels.errorPrefix}: {error}</div>}
          <button type="submit" className="btn-primary login-submit" disabled={isSubmitting}>
            {isSubmitting
              ? (isSignup ? labels.signupLoading : labels.loginLoading)
              : (isSignup ? labels.signupSubmit : labels.loginSubmit)}
          </button>
          <p className="login-note">{labels.loginNote}</p>
          <button
            type="button"
            className="auth-switch"
            onClick={() => {
              setMode(isSignup ? 'login' : 'signup');
              setError('');
              setShowPassword(false);
            }}
          >
            {isSignup ? labels.switchToLogin : labels.switchToSignup}
          </button>
        </form>
      </div>
    </section>
  );
}

function Workspace({ labels, activePanel, onLogout, onGenerated, lastGeneratedScript, currentUser }) {
  return (
    <section className="workspace-screen">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">{labels.workspaceKicker}</p>
          <h1>{labels.workspaceTitle}</h1>
          {currentUser && <p className="user-line">{currentUser.name} · {currentUser.role}</p>}
        </div>
        <button type="button" className="secondary-action" onClick={onLogout}>
          {labels.signOut}
        </button>
      </div>

      {activePanel === 'module-a' && (
        <ModuleA labels={labels} onGenerated={onGenerated} />
      )}
      {activePanel === 'module-b' && (
        <ComingSoon title={labels.moduleBTitle} body={labels.moduleBBody} labels={labels} detail={lastGeneratedScript?.script} />
      )}
      {activePanel === 'module-c' && (
        <ComingSoon title={labels.moduleCTitle} body={labels.moduleCBody} labels={labels} />
      )}
      {activePanel === 'module-d' && (
        <ComingSoon title={labels.moduleDTitle} body={labels.moduleDBody} labels={labels} />
      )}
    </section>
  );
}

function ModuleA({ labels, onGenerated }) {
  const [form, setForm] = useState(initialSpeechForm);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const isLoading = status === 'loading';

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm(current => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus('loading');
    setError('');
    setResult(null);

    try {
      const data = await generateSpeech({
        ...form,
        word_count: Number(form.word_count)
      });
      setResult(data);
      onGenerated(data);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  return (
    <div className="card">
      <h2>{labels.moduleATitle}</h2>
      <form onSubmit={handleSubmit}>
        <div className="field topic-field">
          <label htmlFor="f-topic">{labels.topic || 'Topic'}</label>
          <input
            id="f-topic"
            name="topic"
            type="text"
            value={form.topic}
            minLength="3"
            maxLength="180"
            required
            placeholder="Climate finance for developing countries"
            onChange={updateField}
          />
        </div>
        <div className="form-grid">
          <SelectField label={labels.language} id="f-lang" name="language" value={form.language} onChange={updateField}>
            <option value="ar">العربية - Arabic</option>
            <option value="fr">Français - French</option>
            <option value="en">English</option>
          </SelectField>
          <SelectField label={labels.targetLanguage} id="f-target-lang" name="target_language" value={form.target_language} onChange={updateField}>
            <option value="ar">العربية - Arabic</option>
            <option value="fr">Français - French</option>
            <option value="en">English</option>
          </SelectField>
          <SelectField label={labels.domain} id="f-domain" name="domain" value={form.domain} onChange={updateField}>
            <option value="politics">Politics / السياسة</option>
            <option value="diplomacy">Diplomacy / الدبلوماسية</option>
            <option value="economics">Economics / الاقتصاد</option>
            <option value="climate">Climate / المناخ</option>
            <option value="health">Health / الصحة</option>
            <option value="human rights">Human rights / حقوق الإنسان</option>
            <option value="education">Education / التعليم</option>
          </SelectField>
          <div className="field">
            <label htmlFor="f-words">{labels.wordCount}</label>
            <input id="f-words" name="word_count" type="number" value={form.word_count} min="50" max="800" onChange={updateField} />
          </div>
          <SelectField label={labels.difficulty} id="f-diff" name="difficulty" value={form.difficulty} onChange={updateField}>
            <option value="beginner">Beginner / مبتدئ</option>
            <option value="intermediate">Intermediate / متوسط</option>
            <option value="advanced">Advanced / متقدم</option>
          </SelectField>
          <SelectField label={labels.mode} id="f-mode" name="mode" value={form.mode} onChange={updateField}>
            <option value="consecutive">Consecutive / متتابعة</option>
            <option value="simultaneous">Simultaneous / فورية</option>
            <option value="sight_translation">Sight translation / ترجمة بصرية</option>
          </SelectField>
          <SelectField label={labels.structure} id="f-structure" name="structure" value={form.structure} onChange={updateField}>
            <option value="well-organized">Well organized</option>
            <option value="semi-structured">Semi-structured</option>
            <option value="deliberately disorganized">Disorganized</option>
          </SelectField>
          <SelectField label={labels.numbers} id="f-numbers" name="number_density" value={form.number_density} onChange={updateField}>
            <option value="low">Low / منخفض</option>
            <option value="medium">Medium / متوسط</option>
            <option value="high">High / مرتفع</option>
          </SelectField>
          <div className="field checkbox-field">
            <label>
              <input type="checkbox" name="include_hesitations" checked={form.include_hesitations} onChange={updateField} />
              {labels.hesitations}
            </label>
          </div>
          <div className="field checkbox-field">
            <label>
              <input type="checkbox" name="pressure_enabled" checked={form.pressure_enabled} onChange={updateField} />
              {labels.pressureMode || 'Pressure mode'}
            </label>
          </div>
          <SelectField label={labels.speedPressure || 'Speed pressure'} id="f-speed-pressure" name="speed_pressure" value={form.speed_pressure} onChange={updateField}>
            <option value="normal">Normal</option>
            <option value="fast">Fast</option>
            <option value="very_fast">Very fast</option>
          </SelectField>
          <SelectField label={labels.topicShifts || 'Topic shifts'} id="f-topic-shifts" name="topic_shifts" value={form.topic_shifts} onChange={updateField}>
            <option value="none">None</option>
            <option value="mild">Mild</option>
            <option value="frequent">Frequent</option>
          </SelectField>
          <SelectField label={labels.cognitiveLoad || 'Cognitive load'} id="f-cognitive-load" name="cognitive_load" value={form.cognitive_load} onChange={updateField}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </SelectField>
          <div className="field checkbox-field">
            <label>
              <input type="checkbox" name="context_noise" checked={form.context_noise} onChange={updateField} />
              {labels.contextNoise || 'Context noise'}
            </label>
          </div>
        </div>
        <button type="submit" className="btn-primary" disabled={isLoading}>
          {isLoading ? labels.generating : labels.submit}
        </button>
      </form>

      {isLoading && <p className="loading">{labels.generating}</p>}
      {error && <div className="error-msg">{labels.errorPrefix}: {error}</div>}
      {result && <SpeechResult data={result} labels={labels} />}
    </div>
  );
}

function SelectField({ label, id, name, value, onChange, children }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} name={name} value={value} onChange={onChange}>
        {children}
      </select>
    </div>
  );
}

function SpeechResult({ data, labels }) {
  const duration = useMemo(() => {
    const seconds = Number(data.estimated_duration_seconds || 0);
    if (!seconds) return null;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  }, [data.estimated_duration_seconds]);

  const isArabic = data.language === 'ar';

  return (
    <div className="speech-result">
      <div className="result-meta">
        <span>{data.word_count} {labels.wordsUnit}</span>
        {duration && <span>~{duration}</span>}
        {data.topic && <span>{data.topic}</span>}
        <span>{data.domain}</span>
        <span>{String(data.language || '').toUpperCase()} → {String(data.target_language || '').toUpperCase()}</span>
      </div>
      <div className={`speech-text ${isArabic ? 'arabic' : ''}`}>
        {data.script}
      </div>
      {data.summary && (
        <section className="result-section">
          <h3>{labels.summary || 'Summary'}</h3>
          <p>{data.summary}</p>
        </section>
      )}
      {Array.isArray(data.mcqs) && data.mcqs.length > 0 && (
        <section className="result-section">
          <h3>{labels.mcq || 'MCQ'}</h3>
          <div className="mcq-list">
            {data.mcqs.map((item, index) => (
              <div className="mcq-item" key={`${item.question || 'question'}-${index}`}>
                <p className="mcq-question">{index + 1}. {item.question}</p>
                <ul>
                  {(item.options || []).map((option, optionIndex) => (
                    <li key={`${option}-${optionIndex}`}>{option}</li>
                  ))}
                </ul>
                {item.answer && <p className="mcq-answer">Answer: {item.answer}</p>}
              </div>
            ))}
          </div>
        </section>
      )}
      {Array.isArray(data.glossary) && data.glossary.length > 0 && (
        <section className="result-section">
          <h3>{labels.glossary || 'Glossary'}</h3>
          <div className="glossary-table-wrap">
            <table className="glossary-table">
              <thead>
                <tr>
                  <th>Term</th>
                  <th>Arabic</th>
                  <th>French</th>
                  <th>English</th>
                  <th>Definition</th>
                </tr>
              </thead>
              <tbody>
                {data.glossary.map((item, index) => (
                  <tr key={`${item.term || 'term'}-${index}`}>
                    <td>{item.term}</td>
                    <td>{item.arabic}</td>
                    <td>{item.french}</td>
                    <td>{item.english}</td>
                    <td>{item.definition}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

function ComingSoon({ title, body, labels, detail }) {
  return (
    <div className="card coming-soon">
      <p className="eyebrow">{labels.comingSoon}</p>
      <h2>{title}</h2>
      <p>{body}</p>
      {detail && <p className="module-context">A generated speech is ready for this module once backend endpoints are connected.</p>}
    </div>
  );
}
