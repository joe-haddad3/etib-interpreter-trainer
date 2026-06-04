/**
 * ETIB API Client
 * ================
 * Centralised fetch helpers for all backend endpoints.
 * Import functions from here — don't write raw fetch() calls in main.js.
 *
 * Person 3 maintains this file.
 */

const BASE = 'http://127.0.0.1:5000/api';

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

export async function generateSpeech(params) {
  const res = await fetch(`${BASE}/module-a/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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

export async function transcribeAudio(audioBlob, language = 'ar') {
  const form = new FormData();
  form.append('audio', audioBlob, 'recording.mp3');
  form.append('language', language);
  const res = await fetch(`${BASE}/module-c/transcribe`, {
    method: 'POST',
    body: form
  });
  return parseJsonResponse(res);
}

export async function evaluatePerformance(sourceScript, transcript, language) {
  const res = await fetch(`${BASE}/module-d/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_script: sourceScript, transcript, language })
  });
  return parseJsonResponse(res);
}
