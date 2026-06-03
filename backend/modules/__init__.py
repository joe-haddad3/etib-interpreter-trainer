"""
ETIB Platform — Modules Package
=================================
Four modules forming the interpreter training pipeline:

  Module A → Module B → Module C → Module D
  (LLM)      (TTS)       (ASR)      (Eval)

Each module exposes a Flask Blueprint registered in app.py.
"""
