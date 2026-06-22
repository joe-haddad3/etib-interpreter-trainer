/**
 * ETIB API Client
 * ================
 * Centralised fetch helpers for all backend endpoints.
 * Import functions from here — don't write raw fetch() calls in main.js.
 *
 * Person 3 maintains this file.
 */

const BASE = 'http://127.0.0.1:5000/api';

// ── Groq API key (stored in localStorage, sent as header with every request) ─

const GROQ_KEY_STORAGE = 'etib_groq_api_key';

export function getStoredGroqKey() {
  return localStorage.getItem(GROQ_KEY_STORAGE) || '';
}

export function saveGroqKey(key) {
  if (key) localStorage.setItem(GROQ_KEY_STORAGE, key.trim());
  else localStorage.removeItem(GROQ_KEY_STORAGE);
}

function groqHeaders(extra = {}) {
  const key = getStoredGroqKey();
  return key ? { 'X-Groq-Api-Key': key, ...extra } : { ...extra };
}

// ── Generic helpers ──────────────────────────────────────────────────────────

async function parseJsonResponse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

export async function loginUser(credentials) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(credentials)
  });
  return parseJsonResponse(res);
}

export async function signupUser(account) {
  const res = await fetch(`${BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(account)
  });
  return parseJsonResponse(res);
}

export async function getCurrentUser() {
  const res = await fetch(`${BASE}/auth/me`, {
    credentials: 'include'
  });
  return parseJsonResponse(res);
}

export async function logoutUser() {
  const res = await fetch(`${BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include'
  });
  return parseJsonResponse(res);
}

export async function validateGroqKey(apiKey) {
  const res = await fetch(`${BASE}/auth/validate-groq-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ api_key: apiKey }),
  });
  return parseJsonResponse(res);
}

export async function generateSpeech(params) {
  const res = await fetch(`${BASE}/module-a/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...groqHeaders() },
    credentials: 'include',
    body: JSON.stringify(params)
  });
  return parseJsonResponse(res);
}

export async function generateSpeechFromDocument(file, params) {
  const form = new FormData();
  form.append('document', file);
  Object.entries(params).forEach(([key, value]) => {
    form.append(key, String(value));
  });

  const res = await fetch(`${BASE}/module-a/from-document`, {
    method: 'POST',
    headers: groqHeaders(),
    credentials: 'include',
    body: form
  });
  return parseJsonResponse(res);
}

export async function retrieveDocumentContext(file, params) {
  const form = new FormData();
  form.append('document', file);
  Object.entries(params).forEach(([key, value]) => {
    form.append(key, String(value));
  });

  const res = await fetch(`${BASE}/module-a/retrieve-document-context`, {
    method: 'POST',
    headers: groqHeaders(),
    credentials: 'include',
    body: form
  });
  return parseJsonResponse(res);
}

export async function textToSpeech(params) {
  const res = await fetch(`${BASE}/module-b/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  return parseJsonResponse(res);
}

export async function transcribeAudio(audioFile, language = 'ar', sourceText = '') {
  const form = new FormData();
  const filename = audioFile.name || 'recording.webm';
  form.append('audio', audioFile, filename);
  form.append('language', language);
  if (sourceText) form.append('source_text', sourceText);
  const res = await fetch(`${BASE}/module-c/transcribe`, {
    method: 'POST',
    headers: groqHeaders(),
    credentials: 'include',
    body: form
  });
  return parseJsonResponse(res);
}

export async function generateMaterials(params) {
  const res = await fetch(`${BASE}/module-b/materials`, {
    method: 'POST',
    headers: groqHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  return parseJsonResponse(res);
}

export async function downloadGlossary(params) {
  const res = await fetch(`${BASE}/module-b/glossary/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return res.blob();
}

export async function evaluatePerformance(sourceScript, transcript, language) {
  const res = await fetch(`${BASE}/module-d/evaluate`, {
    method: 'POST',
    headers: groqHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ source_script: sourceScript, transcript, language })
  });
  return parseJsonResponse(res);
}

export async function tashkeelCompare(sourceText, transcript, language) {
  const res = await fetch(`${BASE}/module-d/tashkeel-compare`, {
    method: 'POST',
    headers: groqHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ source_text: sourceText, transcript, language })
  });
  return parseJsonResponse(res);
}

export async function alignPronunciation(audioFile, segments, sourceText, language) {
  const form = new FormData();
  form.append('audio', audioFile, audioFile.name || 'recording.webm');
  form.append('segments', JSON.stringify(segments || []));
  form.append('source_text', sourceText || '');
  form.append('language', language || 'ar');
  const res = await fetch(`${BASE}/module-c/align`, { method: 'POST', headers: groqHeaders(), credentials: 'include', body: form });
  return parseJsonResponse(res);
}

export async function getPronunciationReport(alignment, sourceText, language) {
  const res = await fetch(`${BASE}/module-d/pronunciation`, {
    method: 'POST',
    headers: groqHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ alignment, source_text: sourceText, language })
  });
  return parseJsonResponse(res);
}

export async function generateFeedback(params) {
  const res = await fetch(`${BASE}/module-d/feedback`, {
    method: 'POST',
    headers: groqHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  return parseJsonResponse(res);
}

// ── UN Library ───────────────────────────────────────────────────────────────

export async function searchUNLibrary({ q, language, domain, limit = 10 }) {
  const params = new URLSearchParams({ language, limit });
  if (q) params.append('q', q);
  if (domain) params.append('domain', domain);
  const res = await fetch(`${BASE}/library/search?${params}`);
  return parseJsonResponse(res);
}

export async function fetchUNDocument({ pdf_url, web_url, un_id, title, language }) {
  const res = await fetch(`${BASE}/library/fetch`, {
    method: 'POST',
    headers: groqHeaders({ 'Content-Type': 'application/json' }),
    credentials: 'include',
    body: JSON.stringify({ pdf_url, web_url, un_id, title, language }),
  });
  return parseJsonResponse(res);
}

export async function getSavedSpeeches({ language, domain } = {}) {
  const params = new URLSearchParams();
  if (language) params.append('language', language);
  if (domain)   params.append('domain', domain);
  const res = await fetch(`${BASE}/library/saved?${params}`);
  return parseJsonResponse(res);
}

export async function getSavedSpeech(un_id) {
  const res = await fetch(`${BASE}/library/saved/${un_id}`);
  return parseJsonResponse(res);
}

export async function deleteSavedSpeech(un_id) {
  const res = await fetch(`${BASE}/library/saved/${encodeURIComponent(un_id)}`, {
    method: 'DELETE',
  });
  return parseJsonResponse(res);
}

export async function evaluateWithAudio(audioFile, sourceScript, language, sourceLanguage, domain) {
  const form = new FormData();
  form.append('audio', audioFile, audioFile.name || 'recording.webm');
  form.append('source_script', sourceScript || '');
  form.append('language', language || 'ar');
  form.append('source_language', sourceLanguage || language || 'ar');
  if (domain) form.append('domain', domain);
  const res = await fetch(`${BASE}/module-d/full-evaluation`, {
    method: 'POST',
    headers: groqHeaders(),
    credentials: 'include',
    body: form
  });
  return parseJsonResponse(res);
}

export async function getSessionHistory(limit = 20) {
  const res = await fetch(`${BASE}/module-d/sessions?limit=${limit}`, {
    headers: groqHeaders(),
    credentials: 'include',
  });
  return parseJsonResponse(res);
}

export async function getAdaptiveParams() {
  const res = await fetch(`${BASE}/module-d/adaptive-params`, {
    headers: groqHeaders(),
    credentials: 'include',
  });
  return parseJsonResponse(res);
}
