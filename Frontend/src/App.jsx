import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  generateSpeech,
  generateSpeechFromDocument,
  loginUser,
  logoutUser,
  retrieveDocumentContext,
  signupUser,
  textToSpeech,
  downloadGlossary,
  transcribeAudio,
  generateFeedback,
  evaluateWithAudio,
  tashkeelCompare,
  alignPronunciation,
  getPronunciationReport,
  searchUNLibrary,
  fetchUNDocument,
  getSavedSpeeches,
  getSavedSpeech,
  deleteSavedSpeech,
  getSessionHistory,
  getAdaptiveParams,
  getStoredGroqKey,
  saveGroqKey,
  setCurrentUserId,
  validateGroqKey,
  saveAuthToken,
  sendChatMessage,
  fetchWebPage,
  SERVER_BASE,
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
    navE: 'Progress',
    navSettings: 'Settings',
    settingsTitle: 'Settings',
    settingsGroqTitle: 'Your Groq API Key',
    settingsGroqDesc: 'Paste your personal Groq API key here. It is stored only in your browser and sent securely with each request.',
    settingsGroqPlaceholder: 'gsk_...',
    settingsGroqGetKey: 'Get a free key at console.groq.com',
    settingsGroqTest: 'Test key',
    settingsGroqTesting: 'Testing...',
    settingsGroqSave: 'Save key',
    settingsGroqClear: 'Remove key',
    settingsGroqValid: 'Key is valid and working.',
    settingsGroqInvalid: 'Invalid key — check and try again.',
    settingsGroqNotSet: 'No key saved yet — click the link above to create a free one at console.groq.com, then paste it in the field and save.',
    settingsGroqSaved: 'Key saved.',
    settingsClose: 'Close',
    bannerNoKey: 'No Groq API key configured. Go to Settings to add your personal key, or ask the admin to configure a server key.',
    progressTitle: 'My Progress',
    progressSubtitle: 'Score history and adaptive recommendations',
    progressNoSessions: 'No sessions yet — complete a full evaluation to start tracking your progress.',
    progressSessions: 'Session history',
    progressAdaptive: 'Adaptive recommendations',
    progressAdaptiveSubtitle: 'Based on your recent sessions, the platform recommends:',
    progressApply: 'Apply these settings',
    progressOverall: 'Overall',
    progressFluency: 'Fluency',
    progressCoverage: 'Coverage',
    progressErrors: 'Errors',
    progressLang: 'Language',
    progressDate: 'Date',
    progressScore: 'Score',
    progressLoading: 'Loading history…',
    progressAvgOver: 'Avg. overall',
    progressAvgFluency: 'Avg. fluency',
    progressAvgNumbers: 'Avg. number errors',
    progressTrend: 'Score trend (last 10 sessions)',
    progressLatest: 'Latest session',
    progressProblems: 'Focus areas — what to work on',
    progressImproving: 'Improving',
    progressDeclining: 'Declining',
    progressStable: 'Stable',
    progressStrengths: 'Strengths',
    progressRecs: 'Recommendations',
    progressTopErrors: 'Specific errors',
    progressNoData: 'Not enough data yet',
    moduleATitle: 'Generate training speech',
    groundedSourceLabel: 'Grounded in a real source:',
    ungroundedNote: 'No matching UN document was found — this speech was generated without source grounding.',
    language: 'Speech language',
    targetLanguage: 'Target language',
    topic: 'Topic',
    domain: 'Domain',
    wordCount: 'Speech length',
    wordRangeShort: 'Short',
    wordRangeMedium: 'Medium',
    wordRangeLong: 'Long',
    difficulty: 'Difficulty',
    structure: 'Discourse structure',
    mode: 'Interpretation mode',
    numbers: 'Number density',
    hesitationsSim: 'Simulate hesitations',
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
    moduleBBody: 'Will produce: audio playback, key terms, glossary, and MCQ.',
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
    mcqQuestionHeader: 'Question',
    mcqOptionsHeader: 'Options',
    mcqAnswerHeader: 'Answer',
    glossaryTitle: 'Trilingual glossary (AR – FR – EN)',
    glossaryTermHeader: 'Term',
    glossaryArabicHeader: 'Arabic',
    glossaryFrenchHeader: 'French',
    glossaryEnglishHeader: 'English',
    glossaryDefinitionHeader: 'Definition',
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
    coverageTitle: 'Content coverage',
    coverageHint: 'How much of the source speech was conveyed',
    translationErrors: 'Translation errors',
    sourceSaid: 'Source said',
    studentSaid: 'Student said',
    correctTranslation: 'Correct',
    missingContent: 'Missing content',
    fluencyScore: 'Fluency score',
    pauseAnalysisTitle: 'Pauses & flow',
    repetitionAnalysisTitle: 'Repetitions — analysis',
    numberAccuracyTitle: 'Numbers & dates',
    pronunciationAssessmentTitle: 'Pronunciation feedback',
    numCorrect: 'Correct',
    numIncorrect: 'Incorrect',
    expectedLabel: 'Should be',
    studentSaidShort: 'Said',
    pronunciationTitle: 'Pronunciation Assessment',
    pronunciationMismatches: 'Word-level clarity mismatches',
    runPronunciation: 'Run pronunciation check',
    runningPronunciation: 'Aligning audio against source — may take 1 min...',
    pronunciationScore: 'Confidence',
    wordView: 'Word-by-word view',
    legend: 'Legend',
    legendGood: '≥80% confident',
    legendWarn: '65–80%',
    legendPoor: '<65% — likely error',
    uncertainWords: 'Meaningful low-confidence words',
    expectedForm: 'Expected',
    likelyError: 'Likely error',
    grammaticalRole: 'Grammatical role',
    noUncertain: 'No meaningful low-confidence words',
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
    deleteAudio: 'Delete audio',
    redoTranscript: 'Redo transcription',
    copyText: 'Copy',
    copied: 'Copied!',
    topicPlaceholder: 'Enter a topic or paste text to generate a speech…',
    moreSettings: 'More ⚙',
    lessSettings: 'Less ⚙',
    optConsecutive: 'Consecutive',
    optSimultaneous: 'Simultaneous',
    optSight: 'Sight translation',
    optWellOrganized: 'Well organized',
    optDisorganized: 'Disorganized',
    optLowNumbers: 'Low numbers',
    optHighNumbers: 'High numbers',
    optNormalSpeed: 'Normal speed',
    optFast: 'Fast',
    optVeryFast: 'Very fast',
    optNoShifts: 'No topic shifts',
    optShifts: 'Topic shifts',
    domPolitics: 'Politics',
    domDiplomacy: 'Diplomacy',
    domEconomics: 'Economics',
    domHealth: 'Health',
    domEducation: 'Education',
    domClimate: 'Climate & Environment',
    domHumanRights: 'Human Rights',
    domTechnology: 'Technology & AI',
    domMigration: 'Migration & Refugees',
    domDisarmament: 'Disarmament',
    domWomen: 'Women & Gender',
    domFood: 'Food & Hunger',
    diffBeginner: 'Beginner',
    diffIntermediate: 'Intermediate',
    diffAdvanced: 'Advanced',
    diffHint: 'Beginner: simple vocabulary, short sentences, 1–2 numbers, slow pace. Intermediate: moderate terminology, several statistics, mixed sentences. Advanced: dense terminology, frequent numbers and names, complex syntax, fast pace.',
    demoKeyBanner: 'This platform uses a free AI service (Groq) to generate and evaluate speeches. Right now you are using the platform\'s shared demonstration key, which works but is slower and has shared daily limits. Creating your own free key (2 minutes, no credit card) gives you faster responses and your own quota.',
    demoKeyBtn: 'Add my free key in Settings',
    wordRangeShortFull: 'Short — 120–180 words (≈ 1–1.5 min at 120 wpm)',
    wordRangeMediumFull: 'Medium — 220–320 words (≈ 2–2.5 min)',
    wordRangeLongFull: 'Long — 400–550 words (≈ 3.5–4.5 min)',
    wordRangeExtendedFull: 'Extended — 650–800 words (≈ 5.5–6.5 min)',
    optSemiStructured: 'Semi-structured',
    optDisorganizedFull: 'Deliberately disorganized',
    scenarioLabel: 'Speaker style / setting',
    scenUNGA: 'UN General Assembly',
    scenEUParl: 'EU Parliament',
    scenArabLeague: 'Arab League summit',
    scenPress: 'Press conference',
    scenDiplomatic: 'Diplomatic meeting',
    scenDebate: 'Political debate',
    scenInterview: 'Interview',
    termDensity: 'Terminology density',
    optTermLow: 'Low — everyday vocabulary',
    optTermMedium: 'Medium',
    optTermHigh: 'High — dense specialised terms',
    longTextAsSource: 'Long text detected — it will be used as the source document and the speech will be grounded in it.',
    mcqPickAnswer: 'Select your answer, then check it.',
    mcqCheck: 'Check answer',
    mcqShowAnswer: 'Show answer',
    mcqCorrectMsg: '✓ Correct!',
    mcqWrongMsg: '✗ Not quite. Correct answer:',
    mcqShowAnswerLabel: 'ℹ️ Correct answer:',
    mcqYourScore: 'Your score',
    glossaryEdit: '✏️ Edit glossary',
    glossaryEditDone: '✓ Done editing',
    glossaryEditHint: 'Review and correct the equivalents BEFORE recording your interpretation — the evaluation will then check your terminology against this approved glossary.',
    webPageTab: 'Web page',
    webPageUrlPlaceholder: 'https://… paste the address of an article or report',
    webPageFetch: 'Fetch page',
    webPageFetching: 'Fetching page…',
    webPageHint: 'The readable text of the page will be extracted and used as the source for the speech.',
    scrollerTitle: 'Sight translation — scrolling text',
    scrollerPlay: '▶ Start scrolling',
    scrollerPause: '⏸ Pause',
    scrollerReset: '↺ Reset',
    scrollerSpeed: 'Speed (words/min)',
    scrollerFontSize: 'Text size',
    scrollerColumns: 'Columns',
    scrollerSpacing: 'Line spacing',
    scrollerHint: 'Translate aloud while the text scrolls at your chosen speed — like a real sight translation exercise.',
    notesTitle: '📝 Notes (consecutive)',
    notesTextTab: 'Text notes',
    notesSketchTab: 'Sketch / mind map',
    notesClear: 'Clear',
    notesPlaceholder: 'Take your notes here while listening (symbols, arrows, keywords)…',
    notesHint: 'Your notes stay on this page only — they are not saved or sent anywhere.',
    simulTitle: '🎧 Simultaneous mode',
    simulStart: '▶ Play source + record me',
    simulStop: '⏹ Stop both',
    simulHint: 'Wear headphones so the source audio is not captured by your microphone. The source speech plays while your interpretation is recorded — real simultaneous practice.',
    simulNeedsAudio: 'Generate the source audio in "Audio & materials" first to enable simultaneous mode.',
    prepTimeLabel: 'preparation time before speaking — not counted against fluency',
    fluencyExplain: 'This score is measured from your recording: speaking rate, pauses during delivery, and how clearly each word was recognized. Time you take to prepare before speaking is NOT counted. A word recognized with low confidence means it sounded unclear — it is treated as a clarity signal, not automatically as a mistake.',
    aboutEvalTitle: 'ℹ️ How this evaluation works & where your data goes',
    aboutEvalCriteria: 'What is analyzed: (1) your recording is transcribed by a speech recognizer (Whisper); (2) measurable events are detected directly from the audio — pauses, repetitions, hesitations, speaking rate; (3) an AI evaluator compares your interpretation to the source speech meaning-by-meaning: accuracy, coverage, terminology, numbers and dates, grammar; (4) scores follow a strict professor rubric (most student performances score 4–7/10).',
    aboutEvalReliability: 'Reliability: the transcript is an estimate, not ground truth — especially for Arabic. Unclear audio regions are treated as clarity issues, not automatically as translation errors. Use this report as a training aid, not a final grade.',
    aboutEvalStorage: 'Storage: your audio recording is processed and then deleted from the server — it is not kept. Only the evaluation summary (scores, error counts, recommendations) is saved to your account history to power the Progress page. Generated speeches and transcripts are not stored permanently.',
    creditsLine: 'ETIB · ESIB · CINIA · USJ Beirut',
    modeChoose: 'Practice mode',
    modeSimulDesc: 'The source speech plays while you interpret and record at the same time.',
    modeConsecDesc: 'Listen to the source and take notes, then record your interpretation.',
    modeSightDesc: 'Read the scrolling text and translate aloud while recording yourself.',
    heroTrainIn: 'Train in:',
    heroTitlePre: 'Master interpretation with ',
    heroTitleEm: 'AI-generated',
    heroTitlePost: ' speeches',
    heroParagraph: 'An adaptive training platform that generates realistic conference speeches, builds multilingual glossaries, and evaluates your interpretation performance across Arabic, French, and English.',
    guestBtn: 'Continue as Guest',
    orSep: '— or —',
    srcPanelTitle: 'Add Source',
    srcPanelSubtitle: 'Find a UN document, a web page, or upload your own file to ground the speech in real content.',
    srcTabUN: 'UN Library',
    srcTabUpload: 'Upload file',
    srcUNHint: 'Search the UN Digital Library for your topic, download the PDF, then upload it below.',
    srcUNSearchBtn: 'Search UN Library ↗',
    srcUNUploadAfter: 'Once you have downloaded the PDF, upload it here:',
    srcDropPdf: 'Drop the PDF here or',
    srcDropFile: 'Drop a file here or',
    srcBrowse: 'browse',
    srcFileTypes: 'PDF, Word (.docx), or plain text',
    audioFluencyTitle: 'Audio fluency from the recording',
    coverageScoreLabel: 'Coverage score',
    statSpeechRate: 'Speech rate',
    statLongPauses: 'Long pauses',
    statSilenceRatio: 'Silence ratio',
    statWordConfidence: 'Word confidence',
    verdictGood: 'Good',
    verdictAcceptable: 'Acceptable',
    verdictNeedsWork: 'Needs work',
    nextHintPre: '→ Go to',
    nextHintPost: 'to listen, review questions, and download the glossary.',
    transcriptReady: 'Transcript ready',
    chatGreeting: "Hi! I'm your ETIB assistant. Ask me anything about interpretation techniques, the platform, or terminology.",
    chatPlaceholder: 'Ask anything…',
    chatSend: 'Send',
    chatThinking: 'Thinking…',
    statAvgPerSession: 'avg / session',
    statTotal: 'total',
    statSessions: 'Sessions',
    outsideRange: '(outside requested range)',
    progressGuestNote: 'Progress tracking works with an account. Sign in (or create a free account) so your evaluations are saved and analyzed across sessions.',
    pnTitle: 'Proper nouns (people, organizations, places)',
    pnCorrect: 'Correct',
    pnDistorted: 'Distorted — likely mispronounced',
    pnMissing: 'Omitted',
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
    switchToSignup: 'إنشاء حساب جديد',
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
    navE: 'التقدم',
    navSettings: 'الإعدادات',
    settingsTitle: 'الإعدادات',
    settingsGroqTitle: 'مفتاح Groq API الشخصي',
    settingsGroqDesc: 'الصق مفتاح Groq API الخاص بك. يُحفظ في متصفحك فقط ويُرسل بشكل آمن مع كل طلب.',
    settingsGroqPlaceholder: 'gsk_...',
    settingsGroqGetKey: 'احصل على مفتاح مجاني من console.groq.com',
    settingsGroqTest: 'اختبار المفتاح',
    settingsGroqTesting: 'جارٍ الاختبار...',
    settingsGroqSave: 'حفظ المفتاح',
    settingsGroqClear: 'حذف المفتاح',
    settingsGroqValid: 'المفتاح صالح ويعمل.',
    settingsGroqInvalid: 'مفتاح غير صالح — تحقق وأعد المحاولة.',
    settingsGroqNotSet: 'لا يوجد مفتاح محفوظ — انقر على الرابط أعلاه لإنشاء مفتاح مجاني من console.groq.com ثم الصقه في الحقل واحفظه.',
    settingsGroqSaved: 'تم حفظ المفتاح.',
    settingsClose: 'إغلاق',
    bannerNoKey: 'لم يتم تهيئة مفتاح Groq API. انتقل إلى الإعدادات لإضافة مفتاحك الشخصي.',
    progressTitle: 'تقدمي',
    progressSubtitle: 'سجل الدرجات والتوصيات التكيفية',
    progressNoSessions: 'لا جلسات بعد — أكمل تقييماً كاملاً لبدء تتبع تقدمك.',
    progressSessions: 'سجل الجلسات',
    progressAdaptive: 'التوصيات التكيفية',
    progressAdaptiveSubtitle: 'بناءً على جلساتك الأخيرة، توصي المنصة بما يلي:',
    progressApply: 'تطبيق هذه الإعدادات',
    progressOverall: 'إجمالي',
    progressFluency: 'الطلاقة',
    progressCoverage: 'التغطية',
    progressErrors: 'الأخطاء',
    progressLang: 'اللغة',
    progressDate: 'التاريخ',
    progressScore: 'الدرجة',
    progressLoading: 'جارٍ تحميل السجل…',
    progressAvgOver: 'متوسط الإجمالي',
    progressAvgFluency: 'متوسط الطلاقة',
    progressAvgNumbers: 'متوسط أخطاء الأرقام',
    progressTrend: 'منحنى الدرجات (آخر 10 جلسات)',
    progressLatest: 'آخر جلسة',
    progressProblems: 'نقاط التركيز — ما يجب العمل عليه',
    progressImproving: 'تحسّن',
    progressDeclining: 'تراجع',
    progressStable: 'مستقر',
    progressStrengths: 'نقاط القوة',
    progressRecs: 'التوصيات',
    progressTopErrors: 'أخطاء محددة',
    progressNoData: 'بيانات غير كافية بعد',
    moduleATitle: 'توليد خطاب تدريبي',
    groundedSourceLabel: 'مستند إلى مصدر حقيقي:',
    ungroundedNote: 'لم يتم العثور على وثيقة أممية مطابقة — تم إنشاء هذا الخطاب دون الاستناد إلى مصدر.',
    language: 'لغة الخطاب',
    targetLanguage: 'لغة الترجمة الهدف',
    topic: 'الموضوع',
    domain: 'المجال',
    wordCount: 'طول الخطاب',
    wordRangeShort: 'قصير',
    wordRangeMedium: 'متوسط',
    wordRangeLong: 'طويل',
    difficulty: 'مستوى الصعوبة',
    structure: 'بنية الخطاب',
    mode: 'نوع الترجمة الفورية',
    numbers: 'كثافة الأرقام',
    hesitationsSim: 'محاكاة التردد',
    pressureMode: 'وضع الضغط',
    speedPressure: 'ضغط السرعة',
    topicShifts: 'تحولات الموضوع',
    contextNoise: 'ضوضاء السياق',
    cognitiveLoad: 'العبء المعرفي',
    summary: 'ملخص',
    mcq: 'أسئلة متعددة الخيارات',
    glossary: 'المسرد',
    documentGrounding: 'التوليد من وثيقة',
    documentFile: 'الوثيقة المصدر',
    sharedSettings: 'إعدادات التوليد',
    sharedSettingsHint: 'تُطبَّق هذه الإعدادات على التوليد بالموضوع أو بالوثيقة.',
    generationMethods: 'اختر مصدر التوليد',
    topicOnlyGeneration: 'توليد بالموضوع فقط',
    topicOnlyHint: 'توليد الخطاب من الموضوع والإعدادات المحددة.',
    documentGenerationHint: 'ارفع وثيقة لتوليد خطاب مستند إلى محتواها.',
    generateFromDocument: '▷ توليد من وثيقة',
    retrieveContext: 'معاينة السياق المستخرج',
    retrievedContext: 'السياق المستخرج',
    submit: 'توليد الخطاب',
    generating: 'جارٍ التوليد، يرجى الانتظار...',
    wordsUnit: 'كلمة',
    moduleBTitle: 'الصوت والمواد التعليمية',
    moduleBBody: 'إنتاج الصوت، المصطلحات الأساسية، المسرد، والأسئلة متعددة الخيارات.',
    moduleCTitle: 'التسجيل والتفريغ',
    moduleCBody: 'تسجيل داخل المتصفح، تفريغ آلي، ونص زمني.',
    moduleDTitle: 'تقييم الأداء',
    moduleDBody: 'رصد التردد، الحذف، أخطاء الأرقام، والمشاكل المصطلحية.',
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
    mcqTitle: 'أسئلة الفهم (اختيار متعدد)',
    mcqQuestionHeader: 'السؤال',
    mcqOptionsHeader: 'الخيارات',
    mcqAnswerHeader: 'الإجابة',
    glossaryTitle: 'المسرد الثلاثي (عربي – فرنسي – إنجليزي)',
    glossaryTermHeader: 'المصطلح',
    glossaryArabicHeader: 'العربية',
    glossaryFrenchHeader: 'الفرنسية',
    glossaryEnglishHeader: 'الإنجليزية',
    glossaryDefinitionHeader: 'التعريف',
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
    coverageTitle: 'تغطية المحتوى',
    coverageHint: 'مقدار ما تم نقله من الخطاب المصدر',
    translationErrors: 'أخطاء الترجمة',
    sourceSaid: 'ما قاله المصدر',
    studentSaid: 'ما قاله الطالب',
    correctTranslation: 'الترجمة الصحيحة',
    missingContent: 'محتوى مفقود',
    fluencyScore: 'درجة السلاسة',
    pauseAnalysisTitle: 'التوقفات والانسيابية',
    repetitionAnalysisTitle: 'تحليل التكرارات',
    numberAccuracyTitle: 'الأرقام والتواريخ',
    pronunciationAssessmentTitle: 'ملاحظات على النطق',
    numCorrect: 'صحيح',
    numIncorrect: 'غير صحيح',
    expectedLabel: 'الصواب',
    studentSaidShort: 'ما قاله الطالب',
    pronunciationTitle: 'تقييم النطق',
    pronunciationMismatches: 'تباينات وضوح الكلمات',
    runPronunciation: 'تشغيل فحص النطق',
    runningPronunciation: 'جارٍ المحاذاة الصوتية — قد تستغرق دقيقة...',
    pronunciationScore: 'الثقة',
    wordView: 'عرض كلمة بكلمة',
    legend: 'مفتاح الألوان',
    legendGood: '٪80 أو أكثر — صحيح',
    legendWarn: '٪65–80',
    legendPoor: 'أقل من ٪65 — خطأ محتمل',
    uncertainWords: 'كلمات مهمة منخفضة الثقة',
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
    deleteAudio: 'حذف التسجيل',
    redoTranscript: 'إعادة التفريغ',
    copyText: 'نسخ',
    copied: 'تم النسخ!',
    topicPlaceholder: 'أدخل موضوعاً أو الصق نصاً لتوليد خطاب...',
    moreSettings: 'المزيد ⚙',
    lessSettings: 'أقل ⚙',
    optConsecutive: 'تتابعي',
    optSimultaneous: 'فوري',
    optSight: 'ترجمة بصرية',
    optWellOrganized: 'منظَّم جيداً',
    optDisorganized: 'غير منظَّم',
    optLowNumbers: 'أرقام قليلة',
    optHighNumbers: 'أرقام كثيرة',
    optNormalSpeed: 'سرعة عادية',
    optFast: 'سريع',
    optVeryFast: 'سريع جداً',
    optNoShifts: 'بدون تحولات',
    optShifts: 'تحولات موضوعية',
    domPolitics: 'السياسة',
    domDiplomacy: 'الدبلوماسية',
    domEconomics: 'الاقتصاد',
    domHealth: 'الصحة',
    domEducation: 'التعليم',
    domClimate: 'المناخ والبيئة',
    domHumanRights: 'حقوق الإنسان',
    domTechnology: 'التكنولوجيا والذكاء الاصطناعي',
    domMigration: 'الهجرة واللاجئون',
    domDisarmament: 'نزع السلاح',
    domWomen: 'المرأة والنوع الاجتماعي',
    domFood: 'الغذاء والجوع',
    diffBeginner: 'مبتدئ',
    diffIntermediate: 'متوسط',
    diffAdvanced: 'متقدم',
    diffHint: 'مبتدئ: مفردات بسيطة، جمل قصيرة، رقم أو رقمان، إيقاع بطيء. متوسط: مصطلحات معتدلة، عدة إحصاءات، جمل متنوعة. متقدم: مصطلحات كثيفة، أرقام وأسماء متكررة، تراكيب معقدة، إيقاع سريع.',
    demoKeyBanner: 'تعتمد المنصة على خدمة ذكاء اصطناعي مجانية (Groq) لتوليد الخطابات وتقييمها. أنت تستخدم حالياً المفتاح التجريبي المشترك للمنصة، وهو يعمل لكنه أبطأ وله حدود استخدام مشتركة. إنشاء مفتاحك المجاني الخاص (دقيقتان، دون بطاقة ائتمان) يمنحك استجابات أسرع وحصة خاصة بك.',
    demoKeyBtn: 'أضف مفتاحي المجاني في الإعدادات',
    wordRangeShortFull: 'قصير — 120–180 كلمة (≈ 1–1.5 دقيقة بسرعة 120 كلمة/د)',
    wordRangeMediumFull: 'متوسط — 220–320 كلمة (≈ 2–2.5 دقيقة)',
    wordRangeLongFull: 'طويل — 400–550 كلمة (≈ 3.5–4.5 دقيقة)',
    wordRangeExtendedFull: 'ممتد — 650–800 كلمة (≈ 5.5–6.5 دقيقة)',
    optSemiStructured: 'شبه منظَّم',
    optDisorganizedFull: 'غير منظَّم عمداً',
    scenarioLabel: 'أسلوب المتحدث / السياق',
    scenUNGA: 'الجمعية العامة للأمم المتحدة',
    scenEUParl: 'البرلمان الأوروبي',
    scenArabLeague: 'قمة الجامعة العربية',
    scenPress: 'مؤتمر صحفي',
    scenDiplomatic: 'اجتماع دبلوماسي',
    scenDebate: 'مناظرة سياسية',
    scenInterview: 'مقابلة',
    termDensity: 'الكثافة المصطلحية',
    optTermLow: 'منخفضة — مفردات يومية',
    optTermMedium: 'متوسطة',
    optTermHigh: 'عالية — مصطلحات متخصصة كثيفة',
    longTextAsSource: 'تم رصد نص طويل — سيُستخدم كوثيقة مصدر وسيُبنى الخطاب على محتواه.',
    mcqPickAnswer: 'اختر إجابتك ثم تحقق منها.',
    mcqCheck: 'تحقق من الإجابة',
    mcqShowAnswer: 'أظهر الإجابة',
    mcqCorrectMsg: '✓ صحيح!',
    mcqWrongMsg: '✗ غير صحيح. الإجابة الصحيحة:',
    mcqShowAnswerLabel: 'ℹ️ الإجابة الصحيحة:',
    mcqYourScore: 'نتيجتك',
    glossaryEdit: '✏️ تعديل المسرد',
    glossaryEditDone: '✓ إنهاء التعديل',
    glossaryEditHint: 'راجع المقابلات وصحّحها قبل تسجيل ترجمتك — سيتحقق التقييم من مصطلحاتك وفق هذا المسرد المعتمد.',
    webPageTab: 'صفحة ويب',
    webPageUrlPlaceholder: '…https:// الصق رابط مقال أو تقرير',
    webPageFetch: 'جلب الصفحة',
    webPageFetching: 'جارٍ جلب الصفحة…',
    webPageHint: 'سيُستخرج النص المقروء من الصفحة ويُستخدم كمصدر للخطاب.',
    scrollerTitle: 'الترجمة البصرية — نص متحرك',
    scrollerPlay: '▶ بدء التمرير',
    scrollerPause: '⏸ إيقاف مؤقت',
    scrollerReset: '↺ إعادة',
    scrollerSpeed: 'السرعة (كلمة/دقيقة)',
    scrollerFontSize: 'حجم الخط',
    scrollerColumns: 'الأعمدة',
    scrollerSpacing: 'تباعد الأسطر',
    scrollerHint: 'ترجم بصوت عالٍ أثناء تمرير النص بالسرعة التي تختارها — تماماً كتمرين ترجمة بصرية حقيقي.',
    notesTitle: '📝 الملاحظات (تتابعي)',
    notesTextTab: 'ملاحظات نصية',
    notesSketchTab: 'رسم / خريطة ذهنية',
    notesClear: 'مسح',
    notesPlaceholder: 'دوّن ملاحظاتك هنا أثناء الاستماع (رموز، أسهم، كلمات مفتاحية)…',
    notesHint: 'تبقى ملاحظاتك في هذه الصفحة فقط — لا تُحفظ ولا تُرسل إلى أي مكان.',
    simulTitle: '🎧 الوضع الفوري',
    simulStart: '▶ تشغيل المصدر + تسجيلي',
    simulStop: '⏹ إيقاف الاثنين',
    simulHint: 'استخدم سماعات رأس حتى لا يلتقط الميكروفون صوت المصدر. يُشغَّل الخطاب المصدر بينما تُسجَّل ترجمتك — تدريب فوري حقيقي.',
    simulNeedsAudio: 'ولّد الصوت المصدر أولاً في «الصوت والمواد» لتفعيل الوضع الفوري.',
    prepTimeLabel: 'وقت التحضير قبل البدء بالكلام — لا يُحتسب ضد الطلاقة',
    fluencyExplain: 'تُقاس هذه الدرجة من تسجيلك: سرعة الكلام، التوقفات أثناء الأداء، ووضوح التعرف على كل كلمة. الوقت الذي تستغرقه للتحضير قبل البدء لا يُحتسب. الكلمة المُتعرَّف عليها بثقة منخفضة تعني أنها بدت غير واضحة — وتُعامل كمؤشر وضوح، لا كخطأ تلقائي.',
    aboutEvalTitle: 'ℹ️ كيف يعمل هذا التقييم وأين تذهب بياناتك',
    aboutEvalCriteria: 'ما يُحلَّل: (1) يُفرَّغ تسجيلك بواسطة نظام التعرف على الكلام (Whisper)؛ (2) تُرصد الأحداث القابلة للقياس مباشرة من الصوت — التوقفات، التكرارات، التردد، سرعة الكلام؛ (3) يقارن مقيّم ذكاء اصطناعي ترجمتك بالخطاب المصدر معنىً بمعنى: الدقة، التغطية، المصطلحات، الأرقام والتواريخ، القواعد؛ (4) تتبع الدرجات معيار أستاذ صارم (معظم أداءات الطلاب بين 4–7/10).',
    aboutEvalReliability: 'الموثوقية: النص المفرَّغ تقدير وليس حقيقة مطلقة — خصوصاً للعربية. المقاطع غير الواضحة تُعامل كمشاكل وضوح، لا كأخطاء ترجمة تلقائياً. استخدم هذا التقرير كأداة تدريب، لا كعلامة نهائية.',
    aboutEvalStorage: 'التخزين: يُعالَج تسجيلك الصوتي ثم يُحذف من الخادم — لا يُحتفظ به. يُحفظ فقط ملخص التقييم (الدرجات، عدد الأخطاء، التوصيات) في سجل حسابك لتغذية صفحة التقدم. لا تُخزَّن الخطابات المولَّدة والنصوص المفرَّغة بشكل دائم.',
    creditsLine: 'ETIB · ESIB · CINIA · جامعة القديس يوسف بيروت',
    modeChoose: 'وضع التدريب',
    modeSimulDesc: 'يُشغَّل الخطاب المصدر بينما تترجم وتسجّل في الوقت نفسه.',
    modeConsecDesc: 'استمع إلى المصدر ودوّن ملاحظاتك، ثم سجّل ترجمتك.',
    modeSightDesc: 'اقرأ النص المتحرك وترجم بصوت عالٍ أثناء تسجيل نفسك.',
    heroTrainIn: 'تدرّب بـ:',
    heroTitlePre: 'أتقن الترجمة الفورية مع ',
    heroTitleEm: 'خطابات مولّدة بالذكاء الاصطناعي',
    heroTitlePost: '',
    heroParagraph: 'منصة تدريب تكيفية تولّد خطابات مؤتمرات واقعية، وتبني مسارد متعددة اللغات، وتقيّم أداءك في الترجمة الفورية بين العربية والفرنسية والإنجليزية.',
    guestBtn: 'المتابعة كضيف',
    orSep: '— أو —',
    srcPanelTitle: 'إضافة مصدر',
    srcPanelSubtitle: 'ابحث عن وثيقة أممية أو صفحة ويب أو ارفع ملفك الخاص لتأسيس الخطاب على محتوى حقيقي.',
    srcTabUN: 'مكتبة الأمم المتحدة',
    srcTabUpload: 'رفع ملف',
    srcUNHint: 'ابحث في مكتبة الأمم المتحدة الرقمية عن موضوعك، نزّل ملف PDF، ثم ارفعه أدناه.',
    srcUNSearchBtn: '↗ البحث في مكتبة الأمم المتحدة',
    srcUNUploadAfter: 'بعد تنزيل ملف PDF، ارفعه هنا:',
    srcDropPdf: 'أسقط ملف PDF هنا أو',
    srcDropFile: 'أسقط ملفاً هنا أو',
    srcBrowse: 'تصفّح',
    srcFileTypes: 'PDF أو Word (.docx) أو نص عادي',
    audioFluencyTitle: 'طلاقة الصوت من التسجيل',
    coverageScoreLabel: 'درجة التغطية',
    statSpeechRate: 'سرعة الكلام',
    statLongPauses: 'توقفات طويلة',
    statSilenceRatio: 'نسبة الصمت',
    statWordConfidence: 'وضوح الكلمات',
    verdictGood: 'جيد',
    verdictAcceptable: 'مقبول',
    verdictNeedsWork: 'يحتاج عملاً',
    nextHintPre: '← انتقل إلى',
    nextHintPost: 'للاستماع ومراجعة الأسئلة وتنزيل المسرد.',
    transcriptReady: 'النص المفرَّغ جاهز',
    chatGreeting: 'مرحباً! أنا مساعد ETIB. اسألني عن تقنيات الترجمة الفورية أو المنصة أو المصطلحات.',
    chatPlaceholder: 'اسأل أي شيء…',
    chatSend: 'إرسال',
    chatThinking: 'أفكر…',
    statAvgPerSession: 'متوسط / جلسة',
    statTotal: 'الإجمالي',
    statSessions: 'الجلسات',
    outsideRange: '(خارج النطاق المطلوب)',
    progressGuestNote: 'يعمل تتبع التقدم مع حساب فقط. سجّل الدخول (أو أنشئ حساباً مجانياً) لتُحفظ تقييماتك وتُحلَّل عبر الجلسات.',
    pnTitle: 'أسماء الأعلام (أشخاص، منظمات، أماكن)',
    pnCorrect: 'صحيح',
    pnDistorted: 'محرَّف — نطق خاطئ على الأرجح',
    pnMissing: 'محذوف',
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
    navE: 'Progression',
    navSettings: 'Paramètres',
    settingsTitle: 'Paramètres',
    settingsGroqTitle: 'Votre clé API Groq',
    settingsGroqDesc: 'Collez votre clé API Groq personnelle. Elle est stockée uniquement dans votre navigateur et envoyée de manière sécurisée.',
    settingsGroqPlaceholder: 'gsk_...',
    settingsGroqGetKey: 'Obtenez une clé gratuite sur console.groq.com',
    settingsGroqTest: 'Tester la clé',
    settingsGroqTesting: 'Test en cours...',
    settingsGroqSave: 'Enregistrer',
    settingsGroqClear: 'Supprimer la clé',
    settingsGroqValid: 'Clé valide et fonctionnelle.',
    settingsGroqInvalid: 'Clé invalide — vérifiez et réessayez.',
    settingsGroqNotSet: 'Aucune clé enregistrée — cliquez sur le lien ci-dessus pour en créer une gratuitement sur console.groq.com, puis collez-la dans le champ et enregistrez.',
    settingsGroqSaved: 'Clé enregistrée.',
    settingsClose: 'Fermer',
    bannerNoKey: 'Aucune clé API Groq configurée. Allez dans Paramètres pour ajouter votre clé personnelle.',
    progressTitle: 'Ma progression',
    progressSubtitle: 'Historique des scores et recommandations adaptatives',
    progressNoSessions: 'Aucune session — terminez une évaluation complète pour commencer le suivi.',
    progressSessions: 'Historique des sessions',
    progressAdaptive: 'Recommandations adaptatives',
    progressAdaptiveSubtitle: 'D\’après vos dernières sessions, la plateforme recommande :',
    progressApply: 'Appliquer ces paramètres',
    progressOverall: 'Global',
    progressFluency: 'Fluidité',
    progressCoverage: 'Couverture',
    progressErrors: 'Erreurs',
    progressLang: 'Langue',
    progressDate: 'Date',
    progressScore: 'Score',
    progressLoading: 'Chargement…',
    progressAvgOver: 'Moy. globale',
    progressAvgFluency: 'Moy. fluidité',
    progressAvgNumbers: 'Moy. erreurs numériques',
    progressTrend: 'Courbe des scores (10 dernières sessions)',
    progressLatest: 'Dernière session',
    progressProblems: 'Points de travail — axes prioritaires',
    progressImproving: 'En progression',
    progressDeclining: 'En recul',
    progressStable: 'Stable',
    progressStrengths: 'Points forts',
    progressRecs: 'Recommandations',
    progressTopErrors: 'Erreurs spécifiques',
    progressNoData: 'Pas encore assez de données',
    moduleATitle: 'Générer un discours d’entraînement',
    groundedSourceLabel: 'Basé sur une source réelle :',
    ungroundedNote: 'Aucun document de l’ONU correspondant n’a été trouvé — ce discours a été généré sans source.',
    language: 'Langue du discours',
    targetLanguage: 'Langue cible',
    topic: 'Sujet',
    domain: 'Domaine',
    speedPressure: 'Pression de vitesse',
    topicShifts: 'Changements de sujet',
    pressureMode: 'Mode pression',
    contextNoise: 'Bruit de contexte',
    cognitiveLoad: 'Charge cognitive',
    summary: 'Résumé',
    mcq: 'QCM',
    glossary: 'Glossaire',
    documentGrounding: 'Génération depuis un document',
    documentFile: 'Document source',
    sharedSettings: 'Paramètres de génération',
    sharedSettingsHint: 'Ces paramètres s\'appliquent à la génération par sujet ou par document.',
    generationMethods: 'Choisir la source de génération',
    topicOnlyGeneration: 'Génération par sujet',
    topicOnlyHint: 'Générer à partir du sujet et des paramètres choisis.',
    documentGenerationHint: 'Déposez un document source pour générer un discours ancré dans son contenu.',
    generateFromDocument: 'Générer depuis le document',
    retrieveContext: 'Prévisualiser le contexte extrait',
    retrievedContext: 'Contexte extrait',
    wordCount: 'Longueur du discours',
    wordRangeShort: 'Court',
    wordRangeMedium: 'Moyen',
    wordRangeLong: 'Long',
    difficulty: 'Difficulté',
    structure: 'Structure du discours',
    mode: 'Mode d’interprétation',
    numbers: 'Densité des chiffres',
    hesitationsSim: 'Simuler les hésitations',
    submit: 'Générer le discours',
    generating: 'Génération en cours...',
    wordsUnit: 'mots',
    moduleBTitle: 'Audio et supports pédagogiques',
    moduleBBody: 'Produira : lecture audio, termes clés, glossaire et QCM.',
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
    mcqQuestionHeader: 'Question',
    mcqOptionsHeader: 'Options',
    mcqAnswerHeader: 'Réponse',
    glossaryTitle: 'Glossaire trilingue (AR – FR – EN)',
    glossaryTermHeader: 'Terme',
    glossaryArabicHeader: 'Arabe',
    glossaryFrenchHeader: 'Français',
    glossaryEnglishHeader: 'Anglais',
    glossaryDefinitionHeader: 'Définition',
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
    coverageTitle: 'Couverture du contenu',
    coverageHint: 'Quantité du discours source transmise',
    translationErrors: 'Erreurs de traduction',
    sourceSaid: 'Source a dit',
    studentSaid: "L'étudiant a dit",
    correctTranslation: 'Traduction correcte',
    missingContent: 'Contenu manquant',
    fluencyScore: 'Score de fluidité',
    pauseAnalysisTitle: 'Pauses et rythme',
    repetitionAnalysisTitle: 'Répétitions — analyse',
    numberAccuracyTitle: 'Chiffres et dates',
    pronunciationAssessmentTitle: 'Retour sur la prononciation',
    numCorrect: 'Correct',
    numIncorrect: 'Incorrect',
    expectedLabel: 'Attendu',
    studentSaidShort: 'Dit',
    pronunciationTitle: 'Évaluation de la prononciation',
    pronunciationMismatches: 'Divergences de clarté mot par mot',
    runPronunciation: 'Lancer le contrôle de prononciation',
    runningPronunciation: 'Alignement audio en cours — peut prendre 1 min...',
    pronunciationScore: 'Confiance',
    wordView: 'Vue mot par mot',
    legend: 'Légende',
    legendGood: '≥80% confiant',
    legendWarn: '60–80%',
    legendPoor: '<60% — erreur probable',
    uncertainWords: 'Mots significatifs à faible confiance',
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
    deleteAudio: 'Supprimer l\'audio',
    redoTranscript: 'Refaire la transcription',
    copyText: 'Copier',
    copied: 'Copié !',
    topicPlaceholder: 'Saisissez un sujet ou collez un texte pour générer un discours…',
    moreSettings: 'Plus ⚙',
    lessSettings: 'Moins ⚙',
    optConsecutive: 'Consécutive',
    optSimultaneous: 'Simultanée',
    optSight: 'Traduction à vue',
    optWellOrganized: 'Bien structuré',
    optDisorganized: 'Peu structuré',
    optLowNumbers: 'Peu de chiffres',
    optHighNumbers: 'Beaucoup de chiffres',
    optNormalSpeed: 'Vitesse normale',
    optFast: 'Rapide',
    optVeryFast: 'Très rapide',
    optNoShifts: 'Sans changements',
    optShifts: 'Changements de sujet',
    domPolitics: 'Politique',
    domDiplomacy: 'Diplomatie',
    domEconomics: 'Économie',
    domHealth: 'Santé',
    domEducation: 'Éducation',
    domClimate: 'Climat & Environnement',
    domHumanRights: 'Droits de l\'homme',
    domTechnology: 'Technologie & IA',
    domMigration: 'Migration & Réfugiés',
    domDisarmament: 'Désarmement',
    domWomen: 'Femmes & Genre',
    domFood: 'Alimentation & Faim',
    diffBeginner: 'Débutant',
    diffIntermediate: 'Intermédiaire',
    diffAdvanced: 'Avancé',
    diffHint: 'Débutant : vocabulaire simple, phrases courtes, 1–2 chiffres, débit lent. Intermédiaire : terminologie modérée, plusieurs statistiques, phrases variées. Avancé : terminologie dense, chiffres et noms fréquents, syntaxe complexe, débit rapide.',
    demoKeyBanner: 'La plateforme utilise un service d\'IA gratuit (Groq) pour générer et évaluer les discours. Vous utilisez actuellement la clé de démonstration partagée de la plateforme : elle fonctionne, mais elle est plus lente et soumise à des limites d\'usage partagées. Créer votre propre clé gratuite (2 minutes, sans carte bancaire) vous donne des réponses plus rapides et un quota personnel.',
    demoKeyBtn: 'Ajouter ma clé gratuite dans Paramètres',
    wordRangeShortFull: 'Court — 120–180 mots (≈ 1–1,5 min à 120 mots/min)',
    wordRangeMediumFull: 'Moyen — 220–320 mots (≈ 2–2,5 min)',
    wordRangeLongFull: 'Long — 400–550 mots (≈ 3,5–4,5 min)',
    wordRangeExtendedFull: 'Étendu — 650–800 mots (≈ 5,5–6,5 min)',
    optSemiStructured: 'Semi-structuré',
    optDisorganizedFull: 'Volontairement désorganisé',
    scenarioLabel: 'Style d\'orateur / contexte',
    scenUNGA: 'Assemblée générale de l\'ONU',
    scenEUParl: 'Parlement européen',
    scenArabLeague: 'Sommet de la Ligue arabe',
    scenPress: 'Conférence de presse',
    scenDiplomatic: 'Réunion diplomatique',
    scenDebate: 'Débat politique',
    scenInterview: 'Entrevue',
    termDensity: 'Densité terminologique',
    optTermLow: 'Faible — vocabulaire courant',
    optTermMedium: 'Moyenne',
    optTermHigh: 'Élevée — termes spécialisés denses',
    longTextAsSource: 'Texte long détecté — il sera utilisé comme document source et le discours s\'appuiera sur son contenu.',
    mcqPickAnswer: 'Choisissez votre réponse, puis vérifiez-la.',
    mcqCheck: 'Vérifier la réponse',
    mcqShowAnswer: 'Afficher la réponse',
    mcqCorrectMsg: '✓ Correct !',
    mcqWrongMsg: '✗ Incorrect. Bonne réponse :',
    mcqShowAnswerLabel: 'ℹ️ Bonne réponse :',
    mcqYourScore: 'Votre score',
    glossaryEdit: '✏️ Modifier le glossaire',
    glossaryEditDone: '✓ Terminer la modification',
    glossaryEditHint: 'Relisez et corrigez les équivalents AVANT d\'enregistrer votre prestation — l\'évaluation vérifiera ensuite votre terminologie par rapport à ce glossaire validé.',
    webPageTab: 'Page web',
    webPageUrlPlaceholder: 'https://… collez l\'adresse d\'un article ou d\'un rapport',
    webPageFetch: 'Récupérer la page',
    webPageFetching: 'Récupération…',
    webPageHint: 'Le texte lisible de la page sera extrait et utilisé comme source du discours.',
    scrollerTitle: 'Traduction à vue — texte défilant',
    scrollerPlay: '▶ Lancer le défilement',
    scrollerPause: '⏸ Pause',
    scrollerReset: '↺ Réinitialiser',
    scrollerSpeed: 'Vitesse (mots/min)',
    scrollerFontSize: 'Taille du texte',
    scrollerColumns: 'Colonnes',
    scrollerSpacing: 'Interligne',
    scrollerHint: 'Traduisez à voix haute pendant que le texte défile à la vitesse choisie — comme un vrai exercice de traduction à vue.',
    notesTitle: '📝 Prise de notes (consécutive)',
    notesTextTab: 'Notes texte',
    notesSketchTab: 'Croquis / carte mentale',
    notesClear: 'Effacer',
    notesPlaceholder: 'Prenez vos notes ici pendant l\'écoute (symboles, flèches, mots-clés)…',
    notesHint: 'Vos notes restent sur cette page uniquement — elles ne sont ni enregistrées ni envoyées.',
    simulTitle: '🎧 Mode simultané',
    simulStart: '▶ Lire la source + m\'enregistrer',
    simulStop: '⏹ Tout arrêter',
    simulHint: 'Portez un casque pour que l\'audio source ne soit pas capté par votre micro. Le discours source est lu pendant que votre interprétation est enregistrée — un vrai entraînement simultané.',
    simulNeedsAudio: 'Générez d\'abord l\'audio source dans « Audio et supports » pour activer le mode simultané.',
    prepTimeLabel: 'temps de préparation avant de parler — non compté dans la fluidité',
    fluencyExplain: 'Ce score est mesuré à partir de votre enregistrement : débit de parole, pauses pendant la prestation et clarté de reconnaissance de chaque mot. Le temps de préparation avant de commencer n\'est PAS compté. Un mot reconnu avec une faible confiance signifie qu\'il a semblé peu clair — c\'est un indice de clarté, pas automatiquement une erreur.',
    aboutEvalTitle: 'ℹ️ Comment fonctionne cette évaluation et où vont vos données',
    aboutEvalCriteria: 'Ce qui est analysé : (1) votre enregistrement est transcrit par une reconnaissance vocale (Whisper) ; (2) les événements mesurables sont détectés directement dans l\'audio — pauses, répétitions, hésitations, débit ; (3) un évaluateur IA compare votre interprétation au discours source sens par sens : exactitude, couverture, terminologie, chiffres et dates, grammaire ; (4) les scores suivent un barème de professeur strict (la plupart des prestations étudiantes obtiennent 4–7/10).',
    aboutEvalReliability: 'Fiabilité : la transcription est une estimation, pas une vérité absolue — surtout en arabe. Les passages peu clairs sont traités comme des problèmes de clarté, pas automatiquement comme des erreurs de traduction. Utilisez ce rapport comme outil d\'entraînement, pas comme note finale.',
    aboutEvalStorage: 'Stockage : votre enregistrement audio est traité puis supprimé du serveur — il n\'est pas conservé. Seul le résumé de l\'évaluation (scores, nombre d\'erreurs, recommandations) est enregistré dans l\'historique de votre compte pour alimenter la page Progression. Les discours générés et transcriptions ne sont pas stockés de façon permanente.',
    creditsLine: 'ETIB · ESIB · CINIA · USJ Beyrouth',
    modeChoose: 'Mode d\'entraînement',
    modeSimulDesc: 'Le discours source est lu pendant que vous interprétez et vous enregistrez en même temps.',
    modeConsecDesc: 'Écoutez la source et prenez des notes, puis enregistrez votre interprétation.',
    modeSightDesc: 'Lisez le texte défilant et traduisez à voix haute en vous enregistrant.',
    heroTrainIn: 'Entraînez-vous en :',
    heroTitlePre: "Maîtrisez l'interprétation avec des ",
    heroTitleEm: 'discours générés par IA',
    heroTitlePost: '',
    heroParagraph: "Une plateforme d'entraînement adaptative qui génère des discours de conférence réalistes, construit des glossaires multilingues et évalue vos performances d'interprétation en arabe, français et anglais.",
    guestBtn: 'Continuer en invité',
    orSep: '— ou —',
    srcPanelTitle: 'Ajouter une source',
    srcPanelSubtitle: "Trouvez un document de l'ONU, une page web, ou déposez votre propre fichier pour ancrer le discours dans un contenu réel.",
    srcTabUN: 'Bibliothèque ONU',
    srcTabUpload: 'Déposer un fichier',
    srcUNHint: "Cherchez votre sujet dans la Bibliothèque numérique de l'ONU, téléchargez le PDF, puis déposez-le ci-dessous.",
    srcUNSearchBtn: 'Chercher dans la Bibliothèque ONU ↗',
    srcUNUploadAfter: 'Une fois le PDF téléchargé, déposez-le ici :',
    srcDropPdf: 'Déposez le PDF ici ou',
    srcDropFile: 'Déposez un fichier ici ou',
    srcBrowse: 'parcourir',
    srcFileTypes: 'PDF, Word (.docx) ou texte brut',
    audioFluencyTitle: "Fluidité audio de l'enregistrement",
    coverageScoreLabel: 'Score de couverture',
    statSpeechRate: 'Débit de parole',
    statLongPauses: 'Pauses longues',
    statSilenceRatio: 'Taux de silence',
    statWordConfidence: 'Clarté des mots',
    verdictGood: 'Bien',
    verdictAcceptable: 'Acceptable',
    verdictNeedsWork: 'À travailler',
    nextHintPre: '→ Allez dans',
    nextHintPost: 'pour écouter, réviser les questions et télécharger le glossaire.',
    transcriptReady: 'Transcription prête',
    chatGreeting: "Bonjour ! Je suis votre assistant ETIB. Posez-moi vos questions sur les techniques d'interprétation, la plateforme ou la terminologie.",
    chatPlaceholder: 'Posez une question…',
    chatSend: 'Envoyer',
    chatThinking: 'Réflexion…',
    statAvgPerSession: 'moy. / session',
    statTotal: 'total',
    statSessions: 'Sessions',
    outsideRange: '(hors de la plage demandée)',
    progressGuestNote: 'Le suivi de progression fonctionne avec un compte. Connectez-vous (ou créez un compte gratuit) pour que vos évaluations soient enregistrées et analysées.',
    pnTitle: 'Noms propres (personnes, organisations, lieux)',
    pnCorrect: 'Correct',
    pnDistorted: 'Déformé — probablement mal prononcé',
    pnMissing: 'Omis',
  }
};

// ── Credits (professor request: ESIB + CINIA logos and developer names) ─────
const CREDITS = {
  developers: ['Joe Haddad', 'Kevin Khoury', 'Ali Ali', 'Chris Wehbe', 'Marc Khatar'],
  logos: [
    { src: '/usj-etib-logo.png',  alt: 'USJ — ETIB' },
    { src: '/usj-esib-logo.png',  alt: 'ESIB' },
    { src: '/usj-cinia-logo.png', alt: 'CINIA' },
  ],
};

function AppFooter({ labels }) {
  return (
    <footer style={{
      marginTop: '2.5rem', padding: '1.25rem 1.5rem', borderTop: '1px solid var(--border, #e3ded6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1.25rem', flexWrap: 'wrap',
      fontSize: '0.8rem', color: 'var(--warm-gray, #877)',
    }}>
      {CREDITS.logos.map(logo => (
        <img key={logo.src} src={logo.src} alt={logo.alt} style={{ height: 34, objectFit: 'contain' }} />
      ))}
      <span>{labels.creditsLine}</span>
      <span>·</span>
      <span>{CREDITS.developers.join(' · ')}</span>
    </footer>
  );
}

const NAV_ITEMS = [
  { id: 'module-a', labelKey: 'navA' },
  { id: 'module-b', labelKey: 'navB' },
  { id: 'module-c', labelKey: 'navC' },
  { id: 'module-d', labelKey: 'navD' },
  { id: 'module-e', labelKey: 'navE' },
];

// MARC 041 language codes -> UI language codes / display labels
const UN_LANG_TO_UI = { ara: 'ar', fre: 'fr', eng: 'en' };
const UN_LANG_LABEL = {
  ara: 'AR', fre: 'FR', eng: 'EN',
  chi: 'ZH', rus: 'RU', spa: 'ES'
};

const VOICE_OPTIONS = {
  ar: [
    { label: 'Lebanese Arabic — Male (ar-LB)', labelAr: 'عربية لبنانية - ذكر', accent: 'LB' },
    { label: 'Lebanese Arabic — Female (ar-LB)', labelAr: 'عربية لبنانية - أنثى', accent: 'LB_f' },
    { label: 'Gulf Arabic — Female (ar-SA)', labelAr: 'عربية خليجية - أنثى', accent: 'SA' },
    { label: 'Egyptian Arabic — Female (ar-EG)', labelAr: 'عربية مصرية - أنثى', accent: 'EG' },
    { label: 'Egyptian Arabic — Male (ar-EG)', labelAr: 'عربية مصرية - ذكر', accent: 'EG_m' },
  ],
  fr: [
    { label: 'French (Female)', labelAr: 'فرنسية - أنثى', accent: 'FR' },
    { label: 'French (Male)', labelAr: 'فرنسية - ذكر', accent: 'FR_m' },
    { label: 'Canadian (Female)', labelAr: 'كندية فرنسية - أنثى', accent: 'CA' },
  ],
  en: [
    { label: 'American (Female)', labelAr: 'أمريكية - أنثى', accent: 'US' },
    { label: 'British (Female)', labelAr: 'بريطانية - أنثى', accent: 'GB' },
    { label: 'Australian (Female)', labelAr: 'أسترالية - أنثى', accent: 'AU' },
  ]
};

// ── SVG icons ────────────────────────────────────────────────────────────────
function glossaryValue(item, keys) {
  for (const key of keys) {
    const value = item?.[key];
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value).trim();
    }
  }
  return '';
}

function glossaryArabicValue(item) {
  const combined = Object.values(item || {})
    .filter(value => value !== undefined && value !== null && typeof value !== 'object')
    .map(value => String(value).toLowerCase())
    .join(' ');
  if (combined.includes('giec') || combined.includes('ipcc') || combined.includes('groupe d')) {
    return 'الهيئة الحكومية الدولية المعنية بتغير المناخ';
  }

  const direct = glossaryValue(item, ['arabic', 'Arabic', 'ar', 'AR', 'arabic_term', 'term_ar', 'arabic_translation', 'translation_ar', 'العربية', 'عربي']);
  if (direct) return direct;

  for (const value of Object.values(item || {})) {
    if (value === undefined || value === null || typeof value === 'object') continue;
    const text = String(value).trim();
    if (/[\u0600-\u06FF]/.test(text)) return text;
  }
  return '';
}

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
const IconTrash = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    <line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>
  </svg>
);

function TranscriptBubble({ text, vocalizedText, isArabic, onRetranscribe, onDelete }) {
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
        {onDelete && (
          <button className="bubble-btn bubble-btn-danger" onClick={onDelete} title="Delete transcript">
            <IconTrash />
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
  word_count_range: 'medium',
  difficulty: 'intermediate',
  mode: 'consecutive',
  structure: 'well-organized',
  scenario: 'UN General Assembly',
  number_density: 'low',
  terminology_density: 'medium',
  include_hesitations: false,
  pressure_enabled: false,
  speed_pressure: 'normal',
  topic_shifts: 'none',
  context_noise: false,
  cognitive_load: 'medium'
};

// If the student pastes a full text instead of a short topic, treat the pasted
// text as the SOURCE DOCUMENT (grounding) rather than as a topic string.
const TOPIC_AS_SOURCE_THRESHOLD = 300;

// ── Module E — Progress & Adaptive Difficulty ─────────────────────────────────
function ScoreBadge({ score }) {
  const pct = Math.round((score || 0) * 10);
  const color = score >= 8 ? 'var(--sage)' : score >= 6.5 ? 'var(--primary)' : 'var(--sienna)';
  return (
    <span style={{ fontWeight: 700, color, fontFamily: 'Playfair Display, serif', fontSize: '1rem' }}>
      {score?.toFixed(1) ?? '—'}
    </span>
  );
}

function MiniBar({ value, max = 10, color }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div className="mini-bar-track">
      <div className="mini-bar-fill" style={{ width: `${pct}%`, background: color || 'var(--primary)' }} />
    </div>
  );
}

function TrendBadge({ trend, labels }) {
  if (!trend || trend === 'not_enough_data') return null;
  const map = {
    improving: { icon: '↑', color: 'var(--sage)',   text: labels.progressImproving },
    declining:  { icon: '↓', color: 'var(--sienna)', text: labels.progressDeclining },
    stable:     { icon: '→', color: 'var(--gold)',   text: labels.progressStable },
  };
  const d = map[trend];
  if (!d) return null;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.78rem',
      fontWeight: 700, color: d.color, background: d.color + '18', padding: '0.18rem 0.6rem',
      borderRadius: '999px', marginLeft: '0.5rem' }}>
      {d.icon} {d.text}
    </span>
  );
}

function SeverityDot({ severity }) {
  const c = severity === 'high' ? 'var(--sienna)' : severity === 'medium' ? 'var(--gold)' : 'var(--sage)';
  return <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: c, marginRight: '0.4rem', flexShrink: 0 }} />;
}

function ModuleProgress({ labels, refresh, onApplyParams }) {
  const [sessions, setSessions] = useState([]);
  const [adaptive, setAdaptive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([getSessionHistory(20), getAdaptiveParams()])
      .then(([hist, adap]) => {
        setSessions(hist.sessions || []);
        setAdaptive(adap);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [refresh]);

  const LANG_FLAG = { ar: '🇱🇧', fr: '🇫🇷', en: '🇬🇧' };
  const recentTen = sessions.slice(0, 10).reverse();

  const n = sessions.length;
  const avgOverall  = n ? (sessions.reduce((s, x) => s + (x.overall_score || 0), 0) / n).toFixed(2) : null;
  const avgFluency  = n ? (sessions.reduce((s, x) => s + (x.fluency_score || 0), 0) / n).toFixed(2) : null;
  const avgNumbers  = n ? (sessions.reduce((s, x) => s + (x.error_counts?.number_errors || 0), 0) / n).toFixed(1) : null;

  const latest   = sessions[0] || null;
  const trend    = adaptive?.trend;
  const problems = adaptive?.problems_to_work_on || [];

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', padding: '3rem' }}><div className="spinner" /><p style={{ marginTop: '1rem', color: 'var(--warm-gray)' }}>{labels.progressLoading}</p></div>;
  }

  return (
    <div className="module-b-layout">
      {/* ── Header stat row ── */}
      <div className="progress-stat-row">
        <div className="progress-stat-card">
          <div className="progress-stat-label">{labels.progressAvgOver}</div>
          <div className="progress-stat-value" style={{ color: avgOverall >= 7 ? 'var(--sage)' : avgOverall >= 5.5 ? 'var(--primary)' : 'var(--sienna)' }}>
            {avgOverall ?? '—'}
            {trend && trend !== 'not_enough_data' && <TrendBadge trend={trend} labels={labels} />}
          </div>
          <div className="progress-stat-sub">/ 10 &nbsp;{adaptive?.improvement_pct != null && trend !== 'not_enough_data' && (
            <span style={{ color: adaptive.improvement_pct > 0 ? 'var(--sage)' : 'var(--sienna)' }}>
              ({adaptive.improvement_pct > 0 ? '+' : ''}{adaptive.improvement_pct})
            </span>
          )}</div>
        </div>
        <div className="progress-stat-card">
          <div className="progress-stat-label">{labels.progressAvgFluency}</div>
          <div className="progress-stat-value" style={{ color: avgFluency >= 7 ? 'var(--sage)' : avgFluency >= 5.5 ? 'var(--primary)' : 'var(--sienna)' }}>{avgFluency ?? '—'}</div>
          <div className="progress-stat-sub">/ 10</div>
        </div>
        <div className="progress-stat-card">
          <div className="progress-stat-label">{labels.progressAvgNumbers}</div>
          <div className="progress-stat-value" style={{ color: avgNumbers <= 1 ? 'var(--sage)' : avgNumbers <= 3 ? 'var(--primary)' : 'var(--sienna)' }}>{avgNumbers ?? '—'}</div>
          <div className="progress-stat-sub">{labels.statAvgPerSession}</div>
        </div>
        <div className="progress-stat-card">
          <div className="progress-stat-label">{labels.statSessions}</div>
          <div className="progress-stat-value" style={{ color: 'var(--primary)' }}>{n}</div>
          <div className="progress-stat-sub">{labels.statTotal}</div>
        </div>
      </div>

      {n === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--warm-gray)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📊</div>
          <p>{labels.progressNoSessions}</p>
        </div>
      ) : (
        <>
          {/* ── Latest session card ── */}
          {latest && (
            <div className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
              <h2 className="b-section-title">🎓 {labels.progressLatest}</h2>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                  <div className="progress-stat-card" style={{ minWidth: 90 }}>
                    <div className="progress-stat-label">{labels.progressOverall}</div>
                    <div className="progress-stat-value" style={{ color: latest.overall_score >= 7 ? 'var(--sage)' : latest.overall_score >= 5.5 ? 'var(--gold)' : 'var(--sienna)' }}>{latest.overall_score?.toFixed(1) ?? '—'}</div>
                  </div>
                  <div className="progress-stat-card" style={{ minWidth: 90 }}>
                    <div className="progress-stat-label">{labels.progressFluency}</div>
                    <div className="progress-stat-value" style={{ color: latest.fluency_score >= 7 ? 'var(--sage)' : 'var(--gold)' }}>{latest.fluency_score?.toFixed(1) ?? '—'}</div>
                  </div>
                  <div className="progress-stat-card" style={{ minWidth: 90 }}>
                    <div className="progress-stat-label">{labels.progressCoverage}</div>
                    <div className="progress-stat-value" style={{ color: latest.coverage_score >= 7 ? 'var(--sage)' : 'var(--gold)' }}>{latest.coverage_score?.toFixed(1) ?? '—'}</div>
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  {latest.summary && <p style={{ fontSize: '0.88rem', color: 'var(--warm-gray)', marginBottom: '0.5rem', fontStyle: 'italic' }}>"{latest.summary}"</p>}
                  {(latest.strengths || []).length > 0 && (
                    <div style={{ marginBottom: '0.4rem' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--sage)' }}>{labels.progressStrengths}: </span>
                      <span style={{ fontSize: '0.82rem', color: 'var(--warm-gray)' }}>{latest.strengths.join(' · ')}</span>
                    </div>
                  )}
                  {(latest.recommendations || []).length > 0 && (
                    <div>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--gold)' }}>{labels.progressRecs}: </span>
                      <span style={{ fontSize: '0.82rem', color: 'var(--warm-gray)' }}>{latest.recommendations.slice(0, 2).join(' · ')}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ── Focus areas ── */}
          {problems.length > 0 && (
            <div className="card">
              <h2 className="b-section-title">🔍 {labels.progressProblems}</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {problems.map((p) => (
                  <div key={p.key} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                    background: 'var(--bg-secondary, #f8f7f5)', borderRadius: '8px', padding: '0.75rem 1rem' }}>
                    <SeverityDot severity={p.severity} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary, #1a1a1a)' }}>{p.label}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--warm-gray)', marginTop: '0.1rem' }}>{p.detail}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--primary)', marginTop: '0.25rem' }}>💡 {p.tip}</div>
                    </div>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em',
                      color: p.severity === 'high' ? 'var(--sienna)' : p.severity === 'medium' ? 'var(--gold)' : 'var(--sage)',
                      border: `1px solid currentColor`, borderRadius: '4px', padding: '0.15rem 0.4rem', flexShrink: 0 }}>
                      {p.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Score trend chart ── */}
          <div className="card">
            <h2 className="b-section-title">📈 {labels.progressTrend}</h2>
            <div className="trend-chart">
              {recentTen.map((s, i) => {
                const h = Math.round(((s.overall_score || 0) / 10) * 100);
                const color = s.overall_score >= 8 ? 'var(--sage)' : s.overall_score >= 6.5 ? 'var(--primary)' : 'var(--sienna)';
                return (
                  <div key={i} className="trend-bar-wrap">
                    <div className="trend-score-label" style={{ color }}>{s.overall_score?.toFixed(1)}</div>
                    <div className="trend-bar-outer">
                      <div className="trend-bar-inner" style={{ height: `${h}%`, background: color }} />
                    </div>
                    <div className="trend-lang-label">{LANG_FLAG[s.language] || '🌐'}</div>
                    <div className="trend-date-label">{new Date(s.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Adaptive recommendations ── */}
          {adaptive?.recommended_params && (
            <div className="card">
              <h2 className="b-section-title">🎯 {labels.progressAdaptive}</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--warm-gray)', marginBottom: '1rem' }}>{labels.progressAdaptiveSubtitle}</p>
              <div className="adaptive-grid">
                {[
                  [labels.difficulty, adaptive.recommended_params.difficulty],
                  [labels.wordCount, adaptive.recommended_params.word_count + ' ' + labels.wordsUnit],
                  [labels.numbers, adaptive.recommended_params.number_density],
                  [labels.speedPressure, adaptive.recommended_params.speed_pressure],
                  [labels.structure, adaptive.recommended_params.structure],
                  [labels.topicShifts, adaptive.recommended_params.topic_shifts],
                ].map(([k, v]) => (
                  <div key={k} className="adaptive-param">
                    <div className="adaptive-param-label">{k}</div>
                    <div className="adaptive-param-value">{v}</div>
                  </div>
                ))}
              </div>
              {(adaptive.tips || []).length > 0 && (
                <ul className="adaptive-tips">
                  {adaptive.tips.map((t, i) => <li key={i}>{t}</li>)}
                </ul>
              )}
              {onApplyParams && (
                <div style={{ marginTop: '1.25rem', textAlign: 'right' }}>
                  <button className="btn btn-primary" onClick={() => onApplyParams(adaptive.recommended_params)}>
                    {labels.progressApply}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── Session list ── */}
          <div className="card">
            <h2 className="b-section-title">📋 {labels.progressSessions}</h2>
            <div className="session-list">
              {sessions.map((s, i) => (
                <div key={i} className={`session-row ${expanded === i ? 'session-row--open' : ''}`}
                  onClick={() => setExpanded(expanded === i ? null : i)}>
                  <div className="session-row-main">
                    <span className="session-lang">{LANG_FLAG[s.language] || '🌐'} {(s.language || '').toUpperCase()}</span>
                    <span className="session-date">{new Date(s.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
                    <div className="session-scores">
                      <span title="Overall"><ScoreBadge score={s.overall_score} /></span>
                      <MiniBar value={s.overall_score} color={s.overall_score >= 7 ? 'var(--sage)' : s.overall_score >= 5.5 ? 'var(--primary)' : 'var(--sienna)'} />
                    </div>
                    <div className="session-error-chips">
                      {(s.error_counts?.number_errors > 0) && <span className="err-chip err-chip--num">🔢 {s.error_counts.number_errors}</span>}
                      {(s.error_counts?.repetitions > 0) && <span className="err-chip err-chip--rep">🔁 {s.error_counts.repetitions}</span>}
                      {(s.error_counts?.long_silences > 0) && <span className="err-chip err-chip--sil">🔇 {s.error_counts.long_silences}</span>}
                      {(s.error_counts?.translation_errors > 0) && <span className="err-chip err-chip--loss">🔤 {s.error_counts.translation_errors}</span>}
                    </div>
                    <span className="session-chevron">{expanded === i ? '▲' : '▼'}</span>
                  </div>
                  {expanded === i && (
                    <div className="session-detail">
                      <div className="session-detail-scores">
                        <div><span className="session-detail-label">{labels.progressOverall}</span><ScoreBadge score={s.overall_score} /></div>
                        <div><span className="session-detail-label">{labels.progressFluency}</span><ScoreBadge score={s.fluency_score} /></div>
                        <div><span className="session-detail-label">{labels.progressCoverage}</span><ScoreBadge score={s.coverage_score} /></div>
                      </div>
                      {s.summary && <p style={{ fontSize: '0.82rem', color: 'var(--warm-gray)', marginTop: '0.6rem', fontStyle: 'italic' }}>"{s.summary}"</p>}
                      {(s.strengths || []).length > 0 && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--sage)', textTransform: 'uppercase' }}>{labels.progressStrengths}</span>
                          <ul style={{ margin: '0.25rem 0 0 1rem', fontSize: '0.8rem', color: 'var(--warm-gray)' }}>
                            {s.strengths.map((r, j) => <li key={j}>{r}</li>)}
                          </ul>
                        </div>
                      )}
                      {(s.recommendations || []).length > 0 && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--gold)', textTransform: 'uppercase' }}>{labels.progressRecs}</span>
                          <ul style={{ margin: '0.25rem 0 0 1rem', fontSize: '0.8rem', color: 'var(--warm-gray)' }}>
                            {s.recommendations.map((r, j) => <li key={j}>{r}</li>)}
                          </ul>
                        </div>
                      )}
                      {(s.top_errors || []).length > 0 && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--sienna)', textTransform: 'uppercase' }}>{labels.progressTopErrors}</span>
                          <ul style={{ margin: '0.25rem 0 0 1rem', fontSize: '0.78rem', color: 'var(--warm-gray)' }}>
                            {s.top_errors.map((e, j) => (
                              <li key={j}>
                                {e.type === 'translation' && <><strong>{e.source}</strong> → said: <em>{e.said}</em></>}
                                {e.type === 'number' && <>Expected <strong>{e.expected}</strong>, said: <em>{e.said}</em></>}
                                {e.type === 'missing' && <>Missing: <em>{e.detail}</em></>}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [uiLang, setUiLang] = useState('en');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activePanel, setActivePanel] = useState('module-a');
  const [lastGeneratedScript, setLastGeneratedScript] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const L = UI[uiLang];

  useEffect(() => {
    const isAr = uiLang === 'ar';
    document.documentElement.lang = uiLang;
    document.documentElement.dir = isAr ? 'rtl' : 'ltr';
    document.body.classList.toggle('rtl', isAr);
  }, [uiLang]);

  function handleGuest() {
    saveAuthToken(null);
    setCurrentUserId('guest');
    setCurrentUser({ name: 'Guest', role: 'student', id: 'guest' });
    setIsAuthenticated(true);
  }

  async function handleLogin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      const result = await loginUser({
        email: formData.get('email'),
        password: formData.get('password'),
        role: formData.get('role')
      });
      saveAuthToken(result.token);
      setCurrentUserId(result.user.id);
      setCurrentUser(result.user);
      setIsAuthenticated(true);
    } catch (err) {
      throw err; // let LoginScreen.handleSubmit surface the error
    }
  }

  async function handleSignup(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      const result = await signupUser({
        name: formData.get('name'),
        email: formData.get('email'),
        password: formData.get('password'),
        role: formData.get('role')
      });
      saveAuthToken(result.token);
      setCurrentUserId(result.user.id);
      setCurrentUser(result.user);
      setIsAuthenticated(true);
    } catch (err) {
      throw err;
    }
  }

  async function handleLogout() {
    await logoutUser().catch(() => {});
    saveAuthToken(null);
    setCurrentUserId(null);
    setIsAuthenticated(false);
    setCurrentUser(null);
    setActivePanel('module-a');
    setLastGeneratedScript(null);
  }

  return (
    <div className="shell">
      <Header
        isAuthenticated={isAuthenticated}
        isGuest={currentUser?.id === 'guest'}
        activePanel={activePanel}
        labels={L}
        onPanelChange={setActivePanel}
        uiLang={uiLang}
        onLanguageChange={setUiLang}
        onOpenSettings={() => setShowSettings(true)}
      />
      <main>
        {!isAuthenticated ? (
          <LoginScreen labels={L} onLogin={handleLogin} onSignup={handleSignup} onGuest={handleGuest} />
        ) : (
          <Workspace
            labels={L}
            activePanel={activePanel}
            onPanelChange={setActivePanel}
            onLogout={handleLogout}
            onGenerated={setLastGeneratedScript}
            lastGeneratedScript={lastGeneratedScript}
            currentUser={currentUser}
            isRtl={uiLang === 'ar'}
            onOpenSettings={() => setShowSettings(true)}
          />
        )}
      </main>
      <AppFooter labels={L} />
      {showSettings && (
        <SettingsModal labels={L} onClose={() => setShowSettings(false)} />
      )}
      {isAuthenticated && <ChatWidget labels={L} />}
    </div>
  );
}

function ChatWidget({ labels }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: labels.chatGreeting }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const apiMessages = [...messages, userMsg]
        .filter(m => m.role !== 'assistant' || messages.indexOf(m) > 0)
        .map(m => ({ role: m.role, content: m.content }));
      const { reply } = await sendChatMessage(apiMessages);
      setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 1000 }}>
      {open && (
        <div style={{
          width: 340, height: 440, background: 'var(--surface, #fff)',
          border: '1px solid var(--border, #ddd)', borderRadius: 16,
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)', display: 'flex',
          flexDirection: 'column', marginBottom: '0.75rem', overflow: 'hidden'
        }}>
          <div style={{
            background: 'var(--primary, #1a3a5c)', color: '#fff',
            padding: '0.85rem 1rem', fontWeight: 600, fontSize: '0.95rem',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span>ETIB Assistant</span>
            <button onClick={() => setOpen(false)} style={{
              background: 'none', border: 'none', color: '#fff',
              fontSize: '1.2rem', cursor: 'pointer', lineHeight: 1
            }}>×</button>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                background: m.role === 'user' ? 'var(--primary, #1a3a5c)' : 'var(--surface-raised, #f0f4f8)',
                color: m.role === 'user' ? '#fff' : 'inherit',
                padding: '0.55rem 0.85rem', borderRadius: 12,
                maxWidth: '85%', fontSize: '0.875rem', lineHeight: 1.5,
                whiteSpace: 'pre-wrap'
              }}>
                {m.content}
              </div>
            ))}
            {loading && (
              <div style={{
                alignSelf: 'flex-start', background: 'var(--surface-raised, #f0f4f8)',
                padding: '0.55rem 0.85rem', borderRadius: 12, fontSize: '0.875rem',
                color: 'var(--warm-gray, #888)'
              }}>{labels.chatThinking}</div>
            )}
            <div ref={bottomRef} />
          </div>
          <div style={{ padding: '0.65rem', borderTop: '1px solid var(--border, #ddd)', display: 'flex', gap: '0.5rem' }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder={labels.chatPlaceholder}
              style={{
                flex: 1, padding: '0.5rem 0.75rem', borderRadius: 8,
                border: '1px solid var(--border, #ddd)', fontSize: '0.875rem',
                outline: 'none', background: 'var(--bg, #fff)'
              }}
            />
            <button onClick={handleSend} disabled={loading || !input.trim()} style={{
              padding: '0.5rem 0.9rem', borderRadius: 8, border: 'none',
              background: 'var(--primary, #1a3a5c)', color: '#fff',
              cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem',
              opacity: loading || !input.trim() ? 0.5 : 1
            }}>{labels.chatSend}</button>
          </div>
        </div>
      )}
      <button onClick={() => setOpen(o => !o)} style={{
        width: 52, height: 52, borderRadius: '50%',
        background: 'var(--primary, #1a3a5c)', color: '#fff',
        border: 'none', cursor: 'pointer', fontSize: '1.5rem',
        boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        💬
      </button>
    </div>
  );
}

function SettingsModal({ labels, onClose }) {
  const [keyInput, setKeyInput] = useState(getStoredGroqKey());
  const [status, setStatus] = useState('');  // 'valid' | 'invalid' | 'saved' | ''
  const [testing, setTesting] = useState(false);
  const hasKey = Boolean(getStoredGroqKey());

  async function handleTest() {
    setTesting(true);
    setStatus('');
    try {
      const res = await validateGroqKey(keyInput.trim());
      setStatus(res.valid ? 'valid' : 'invalid');
    } catch {
      setStatus('invalid');
    } finally {
      setTesting(false);
    }
  }

  function handleSave() {
    saveGroqKey(keyInput.trim());
    setStatus('saved');
  }

  function handleClear() {
    saveGroqKey('');
    setKeyInput('');
    setStatus('');
  }

  return (
    <div className="settings-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="settings-modal">
        <div className="settings-modal-header">
          <h2>{labels.settingsTitle}</h2>
          <button type="button" className="settings-close-btn" onClick={onClose}>{labels.settingsClose}</button>
        </div>
        <div className="settings-section">
          <h3>{labels.settingsGroqTitle}</h3>
          <p className="settings-desc">{labels.settingsGroqDesc}</p>
          <a
            href="https://console.groq.com/keys"
            target="_blank"
            rel="noopener noreferrer"
            className="settings-link"
          >
            {labels.settingsGroqGetKey}
          </a>
          <div className="settings-key-row">
            <input
              type="password"
              className="settings-key-input"
              placeholder={labels.settingsGroqPlaceholder}
              value={keyInput}
              onChange={e => { setKeyInput(e.target.value); setStatus(''); }}
              autoComplete="off"
              spellCheck={false}
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={handleTest}
              disabled={testing || !keyInput.trim()}
            >
              {testing ? labels.settingsGroqTesting : labels.settingsGroqTest}
            </button>
          </div>
          {status === 'valid'   && <p className="settings-status ok">{labels.settingsGroqValid}</p>}
          {status === 'invalid' && <p className="settings-status err">{labels.settingsGroqInvalid}</p>}
          {status === 'saved'   && <p className="settings-status ok">{labels.settingsGroqSaved}</p>}
          {!status && !hasKey   && <p className="settings-status warn">{labels.settingsGroqNotSet}</p>}
          <div className="settings-btn-row">
            <button
              type="button"
              className="btn-primary"
              onClick={handleSave}
              disabled={!keyInput.trim()}
            >
              {labels.settingsGroqSave}
            </button>
            {hasKey && (
              <button type="button" className="btn-danger" onClick={handleClear}>
                {labels.settingsGroqClear}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Header({ isAuthenticated, isGuest, activePanel, labels, onPanelChange, uiLang, onLanguageChange, onOpenSettings }) {
  const hasKey = Boolean(getStoredGroqKey());
  // Progress needs an account — guests have no saved history to show.
  const navItems = NAV_ITEMS.filter(item => item.id !== 'module-e' || !isGuest);
  return (
    <header className="fade-up">
      <div className="header-logos">
        <img src="/usj-etib-logo.png" style={{ height: '44px', objectFit: 'contain' }} alt="USJ - 150 ans - ETIB" />
        <div className="header-title">
          <div className="header-title-main">ETIB <span>Interpreter</span> Trainer</div>
          <div className="header-title-sub">AI Self-Training Platform · USJ Beirut</div>
        </div>
      </div>
      {isAuthenticated && (
        <nav aria-label="Training modules">
          {navItems.map(item => (
            <button
              key={item.id}
              type="button"
              className={`nav-btn ${activePanel === item.id ? 'active' : ''}`}
              onClick={() => onPanelChange(item.id)}
            >
              {labels[item.labelKey]}
            </button>
          ))}
          <button
            type="button"
            className="nav-btn settings-btn"
            onClick={onOpenSettings}
            title={labels.navSettings}
          >
            ⚙ {!hasKey && <span className="key-missing-dot" title={labels.bannerNoKey} />}
          </button>
        </nav>
      )}
      <label className="lang-picker">
        <span>{labels.uiLanguage}</span>
        <select value={uiLang} onChange={event => onLanguageChange(event.target.value)}>
          <option value="en">English</option>
          <option value="fr">Français</option>
          <option value="ar">العربية</option>
        </select>
      </label>
    </header>
  );
}

function LoginScreen({ labels, onLogin, onSignup, onGuest }) {
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
    <section className="hero fade-up delay-1">
      {/* Left: marketing copy */}
      <div className="hero-text">
        <div className="lang-tabs">
          <span className="lang-tabs-label">{labels.heroTrainIn}</span>
          <span className="lang-tab lang-tab-ar">عربي</span>
          <span className="lang-tab lang-tab-fr">Français</span>
          <span className="lang-tab lang-tab-en">English</span>
        </div>
        <h1>{labels.heroTitlePre}<em>{labels.heroTitleEm}</em>{labels.heroTitlePost}</h1>
        <p>{labels.heroParagraph}</p>
      </div>

      {/* Right: auth form */}
      <div className="login-panel">
        <h2>{isSignup ? labels.signupTitle : labels.loginTitle}</h2>
        <p className="sub">{isSignup ? labels.signupSubtitle : labels.loginSubtitle}</p>
        <form onSubmit={handleSubmit}>
          {isSignup && (
            <div className="field">
              <label htmlFor="login-name">{labels.name}</label>
              <input id="login-name" name="name" type="text" autoComplete="name" required placeholder="Your full name" />
            </div>
          )}
          <div className="field">
            <label htmlFor="login-email">{labels.email}</label>
            <input id="login-email" name="email" type="email" autoComplete="email" required placeholder="name@usj.edu.lb" />
          </div>
          <div className="field">
            <label htmlFor="login-password">{labels.password}</label>
            <div className="field-row">
              <input
                id="login-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                minLength="4"
              />
              <button type="button" className="show-btn" onClick={() => setShowPassword(v => !v)}>
                {showPassword ? labels.hidePassword : labels.showPassword}
              </button>
            </div>
          </div>
          {error && <div className="error-msg">{labels.errorPrefix}: {error}</div>}
          <button type="submit" className="btn-primary login-submit" disabled={isSubmitting}>
            {isSubmitting ? (isSignup ? labels.signupLoading : labels.loginLoading) : (isSignup ? labels.signupSubmit : labels.loginSubmit)}
          </button>
          <p className="login-note">{labels.loginNote}</p>
          <div className="login-switch">
            <button type="button" onClick={() => { setMode(isSignup ? 'login' : 'signup'); setError(''); setShowPassword(false); }}>
              {isSignup ? labels.switchToLogin : labels.switchToSignup}
            </button>
          </div>
          <div style={{ textAlign: 'center', margin: '0.75rem 0 0' }}>
            <span style={{ color: '#aaa', fontSize: '0.8rem' }}>{labels.orSep}</span>
          </div>
          <button
            type="button"
            onClick={onGuest}
            style={{
              width: '100%', marginTop: '0.5rem', padding: '0.6rem',
              background: 'transparent', border: '1.5px solid #ccc',
              borderRadius: 8, cursor: 'pointer', fontSize: '0.9rem',
              color: '#555', fontWeight: 500,
            }}
          >
            {labels.guestBtn}
          </button>
        </form>
      </div>
    </section>
  );
}

function Workspace({ labels, activePanel, onPanelChange, onLogout, onGenerated, lastGeneratedScript, currentUser, isRtl, onOpenSettings }) {
  const [sharedAudioUrl, setSharedAudioUrl] = useState(null);
  const [lastTranscript, setLastTranscript] = useState(null);
  const [lastRecordingBlob, setLastRecordingBlob] = useState(null);
  const [progressRefresh, setProgressRefresh] = useState(0);
  const [adaptiveParams, setAdaptiveParams] = useState(null);
  const hasKey = Boolean(getStoredGroqKey());

  return (
    <section>
      <div className="workspace-header fade-up">
        <span className="workspace-user">
          {currentUser && <><strong>{currentUser.name}</strong> · {currentUser.role}</>}
        </span>
        <button type="button" className="sign-out-btn" onClick={onLogout}>{labels.signOut}</button>
      </div>

      {!hasKey && (
        <div style={{
          background: '#eaf2fb', border: '1px solid #b6d4f5', borderRadius: 10,
          padding: '0.85rem 1.2rem', margin: '0 0 1rem 0',
          display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap'
        }}>
          <span style={{ flex: 1, fontSize: '0.92rem' }}>
            ℹ️ {labels.demoKeyBanner}
          </span>
          <button
            onClick={() => { onOpenSettings(); }}
            style={{
              background: '#1a3a5c', color: '#fff', border: 'none', borderRadius: 7,
              padding: '0.45rem 1rem', cursor: 'pointer', fontWeight: 600, fontSize: '0.88rem', whiteSpace: 'nowrap'
            }}
          >
            ⚙ {labels.demoKeyBtn}
          </button>
        </div>
      )}

      {/* Keep all panels mounted — state persists when switching tabs */}
      <div style={{ display: activePanel === 'module-a' ? 'block' : 'none' }}>
        <ModuleA labels={labels} onGenerated={onGenerated} isRtl={isRtl} adaptiveParams={adaptiveParams} />
      </div>
      <div style={{ display: activePanel === 'module-b' ? 'block' : 'none' }}>
        <ModuleB labels={labels} lastGeneratedScript={lastGeneratedScript}
          onAudioGenerated={setSharedAudioUrl} onScriptUpdate={onGenerated} isRtl={isRtl} />
      </div>
      <div style={{ display: activePanel === 'module-c' ? 'block' : 'none' }}>
        <ModuleC labels={labels} referenceAudioUrl={sharedAudioUrl}
          sourceScript={lastGeneratedScript?.script || ''}
          targetLanguage={lastGeneratedScript?.target_language || ''}
          onTranscriptComplete={setLastTranscript}
          onRecordingComplete={setLastRecordingBlob} />
      </div>
      <div style={{ display: activePanel === 'module-d' ? 'block' : 'none' }}>
        <ModuleD labels={labels} lastTranscript={lastTranscript}
          lastGeneratedScript={lastGeneratedScript}
          lastRecordingBlob={lastRecordingBlob}
          onEvaluationSaved={() => setProgressRefresh(n => n + 1)} />
      </div>
      <div style={{ display: activePanel === 'module-e' ? 'block' : 'none' }}>
        {currentUser?.id === 'guest' ? (
          <div className="card coming-soon">
            <p className="eyebrow">{labels.navE}</p>
            <p>{labels.progressGuestNote}</p>
          </div>
        ) : (
        <ModuleProgress labels={labels} refresh={progressRefresh}
          onApplyParams={(params) => {
            // Adaptive difficulty (cahier D12): apply the recommended
            // parameters to the generation form, then jump to Module A.
            setAdaptiveParams({ ...params, _appliedAt: Date.now() });
            onPanelChange('module-a');
          }} />
        )}
      </div>

    </section>
  );
}

// ── Sources Panel ─────────────────────────────────────────────────────────────

function SourcesPanel({ labels, language, domain, initialQuery, onSelectLibrary, onSelectFile, onClose }) {
  const [tab, setTab]   = useState('library');  // 'library' | 'upload' | 'webpage'
  const [query, setQuery] = useState(initialQuery || '');
  const [pageUrl, setPageUrl] = useState('');
  const [urlStatus, setUrlStatus] = useState('idle');
  const [urlError, setUrlError] = useState('');

  function handleFileChosen(file) {
    if (!file) return;
    onSelectFile(file);
    onClose();
  }

  async function handleFetchUrl() {
    if (!pageUrl.trim()) return;
    setUrlStatus('loading'); setUrlError('');
    try {
      const data = await fetchWebPage(pageUrl.trim());
      onSelectLibrary({ text: data.text, title: data.title || pageUrl, un_id: '', web_url: data.url });
      onClose();
    } catch (err) {
      setUrlError(err.message);
      setUrlStatus('error');
    }
  }

  const unSearchUrl = `https://digitallibrary.un.org/search?p=${encodeURIComponent(query || 'United Nations')}&ln=en&sf=date&so=d&of=hb&fct__1=Documents+and+Publications`;

  return (
    <div className="library-overlay">
      <div className="library-panel">
        <div className="library-header">
          <h2 className="library-title">{labels?.srcPanelTitle || 'Add Source'}</h2>
          <button className="library-close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <p className="library-subtitle">{labels?.srcPanelSubtitle}</p>

        <div className="library-tabs">
          <button className={`lib-tab ${tab === 'library' ? 'lib-tab-active' : ''}`} onClick={() => setTab('library')}>{labels?.srcTabUN || 'UN Library'}</button>
          <button className={`lib-tab ${tab === 'webpage' ? 'lib-tab-active' : ''}`} onClick={() => setTab('webpage')}>🔗 {labels?.webPageTab || 'Web page'}</button>
          <button className={`lib-tab ${tab === 'upload' ? 'lib-tab-active' : ''}`} onClick={() => setTab('upload')}>{labels?.srcTabUpload || 'Upload file'}</button>
        </div>

        {tab === 'webpage' && (
          <div style={{ padding: '1.2rem 0' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--warm-gray)', marginBottom: '1rem', lineHeight: 1.6 }}>
              {labels?.webPageHint || 'The readable text of the page will be extracted and used as the source for the speech.'}
            </p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                className="library-search-input"
                type="url"
                value={pageUrl}
                onChange={e => { setPageUrl(e.target.value); setUrlError(''); setUrlStatus('idle'); }}
                placeholder={labels?.webPageUrlPlaceholder || 'https://…'}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleFetchUrl(); } }}
                disabled={urlStatus === 'loading'}
              />
              <button
                type="button"
                className="btn-primary"
                style={{ whiteSpace: 'nowrap' }}
                onClick={handleFetchUrl}
                disabled={urlStatus === 'loading' || !pageUrl.trim()}
              >
                {urlStatus === 'loading' ? (labels?.webPageFetching || 'Fetching…') : (labels?.webPageFetch || 'Fetch page')}
              </button>
            </div>
            {urlError && <div className="error-msg" style={{ marginTop: '0.75rem' }}>{urlError}</div>}
          </div>
        )}

        {tab === 'library' && (
          <div style={{ padding: '1.2rem 0' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--warm-gray)', marginBottom: '1rem', lineHeight: 1.6 }}>
              {labels?.srcUNHint}
            </p>

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.2rem' }}>
              <input
                className="library-search-input"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="e.g. climate change, AI governance…"
                onKeyDown={e => { if (e.key === 'Enter') window.open(unSearchUrl, '_blank'); }}
              />
              <a
                href={unSearchUrl}
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{ whiteSpace: 'nowrap', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
              >
                {labels?.srcUNSearchBtn || 'Search UN Library ↗'}
              </a>
            </div>

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.1rem' }}>
              <p style={{ fontSize: '0.82rem', color: 'var(--warm-gray)', marginBottom: '0.75rem' }}>
                {labels?.srcUNUploadAfter}
              </p>
              <label
                className="upload-zone"
                onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={e => { e.preventDefault(); e.stopPropagation(); handleFileChosen(e.dataTransfer.files?.[0] || null); }}
              >
                <input
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={e => handleFileChosen(e.target.files?.[0] || null)}
                  style={{ display: 'none' }}
                />
                <svg className="upload-zone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <div className="upload-zone-label">{labels?.srcDropPdf} <span className="upload-zone-browse">{labels?.srcBrowse}</span></div>
                <div className="upload-zone-hint">{labels?.srcFileTypes}</div>
              </label>
            </div>
          </div>
        )}

        {tab === 'upload' && (
          <div className="library-results" style={{ padding: '0.9rem 0 0' }}>
            <label
              className="upload-zone"
              onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
              onDrop={e => { e.preventDefault(); e.stopPropagation(); handleFileChosen(e.dataTransfer.files?.[0] || null); }}
            >
              <input
                type="file"
                accept=".txt,.docx,.pdf"
                onChange={e => handleFileChosen(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
              />
              <svg className="upload-zone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <div className="upload-zone-label">{labels?.srcDropFile} <span className="upload-zone-browse">{labels?.srcBrowse}</span></div>
              <div className="upload-zone-hint">{labels?.srcFileTypes}</div>
            </label>
          </div>
        )}
      </div>
    </div>
  );
}

function ModuleA({ labels, onGenerated, isRtl, adaptiveParams }) {
  const [form, setForm] = useState(initialSpeechForm);

  // Adaptive difficulty (cahier D12): merge the recommended parameters from
  // the Progress page into the generation form whenever the student clicks
  // "Apply these settings".
  useEffect(() => {
    if (!adaptiveParams) return;
    const wc = Number(adaptiveParams.word_count || 0);
    const word_count_range = wc <= 180 ? 'short' : wc <= 320 ? 'medium' : wc <= 550 ? 'long' : 'extended';
    setForm(current => ({
      ...current,
      difficulty: adaptiveParams.difficulty || current.difficulty,
      word_count_range: wc ? word_count_range : current.word_count_range,
      number_density: adaptiveParams.number_density || current.number_density,
      speed_pressure: adaptiveParams.speed_pressure || current.speed_pressure,
      structure: adaptiveParams.structure || current.structure,
      topic_shifts: adaptiveParams.topic_shifts || current.topic_shifts,
    }));
  }, [adaptiveParams]);
  const [documentFiles, setDocumentFiles] = useState([]);   // File[]
  const [librarySources, setLibrarySources] = useState([]); // {text, title, un_id}[]
  const [retrievalResult, setRetrievalResult] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(true);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [showLibrary, setShowLibrary] = useState(false);
  const isLoading = status === 'loading';

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    // Changing topic or domain after attaching sources means the student
    // changed their mind — clear sources so generation isn't grounded in
    // now-irrelevant documents.
    if ((name === 'topic' || name === 'domain') && (documentFiles.length > 0 || librarySources.length > 0)) {
      setDocumentFiles([]);
      setLibrarySources([]);
      setRetrievalResult(null);
    }
    setForm(current => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  }

  const topicIsLongText = form.topic.trim().length > TOPIC_AS_SOURCE_THRESHOLD;

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus('loading'); setError(''); setResult(null);
    try {
      let params = form;
      if (topicIsLongText) {
        // Pasted full text → use it as the grounding source document and
        // derive a short topic from its first words.
        const pasted = form.topic.trim();
        params = {
          ...form,
          topic: pasted.split(/\s+/).slice(0, 12).join(' '),
          source_text: pasted,
          source_title: 'Pasted text',
        };
      }
      const data = await generateSpeech(params);
      setResult(data); onGenerated(data); setStatus('success');
    } catch (err) { setError(err.message); setStatus('error'); }
  }

  function buildAllSourceFiles() {
    const libFiles = librarySources.map(src => {
      const blob = new Blob([src.text], { type: 'text/plain' });
      return new File([blob], `${src.un_id || 'source'}.txt`, { type: 'text/plain' });
    });
    return [...documentFiles, ...libFiles];
  }

  const hasSources = documentFiles.length > 0 || librarySources.length > 0;

  async function handleDocumentGenerate() {
    setStatus('loading'); setError(''); setResult(null); setRetrievalResult(null);
    try {
      const allFiles = buildAllSourceFiles();
      if (!allFiles.length) throw new Error('Add at least one source document first.');
      const topicFallback = form.topic || librarySources[0]?.title || '';
      const data = await generateSpeechFromDocument(allFiles, { ...form, topic: topicFallback });
      setResult(data); onGenerated(data); setStatus('success');
    } catch (err) { setError(err.message); setStatus('error'); }
  }

  async function handleRetrieveContext() {
    setStatus('loading'); setError(''); setRetrievalResult(null);
    try {
      const allFiles = buildAllSourceFiles();
      if (!allFiles.length) throw new Error('Add at least one source document first.');
      const data = await retrieveDocumentContext(allFiles, {
        query: form.topic, language: form.language, domain: form.domain,
        scenario: 'UN General Assembly', difficulty: form.difficulty,
        mode: form.mode, number_density: form.number_density, max_chunks: 4
      });
      setRetrievalResult(data); setStatus('success');
    } catch (err) { setError(err.message); setStatus('error'); }
  }

  const LANG_LABEL = { ar: 'AR', fr: 'FR', en: 'EN' };

  return (
    <div className="card module-a-card">
      <form onSubmit={handleSubmit}>

        {/* ── Main topic bar — textarea so full texts can be pasted ── */}
        <div className="topic-bar">
          <textarea
            className="topic-input"
            name="topic"
            value={form.topic}
            minLength="3"
            maxLength="12000"
            required
            rows={topicIsLongText ? 6 : 1}
            placeholder={labels.topicPlaceholder || 'Enter a topic or paste text to generate a speech…'}
            onChange={updateField}
            disabled={isLoading}
            style={{ resize: 'vertical', overflow: 'auto', minHeight: '2.6rem' }}
          />
        </div>
        {topicIsLongText && (
          <div className="info-tip" style={{ marginTop: '0.4rem' }}>📄 {labels.longTextAsSource}</div>
        )}

        {/* ── Attached source chips ── */}
        {documentFiles.map((f, i) => (
          <div key={i} className="file-chip">
            <span>📄 {f.name}</span>
            <button type="button" className="file-chip-remove" onClick={() => {
              setDocumentFiles(prev => prev.filter((_, idx) => idx !== i));
              setRetrievalResult(null); setResult(null); setError('');
            }}>×</button>
          </div>
        ))}
        {librarySources.map((src, i) => (
          <div key={i} className="file-chip file-chip-un">
            <span>📚 {src.title.slice(0, 60)}{src.title.length > 60 ? '…' : ''}</span>
            <button type="button" className="file-chip-remove" onClick={() => {
              setLibrarySources(prev => prev.filter((_, idx) => idx !== i));
              setResult(null); setError('');
            }} title="Remove source">×</button>
          </div>
        ))}

        {/* ── Language + quick settings row ── */}
        <div className="quick-settings-row">
          <div className="lang-pair">
            <select name="language" value={form.language} onChange={updateField} className="lang-select" title="Speech language">
              <option value="ar">AR</option>
              <option value="fr">FR</option>
              <option value="en">EN</option>
            </select>
            <span className="lang-arrow">{isRtl ? '←' : '→'}</span>
            <select name="target_language" value={form.target_language} onChange={updateField} className="lang-select" title="Interpretation target">
              <option value="ar">AR</option>
              <option value="fr">FR</option>
              <option value="en">EN</option>
            </select>
          </div>

          <select name="difficulty" value={form.difficulty} onChange={updateField} className="quick-select">
            <option value="beginner">{labels.diffBeginner || 'Beginner'}</option>
            <option value="intermediate">{labels.diffIntermediate || 'Intermediate'}</option>
            <option value="advanced">{labels.diffAdvanced || 'Advanced'}</option>
          </select>

          <button
            type="button"
            className={`advanced-toggle ${showAdvanced ? 'advanced-toggle-active' : ''}`}
            onClick={() => setShowAdvanced(v => !v)}
          >
            {showAdvanced ? (labels.lessSettings || '⚙ Less') : (labels.moreSettings || '⚙ More')}
          </button>
        </div>

        {/* ── Advanced options (collapsible) ── */}
        {showAdvanced && (
          <div className="advanced-panel">
            <div className="form-grid">
              <SelectField label={labels.wordCount} id="f-words" name="word_count_range" value={form.word_count_range} onChange={updateField}>
                <option value="short">{labels.wordRangeShortFull || 'Short — 120–180 words (≈1–1.5 min)'}</option>
                <option value="medium">{labels.wordRangeMediumFull || 'Medium — 220–320 words (≈2–2.5 min)'}</option>
                <option value="long">{labels.wordRangeLongFull || 'Long — 400–550 words (≈3.5–4.5 min)'}</option>
                <option value="extended">{labels.wordRangeExtendedFull || 'Extended — 650–800 words (≈5.5–6.5 min)'}</option>
              </SelectField>
              <SelectField label={labels.domain} id="f-domain" name="domain" value={form.domain} onChange={updateField}>
                <option value="politics">{labels.domPolitics || 'Politics'}</option>
                <option value="diplomacy">{labels.domDiplomacy || 'Diplomacy'}</option>
                <option value="economics">{labels.domEconomics || 'Economics'}</option>
                <option value="climate">{labels.domClimate || 'Climate & Environment'}</option>
                <option value="health">{labels.domHealth || 'Health'}</option>
                <option value="human rights">{labels.domHumanRights || 'Human Rights'}</option>
                <option value="education">{labels.domEducation || 'Education'}</option>
                <option value="technology">{labels.domTechnology || 'Technology & AI'}</option>
                <option value="migration">{labels.domMigration || 'Migration & Refugees'}</option>
                <option value="disarmament">{labels.domDisarmament || 'Disarmament'}</option>
                <option value="women">{labels.domWomen || 'Women & Gender'}</option>
                <option value="food">{labels.domFood || 'Food & Hunger'}</option>
              </SelectField>
              <SelectField label={labels.scenarioLabel || 'Speaker style / setting'} id="f-scenario" name="scenario" value={form.scenario} onChange={updateField}>
                <option value="UN General Assembly">{labels.scenUNGA || 'UN General Assembly'}</option>
                <option value="EU Parliament">{labels.scenEUParl || 'EU Parliament'}</option>
                <option value="Arab League summit">{labels.scenArabLeague || 'Arab League summit'}</option>
                <option value="press conference">{labels.scenPress || 'Press conference'}</option>
                <option value="diplomatic meeting">{labels.scenDiplomatic || 'Diplomatic meeting'}</option>
                <option value="political debate">{labels.scenDebate || 'Political debate'}</option>
                <option value="interview">{labels.scenInterview || 'Interview'}</option>
              </SelectField>
              <SelectField label={labels.structure} id="f-structure" name="structure" value={form.structure} onChange={updateField}>
                <option value="well-organized">{labels.optWellOrganized || 'Well organized'}</option>
                <option value="semi-structured">{labels.optSemiStructured || 'Semi-structured'}</option>
                <option value="deliberately disorganized">{labels.optDisorganizedFull || 'Deliberately disorganized'}</option>
              </SelectField>
              <SelectField label={labels.numbers} id="f-numbers" name="number_density" value={form.number_density} onChange={updateField}>
                <option value="low">{labels.optLowNumbers || 'Low numbers'}</option>
                <option value="medium">{labels.optTermMedium || 'Medium'}</option>
                <option value="high">{labels.optHighNumbers || 'High numbers'}</option>
              </SelectField>
              <SelectField label={labels.termDensity || 'Terminology density'} id="f-term" name="terminology_density" value={form.terminology_density} onChange={updateField}>
                <option value="low">{labels.optTermLow || 'Low — everyday vocabulary'}</option>
                <option value="medium">{labels.optTermMedium || 'Medium'}</option>
                <option value="high">{labels.optTermHigh || 'High — dense specialised terms'}</option>
              </SelectField>
              <SelectField label={labels.speedPressure || 'Speed pressure'} id="f-speed" name="speed_pressure" value={form.speed_pressure} onChange={updateField}>
                <option value="normal">{labels.optNormalSpeed || 'Normal speed'}</option>
                <option value="fast">{labels.optFast || 'Fast'}</option>
                <option value="very_fast">{labels.optVeryFast || 'Very fast'}</option>
              </SelectField>
              <SelectField label={labels.topicShifts || 'Topic shifts'} id="f-shifts" name="topic_shifts" value={form.topic_shifts} onChange={updateField}>
                <option value="none">{labels.optNoShifts || 'No topic shifts'}</option>
                <option value="mild">{labels.optShifts || 'Topic shifts'}</option>
              </SelectField>
              <div className="field" style={{ display: 'flex', alignItems: 'flex-end' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 500 }}>
                  <input
                    type="checkbox"
                    name="include_hesitations"
                    checked={form.include_hesitations}
                    onChange={updateField}
                  />
                  {labels.hesitationsSim || 'Simulate hesitations'}
                </label>
              </div>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--warm-gray)', marginTop: '0.75rem', lineHeight: 1.5 }}>
              💡 {labels.diffHint}
            </p>
          </div>
        )}

        {/* ── Action buttons ── */}
        <div className="action-row">
          <button type="button" className="btn-un-library" onClick={() => setShowLibrary(true)} disabled={isLoading}>
            📚 Add source
          </button>
          {hasSources ? (
            <>
              <button type="button" className="btn-secondary" onClick={handleRetrieveContext} disabled={isLoading}>
                Preview context
              </button>
              <button type="button" className="btn-primary" onClick={handleDocumentGenerate} disabled={isLoading}>
                {isLoading ? labels.generating : `▷ ${labels.generateFromDocument || 'Generate from document'}`}
              </button>
            </>
          ) : (
            <button type="submit" className="btn-primary" disabled={isLoading}>
              {isLoading ? labels.generating : `▷ ${labels.submit || 'Generate speech'}`}
            </button>
          )}
        </div>

      </form>

      {error && <div className="error-msg" style={{ marginTop: '0.75rem' }}>{labels.errorPrefix}: {error}</div>}
      {isLoading && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', marginTop: '1rem' }}>
          <div className="spinner" />
          <p style={{ marginTop: '1rem', color: 'var(--warm-gray)' }}>{labels.generating}</p>
        </div>
      )}
      {retrievalResult && <RetrievalResult data={retrievalResult} labels={labels} onDismiss={() => setRetrievalResult(null)} />}
      {result && <SpeechResult data={result} labels={labels} />}

      {showLibrary && (
        <SourcesPanel
          labels={labels}
          language={form.language}
          domain={form.domain}
          initialQuery={form.topic}
          onSelectLibrary={src => { setLibrarySources(prev => [...prev, src]); setRetrievalResult(null); setResult(null); setError(''); }}
          onSelectFile={file => { setDocumentFiles(prev => [...prev, file]); setRetrievalResult(null); setResult(null); setError(''); }}
          onClose={() => setShowLibrary(false)}
        />
      )}
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

function SummaryBlock({ text, isArabic }) {
  const lines = (text || '').split('\n');
  return (
    <div className={`summary-block ${isArabic ? 'arabic' : ''}`}>
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return null;
        if (/^[IVXLCDM]+[.)]\s/.test(trimmed)) {
          return <div key={i} className="summary-heading">{trimmed}</div>;
        }
        if (/^[-•*]\s/.test(trimmed)) {
          return <div key={i} className="summary-bullet">{trimmed.replace(/^[-•*]\s/, '')}</div>;
        }
        if (/^\d+[.)]\s/.test(trimmed)) {
          return <div key={i} className="summary-subpoint">{trimmed}</div>;
        }
        return <div key={i} className="summary-line">{trimmed}</div>;
      })}
    </div>
  );
}

function RetrievalResult({ data, labels, onDismiss }) {
  return (
    <section className="retrieval-result">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <h3 style={{ margin: 0 }}>{labels.retrievedContext || 'Retrieved context'}</h3>
        {onDismiss && <button type="button" className="file-chip-remove" onClick={onDismiss} title="Clear context" style={{ fontSize: '1.1rem', padding: '0.1rem 0.4rem' }}>×</button>}
      </div>
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
  const requestedRange = data.word_count_range?.label;
  const rangeMissed = data.word_count_range && data.word_count_range.within_range === false;
  const topicLooksLikeDomain = String(data.topic || '').trim().toLowerCase()
    === String(data.domain || '').trim().toLowerCase();
  const visibleDomain = (!['groq', 'openai', 'gemini', 'local_aya', 'remote_aya'].includes(
    String(data.domain || '').trim().toLowerCase()
  ) && !topicLooksLikeDomain) ? data.domain : '';

  return (
    <div className="speech-result">
      <div className="result-meta">
        <span>
          {data.word_count} {labels.wordsUnit}
          {requestedRange ? ` / ${requestedRange}` : ''}
          {rangeMissed ? ` ${labels.outsideRange}` : ''}
        </span>
        {duration && <span>~{duration}</span>}
        {data.topic && <span>{data.topic}</span>}
        {visibleDomain && <span>{visibleDomain}</span>}
        <span>{String(data.language || '').toUpperCase()} → {String(data.target_language || '').toUpperCase()}</span>
      </div>
      {data.mode === 'un_library_grounded' && data.source_speech && (
        <p className="grounded-source-note">
          {labels.groundedSourceLabel}{' '}
          {data.source_speech.source_label ? `[${data.source_speech.source_label}] ` : ''}
          {data.source_speech.web_url ? (
            <a href={data.source_speech.web_url} target="_blank" rel="noopener noreferrer">
              {data.source_speech.title || data.source_speech.un_id}
            </a>
          ) : (
            data.source_speech.title || data.source_speech.un_id
          )}
          {data.source_speech.date ? ` (${data.source_speech.date})` : ''}
        </p>
      )}
      <div className={`speech-text ${isArabic ? 'arabic' : ''}`}>
        {data.script}
      </div>
      <p className="speech-next-hint">{labels.nextHintPre} <strong>{labels.navB}</strong> {labels.nextHintPost}</p>
    </div>
  );
}

// ── Interactive MCQ quiz — answers hidden until the student answers ─────────

function McqQuiz({ mcqs, labels, isArabic }) {
  const [answers, setAnswers] = useState({});

  function getCorrectText(item) {
    if (item.answer_text) return item.answer_text;
    if (Number.isInteger(item.answer_index) && Array.isArray(item.options))
      return item.options[item.answer_index] || '';
    const letter = String(item.answer || '').trim().toUpperCase();
    const idx = { A: 0, B: 1, C: 2, D: 3 }[letter];
    if (idx !== undefined && Array.isArray(item.options)) return item.options[idx] || '';
    return item.answer || '';
  }

  function isCorrectOption(item, option) {
    if (Number.isInteger(item.answer_index) && Array.isArray(item.options))
      return item.options[item.answer_index] === option;
    return option === getCorrectText(item);
  }

  function select(qi, option) {
    setAnswers(prev => (prev[qi]?.revealed ? prev : { ...prev, [qi]: { selected: option, revealed: false } }));
  }

  function check(qi) {
    setAnswers(prev => ({ ...prev, [qi]: { ...(prev[qi] || {}), revealed: true } }));
  }

  const revealedCount = mcqs.filter((_, qi) => answers[qi]?.revealed).length;
  const correctCount = mcqs.filter((item, qi) =>
    answers[qi]?.revealed && answers[qi]?.selected && isCorrectOption(item, answers[qi].selected)
  ).length;

  return (
    <div>
      <p style={{ fontSize: '0.83rem', color: 'var(--warm-gray)', marginBottom: '0.9rem' }}>
        {labels.mcqPickAnswer}
        {revealedCount > 0 && (
          <strong style={{ marginInlineStart: '0.75rem' }}>
            {labels.mcqYourScore}: {correctCount}/{revealedCount}
          </strong>
        )}
      </p>
      {mcqs.map((item, qi) => {
        const state = answers[qi] || {};
        const revealed = Boolean(state.revealed);
        const selectedIsCorrect = state.selected ? isCorrectOption(item, state.selected) : false;
        const correctText = getCorrectText(item);
        return (
          <div key={qi} className="eval-item" style={{ marginBottom: '1.1rem', paddingBottom: '0.9rem', borderBottom: '1px solid var(--border, #eee)' }}>
            <div className={`mcq-q ${isArabic ? 'arabic' : ''}`} style={{ fontWeight: 600, marginBottom: '0.55rem' }}>
              {qi + 1}. {item.question}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {(item.options || []).map((opt, oi) => {
                const letter = 'ABCD'[oi] || String(oi + 1);
                const isSelected = state.selected === opt;
                const optionCorrect = isCorrectOption(item, opt);
                let border = '1.5px solid var(--border, #ddd)';
                let background = 'transparent';
                if (revealed && optionCorrect) { border = '1.5px solid #2D5A4E'; background = '#2d5a4e14'; }
                else if (revealed && isSelected && !optionCorrect) { border = '1.5px solid #8B3A2A'; background = '#8b3a2a14'; }
                else if (isSelected) { border = '1.5px solid var(--primary, #1a3a5c)'; background = '#1a3a5c0d'; }
                return (
                  <button
                    key={oi}
                    type="button"
                    onClick={() => select(qi, opt)}
                    className={isArabic ? 'arabic' : ''}
                    style={{
                      textAlign: 'start', padding: '0.5rem 0.75rem', borderRadius: 8,
                      border, background, cursor: revealed ? 'default' : 'pointer',
                      fontSize: '0.86rem', lineHeight: 1.45,
                      display: 'flex', gap: '0.55rem', alignItems: 'flex-start',
                    }}
                  >
                    <span style={{ fontWeight: 700, minWidth: '1.1rem', color: 'var(--warm-gray)' }}>{letter}.</span>
                    <span style={{ flex: 1 }}>{opt}{revealed && optionCorrect && ' ✓'}</span>
                  </button>
                );
              })}
            </div>
            {!revealed ? (
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.55rem' }}>
                <button type="button" className="btn-secondary btn-sm" onClick={() => check(qi)} disabled={!state.selected}>
                  {labels.mcqCheck}
                </button>
                <button type="button" className="btn-secondary btn-sm" style={{ opacity: 0.7 }} onClick={() => check(qi)}>
                  {labels.mcqShowAnswer}
                </button>
              </div>
            ) : (
              <p style={{ marginTop: '0.55rem', fontSize: '0.84rem', fontWeight: 600,
                color: state.selected ? (selectedIsCorrect ? '#2D5A4E' : '#8B3A2A') : 'var(--warm-gray)' }}>
                {state.selected
                  ? (selectedIsCorrect
                    ? labels.mcqCorrectMsg
                    : <>{labels.mcqWrongMsg} <strong>{correctText}</strong></>)
                  : <>{labels.mcqShowAnswerLabel} <strong>{correctText}</strong></>}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Sight translation scroller (professor request, cf. scroller.dipintra.it) ─
// Continuous vertical scroll at a words/min pace with a live dashboard
// (elapsed / remaining), like the University of Bologna Scroller tool.

function SightScroller({ script, isArabic, labels }) {
  const [playing, setPlaying] = useState(false);
  const [wpm, setWpm] = useState(120);
  const [fontSize, setFontSize] = useState(1.15);   // rem
  const [columns, setColumns] = useState(1);
  const [spacing, setSpacing] = useState(1.9);      // line-height
  const [progress, setProgress] = useState(0);      // 0..1 of the exercise
  const wrapRef = useRef(null);
  const rafRef = useRef(null);
  const lastTsRef = useRef(null);
  const lastUiUpdateRef = useRef(0);
  // Time-driven engine (like scroller.dipintra.it): progress is a fraction of
  // elapsed exercise TIME, and the scroll position is derived from it each
  // frame. Timer and scroll can never disagree, and the float accumulator
  // avoids the whole-pixel scrollTop rounding that froze slow speeds.
  const progressRef = useRef(0);

  const wordCount = useMemo(() => String(script || '').split(/\s+/).filter(Boolean).length, [script]);
  const totalSeconds = (wordCount / Math.max(40, wpm)) * 60;

  useEffect(() => {
    if (!playing) {
      cancelAnimationFrame(rafRef.current);
      lastTsRef.current = null;
      return;
    }
    // Re-sync with the scrollbar (the user may have dragged it while paused).
    const wrapAtStart = wrapRef.current;
    if (wrapAtStart) {
      const scrollable = wrapAtStart.scrollHeight - wrapAtStart.clientHeight;
      if (scrollable > 0 && wrapAtStart.scrollTop > 0) {
        progressRef.current = wrapAtStart.scrollTop / scrollable;
      }
    }
    function step(ts) {
      const wrap = wrapRef.current;
      if (!wrap) return;
      if (lastTsRef.current != null && totalSeconds > 0) {
        const dt = (ts - lastTsRef.current) / 1000;
        progressRef.current = Math.min(1, progressRef.current + dt / totalSeconds);
        const scrollable = wrap.scrollHeight - wrap.clientHeight;
        if (scrollable > 0) {
          wrap.scrollTop = progressRef.current * scrollable;
        }
        if (ts - lastUiUpdateRef.current > 200) {
          lastUiUpdateRef.current = ts;
          setProgress(progressRef.current);
        }
        if (progressRef.current >= 1) {
          setProgress(1);
          setPlaying(false);
        }
      }
      lastTsRef.current = ts;
      rafRef.current = requestAnimationFrame(step);
    }
    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing, totalSeconds]);

  function reset() {
    setPlaying(false);
    setProgress(0);
    progressRef.current = 0;
    if (wrapRef.current) wrapRef.current.scrollTop = 0;
  }

  function fmtTime(seconds) {
    const s = Math.max(0, Math.round(seconds));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  }

  const elapsed = progress * totalSeconds;
  const wordsRead = Math.round(progress * wordCount);

  return (
    <div>
      <p style={{ fontSize: '0.83rem', color: 'var(--warm-gray)', marginBottom: '0.75rem' }}>{labels.scrollerHint}</p>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: '0.9rem' }}>
        <div className="field" style={{ minWidth: 160 }}>
          <label>{labels.scrollerSpeed}: <strong>{wpm}</strong></label>
          <input type="range" min="80" max="240" step="10" value={wpm}
            onChange={e => setWpm(Number(e.target.value))} className="rate-slider" />
        </div>
        <div className="field" style={{ minWidth: 100 }}>
          <label>{labels.scrollerFontSize}</label>
          <select value={fontSize} onChange={e => setFontSize(Number(e.target.value))}>
            <option value={0.95}>A</option>
            <option value={1.15}>A+</option>
            <option value={1.45}>A++</option>
            <option value={1.8}>A+++</option>
          </select>
        </div>
        <div className="field" style={{ minWidth: 90 }}>
          <label>{labels.scrollerColumns}</label>
          <select value={columns} onChange={e => setColumns(Number(e.target.value))}>
            <option value={1}>1</option>
            <option value={2}>2</option>
          </select>
        </div>
        <div className="field" style={{ minWidth: 100 }}>
          <label>{labels.scrollerSpacing}</label>
          <select value={spacing} onChange={e => setSpacing(Number(e.target.value))}>
            <option value={1.55}>1</option>
            <option value={1.9}>1.5</option>
            <option value={2.4}>2</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="button" className="btn-primary" onClick={() => setPlaying(p => !p)}>
            {playing ? labels.scrollerPause : labels.scrollerPlay}
          </button>
          <button type="button" className="btn-secondary" onClick={reset}>{labels.scrollerReset}</button>
        </div>
      </div>

      {/* Live dashboard — elapsed / remaining / words, like the Bologna tool */}
      <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', marginBottom: '0.6rem',
        fontSize: '0.8rem', color: 'var(--warm-gray)', fontVariantNumeric: 'tabular-nums' }}>
        <span>⏱ {fmtTime(elapsed)} / {fmtTime(totalSeconds)}</span>
        <span>⏳ −{fmtTime(totalSeconds - elapsed)}</span>
        <span>📖 {wordsRead} / {wordCount} {labels.wordsUnit}</span>
        <span style={{ flex: 1, alignSelf: 'center', height: 4, background: 'rgba(27,58,107,0.12)', borderRadius: 2, minWidth: 120 }}>
          <span style={{ display: 'block', height: '100%', width: `${Math.round(progress * 100)}%`,
            background: 'var(--primary, #1a3a5c)', borderRadius: 2, transition: 'width 0.25s linear' }} />
        </span>
      </div>

      {/* Outer wrapper owns the fixed height + vertical scrollbar; the inner
          block owns the column layout with natural height — putting both on
          one element makes CSS columns overflow horizontally (no scrolling).
          Spacer divs make the text enter from the bottom and exit through the
          top, teleprompter-style, like the Bologna Scroller tool. */}
      <div
        ref={wrapRef}
        style={{
          height: 340, overflowY: 'auto', overflowX: 'hidden',
          border: '1px solid var(--border, #ddd)', borderRadius: 10,
          background: 'var(--surface, #fff)',
        }}
      >
        <div aria-hidden="true" style={{ height: 300 }} />
        <div
          className={isArabic ? 'arabic' : ''}
          dir={isArabic ? 'rtl' : 'ltr'}
          style={{
            padding: '0 1.5rem',
            fontSize: `${fontSize}rem`, lineHeight: spacing,
            columnCount: columns, columnGap: '2.5rem', whiteSpace: 'pre-wrap',
          }}
        >
          {script}
        </div>
        <div aria-hidden="true" style={{ height: 280 }} />
      </div>
    </div>
  );
}

// ── Module B — TTS + Pedagogical Materials ──────────────────────────────────

function ModuleB({ labels, lastGeneratedScript, onAudioGenerated, onScriptUpdate, isRtl }) {
  const language = lastGeneratedScript?.language || 'ar';
  const isArabic = language === 'ar';
  const voiceOptions = VOICE_OPTIONS[language] || VOICE_OPTIONS.en;
  const speechId = lastGeneratedScript?.script?.slice(0, 50) || '';

  const [selectedAccent, setSelectedAccent] = useState(voiceOptions[0]?.accent || '');
  const [speechRate, setSpeechRate] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioStatus, setAudioStatus] = useState('idle');
  const [audioError, setAudioError] = useState('');
  const [editingGlossary, setEditingGlossary] = useState(false);

  function updateGlossaryCell(index, key, value) {
    const current = lastGeneratedScript?.glossary || [];
    const updated = current.map((row, i) => (i === index ? { ...row, [key]: value } : row));
    // Propagate upward so Module D evaluates terminology against the
    // student-corrected glossary (cahier des charges request).
    onScriptUpdate?.({ ...lastGeneratedScript, glossary: updated });
  }

  useEffect(() => {
    const opts = VOICE_OPTIONS[language] || VOICE_OPTIONS.en;
    setSelectedAccent(opts[0]?.accent || '');
    setAudioUrl(null);
    setAudioStatus('idle');
    setAudioError('');
  }, [speechId]);

  if (!lastGeneratedScript) {
    return (
      <div className="card coming-soon">
        <p className="eyebrow">{labels.moduleBTitle}</p>
        <p>{labels.noSpeechYet}</p>
      </div>
    );
  }

  const summary  = lastGeneratedScript.summary  || '';
  const mcqs     = lastGeneratedScript.mcqs     || [];
  const glossary = lastGeneratedScript.glossary || [];

  async function handleGenerateAudio() {
    setAudioStatus('loading'); setAudioError('');
    try {
      const data = await textToSpeech({ text: lastGeneratedScript.script, language, accent: selectedAccent, rate_adjustment: speechRate });
      const url = `${SERVER_BASE}${data.audio_url}`;
      setAudioUrl(url); onAudioGenerated?.(url); setAudioStatus('success');
    } catch (err) { setAudioError(err.message); setAudioStatus('error'); }
  }

  async function handleDownloadGlossary() {
    try {
      const mapped = glossary.map(item => ({
        ar: glossaryArabicValue(item),
        fr: glossaryValue(item, ['french', 'French', 'fr', 'FR', 'french_term', 'term_fr', 'french_translation', 'translation_fr', 'français', 'francais']),
        en: glossaryValue(item, ['english', 'English', 'en', 'EN', 'english_term', 'term_en', 'english_translation', 'translation_en']),
      }));
      const blob = await downloadGlossary({ glossary: mapped, domain: lastGeneratedScript.domain });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url;
      a.download = `glossary_${lastGeneratedScript.domain}.docx`; a.click();
      URL.revokeObjectURL(url);
    } catch (err) { alert(`${labels.errorPrefix}: ${err.message}`); }
  }

  return (
    <div className="module-b-layout">

      {/* ── Audio ── */}
      <div className="card">
        <h2 className="b-section-title">🔊 {labels.moduleBTitle}</h2>
        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <SelectField label={labels.voiceAccent} id="b-voice" name="voice"
            value={selectedAccent} onChange={e => setSelectedAccent(e.target.value)}>
            {voiceOptions.map(v => (
              <option key={v.accent} value={v.accent}>{isRtl ? (v.labelAr || v.label) : v.label}</option>
            ))}
          </SelectField>
          <div className="field">
            <label htmlFor="b-rate">{labels.speechRate}: {speechRate > 0 ? `+${speechRate}` : speechRate}%</label>
            <input id="b-rate" type="range" min="-20" max="20" step="5"
              value={speechRate} onChange={e => setSpeechRate(Number(e.target.value))} className="rate-slider" />
          </div>
        </div>
        <button className="btn-primary" onClick={handleGenerateAudio} disabled={audioStatus === 'loading'}>
          {audioStatus === 'loading' ? labels.generatingAudio : `▷ ${labels.generateAudio}`}
        </button>
        {audioError && <div className="error-msg" style={{ marginTop: '0.75rem' }}>{labels.errorPrefix}: {audioError}</div>}
        {audioUrl && <div style={{ marginTop: '1rem' }}><audio key={audioUrl} controls src={audioUrl} style={{ width: '100%' }} /></div>}
      </div>

      {/* ── Summary ── */}
      {summary && (
        <div className="card">
          <h2 className="b-section-title">📋 {labels.summaryTitle}</h2>
          <SummaryBlock text={summary} isArabic={isArabic} />
        </div>
      )}

      {/* ── MCQ — interactive: the answer stays hidden until the student answers ── */}
      {mcqs.length > 0 && (
        <div className="card">
          <h2 className="b-section-title">❓ {labels.mcqTitle}</h2>
          {/* key = speech fingerprint: a new speech mounts a fresh quiz,
              otherwise answers from the previous text stay selected */}
          <McqQuiz key={speechId} mcqs={mcqs} labels={labels} isArabic={isArabic} />
        </div>
      )}

      {/* ── Glossary — editable BEFORE recording; evaluation checks against it ── */}
      {glossary.length > 0 && (
        <div className="card">
          <div className="b-section-header">
            <h2 className="b-section-title">📖 {labels.glossaryTitle}</h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn-secondary btn-sm" onClick={() => setEditingGlossary(v => !v)}>
                {editingGlossary ? labels.glossaryEditDone : labels.glossaryEdit}
              </button>
              <button className="btn-secondary btn-sm" onClick={handleDownloadGlossary}>{labels.downloadGlossary}</button>
            </div>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--warm-gray)', marginBottom: '0.75rem' }}>
            💡 {labels.glossaryEditHint}
          </p>
          <div className="table-responsive">
            <table className="glossary-table">
              <thead>
                <tr>
                  <th>{labels.glossaryTermHeader || 'Term'}</th>
                  <th>{labels.glossaryArabicHeader || 'Arabic'}</th>
                  <th>{labels.glossaryFrenchHeader || 'French'}</th>
                  <th>{labels.glossaryEnglishHeader || 'English'}</th>
                  <th>{labels.glossaryDefinitionHeader || 'Definition'}</th>
                </tr>
              </thead>
              <tbody>
                {glossary.map((item, i) => (
                  <tr key={i}>
                    {editingGlossary ? (
                      <>
                        <td><input className="glossary-edit-input" value={item.term || ''} onChange={e => updateGlossaryCell(i, 'term', e.target.value)} /></td>
                        <td><input className="glossary-edit-input arabic" dir="rtl" value={glossaryArabicValue(item)} onChange={e => updateGlossaryCell(i, 'arabic', e.target.value)} /></td>
                        <td><input className="glossary-edit-input" value={glossaryValue(item, ['french', 'French', 'fr', 'FR', 'french_term', 'term_fr', 'french_translation', 'translation_fr', 'français', 'francais'])} onChange={e => updateGlossaryCell(i, 'french', e.target.value)} /></td>
                        <td><input className="glossary-edit-input" value={glossaryValue(item, ['english', 'English', 'en', 'EN', 'english_term', 'term_en', 'english_translation', 'translation_en'])} onChange={e => updateGlossaryCell(i, 'english', e.target.value)} /></td>
                        <td><input className="glossary-edit-input" value={item.definition || ''} onChange={e => updateGlossaryCell(i, 'definition', e.target.value)} /></td>
                      </>
                    ) : (
                      <>
                        <td><strong>{item.term}</strong></td>
                        <td className="arabic" dir="rtl">{glossaryArabicValue(item)}</td>
                        <td>{glossaryValue(item, ['french', 'French', 'fr', 'FR', 'french_term', 'term_fr', 'french_translation', 'translation_fr', 'français', 'francais'])}</td>
                        <td>{glossaryValue(item, ['english', 'English', 'en', 'EN', 'english_term', 'term_en', 'english_translation', 'translation_en'])}</td>
                        <td className="gloss-def">{item.definition || ''}</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}

// ── Note-taking space for consecutive interpretation (text + sketch) ─────────

function NotesPad({ labels }) {
  const [tab, setTab] = useState('text');   // 'text' | 'sketch'
  const [notes, setNotes] = useState('');
  const canvasRef = useRef(null);
  const drawingRef = useRef(false);
  const lastPointRef = useRef(null);

  function canvasPos(e) {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const source = e.touches ? e.touches[0] : e;
    return {
      x: (source.clientX - rect.left) * (canvas.width / rect.width),
      y: (source.clientY - rect.top) * (canvas.height / rect.height),
    };
  }

  function startDraw(e) {
    drawingRef.current = true;
    lastPointRef.current = canvasPos(e);
  }

  function draw(e) {
    if (!drawingRef.current) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const point = canvasPos(e);
    ctx.strokeStyle = '#1a3a5c';
    ctx.lineWidth = 2.2;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
    ctx.lineTo(point.x, point.y);
    ctx.stroke();
    lastPointRef.current = point;
  }

  function endDraw() {
    drawingRef.current = false;
  }

  function clearAll() {
    if (tab === 'text') {
      setNotes('');
    } else {
      const canvas = canvasRef.current;
      canvas?.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  return (
    <div className="record-section" style={{ marginTop: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.6rem', flexWrap: 'wrap' }}>
        <p className="record-section-label" style={{ margin: 0 }}>{labels.notesTitle}</p>
        <div style={{ display: 'flex', gap: '0.35rem' }}>
          <button type="button" className={`lib-tab ${tab === 'text' ? 'lib-tab-active' : ''}`} onClick={() => setTab('text')}>
            {labels.notesTextTab}
          </button>
          <button type="button" className={`lib-tab ${tab === 'sketch' ? 'lib-tab-active' : ''}`} onClick={() => setTab('sketch')}>
            {labels.notesSketchTab}
          </button>
        </div>
        <button type="button" className="btn-secondary btn-sm" onClick={clearAll}>{labels.notesClear}</button>
      </div>

      {tab === 'text' ? (
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder={labels.notesPlaceholder}
          style={{
            width: '100%', minHeight: 160, padding: '0.75rem 1rem',
            border: '1px solid var(--border, #ddd)', borderRadius: 10,
            fontSize: '0.92rem', lineHeight: 1.6, resize: 'vertical',
            fontFamily: 'inherit', background: 'var(--surface, #fff)',
          }}
        />
      ) : (
        <canvas
          ref={canvasRef}
          width={900}
          height={360}
          style={{
            width: '100%', height: 240, border: '1px solid var(--border, #ddd)',
            borderRadius: 10, background: 'var(--surface, #fff)', touchAction: 'none', cursor: 'crosshair',
          }}
          onMouseDown={startDraw} onMouseMove={draw} onMouseUp={endDraw} onMouseLeave={endDraw}
          onTouchStart={startDraw} onTouchMove={draw} onTouchEnd={endDraw}
        />
      )}
      <p style={{ fontSize: '0.75rem', color: 'var(--warm-gray)', marginTop: '0.4rem' }}>{labels.notesHint}</p>
    </div>
  );
}

// ── Module C — ASR Transcription + Browser Recording ────────────────────────

function ModuleC({ labels, referenceAudioUrl, sourceScript, targetLanguage, onTranscriptComplete, onRecordingComplete }) {
  const [language, setLanguage] = useState('ar');

  // The student interprets INTO the target language chosen in Module A —
  // preselect it so the recognizer transcribes in the right language.
  useEffect(() => {
    if (targetLanguage && ['ar', 'fr', 'en'].includes(targetLanguage)) {
      setLanguage(targetLanguage);
    }
  }, [targetLanguage]);
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
  const fileInputRef = useRef(null);
  const referenceAudioRef = useRef(null);
  const [simultaneousActive, setSimultaneousActive] = useState(false);
  // 3 practice modes (professor request): simultaneous | consecutive | sight
  const [interpMode, setInterpMode] = useState('consecutive');
  const sourceIsArabic = /[؀-ۿ]/.test(sourceScript || '');

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

  // Simultaneous interpretation: the source speech plays WHILE the student
  // records — echo cancellation reduces source bleed; headphones recommended.
  async function startSimultaneous() {
    const player = referenceAudioRef.current;
    if (!player) return;
    try {
      player.currentTime = 0;
      setSimultaneousActive(true);
      const started = await startRecording({ echoCancellation: true, noiseSuppression: true });
      if (!started) { setSimultaneousActive(false); return; }
      await player.play();
      player.onended = () => stopSimultaneous();
    } catch (err) {
      setSimultaneousActive(false);
      setError('Could not start simultaneous mode — check microphone permission.');
    }
  }

  function stopSimultaneous() {
    const player = referenceAudioRef.current;
    if (player) { player.pause(); player.onended = null; }
    setSimultaneousActive(false);
    stopRecording();
  }

  async function startRecording(audioConstraints) {
    try {
      // Guard: when used as onClick handler the first arg is the click event.
      const isConstraintObject = audioConstraints && typeof audioConstraints === 'object'
        && !('target' in audioConstraints);
      const constraints = { audio: isConstraintObject ? audioConstraints : true };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
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
      return true;
    } catch (err) {
      setError('Microphone access denied — please allow microphone permission and try again.');
      return false;
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    clearInterval(timerRef.current);
  }

  function clearTranscript() {
    setResult(null);
    setError('');
  }

  function clearAudio() {
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedBlob(null);
    setRecordedUrl(null);
    setResult(null);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    onRecordingComplete?.(null);
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

        {/* ── Practice mode selector: simultaneous | consecutive | sight ── */}
        <div style={{ marginBottom: '1.25rem' }}>
          <p className="record-section-label" style={{ marginBottom: '0.5rem' }}>{labels.modeChoose}</p>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {[
              { id: 'simultaneous', name: labels.optSimultaneous, icon: '🎧' },
              { id: 'consecutive',  name: labels.optConsecutive,  icon: '📝' },
              { id: 'sight',        name: labels.optSight,        icon: '📜' },
            ].map(m => (
              <button
                key={m.id}
                type="button"
                onClick={() => setInterpMode(m.id)}
                style={{
                  flex: '1 1 140px', padding: '0.65rem 0.9rem', borderRadius: 10, cursor: 'pointer',
                  border: interpMode === m.id ? '2px solid var(--primary, #1a3a5c)' : '1.5px solid var(--border, #ddd)',
                  background: interpMode === m.id ? 'rgba(27,58,107,0.07)' : 'transparent',
                  fontWeight: interpMode === m.id ? 700 : 500, fontSize: '0.9rem',
                }}
              >
                {m.icon} {m.name}
              </button>
            ))}
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--warm-gray)', marginTop: '0.5rem' }}>
            {interpMode === 'simultaneous' && labels.modeSimulDesc}
            {interpMode === 'consecutive' && labels.modeConsecDesc}
            {interpMode === 'sight' && labels.modeSightDesc}
          </p>
        </div>

        {/* Reference audio from Module B — for simultaneous & consecutive */}
        {interpMode !== 'sight' && referenceAudioUrl && (
          <div className="reference-audio-box">
            <p className="ref-audio-label">🔊 {labels.sourceAudio}</p>
            <audio ref={referenceAudioRef} controls src={referenceAudioUrl} style={{ width: '100%' }} />
          </div>
        )}

        {/* Simultaneous — source plays while the student records */}
        {interpMode === 'simultaneous' && (
          <div className="record-section" style={{ borderLeft: '3px solid var(--primary, #1a3a5c)', paddingLeft: '0.9rem', marginBottom: '1rem' }}>
            <p className="record-section-label">{labels.simulTitle}</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--warm-gray)', margin: '0.3rem 0 0.6rem' }}>
              {referenceAudioUrl ? labels.simulHint : labels.simulNeedsAudio}
            </p>
            {referenceAudioUrl && (
              !simultaneousActive ? (
                <button className="btn-primary" onClick={startSimultaneous} disabled={isRecording}>
                  {labels.simulStart}
                </button>
              ) : (
                <button className="btn-record recording-active" onClick={stopSimultaneous}>
                  <span className="rec-dot" /> {labels.simulStop} — {formatTime(recordingTime)}
                </button>
              )
            )}
          </div>
        )}

        {/* Sight translation — scrolling source text, record while translating */}
        {interpMode === 'sight' && (
          <div className="record-section" style={{ marginBottom: '1rem' }}>
            {sourceScript ? (
              <SightScroller key={sourceScript.slice(0, 50)} script={sourceScript} isArabic={sourceIsArabic} labels={labels} />
            ) : (
              <div className="info-tip">ℹ️ {labels.needsSource}</div>
            )}
          </div>
        )}

        {/* Recording section */}
        <div className="record-section">
          <p className="record-section-label">🎙 {labels.yourInterpretation}</p>

          <div className="record-controls">
            {!isRecording ? (
              <button className="btn-record" onClick={startRecording} disabled={simultaneousActive}>
                {labels.recordBtn}
              </button>
            ) : !simultaneousActive ? (
              <button className="btn-record recording-active" onClick={stopRecording}>
                <span className="rec-dot" /> {labels.stopBtn} — {formatTime(recordingTime)}
              </button>
            ) : (
              <span style={{ fontSize: '0.85rem', color: 'var(--warm-gray)' }}>
                {labels.recordingLive}… ({labels.simulTitle})
              </span>
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
              <div className="recorded-audio-row">
                <audio controls src={recordedUrl} style={{ width: '100%' }} />
                <button className="btn-icon-danger" onClick={clearAudio} title={labels.deleteAudio}>
                  <IconTrash />
                </button>
              </div>
              <div className="record-controls" style={{ marginTop: '0.75rem' }}>
                {!autoTranscribe && (
                  <button className="btn-primary"
                    onClick={() => runTranscription(recordedBlob)}
                    disabled={status === 'loading'}>
                    {status === 'loading' ? labels.transcribing : labels.transcribeBtn}
                  </button>
                )}
                {result && (
                  <button className="btn-secondary"
                    onClick={() => runTranscription(recordedBlob)}
                    disabled={status === 'loading'}>
                    ↻ {labels.redoTranscript}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Note-taking space — consecutive mode only */}
        {interpMode === 'consecutive' && <NotesPad labels={labels} />}

        {/* Upload fallback */}
        <details className="upload-fallback">
          <summary>{labels.orUpload}</summary>
          <div className="upload-fallback-row" style={{ marginTop: '0.75rem' }}>
            <input ref={fileInputRef} type="file" accept=".mp3,.wav,.m4a,.ogg,.webm" className="file-input"
              onChange={e => {
                const f = e.target.files[0];
                if (f) {
                  setRecordedBlob(f);
                  onRecordingComplete?.(f);
                  runTranscription(f);
                }
              }} />
            {recordedBlob && (
              <button className="btn-icon-danger" onClick={clearAudio} title={labels.deleteAudio}>
                <IconTrash />
              </button>
            )}
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
                onDelete={clearTranscript}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Module D — Full Evaluation Report ────────────────────────────────────────

function ScoreBar({ score, labels }) {
  const pct = Math.round((score / 10) * 100);
  const color = score >= 7 ? '#2D5A4E' : score >= 5 ? '#1B3A6B' : '#8B3A2A';
  const circumference = 188.5;
  const offset = circumference - (circumference * pct / 100);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
      <div className="prog-ring" style={{ width: 64, height: 64 }}>
        <svg viewBox="0 0 70 70"><circle className="prog-ring-bg" cx="35" cy="35" r="30"/><circle className="prog-ring-fill" cx="35" cy="35" r="30" stroke={color} strokeDasharray={circumference} strokeDashoffset={offset}/></svg>
        <div className="prog-pct" style={{ fontSize: '0.85rem' }}>{score.toFixed(1)}</div>
      </div>
      <div>
        <div className="score-bar-wrap"><div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} /></div>
        <div style={{ fontSize: '0.74rem', color: 'var(--warm-gray)', marginTop: '0.3rem' }}>{pct}% — {score >= 7 ? (labels?.verdictGood || 'Good') : score >= 5 ? (labels?.verdictAcceptable || 'Acceptable') : (labels?.verdictNeedsWork || 'Needs work')}</div>
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
    ? (result.coverage_score >= 8 ? '#1a6b3c' : result.coverage_score >= 6 ? '#1B3A6B' : '#c0392b')
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
              <p className="report-label">{labels.coverageScoreLabel}</p>
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
              <h4 style={{ color: '#1B3A6B', fontSize: '0.85rem', fontWeight: 700,
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

function ModuleD({ labels, lastTranscript, lastGeneratedScript, lastRecordingBlob, onEvaluationSaved }) {
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
          lastGeneratedScript?.language || language,
          lastGeneratedScript?.domain || '',
          lastGeneratedScript?.glossary || []   // student-reviewed glossary → terminology check
        );
      } else {
        // Fallback: use stored Groq transcript (less accurate for hesitations)
        data = await generateFeedback({
          source_script:   lastGeneratedScript?.script || '',
          transcript_text: lastTranscript.full_text,
          transcript:      lastTranscript,
          language,
          glossary:        lastGeneratedScript?.glossary || []
        });
      }
      // Attach pronunciation report for the pronunciation panel
      if (data.pronunciation) {
        data._pronunciationForPanel = {
          overall_score: data.pronunciation.overall_score,
          uncertain_count: data.pronunciation.uncertain_count,
          flagged_words: data.pronunciation.flagged_words || [],
          summary: data.pronunciation.summary,
        };
      }
      setReport(data);
      setStatus('success');
      onEvaluationSaved?.();
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
  const fluency = report?.fluency || null;
  const isAr = (lastTranscript.language || lastTranscript.language_detected) === 'ar';
  const llmNumberErrors = (report?.number_accuracy || [])
    .filter(item => item && item.correct === false)
    .map(item => ({
      ...item,
      message: `${item.source_value || ''} was rendered as ${item.student_said || 'missing'}`.trim(),
    }));
  const displayNumberErrors = llmNumberErrors.length > 0 ? llmNumberErrors : (algo.number_errors || []);

  return (
    <div>
      <div className="card">
        <h2>{labels.moduleDTitle}</h2>
        <div className="info-tip" style={{ marginBottom: '1rem' }}>
          📄 {labels.transcriptReady} ({lastTranscript.duration_seconds}s · {(lastTranscript.language_detected || '').toUpperCase()})
          {lastGeneratedScript && <> · {labels.source}: {lastGeneratedScript.domain}</>}
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
                <ScoreBar score={report.overall_score || 0} labels={labels} />
              </div>
              {report.fluency_score !== undefined && (
                <div>
                  <p className="report-label">{labels.fluencyScore}</p>
                  <ScoreBar score={report.fluency_score || 0} labels={labels} />
                </div>
              )}
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
                { label: labels.numberErrors,  icon: '🔢', items: displayNumberErrors },
              ].map(({ label, icon, items }) => (
                <div key={label} className={`algo-card ${items.length > 0 ? 'algo-card-warn' : ''}`}>
                  <span className="algo-icon">{icon}</span>
                  <span className="algo-count">{items.length}</span>
                  <span className="algo-label">{label}</span>
                </div>
              ))}
            </div>
            {/* Detail lists */}
            {(algo.long_silences || []).length > 0 && (
              <div className="algo-detail-block">
                <p className="algo-detail-title">🔇 {labels.longSilences}</p>
                {algo.long_silences.map((s, i) => {
                  const isPrep = String(s.type || '').includes('leading') || Number(s.at_seconds) === 0;
                  return (
                    <div key={i} className="algo-detail-row">
                      <span className={`algo-detail-badge ${isPrep ? 'algo-badge-gold' : 'algo-badge-warn'}`}>{s.duration_seconds}s</span>
                      <span className="algo-detail-text">
                        {isPrep
                          ? <>⏱ {labels.prepTimeLabel}</>
                          : <>at {s.at_seconds}s{s.after_text ? ` after: "${s.after_text}"` : ''}</>}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
            {(algo.repetitions || []).length > 0 && (
              <div className="algo-detail-block">
                <p className="algo-detail-title">🔁 {labels.repetitions}</p>
                {algo.repetitions.map((r, i) => (
                  <div key={i} className="algo-detail-row">
                    <span className="algo-detail-badge algo-badge-gold">"{r.word}"</span>
                    <span className="algo-detail-text">
                      {r.at_seconds !== undefined
                        ? `at ${r.at_seconds}s${r.second_occurrence !== undefined ? ` · again at ${r.second_occurrence}s` : ''}`
                        : `near word ${r.position ?? i}`}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {(algo.hesitation_words || []).length > 0 && (
              <div className="algo-detail-block">
                <p className="algo-detail-title">🗣️ {labels.hesitations}</p>
                <div className="algo-chips">
                  {algo.hesitation_words.map((h, i) => (
                    <span key={i} className="algo-chip">
                      "{h.word}" <small>{h.at_seconds !== undefined ? `${h.at_seconds}s` : ''}</small>
                    </span>
                  ))}
                </div>
              </div>
            )}
            {displayNumberErrors.length > 0 && (
              <div className="algo-detail-block">
                <p className="algo-detail-title">🔢 {labels.numberErrors}</p>
                <div className="algo-chips">
                  {displayNumberErrors.map((n, i) => (
                    <span key={i} className="algo-chip algo-chip-err">
                      {typeof n === 'string' ? n : (n.message || `${n.expected || ''} → ${n.heard || ''}`)}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Pause & flow analysis */}
          {report.pause_analysis && (
            <div className="card">
              <h3 className="report-section-title">⏸️ {labels.pauseAnalysisTitle}</h3>
              {report.pause_analysis.comment && (
                <p className={isAr ? 'arabic' : ''} style={{ fontSize: '0.85rem', color: 'var(--ink)' }}>{report.pause_analysis.comment}</p>
              )}
              {(report.pause_analysis.problem_pauses || []).map((p, i) => {
                const detectedPause = (algo.long_silences || [])[i] || {};
                const duration = detectedPause.duration_seconds ?? p.duration_seconds;
                const atSeconds = detectedPause.at_seconds ?? p.at_seconds;
                return (
                  <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--sienna)', paddingLeft: '0.75rem', marginTop: '0.5rem' }}>
                    <strong style={{ fontSize: '0.84rem' }}>
                      {duration}s {labels.longSilences.toLowerCase()}
                      {Number.isFinite(Number(atSeconds)) && (
                        Number(atSeconds) === 0 ? ' — at start' : ` — at ${atSeconds}s`
                      )}
                    </strong>
                    {p.impact && <div className={`eval-explanation ${isAr ? 'arabic' : ''}`}>{p.impact}</div>}
                  </div>
                );
              })}
            </div>
          )}

          {/* Repetition analysis */}
          {report.repetition_analysis?.comment && (
            <div className="card">
              <h3 className="report-section-title">🔁 {labels.repetitionAnalysisTitle}</h3>
              <p className={isAr ? 'arabic' : ''} style={{ fontSize: '0.85rem', color: 'var(--ink)' }}>{report.repetition_analysis.comment}</p>
            </div>
          )}

          {/* Number & date accuracy */}
          {(report.number_accuracy || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">🔢 {labels.numberAccuracyTitle}</h3>
              {report.number_accuracy.map((n, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: `3px solid ${n.correct ? 'var(--sage)' : 'var(--sienna)'}`, paddingLeft: '0.75rem', marginBottom: '0.6rem' }}>
                  <div style={{ fontSize: '0.84rem' }}>
                    <strong>{n.source_value}</strong>
                    <span style={{ color: 'var(--warm-gray)' }}> — {labels.expectedLabel}: </span>
                    <strong style={{ color: 'var(--sage)' }} className={isAr ? 'arabic' : ''}>{n.expected_in_target}</strong>
                    <span style={{ color: 'var(--warm-gray)' }}> · {labels.studentSaidShort}: </span>
                    <strong style={{ color: n.correct ? 'var(--sage)' : 'var(--sienna)' }} className={isAr ? 'arabic' : ''}>{n.student_said || '—'}</strong>
                    <span className={`importance-badge importance-${n.correct ? 'low' : 'high'}`} style={{ marginLeft: '0.5rem' }}>
                      {n.correct ? labels.numCorrect : labels.numIncorrect}
                    </span>
                  </div>
                  {n.note && <div className={`eval-explanation ${isAr ? 'arabic' : ''}`}>{n.note}</div>}
                </div>
              ))}
            </div>
          )}

          {/* Pronunciation assessment (LLM commentary, all languages) */}
          {false && report.pronunciation_assessment?.comment && (
            <div className="card">
              <h3 className="report-section-title">🗣️ {labels.pronunciationAssessmentTitle}</h3>
              <p className={isAr ? 'arabic' : ''} style={{ fontSize: '0.85rem', color: 'var(--ink)', marginBottom: '0.6rem' }}>{report.pronunciation_assessment.comment}</p>
              {(report.pronunciation_assessment.issues || []).map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--gold)', paddingLeft: '0.75rem', marginBottom: '0.5rem' }}>
                  <strong className={isAr ? 'arabic' : ''}>"{item.word}"</strong>
                  {item.issue && <div className={`eval-explanation ${isAr ? 'arabic' : ''}`}>{item.issue}</div>}
                  {item.correction && <div className="eval-correction">✓ {labels.correction}: <strong className={isAr ? 'arabic' : ''}>{item.correction}</strong></div>}
                </div>
              ))}
            </div>
          )}

          {/* Audio-based fluency */}
          {fluency && (
            <div className="card">
              <h3 className="report-section-title">{labels.audioFluencyTitle}</h3>
              <div className="report-score-row">
                <div>
                  <p className="report-label">{labels.fluencyScore}</p>
                  <ScoreBar score={fluency.fluency_score || 0} labels={labels} />
                </div>
                <div className="report-summary">
                  <p>{fluency.summary}</p>
                  <p style={{ fontSize: '0.82rem', color: 'var(--warm-gray)', marginTop: '0.45rem' }}>
                    {labels.fluencyExplain}
                  </p>
                  {fluency.preparation_seconds > 0 && (
                    <p style={{ fontSize: '0.82rem', color: 'var(--sage)', marginTop: '0.35rem' }}>
                      ⏱ {fluency.preparation_seconds}s {labels.prepTimeLabel}
                    </p>
                  )}
                </div>
              </div>
              <div className="algo-grid" style={{ marginTop: '1rem' }}>
                {[
                  { label: labels.statSpeechRate, value: `${fluency.speech_rate_wpm || 0} wpm` },
                  { label: labels.statLongPauses, value: fluency.long_pause_count || 0 },
                  { label: labels.statSilenceRatio, value: `${Math.round((fluency.silence_ratio || 0) * 100)}%` },
                  { label: labels.statWordConfidence, value: `${Math.round((fluency.average_word_confidence || 0) * 100)}%` },
                ].map(({ label, value }) => (
                  <div key={label} className="algo-card">
                    <span className="algo-count">{value}</span>
                    <span className="algo-label">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Coverage score */}
          {report.coverage_score !== undefined && (
            <div className="card">
              <h3 className="report-section-title">📊 {labels.coverageTitle}</h3>
              <ScoreBar score={report.coverage_score} labels={labels} />
              <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--warm-gray)' }}>
                {labels.coverageHint}
              </p>
            </div>
          )}

          {/* Translation errors */}
          {(report.translation_errors || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">🔄 {labels.translationErrors}</h3>
              {(report.translation_errors || []).map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--sienna)', paddingLeft: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--warm-gray)', marginBottom: '0.2rem' }}>{labels.sourceSaid}:</div>
                  <div className="eval-text" style={{ marginBottom: '0.25rem' }}>"{item.source_text}"</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--warm-gray)', marginBottom: '0.2rem' }}>{labels.studentSaid}: <strong style={{ color: 'var(--sienna)' }}>{item.student_said}</strong></div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--warm-gray)', marginBottom: '0.2rem' }}>{labels.correctTranslation}: <strong style={{ color: 'var(--sage)' }}>{item.correct_translation}</strong></div>
                  {item.explanation && <div className="eval-explanation">{item.explanation}</div>}
                </div>
              ))}
            </div>
          )}

          {/* Proper nouns — names of people, organizations, places */}
          {(report.proper_nouns || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">🏛️ {labels.pnTitle}</h3>
              {report.proper_nouns.map((pn, i) => {
                const status = String(pn.status || '').toLowerCase();
                const color = status === 'correct' ? 'var(--sage)' : status === 'missing' ? 'var(--warm-gray)' : 'var(--sienna)';
                const statusLabel = status === 'correct' ? labels.pnCorrect : status === 'missing' ? labels.pnMissing : labels.pnDistorted;
                return (
                  <div key={i} className="eval-item" style={{ borderLeft: `3px solid ${color}`, paddingLeft: '0.75rem', marginBottom: '0.6rem' }}>
                    <div style={{ fontSize: '0.84rem' }}>
                      <strong>{pn.source_name}</strong>
                      {pn.student_said && status !== 'missing' && (
                        <>
                          <span style={{ color: 'var(--warm-gray)' }}> · {labels.studentSaidShort}: </span>
                          <strong style={{ color }} className={isAr ? 'arabic' : ''}>{pn.student_said}</strong>
                        </>
                      )}
                      <span className={`importance-badge importance-${status === 'correct' ? 'low' : 'high'}`} style={{ marginLeft: '0.5rem' }}>
                        {statusLabel}
                      </span>
                    </div>
                    {pn.note && <div className={`eval-explanation ${isAr ? 'arabic' : ''}`}>{pn.note}</div>}
                  </div>
                );
              })}
            </div>
          )}

          {/* Missing content */}
          {(report.missing_content || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">📉 {labels.missingContent}</h3>
              {(report.missing_content || []).map((item, i) => (
                <div key={i} className="eval-item" style={{ marginBottom: '0.5rem' }}>
                  <span className="eval-text">{item.content}</span>
                  {item.importance && <span className={`importance-badge importance-${item.importance}`}>{item.importance}</span>}
                </div>
              ))}
            </div>
          )}

          {/* Language errors (grammar / syntax) */}
          {(report.language_errors || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">⚠️ {labels.languageErrors}</h3>
              {report.language_errors.map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--gold)', paddingLeft: '0.75rem', marginBottom: '0.6rem' }}>
                  <div className={`eval-text ${isAr ? 'arabic' : ''}`}>"{item.text}"</div>
                  {item.explanation && <div className={`eval-explanation ${isAr ? 'arabic' : ''}`}>{item.explanation}</div>}
                  {item.correction && <div className="eval-correction">✓ {labels.correction}: <strong className={isAr ? 'arabic' : ''}>{item.correction}</strong></div>}
                </div>
              ))}
            </div>
          )}

          {/* Auto-corrections (self-corrections the student made mid-speech) */}
          {(report.auto_corrections || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">✏️ {labels.autoCorrections}</h3>
              {report.auto_corrections.map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--sage)', paddingLeft: '0.75rem', marginBottom: '0.5rem' }}>
                  <div className={`eval-text ${isAr ? 'arabic' : ''}`}>"{item.text}"</div>
                </div>
              ))}
            </div>
          )}

          {/* False starts (incomplete phrases abandoned mid-sentence) */}
          {(report.false_starts || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">↩️ {labels.falseStarts}</h3>
              {report.false_starts.map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--sienna)', paddingLeft: '0.75rem', marginBottom: '0.5rem' }}>
                  <div className={`eval-text ${isAr ? 'arabic' : ''}`}>"{item.text}"</div>
                </div>
              ))}
            </div>
          )}

          {/* Lapsus linguae (slips of the tongue) */}
          {(report.lapsus_linguae || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">👅 {labels.lapsusLinguae}</h3>
              {report.lapsus_linguae.map((item, i) => (
                <div key={i} className="eval-item" style={{ borderLeft: '3px solid var(--gold)', paddingLeft: '0.75rem', marginBottom: '0.5rem' }}>
                  <div className={`eval-text ${isAr ? 'arabic' : ''}`}>"{item.text}"</div>
                  {item.likely_intended && <div className="eval-correction">→ {labels.correction}: <strong className={isAr ? 'arabic' : ''}>{item.likely_intended}</strong></div>}
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {(report.recommendations || []).length > 0 && (
            <div className="card">
              <h3 className="report-section-title">💡 {labels.recommendations}</h3>
              <ul className="recommendations-list">
                {report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {/* Transparency: evaluation criteria, reliability, data storage */}
          <div className="card">
            <details>
              <summary style={{ cursor: 'pointer', fontWeight: 700, fontSize: '0.92rem' }}>
                {labels.aboutEvalTitle}
              </summary>
              <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', lineHeight: 1.65, color: 'var(--ink, #333)', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                <p>{labels.aboutEvalCriteria}</p>
                <p>{labels.aboutEvalReliability}</p>
                <p>{labels.aboutEvalStorage}</p>
              </div>
            </details>
          </div>
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
