import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  generateSpeech,
  generateSpeechFromDocument,
  loginUser,
  logoutUser,
  retrieveDocumentContext,
  signupUser,
  textToSpeech,
  generateMaterials,
  downloadGlossary,
  transcribeAudio,
  generateFeedback,
  evaluateWithAudio,
  tashkeelCompare,
  alignPronunciation,
  getPronunciationReport,
} from './api.js';

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
    documentGrounding: 'Document grounding',
    documentFile: 'Source document',
    sharedSettings: 'Generation settings',
    sharedSettingsHint: 'These settings apply to both topic-only generation and document-grounded generation.',
    generationMethods: 'Choose generation source',
    topicOnlyGeneration: 'Topic-only generation',
    topicOnlyHint: 'Generate from the topic and selected settings.',
    documentGenerationHint: 'Upload a source file and generate a speech grounded in its content.',
    generateFromDocument: 'Generate from document',
    retrieveContext: 'Preview retrieved context',
    retrievedContext: 'Retrieved context',
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
    errorPrefix: 'Error',
    noSpeechYet: 'Generate a speech in Module A first, then come back here.',
    voiceAccent: 'Voice accent',
    speechRate: 'Speech rate',
    generateAudio: 'Generate audio',
    generatingAudio: 'Generating audio...',
    materialsTitle: 'Pedagogical materials',
    generateMaterials: 'Generate materials',
    generatingMaterials: 'Generating materials...',
    keyTerms: 'Key terms',
    summaryTitle: 'Thematic summary',
    mcqTitle: 'Comprehension questions (MCQ)',
    glossaryTitle: 'Trilingual glossary (AR – FR – EN)',
    downloadGlossary: 'Download glossary (DOCX)',
    uploadAudio: 'Upload your interpretation (MP3, WAV, M4A)',
    transcribeBtn: 'Transcribe',
    transcribing: 'Transcribing — may take 1–2 min for Arabic...',
    transcriptLabel: 'Transcript',
    lowConfidence: 'Low-confidence words (possible errors)',
    arabicTip: 'For best results: speak clearly in Modern Standard Arabic (فصحى) in a quiet room.',
    noTranscriptYet: 'Record your interpretation in "Record & transcribe" first, then come back here.',
    runEvaluation: 'Run full evaluation',
    runningEvaluation: 'Analyzing your interpretation...',
    overallScore: 'Overall score',
    evalSummary: 'Overall assessment',
    strengths: 'Strengths',
    recommendations: 'Recommendations',
    algorithmicTitle: 'Automatic detections',
    longSilences: 'Long silences',
    repetitions: 'Repetitions',
    hesitations: 'Hesitations',
    numberErrors: 'Number errors',
    llmTitle: 'AI language analysis',
    languageErrors: 'Language errors',
    autoCorrections: 'Auto-corrections',
    falseStarts: 'False starts',
    lapsusLinguae: 'Lapsus linguae',
    terminologyProblems: 'Terminology problems',
    informationLoss: 'Information loss',
    noIssues: 'None detected',
    correction: 'Correction',
    source: 'Source',
    used: 'Used',
    correct: 'Correct term',
    pronunciationTitle: 'Pronunciation Assessment (إعراب)',
    runPronunciation: 'Run pronunciation check',
    runningPronunciation: 'Aligning audio against source — may take 1 min...',
    pronunciationScore: 'Pronunciation confidence',
    wordView: 'Word-by-word view',
    legend: 'Legend',
    legendGood: '≥80% confident',
    legendWarn: '65–80%',
    legendPoor: '<65% — likely error',
    uncertainWords: 'Uncertain words — likely pronunciation errors',
    expectedForm: 'Expected',
    likelyError: 'Likely error',
    grammaticalRole: 'Grammatical role',
    noUncertain: 'All words pronounced with high confidence',
    whisperxBadge: 'WhisperX aligned',
    fallbackBadge: 'Whisper scores',
    needsArabic: 'Pronunciation check is available for Arabic interpretations only.',
    needsSource: 'Generate a speech in Module A first so the source text is available.',
    sourceAudio: 'Source speech audio',
    yourInterpretation: 'Your interpretation',
    recordBtn: '🎙 Start recording',
    stopBtn: '⏹ Stop recording',
    recordingLive: 'Recording',
    autoTranscribe: 'Transcribe automatically after recording',
    orUpload: 'Or upload an audio file',
    copyText: 'Copy',
    copied: 'Copied!'
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
    errorPrefix: 'خطأ',
    noSpeechYet: 'ولّد خطاباً في الوحدة أ أولاً، ثم عد إلى هنا.',
    voiceAccent: 'نبرة الصوت',
    speechRate: 'سرعة الإلقاء',
    generateAudio: 'توليد الصوت',
    generatingAudio: 'جارٍ توليد الصوت...',
    materialsTitle: 'المواد التعليمية',
    generateMaterials: 'توليد المواد',
    generatingMaterials: 'جارٍ توليد المواد...',
    keyTerms: 'المصطلحات الأساسية',
    summaryTitle: 'الملخص الموضوعي',
    mcqTitle: 'أسئلة الفهم (MCQ)',
    glossaryTitle: 'المسرد الثلاثي (AR – FR – EN)',
    downloadGlossary: 'تنزيل المسرد (DOCX)',
    uploadAudio: 'ارفع تسجيل ترجمتك (MP3, WAV, M4A)',
    transcribeBtn: 'فرّغ الصوت',
    transcribing: 'جارٍ التفريغ — قد يستغرق دقيقتين للعربية...',
    transcriptLabel: 'النص المفرَّغ',
    lowConfidence: 'كلمات غير مؤكدة (أخطاء محتملة)',
    arabicTip: 'للحصول على أفضل النتائج: تحدث بالعربية الفصحى في غرفة هادئة.',
    noTranscriptYet: 'سجّل ترجمتك أولاً في "التسجيل والتفريغ"، ثم عد إلى هنا.',
    runEvaluation: 'تشغيل التقييم الكامل',
    runningEvaluation: 'جارٍ تحليل الأداء...',
    overallScore: 'التقييم الإجمالي',
    evalSummary: 'التقييم العام',
    strengths: 'نقاط القوة',
    recommendations: 'التوصيات',
    algorithmicTitle: 'الرصد التلقائي',
    longSilences: 'صمت طويل',
    repetitions: 'تكرارات',
    hesitations: 'تردد',
    numberErrors: 'أخطاء في الأرقام',
    llmTitle: 'التحليل اللغوي بالذكاء الاصطناعي',
    languageErrors: 'أخطاء لغوية',
    autoCorrections: 'تصحيحات ذاتية',
    falseStarts: 'فروع زائفة',
    lapsusLinguae: 'زلّات لسان',
    terminologyProblems: 'مشاكل مصطلحية',
    informationLoss: 'فقدان معلومات',
    noIssues: 'لا توجد مشكلات',
    correction: 'التصحيح',
    source: 'المصدر',
    used: 'ما قيل',
    correct: 'المصطلح الصحيح',
    pronunciationTitle: 'تقييم النطق والإعراب',
    runPronunciation: 'تشغيل فحص النطق',
    runningPronunciation: 'جارٍ المحاذاة الصوتية — قد تستغرق دقيقة...',
    pronunciationScore: 'ثقة النطق',
    wordView: 'عرض كلمة بكلمة',
    legend: 'المفتاح',
    legendGood: '٪80 أو أكثر',
    legendWarn: '٪60–80',
    legendPoor: 'أقل من ٪60 — خطأ محتمل',
    uncertainWords: 'كلمات غير مؤكدة — أخطاء نطق محتملة',
    expectedForm: 'الشكل الصحيح',
    likelyError: 'الخطأ المحتمل',
    grammaticalRole: 'الدور النحوي',
    noUncertain: 'جميع الكلمات نُطقت بثقة عالية',
    whisperxBadge: 'محاذاة WhisperX',
    fallbackBadge: 'نتائج Whisper',
    needsArabic: 'فحص النطق متاح للترجمات العربية فقط.',
    needsSource: 'ولّد خطاباً في الوحدة أ أولاً لتوفير النص المرجعي.',
    sourceAudio: 'الصوت المرجعي للخطاب',
    yourInterpretation: 'ترجمتك الفورية',
    recordBtn: '🎙 بدء التسجيل',
    stopBtn: '⏹ إيقاف التسجيل',
    recordingLive: 'جارٍ التسجيل',
    autoTranscribe: 'تفريغ تلقائي بعد التسجيل',
    orUpload: 'أو ارفع ملف صوتي',
    copyText: 'نسخ',
    copied: 'تم النسخ!'
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
    errorPrefix: 'Erreur',
    noSpeechYet: 'Générez d\'abord un discours dans le Module A, puis revenez ici.',
    voiceAccent: 'Accent vocal',
    speechRate: 'Débit de parole',
    generateAudio: 'Générer l\'audio',
    generatingAudio: 'Génération audio...',
    materialsTitle: 'Supports pédagogiques',
    generateMaterials: 'Générer les supports',
    generatingMaterials: 'Génération des supports...',
    keyTerms: 'Termes clés',
    summaryTitle: 'Résumé thématique',
    mcqTitle: 'Questions de compréhension (QCM)',
    glossaryTitle: 'Glossaire trilingue (AR – FR – EN)',
    downloadGlossary: 'Télécharger le glossaire (DOCX)',
    uploadAudio: 'Déposez votre interprétation (MP3, WAV, M4A)',
    transcribeBtn: 'Transcrire',
    transcribing: 'Transcription en cours — 1–2 min pour l\'arabe...',
    transcriptLabel: 'Transcription',
    lowConfidence: 'Mots peu fiables (erreurs possibles)',
    arabicTip: 'Pour de meilleurs résultats : parlez clairement en arabe standard (فصحى) dans une pièce calme.',
    noTranscriptYet: 'Enregistrez d\'abord une interprétation dans "Enregistrer et transcrire", puis revenez ici.',
    runEvaluation: 'Lancer l\'évaluation complète',
    runningEvaluation: 'Analyse en cours...',
    overallScore: 'Score global',
    evalSummary: 'Évaluation globale',
    strengths: 'Points forts',
    recommendations: 'Recommandations',
    algorithmicTitle: 'Détections automatiques',
    longSilences: 'Longs silences',
    repetitions: 'Répétitions',
    hesitations: 'Hésitations',
    numberErrors: 'Erreurs de chiffres',
    llmTitle: 'Analyse linguistique IA',
    languageErrors: 'Erreurs linguistiques',
    autoCorrections: 'Auto-corrections',
    falseStarts: 'Faux départs',
    lapsusLinguae: 'Lapsus linguae',
    terminologyProblems: 'Problèmes terminologiques',
    informationLoss: 'Perte d\'information',
    noIssues: 'Aucun détecté',
    correction: 'Correction',
    source: 'Source',
    used: 'Utilisé',
    correct: 'Terme correct',
    pronunciationTitle: 'Évaluation de la prononciation (إعراب)',
    runPronunciation: 'Lancer le contrôle de prononciation',
    runningPronunciation: 'Alignement audio en cours — peut prendre 1 min...',
    pronunciationScore: 'Confiance en prononciation',
    wordView: 'Vue mot par mot',
    legend: 'Légende',
    legendGood: '≥80% confiant',
    legendWarn: '60–80%',
    legendPoor: '<60% — erreur probable',
    uncertainWords: 'Mots incertains — erreurs de prononciation probables',
    expectedForm: 'Forme attendue',
    likelyError: 'Erreur probable',
    grammaticalRole: 'Rôle grammatical',
    noUncertain: 'Tous les mots prononcés avec haute confiance',
    whisperxBadge: 'WhisperX aligné',
    fallbackBadge: 'Scores Whisper',
    needsArabic: 'Le contrôle de prononciation est disponible pour l\'arabe uniquement.',
    needsSource: 'Générez d\'abord un discours dans le Module A.',
    sourceAudio: 'Audio du discours source',
    yourInterpretation: 'Votre interprétation',
    recordBtn: '🎙 Démarrer l\'enregistrement',
    stopBtn: '⏹ Arrêter l\'enregistrement',
    recordingLive: 'Enregistrement en cours',
    autoTranscribe: 'Transcrire automatiquement après l\'enregistrement',
    orUpload: 'Ou déposez un fichier audio',
    copyText: 'Copier',
    copied: 'Copié !'
  }
};

const NAV_ITEMS = [
  { id: 'module-a', labelKey: 'navA' },
  { id: 'module-b', labelKey: 'navB' },
  { id: 'module-c', labelKey: 'navC' },
  { id: 'module-d', labelKey: 'navD' }
];

const VOICE_OPTIONS = {
  ar: [
    { label: 'Lebanese Arabic — Male (ar-LB)',   accent: 'LB' },
    { label: 'Lebanese Arabic — Female (ar-LB)', accent: 'LB_f' },
    { label: 'Gulf Arabic — Female (ar-SA)',     accent: 'SA' },
    { label: 'Egyptian Arabic — Female (ar-EG)', accent: 'EG' },
    { label: 'Egyptian Arabic — Male (ar-EG)',   accent: 'EG_m' },
  ],
  fr: [
    { label: 'French (Female)',   accent: 'FR' },
    { label: 'French (Male)',     accent: 'FR_m' },
    { label: 'Canadian (Female)', accent: 'CA' },
  ],
  en: [
    { label: 'American (Female)', accent: 'US' },
    { label: 'British (Female)',  accent: 'GB' },
    { label: 'Australian (Female)', accent: 'AU' },
  ]
};

// ── SVG icons ────────────────────────────────────────────────────────────────
const IconCopy = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
);
const IconThumbUp = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
  </svg>
);
const IconThumbDown = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
  </svg>
);
const IconRefresh = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

function TranscriptBubble({ text, vocalizedText, isArabic, onRetranscribe }) {
  const [copied, setCopied]       = useState(false);
  const [feedback, setFeedback]   = useState(null);
  const [showVocalized, setShowVocalized] = useState(true);

  const displayText = (isArabic && vocalizedText && showVocalized) ? vocalizedText : text;

  function copy() {
    navigator.clipboard.writeText(displayText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="message-bubble">
      {/* Tashkeel toggle — only for Arabic with vocalized version */}
      {isArabic && vocalizedText && (
        <div className="tashkeel-toggle">
          <button
            className={`tashkeel-btn ${showVocalized ? 'tashkeel-active' : ''}`}
            onClick={() => setShowVocalized(true)}
          >
            بِالتَّشْكِيل
          </button>
          <button
            className={`tashkeel-btn ${!showVocalized ? 'tashkeel-active' : ''}`}
            onClick={() => setShowVocalized(false)}
          >
            بدون تشكيل
          </button>
        </div>
      )}

      <div className={`bubble-text ${isArabic ? 'arabic' : ''}`}>{displayText}</div>

      <div className="bubble-actions">
        <button className={`bubble-btn ${copied ? 'bubble-btn-active' : ''}`} onClick={copy} title="Copy">
          <IconCopy />
        </button>
        <button className={`bubble-btn ${feedback === 'up' ? 'bubble-btn-active' : ''}`}
          onClick={() => setFeedback(f => f === 'up' ? null : 'up')} title="Good transcription">
          <IconThumbUp />
        </button>
        <button className={`bubble-btn ${feedback === 'down' ? 'bubble-btn-active' : ''}`}
          onClick={() => setFeedback(f => f === 'down' ? null : 'down')} title="Poor transcription">
          <IconThumbDown />
        </button>
        {onRetranscribe && (
          <button className="bubble-btn" onClick={onRetranscribe} title="Re-transcribe">
            <IconRefresh />
          </button>
        )}
      </div>
    </div>
  );
}

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
  const [sharedAudioUrl, setSharedAudioUrl] = useState(null);
  const [lastTranscript, setLastTranscript] = useState(null);
  const [lastRecordingBlob, setLastRecordingBlob] = useState(null);

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

      {/* Keep all panels mounted — state persists when switching tabs */}
      <div style={{ display: activePanel === 'module-a' ? 'block' : 'none' }}>
        <ModuleA labels={labels} onGenerated={onGenerated} />
      </div>
      <div style={{ display: activePanel === 'module-b' ? 'block' : 'none' }}>
        <ModuleB labels={labels} lastGeneratedScript={lastGeneratedScript}
          onAudioGenerated={setSharedAudioUrl} />
      </div>
      <div style={{ display: activePanel === 'module-c' ? 'block' : 'none' }}>
        <ModuleC labels={labels} referenceAudioUrl={sharedAudioUrl}
          sourceScript={lastGeneratedScript?.script || ''}
          onTranscriptComplete={setLastTranscript}
          onRecordingComplete={setLastRecordingBlob} />
      </div>
      <div style={{ display: activePanel === 'module-d' ? 'block' : 'none' }}>
        <ModuleD labels={labels} lastTranscript={lastTranscript}
          lastGeneratedScript={lastGeneratedScript}
          lastRecordingBlob={lastRecordingBlob} />
      </div>
    </section>
  );
}

function ModuleA({ labels, onGenerated }) {
  const [form, setForm] = useState(initialSpeechForm);
  const [documentFile, setDocumentFile] = useState(null);
  const [retrievalResult, setRetrievalResult] = useState(null);
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

  async function handleDocumentGenerate() {
    setStatus('loading');
    setError('');
    setResult(null);
    setRetrievalResult(null);

    try {
      if (!documentFile) {
        throw new Error('Choose a TXT, DOCX, or PDF document first.');
      }

      const data = await generateSpeechFromDocument(documentFile, {
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

  async function handleRetrieveContext() {
    setStatus('loading');
    setError('');
    setRetrievalResult(null);

    try {
      if (!documentFile) {
        throw new Error('Choose a TXT, DOCX, or PDF document first.');
      }

      const data = await retrieveDocumentContext(documentFile, {
        query: form.topic,
        language: form.language,
        domain: form.domain,
        scenario: 'UN General Assembly',
        difficulty: form.difficulty,
        mode: form.mode,
        number_density: form.number_density,
        max_chunks: 4
      });
      setRetrievalResult(data);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  return (
    <div className="card">
      <h2>{labels.moduleATitle}</h2>
      <form className="generation-settings" onSubmit={handleSubmit}>
        <div className="section-heading">
          <h3>{labels.sharedSettings || 'Generation settings'}</h3>
          <p>{labels.sharedSettingsHint || 'These settings apply to both topic-only generation and document-grounded generation.'}</p>
        </div>
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
            placeholder="Artificial intelligence in public policy"
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
            <option value="health">Health / الصحة</option>
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
          </SelectField>
          <SelectField label={labels.structure} id="f-structure" name="structure" value={form.structure} onChange={updateField}>
            <option value="well-organized">Well organized</option>
            <option value="deliberately disorganized">Disorganized</option>
          </SelectField>
          <SelectField label={labels.numbers} id="f-numbers" name="number_density" value={form.number_density} onChange={updateField}>
            <option value="low">Low / منخفض</option>
            <option value="high">High / مرتفع</option>
          </SelectField>
          <SelectField label={labels.speedPressure || 'Speed pressure'} id="f-speed-pressure" name="speed_pressure" value={form.speed_pressure} onChange={updateField}>
            <option value="normal">Normal</option>
            <option value="fast">Fast</option>
            <option value="very_fast">Very fast</option>
          </SelectField>
          <SelectField label={labels.topicShifts || 'Topic shifts'} id="f-topic-shifts" name="topic_shifts" value={form.topic_shifts} onChange={updateField}>
            <option value="none">None</option>
            <option value="mild">Topic shifts</option>
          </SelectField>
        </div>
        <section className="generation-methods">
          <div className="section-heading">
            <h3>{labels.generationMethods || 'Choose generation source'}</h3>
          </div>
          <div className="method-grid">
            <div className="method-panel">
              <h4>{labels.topicOnlyGeneration || 'Topic-only generation'}</h4>
              <p>{labels.topicOnlyHint || 'Generate from the topic and selected settings.'}</p>
              <button type="submit" className="btn-primary" disabled={isLoading}>
                {isLoading ? labels.generating : labels.submit}
              </button>
            </div>
            <div className="method-panel">
              <h4>{labels.documentGrounding || 'Document grounding'}</h4>
              <p>{labels.documentGenerationHint || 'Upload a source file and generate a speech grounded in its content.'}</p>
              <div className="document-actions">
                <div className="field">
                  <label htmlFor="f-document">{labels.documentFile || 'Source document'}</label>
                  <input
                    id="f-document"
                    type="file"
                    accept=".txt,.docx,.pdf"
                    onChange={event => {
                      setDocumentFile(event.target.files?.[0] || null);
                      setRetrievalResult(null);
                    }}
                  />
                </div>
                <button type="button" className="secondary-action" onClick={handleRetrieveContext} disabled={isLoading || !documentFile}>
                  {labels.retrieveContext || 'Preview retrieved context'}
                </button>
                <button type="button" className="btn-primary" onClick={handleDocumentGenerate} disabled={isLoading || !documentFile}>
                  {isLoading ? labels.generating : (labels.generateFromDocument || 'Generate from document')}
                </button>
              </div>
            </div>
          </div>
        </section>
      </form>

      {isLoading && <p className="loading">{labels.generating}</p>}
      {error && <div className="error-msg">{labels.errorPrefix}: {error}</div>}
      {retrievalResult && <RetrievalResult data={retrievalResult} labels={labels} />}
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

function RetrievalResult({ data, labels }) {
  return (
    <section className="retrieval-result">
      <h3>{labels.retrievedContext || 'Retrieved context'}</h3>
      <div className="result-meta">
        <span>{data.selected_chunk_count || 0} chunks</span>
        {(data.documents_processed || []).map((doc, index) => (
          <span key={`${doc.filename}-${index}`}>{doc.filename}</span>
        ))}
      </div>
      <div className="chunk-list">
        {(data.selected_chunks || []).map((chunk, index) => (
          <article className="chunk-item" key={`${chunk.source_filename}-${chunk.chunk_index}-${index}`}>
            <p className="chunk-source">
              {chunk.source_filename} · chunk {Number(chunk.chunk_index || 0) + 1}
            </p>
            <p>{chunk.text}</p>
          </article>
        ))}
      </div>
      {Array.isArray(data.document_errors) && data.document_errors.length > 0 && (
        <div className="error-msg">
          {data.document_errors.map((item, index) => (
            <p key={`${item.filename}-${index}`}>{item.filename}: {item.error}</p>
          ))}
        </div>
      )}
    </section>
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

// ── Module B — TTS + Pedagogical Materials ──────────────────────────────────

function ModuleB({ labels, lastGeneratedScript, onAudioGenerated }) {
  const language = lastGeneratedScript?.language || 'ar';
  const voiceOptions = VOICE_OPTIONS[language] || VOICE_OPTIONS.en;

  const [selectedAccent, setSelectedAccent] = useState(voiceOptions[0]?.accent || '');
  const [speechRate, setSpeechRate] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [materials, setMaterials] = useState(null);
  const [audioStatus, setAudioStatus] = useState('idle');
  const [materialsStatus, setMaterialsStatus] = useState('idle');
  const [audioError, setAudioError] = useState('');
  const [materialsError, setMaterialsError] = useState('');

  useEffect(() => {
    const opts = VOICE_OPTIONS[language] || VOICE_OPTIONS.en;
    setSelectedAccent(opts[0]?.accent || '');
    setAudioUrl(null);
    setMaterials(null);
    setAudioStatus('idle');
    setMaterialsStatus('idle');
  }, [language]);

  if (!lastGeneratedScript) {
    return (
      <div className="card coming-soon">
        <p className="eyebrow">{labels.moduleBTitle}</p>
        <p>{labels.noSpeechYet}</p>
      </div>
    );
  }

  async function handleGenerateAudio() {
    setAudioStatus('loading');
    setAudioError('');
    try {
      const data = await textToSpeech({
        text: lastGeneratedScript.script,
        language,
        accent: selectedAccent,
        rate_adjustment: speechRate
      });
      const url = `http://127.0.0.1:5000${data.audio_url}`;
      setAudioUrl(url);
      onAudioGenerated?.(url);
      setAudioStatus('success');
    } catch (err) {
      setAudioError(err.message);
      setAudioStatus('error');
    }
  }

  async function handleGenerateMaterials() {
    setMaterialsStatus('loading');
    setMaterialsError('');
    try {
      const data = await generateMaterials({
        script: lastGeneratedScript.script,
        language,
        domain: lastGeneratedScript.domain
      });
      setMaterials(data);
      setMaterialsStatus('success');
    } catch (err) {
      setMaterialsError(err.message);
      setMaterialsStatus('error');
    }
  }

  async function handleDownloadGlossary() {
    try {
      const blob = await downloadGlossary({
        glossary: materials.glossary,
        domain: lastGeneratedScript.domain
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `glossary_${lastGeneratedScript.domain}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`${labels.errorPrefix}: ${err.message}`);
    }
  }

  return (
    <div>
      {/* TTS Card */}
      <div className="card">
        <h2>{labels.moduleBTitle}</h2>
        <div className="form-grid">
          <SelectField label={labels.voiceAccent} id="b-voice" name="voice"
            value={selectedAccent} onChange={e => setSelectedAccent(e.target.value)}>
            {voiceOptions.map(v => (
              <option key={v.accent} value={v.accent}>{v.label}</option>
            ))}
          </SelectField>
          <div className="field">
            <label htmlFor="b-rate">
              {labels.speechRate}: {speechRate > 0 ? `+${speechRate}` : speechRate}%
            </label>
            <input
              id="b-rate"
              type="range"
              min="-30" max="20" step="5"
              value={speechRate}
              onChange={e => setSpeechRate(Number(e.target.value))}
              className="rate-slider"
            />
          </div>
        </div>
        <button className="btn-primary" onClick={handleGenerateAudio}
          disabled={audioStatus === 'loading'}>
          {audioStatus === 'loading' ? labels.generatingAudio : labels.generateAudio}
        </button>
        {audioStatus === 'loading' && <p className="loading">{labels.generatingAudio}</p>}
        {audioError && <div className="error-msg">{labels.errorPrefix}: {audioError}</div>}
        {audioUrl && (
          <div className="audio-player">
            <audio key={audioUrl} controls src={audioUrl} />
          </div>
        )}
      </div>

      {/* Materials Card */}
      <div className="card">
        <h2>{labels.materialsTitle}</h2>
        <button className="btn-primary" onClick={handleGenerateMaterials}
          disabled={materialsStatus === 'loading'}>
          {materialsStatus === 'loading' ? labels.generatingMaterials : labels.generateMaterials}
        </button>
        {materialsStatus === 'loading' && <p className="loading">{labels.generatingMaterials}</p>}
        {materialsError && <div className="error-msg">{labels.errorPrefix}: {materialsError}</div>}

        {materials && (
          <div className="materials-body">

            <section className="materials-section">
              <h3>{labels.keyTerms}</h3>
              <div className="key-terms-list">
                {(materials.key_terms || []).map((term, i) => (
                  <span key={i} className="key-term-badge">{term}</span>
                ))}
              </div>
            </section>

            <section className="materials-section">
              <h3>{labels.summaryTitle}</h3>
              <pre className="mind-map">{materials.summary}</pre>
            </section>

            <section className="materials-section">
              <h3>{labels.mcqTitle}</h3>
              {(materials.mcq || []).map((q, i) => (
                <div key={i} className="mcq-item">
                  <p className="mcq-question">{i + 1}. {q.question}</p>
                  <ul className="mcq-options">
                    {(q.options || []).map((opt, j) => (
                      <li key={j} className={opt.startsWith(q.answer + '.') || opt.startsWith(q.answer + ' ') ? 'mcq-correct' : ''}>
                        {opt}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </section>

            <section className="materials-section">
              <div className="glossary-header">
                <h3>{labels.glossaryTitle}</h3>
                <button className="btn-secondary" onClick={handleDownloadGlossary}>
                  {labels.downloadGlossary}
                </button>
              </div>
              <table className="glossary-table">
                <thead>
                  <tr><th>العربية</th><th>Français</th><th>English</th></tr>
                </thead>
                <tbody>
                  {(materials.glossary || []).map((entry, i) => (
                    <tr key={i}>
                      <td className="arabic" dir="rtl">{entry.ar}</td>
                      <td>{entry.fr}</td>
                      <td>{entry.en}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

          </div>
        )}
      </div>
    </div>
  );
}

// ── Module C — ASR Transcription + Browser Recording ────────────────────────

function ModuleC({ labels, referenceAudioUrl, sourceScript, onTranscriptComplete, onRecordingComplete }) {
  const [language, setLanguage] = useState('ar');
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordedUrl, setRecordedUrl] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [autoTranscribe, setAutoTranscribe] = useState(true);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const lowConfWords = useMemo(() =>
    (result?.segments || []).flatMap(seg =>
      (seg.words || []).filter(w => w.probability < 0.6)
    ), [result]);

  function formatTime(s) {
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  }

  async function runTranscription(audioInput) {
    setStatus('loading');
    setError('');
    setResult(null);
    try {
      const fileToSend = audioInput instanceof File
        ? audioInput
        : new File([audioInput], 'recording.webm', { type: audioInput.type });
      const data = await transcribeAudio(fileToSend, language, sourceScript || '');
      setResult(data);
      onTranscriptComplete?.({ ...data, language, sourceScript: sourceScript || '' });
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus' : 'audio/webm';
      const mr = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mr;
      chunksRef.current = [];
      setRecordingTime(0);
      setResult(null);
      setError('');

      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        stream.getTracks().forEach(t => t.stop());
        clearInterval(timerRef.current);
        setRecordedBlob(blob);
        onRecordingComplete?.(blob);
        if (recordedUrl) URL.revokeObjectURL(recordedUrl);
        setRecordedUrl(URL.createObjectURL(blob));
        if (autoTranscribe) runTranscription(blob);
      };

      mr.start(250);
      setIsRecording(true);
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } catch (err) {
      setError('Microphone access denied — please allow microphone permission and try again.');
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    clearInterval(timerRef.current);
  }

  const isArabic = result?.language_detected === 'ar' || language === 'ar';

  return (
    <div>
      <div className="card">
        <h2>{labels.moduleCTitle}</h2>

        {language === 'ar' && (
          <div className="info-tip">💡 {labels.arabicTip}</div>
        )}

        {/* Language selector */}
        <div style={{ marginBottom: '1.25rem', maxWidth: 280 }}>
          <SelectField label={labels.language} id="c-lang" name="c-lang"
            value={language} onChange={e => { setLanguage(e.target.value); setResult(null); }}>
            <option value="ar">العربية - Arabic</option>
            <option value="fr">Français - French</option>
            <option value="en">English</option>
          </SelectField>
        </div>

        {/* Reference audio from Module B */}
        {referenceAudioUrl && (
          <div className="reference-audio-box">
            <p className="ref-audio-label">🔊 {labels.sourceAudio}</p>
            <audio controls src={referenceAudioUrl} style={{ width: '100%' }} />
          </div>
        )}

        {/* Recording section */}
        <div className="record-section">
          <p className="record-section-label">🎙 {labels.yourInterpretation}</p>

          <div className="record-controls">
            {!isRecording ? (
              <button className="btn-record" onClick={startRecording}>
                {labels.recordBtn}
              </button>
            ) : (
              <button className="btn-record recording-active" onClick={stopRecording}>
                <span className="rec-dot" /> {labels.stopBtn} — {formatTime(recordingTime)}
              </button>
            )}

            <label className="auto-transcribe-toggle">
              <input type="checkbox" checked={autoTranscribe}
                onChange={e => setAutoTranscribe(e.target.checked)} />
              {labels.autoTranscribe}
            </label>
          </div>

          {/* Recorded audio playback */}
          {recordedUrl && !isRecording && (
            <div style={{ marginTop: '0.75rem' }}>
              <audio controls src={recordedUrl} style={{ width: '100%' }} />
              {!autoTranscribe && (
                <button className="btn-primary" style={{ marginTop: '0.75rem' }}
                  onClick={() => runTranscription(recordedBlob)}
                  disabled={status === 'loading'}>
                  {status === 'loading' ? labels.transcribing : labels.transcribeBtn}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Upload fallback */}
        <details className="upload-fallback">
          <summary>{labels.orUpload}</summary>
          <div style={{ marginTop: '0.75rem' }}>
            <input type="file" accept=".mp3,.wav,.m4a,.ogg,.webm" className="file-input"
              onChange={e => {
                const f = e.target.files[0];
                if (f) runTranscription(f);
              }} />
          </div>
        </details>
      </div>

      {/* Results card */}
      {(status === 'loading' || result || error) && (
        <div className="card">
          {status === 'loading' && (
            <div className="transcribing-state">
              <div className="spinner" />
              <p>{labels.transcribing}</p>
            </div>
          )}
          {error && <div className="error-msg">{labels.errorPrefix}: {error}</div>}

          {result && (
            <div className="transcript-result">
              <div className="result-meta" style={{ marginBottom: '0.75rem' }}>
                {result.duration_seconds > 0 && <span>{result.duration_seconds}s</span>}
                <span>{(result.language_detected || '').toUpperCase()}</span>
                {result.method && <span className="method-badge">{result.method}</span>}
              </div>

              {lowConfWords.length > 0 && (
                <div className="warning-msg" style={{ marginBottom: '0.75rem' }}>
                  ⚠️ {labels.lowConfidence}: {lowConfWords.slice(0, 10).map(w => w.word.trim()).join(', ')}
                </div>
              )}

              <TranscriptBubble
                text={result.full_text}
                vocalizedText={result.vocalized_text}
                isArabic={isArabic}
                onRetranscribe={recordedBlob ? () => runTranscription(recordedBlob) : null}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Module D — Full Evaluation Report ────────────────────────────────────────

function ScoreBar({ score }) {
  const pct = Math.round((score / 10) * 100);
  const color = score >= 7 ? '#1a6b3c' : score >= 5 ? '#b0772f' : '#c0392b';
  return (
    <div className="score-bar-wrap">
      <div className="score-number" style={{ color }}>{score.toFixed(1)}<span>/10</span></div>
      <div className="score-track">
        <div className="score-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

function EvalSection({ title, icon, items, renderItem, emptyLabel }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="eval-section">
      <button className="eval-section-header" onClick={() => setOpen(o => !o)}>
        <span>{icon} {title}</span>
        <span className={`eval-badge ${items.length > 0 ? 'eval-badge-warn' : 'eval-badge-ok'}`}>
          {items.length}
        </span>
        <span className="eval-chevron">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="eval-section-body">
          {items.length === 0
            ? <p className="eval-empty">✓ {emptyLabel}</p>
            : items.map((item, i) => <div key={i} className="eval-item">{renderItem(item)}</div>)
          }
        </div>
      )}
    </div>
  );
}

// ── Tashkeel / Pronunciation Panel (text comparison — no audio needed) ───────

function PronunciationPanel({ labels, lastTranscript, lastGeneratedScript }) {
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError]   = useState('');

  const language   = lastTranscript?.language || lastTranscript?.language_detected || 'ar';
  const sourceText = lastGeneratedScript?.script || '';
  const transcript = lastTranscript?.full_text  || '';

  if (language !== 'ar') return <div className="info-tip">ℹ️ {labels.needsArabic}</div>;
  if (!sourceText)       return <div className="info-tip">ℹ️ {labels.needsSource}</div>;

  async function runCompare() {
    setStatus('loading');
    setError('');
    setResult(null);
    try {
      const data = await tashkeelCompare(sourceText, transcript, language);
      setResult(data);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  const coverageColor = result
    ? (result.coverage_score >= 8 ? '#1a6b3c' : result.coverage_score >= 6 ? '#b0772f' : '#c0392b')
    : 'var(--color-text)';

  return (
    <div>
      <button className="btn-primary" onClick={runCompare} disabled={status === 'loading'}>
        {status === 'loading' ? labels.runningPronunciation : labels.runPronunciation}
      </button>

      {status === 'loading' && (
        <div className="transcribing-state" style={{ marginTop: '1rem' }}>
          <div className="spinner" /><p>{labels.runningPronunciation}</p>
        </div>
      )}
      {error && <div className="error-msg" style={{ marginTop: '0.75rem' }}>{labels.errorPrefix}: {error}</div>}

      {result && (
        <div style={{ marginTop: '1.5rem' }}>

          {/* Scores */}
          <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <div>
              <p className="report-label">Coverage score</p>
              <div className="score-number" style={{ color: coverageColor }}>
                {result.coverage_score?.toFixed(1)}<span>/10</span>
              </div>
            </div>
            <div>
              <p className="report-label">{labels.overallScore}</p>
              <div className="score-number" style={{ color: coverageColor }}>
                {result.overall_score?.toFixed(1)}<span>/10</span>
              </div>
            </div>
          </div>

          {result.summary && (
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
              {result.summary}
            </p>
          )}

          {/* Missing information */}
          {(result.missing_content || []).length > 0 && (
            <div className="materials-section">
              <h4 style={{ color: '#c0392b', fontSize: '0.85rem', fontWeight: 700,
                textTransform: 'uppercase', marginBottom: '0.6rem' }}>
                📉 {labels.informationLoss} ({result.missing_content.length})
              </h4>
              {result.missing_content.map((item, i) => (
                <div key={i} className="eval-item">
                  <span className="eval-text">{item.content || item}</span>
                  {item.importance && (
                    <span className={`importance-badge importance-${item.importance}`}>
                      {item.importance}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Tashkeel errors */}
          {(result.tashkeel_errors || []).length > 0 && (
            <div className="materials-section">
              <h4 style={{ color: '#b0772f', fontSize: '0.85rem', fontWeight: 700,
                textTransform: 'uppercase', marginBottom: '0.6rem' }}>
                ⚠️ {labels.languageErrors} — إعراب / تشكيل ({result.tashkeel_errors.length})
              </h4>
              {result.tashkeel_errors.map((err, i) => (
                <div key={i} className="uncertain-word-card">
                  <div className="uncertain-word-header">
                    <span className="uncertain-word arabic">{err.word}</span>
                    {err.expected_form && (
                      <span className="detail-label" style={{ marginLeft: '0.5rem' }}>
                        → <span className="arabic" style={{ fontSize: '1.1rem', color: '#1a6b3c' }}>{err.expected_form}</span>
                      </span>
                    )}
                  </div>
                  {err.expected_case && (
                    <div className="uncertain-detail">
                      <span className="detail-label">{labels.grammaticalRole}:</span>
                      <span className="detail-value">{err.expected_case}</span>
                    </div>
                  )}
                  {err.likely_student_error && (
                    <div className="uncertain-detail">
                      <span className="detail-label">{labels.likelyError}:</span>
                      <span className="detail-value" style={{ color: '#c0392b' }}>{err.likely_student_error}</span>
                    </div>
                  )}
                  {err.explanation && <p className="uncertain-explanation">{err.explanation}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Correct tashkeel */}
          {(result.tashkeel_correct || []).length > 0 && (
            <div className="materials-section">
              <h4 style={{ color: '#1a6b3c', fontSize: '0.85rem', fontWeight: 700,
                textTransform: 'uppercase', marginBottom: '0.6rem' }}>
                ✅ Correct tashkeel ({result.tashkeel_correct.length})
              </h4>
              <div className="key-terms-list">
                {result.tashkeel_correct.map((w, i) => (
                  <span key={i} className="key-term-badge arabic" style={{ fontSize: '1rem' }}
                    title={w.note}>{w.form || w.word}</span>
                ))}
              </div>
            </div>
          )}

          {(result.tashkeel_errors || []).length === 0 && (result.missing_content || []).length === 0 && (
            <div className="eval-item">✓ {labels.noIssues}</div>
          )}
        </div>
      )}
    </div>
  );
}

function ModuleD({ labels, lastTranscript, lastGeneratedScript, lastRecordingBlob }) {
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');

  const language = lastTranscript?.language || lastTranscript?.language_detected || 'ar';

  async function handleEvaluate() {
    setStatus('loading');
    setError('');
    setReport(null);
    try {
      let data;
      if (lastRecordingBlob) {
        // Best path: re-transcribe locally for word timestamps + detect everything
        const audioFile = new File([lastRecordingBlob], 'recording.webm',
          { type: lastRecordingBlob.type });
        data = await evaluateWithAudio(
          audioFile,
          lastGeneratedScript?.script || '',
          language,
          lastGeneratedScript?.language || language
        );
      } else {
        // Fallback: use stored Groq transcript (less accurate for hesitations)
        data = await generateFeedback({
          source_script:   lastGeneratedScript?.script || '',
          transcript_text: lastTranscript.full_text,
          transcript:      lastTranscript,
          language
        });
      }
      // If full-evaluation returned word scores, attach to lastTranscript for pronunciation panel
      if (data.pronunciation) {
        const wordDisplay = (data.pronunciation.words || []).map(w => ({
          ...w,
          word: w.word
        }));
        data._pronunciationForPanel = {
          word_display:  wordDisplay,
          overall_score: data.pronunciation.overall_score,
          errors_found:  data.pronunciation.errors_found,
          summary:       data.pronunciation.overall_score >= 0.8
            ? 'Good pronunciation confidence.'
            : `${data.pronunciation.errors_found} word(s) with low confidence.`,
          whisperx_used: false
        };
      }
      setReport(data);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  if (!lastTranscript) {
    return (
      <div className="card coming-soon">
        <p className="eyebrow">{labels.moduleDTitle}</p>
        <p>{labels.noTranscriptYet}</p>
      </div>
    );
  }

  const algo = report?.algorithmic || {};
  const isAr = (lastTranscript.language || lastTranscript.language_detected) === 'ar';

  return (
    <div>
      <div className="card">
        <h2>{labels.moduleDTitle}</h2>
        <div className="info-tip" style={{ marginBottom: '1rem' }}>
          📄 Transcript ready ({lastTranscript.duration_seconds}s · {(lastTranscript.language_detected || '').toUpperCase()})
          {lastGeneratedScript && <> · Source: {lastGeneratedScript.domain}</>}
        </div>
        <button className="btn-primary" onClick={handleEvaluate} disabled={status === 'loading'}>
          {status === 'loading' ? labels.runningEvaluation : labels.runEvaluation}
        </button>
        {status === 'loading' && (
          <div className="transcribing-state" style={{ marginTop: '1rem' }}>
            <div className="spinner" /><p>{labels.runningEvaluation}</p>
          </div>
        )}
        {error && <div className="error-msg" style={{ marginTop: '1rem' }}>{labels.errorPrefix}: {error}</div>}
      </div>

      {report && (
        <div className="report-card">

          {/* Score + Summary */}
          <div className="card report-header">
            <div className="report-score-row">
              <div>
                <p className="report-label">{labels.overallScore}</p>
                <ScoreBar score={report.overall_score || 0} />
              </div>
              {(report.strengths || []).length > 0 && (
                <div className="report-strengths">
                  <p className="report-label">✅ {labels.strengths}</p>
                  <ul>{(report.strengths || []).map((s, i) => <li key={i}>{s}</li>)}</ul>
                </div>
              )}
            </div>
            {report.summary && (
              <div className="report-summary">
                <p className="report-label">📋 {labels.evalSummary}</p>
                <p className={isAr ? 'arabic' : ''}>{report.summary}</p>
              </div>
            )}
          </div>

          {/* Algorithmic detections */}
          <div className="card">
            <h3 className="report-section-title">🔍 {labels.algorithmicTitle}</h3>
            <div className="algo-grid">
              {[
                { label: labels.longSilences,  icon: '🔇', items: algo.long_silences || [] },
                { label: labels.repetitions,   icon: '🔁', items: algo.repetitions || [] },
                { label: labels.hesitations,   icon: '🗣️', items: algo.hesitation_words || [] },
                { label: labels.numberErrors,  icon: '🔢', items: algo.number_errors || [] },
              ].map(({ label, icon, items }) => (
                <div key={label} className={`algo-card ${items.length > 0 ? 'algo-card-warn' : ''}`}>
                  <span className="algo-icon">{icon}</span>
                  <span className="algo-count">{items.length}</span>
                  <span className="algo-label">{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Coverage score */}
          {report.coverage_score !== undefined && (
            <div className="card">
              <h3 className="report-section-title">📊 Content coverage</h3>
              <ScoreBar score={report.coverage_score} />
              <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#666' }}>
                How much of the source speech was conveyed in the interpretation
              </p>
            </div>
          )}

          {/* Translation errors */}
          {(report.translation_errors || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">🔄 Translation errors</h3>
              {(report.translation_errors || []).map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid #e53e3e', paddingLeft: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '0.25rem' }}>Source said:</div>
                  <div className="eval-text" style={{ marginBottom: '0.25rem' }}>"{item.source_text}"</div>
                  <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '0.25rem' }}>Student said: <strong style={{ color: '#e53e3e' }}>{item.student_said}</strong></div>
                  <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '0.25rem' }}>Correct: <strong style={{ color: '#38a169' }}>{item.correct_translation}</strong></div>
                  {item.explanation && <div className="eval-explanation">{item.explanation}</div>}
                </div>
              ))}
            </div>
          )}

          {/* Missing content */}
          {(report.missing_content || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">📉 Missing content</h3>
              {(report.missing_content || []).map((item, i) => (
                <div key={i} className="eval-item" style={{ marginBottom: '0.5rem' }}>
                  <span className="eval-text">{item.content}</span>
                  {item.importance && <span className={`importance-badge importance-${item.importance}`}>{item.importance}</span>}
                </div>
              ))}
            </div>
          )}

          {/* Pronunciation flags */}
          {(report.pronunciation_flags || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">🔊 Pronunciation flags</h3>
              <p style={{ fontSize: '0.82rem', color: '#666', marginBottom: '0.75rem' }}>
                Words Whisper was uncertain about — may indicate unclear or incorrect pronunciation
              </p>
              {(report.pronunciation_flags || []).map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid #ed8936', paddingLeft: '0.75rem', marginBottom: '0.5rem' }}>
                  <strong>"{item.word}"</strong>
                  {item.confidence !== undefined && <span style={{ fontSize: '0.78rem', color: '#888', marginLeft: '0.5rem' }}>confidence: {(item.confidence * 100).toFixed(0)}%</span>}
                  {item.likely_issue && <div className="eval-explanation">{item.likely_issue}</div>}
                </div>
              ))}
            </div>
          )}

          {/* LLM analysis sections */}
          <div className="card">
            <h3 className="report-section-title">🤖 {labels.llmTitle}</h3>
            <EvalSection title={labels.languageErrors} icon="⚠️"
              items={report.language_errors || []} emptyLabel={labels.noIssues}
              renderItem={item => (
                <div>
                  <span className={`eval-text ${isAr ? 'arabic' : ''}`}>"{item.text}"</span>
                  <span className="eval-explanation"> — {item.explanation}</span>
                  {item.correction && <div className="eval-correction">✓ {labels.correction}: <strong>{item.correction}</strong></div>}
                </div>
              )} />
            <EvalSection title={labels.autoCorrections} icon="✏️"
              items={report.auto_corrections || []} emptyLabel={labels.noIssues}
              renderItem={item => <span className={isAr ? 'arabic' : ''}>{item.text}</span>} />
            <EvalSection title={labels.falseStarts} icon="🚦"
              items={report.false_starts || []} emptyLabel={labels.noIssues}
              renderItem={item => <span className={isAr ? 'arabic' : ''}>{item.text}</span>} />
            <EvalSection title={labels.lapsusLinguae} icon="👅"
              items={report.lapsus_linguae || []} emptyLabel={labels.noIssues}
              renderItem={item => (
                <div>
                  <span className={`eval-text ${isAr ? 'arabic' : ''}`}>"{item.text}"</span>
                  {item.likely_intended && <span className="eval-explanation"> → {item.likely_intended}</span>}
                </div>
              )} />
            <EvalSection title={labels.terminologyProblems} icon="📚"
              items={report.terminology_problems || []} emptyLabel={labels.noIssues}
              renderItem={item => (
                <div className="term-row">
                  <span className="term-cell"><small>{labels.source}:</small> {item.source_term}</span>
                  <span className="term-cell"><small>{labels.used}:</small> <strong className="term-wrong">{item.student_used}</strong></span>
                  <span className="term-cell"><small>{labels.correct}:</small> <strong className="term-right">{item.correct_equivalent}</strong></span>
                </div>
              )} />
            <EvalSection title={labels.informationLoss} icon="📉"
              items={report.information_loss || []} emptyLabel={labels.noIssues}
              renderItem={item => (
                <div>
                  <span className="eval-text">{item.lost_content}</span>
                  {item.importance && <span className={`importance-badge importance-${item.importance}`}>{item.importance}</span>}
                </div>
              )} />
          </div>

          {/* Recommendations */}
          {(report.recommendations || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">💡 {labels.recommendations}</h3>
              <ul className="recommendations-list">
                {report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Pronunciation Assessment — Arabic only */}
      {lastTranscript && (lastTranscript.language || lastTranscript.language_detected) === 'ar' && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3 className="report-section-title">🔤 {labels.pronunciationTitle}</h3>
          <PronunciationPanel
            labels={labels}
            lastTranscript={lastTranscript}
            lastGeneratedScript={lastGeneratedScript}
          />
        </div>
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
