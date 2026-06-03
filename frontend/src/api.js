/**
 * ETIB API Client
 * ================
 * Centralised fetch helpers for all backend endpoints.
 * Import functions from here — don't write raw fetch() calls in main.js.
 *
 * Person 3 maintains this file.
 */

const BASE = 'http://localhost:5000/api';

export async function generateSpeech(params) {
  const res = await fetch(`${BASE}/module-a/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function textToSpeech(params) {
  const res = await fetch(`${BASE}/module-b/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function transcribeAudio(audioBlob, language = 'ar') {
  const form = new FormData();
  form.append('audio', audioBlob, 'recording.mp3');
  form.append('language', language);
  const res = await fetch(`${BASE}/module-c/transcribe`, {
    method: 'POST',
    body: form
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function evaluatePerformance(sourceScript, transcript, language) {
  const res = await fetch(`${BASE}/module-d/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_script: sourceScript, transcript, language })
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
