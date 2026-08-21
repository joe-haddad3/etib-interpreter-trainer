"""
Terminology grounding against real institutional bases
=====================================================

ETIB feedback (Lina, 21 Aug 2026): the generated glossary should not be the
model's own invention — it should come from the established terminology bases.

Which bases can actually be queried from a server (checked live, 21 Aug 2026):

  UNBIS Thesaurus  metadata.un.org/skosmos  — YES. Public Skosmos REST API, no
                   key. Official UN terminology in the six UN languages, so it
                   is the ONLY machine-readable source that gives us ARABIC —
                   which is the whole point for ETIB. This is the first choice
                   for institutional/UN terms.
  IATE             iate.europa.eu/em-api    — YES. Public search API (POST with
                   a JSON body). EU institutional/legal/economic terminology,
                   24 EU languages: excellent FR/EN, no Arabic.
  FranceTerme      data.gouv.fr open data   — YES, as a bulk XML export (~9 MB,
                   Licence Ouverte). Officially recommended FRENCH terms with
                   definitions and English equivalents. Downloaded lazily, once,
                   and cached; it is never fetched unless a lookup needs it.

  UNTERM           — NO. Single-page app behind reCAPTCHA v3; every path returns
                   the SPA shell. Not machine-queryable.
  ETIB-CERTTAL     — NO. Sits behind an F5/BIG-IP bot challenge (TSPD cookie).
  OQLF Vitrine     — NO. Bot-protected; returns an empty body to non-browsers.

Everything here fails OPEN: any timeout, error or unexpected payload simply
leaves the model's own equivalent in place. Terminology grounding must never be
able to break speech generation.
"""
from __future__ import annotations

import os
import re
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import (
    TERMINOLOGY_GROUNDING_ENABLED,
    TERMINOLOGY_TIMEOUT,
    TERMINOLOGY_MAX_TERMS,
    FRANCETERME_ENABLED,
)

_UA = 'ETIB-Interpreter-Trainer/1.0 (USJ Beirut; terminology grounding)'

UNBIS_SEARCH = 'https://metadata.un.org/skosmos/rest/v1/thesaurus/search'
UNBIS_DATA = 'https://metadata.un.org/skosmos/rest/v1/thesaurus/data'
IATE_SEARCH = 'https://iate.europa.eu/em-api/entries/_search'
FRANCETERME_XML = 'http://www.franceterme.culture.gouv.fr/public/FranceTerme.xml'

# ── caches ───────────────────────────────────────────────────────────────────
_cache: dict[str, dict | None] = {}
_cache_lock = threading.Lock()
_ft_index: dict[str, dict] | None = None
_ft_lock = threading.Lock()


def _norm(text: str) -> str:
    return re.sub(r'\s+', ' ', str(text or '')).strip().lower()


def _fix_case(label: str) -> str:
    """UNBIS stores its Latin-script labels in CAPITALS ("REFUGEE ASSISTANCE").
    Interpreters want the normal form, so lower-case a shouting label but leave
    a properly-cased one (and any acronym) alone."""
    label = str(label or '').strip()
    letters = [c for c in label if c.isalpha()]
    if len(letters) > 3 and all(c.isupper() for c in letters):
        return label.lower()
    return label


# ── UNBIS Thesaurus (AR / FR / EN) ───────────────────────────────────────────

def _unbis_lookup(term: str, lang: str = 'en') -> dict | None:
    try:
        resp = requests.get(
            UNBIS_SEARCH,
            params={'query': f'{term}*', 'lang': lang, 'maxhits': 1, 'unique': 'true'},
            headers={'Accept': 'application/json', 'User-Agent': _UA},
            timeout=TERMINOLOGY_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        results = (resp.json() or {}).get('results') or []
        if not results:
            return None
        uri = results[0].get('uri')
        if not uri:
            return None

        resp = requests.get(
            UNBIS_DATA,
            params={'uri': uri, 'format': 'application/json'},
            headers={'Accept': 'application/json', 'User-Agent': _UA},
            timeout=TERMINOLOGY_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        graph = (resp.json() or {}).get('graph') or []
        node = next((g for g in graph if g.get('uri') == uri), None)
        if not node:
            return None

        labels = node.get('prefLabel')
        labels = labels if isinstance(labels, list) else [labels]
        out: dict = {'source': 'UNBIS', 'source_uri': uri}
        for item in labels:
            if not isinstance(item, dict):
                continue
            code, value = item.get('lang'), item.get('value')
            if not value:
                continue
            if code == 'ar':
                out['arabic'] = value.strip()
            elif code == 'fr':
                out['french'] = _fix_case(value)
            elif code == 'en':
                out['english'] = _fix_case(value)

        # Scope note = a usable short definition, when the concept has one.
        note = node.get('scopeNote')
        note = note if isinstance(note, list) else ([note] if note else [])
        for item in note:
            if isinstance(item, dict) and item.get('lang') == 'en' and item.get('value'):
                out['definition'] = str(item['value']).strip()
                break

        return out if any(k in out for k in ('arabic', 'french', 'english')) else None
    except Exception:
        return None


# ── IATE (FR / EN) ───────────────────────────────────────────────────────────

def _iate_lookup(term: str, source: str = 'en', targets: tuple = ('fr', 'en')) -> dict | None:
    try:
        resp = requests.post(
            IATE_SEARCH,
            params={'expand': 'true', 'offset': 0, 'limit': 1},
            json={
                'query': term,
                'source': source,
                'targets': list(targets),
                'search_in_fields': [0],
                'search_in_term_types': [0, 1, 2, 3, 4],
                'query_operator': 3,          # exact match — never a fuzzy guess
            },
            headers={'Accept': 'application/json', 'User-Agent': _UA},
            timeout=TERMINOLOGY_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        items = (resp.json() or {}).get('items') or []
        if not items:
            return None
        languages = items[0].get('language') or {}
        out: dict = {'source': 'IATE'}
        for code, key in (('fr', 'french'), ('en', 'english')):
            entry = languages.get(code) or {}
            terms = entry.get('term_entries') or []
            for t in terms:
                value = t.get('term_value')
                if value:
                    out[key] = str(value).strip()
                    break
        return out if len(out) > 1 else None
    except Exception:
        return None


# ── FranceTerme (official FR + EN equivalent + definition) ───────────────────

def _franceterme_index() -> dict[str, dict]:
    """Build (once) an in-memory index of the FranceTerme open-data export.

    ~8 400 articles. Downloaded lazily on the first lookup that needs it, so a
    deployment that never grounds terminology never pays for it.
    """
    global _ft_index
    if _ft_index is not None:
        return _ft_index
    index: dict[str, dict] = {}
    if True:
        try:
            resp = requests.get(FRANCETERME_XML, headers={'User-Agent': _UA}, timeout=60)
            resp.raise_for_status()
            xml = resp.content.decode('utf-8', errors='replace')
            for article in re.finditer(r'<Article\b.*?</Article>', xml, re.S):
                block = article.group()
                fr = re.search(r'<Terme\b[^>]*statut="privilegie"[^>]*Terme="([^"]+)"', block)
                if not fr:
                    continue
                french = fr.group(1).strip()
                en = re.search(r'<Equivalent\b[^>]*>(?:\s*<Equi_prop>)?\s*([^<]{2,80})', block)
                english = en.group(1).strip() if en else ''
                dfn = re.search(r'<Definition>\s*(.*?)</Definition>', block, re.S)
                definition = re.sub(r'\s+', ' ', dfn.group(1)).strip() if dfn else ''
                row = {'french': french, 'source': 'FranceTerme'}
                if english:
                    row['english'] = english
                if definition:
                    row['definition'] = definition
                index.setdefault(_norm(french), row)
                if english:
                    index.setdefault(_norm(english), row)
        except Exception:
            index = {}          # unreachable dataset → the source is simply skipped
        _ft_index = index
        return _ft_index


_ft_thread: threading.Thread | None = None


def _franceterme_lookup(term: str) -> dict | None:
    """Never blocks. The first call starts the download in the background and
    returns None; from the moment the index is ready, lookups are instant.

    Blocking here would mean a student's first speech of the day waits ~2 min
    for a 9 MB dataset on a cold Space — the other two bases already answer in
    about a second, so FranceTerme simply joins in once it is loaded."""
    global _ft_thread
    if not FRANCETERME_ENABLED:
        return None
    if _ft_index is not None:
        return _ft_index.get(_norm(term))
    with _ft_lock:
        if _ft_thread is None:
            _ft_thread = threading.Thread(target=_franceterme_index, daemon=True)
            _ft_thread.start()
    return None


# ── one term, all bases ──────────────────────────────────────────────────────

def lookup_term(term: str, lang: str = 'en') -> dict | None:
    """Attested equivalents for one term, or None if no base knows it.

    Order of authority: UNBIS (UN, and the only Arabic source) → IATE (EU) →
    FranceTerme (official French). Later sources only FILL GAPS; they never
    overwrite an equivalent an earlier, more authoritative base supplied.
    """
    term = str(term or '').strip()
    if not term or len(term) > 120:
        return None

    key = f'{lang}:{_norm(term)}'
    with _cache_lock:
        if key in _cache:
            return _cache[key]

    hits: dict[str, dict] = {}
    for name, finder in (
        ('UNBIS', lambda: _unbis_lookup(term, lang if lang in ('en', 'fr', 'ar') else 'en')),
        ('IATE', lambda: _iate_lookup(term, 'en' if lang == 'ar' else lang)),
        ('FranceTerme', lambda: _franceterme_lookup(term)),
    ):
        try:
            found = finder()
        except Exception:
            found = None
        if found:
            hits[name] = found

    # Per-field authority. Arabic exists in UNBIS only. For French, FranceTerme
    # (officially recommended term) then IATE come first, because UNBIS stores
    # its Latin-script labels unaccented and in capitals ("ASSISTANCE AUX
    # REFUGIES") — correct as a concept label, wrong as an interpreter's term.
    PRIORITY = {
        'arabic':     ('UNBIS',),
        'french':     ('FranceTerme', 'IATE', 'UNBIS'),
        'english':    ('IATE', 'UNBIS', 'FranceTerme'),
        'definition': ('FranceTerme', 'UNBIS'),
    }
    merged: dict = {}
    used: list[str] = []
    for field, order in PRIORITY.items():
        for name in order:
            value = (hits.get(name) or {}).get(field)
            if value:
                merged[field] = value
                if name not in used:
                    used.append(name)
                break

    result = None
    if any(merged.get(f) for f in ('arabic', 'french', 'english')):
        merged['sources'] = used
        result = merged

    with _cache_lock:
        _cache[key] = result
    return result


# ── a whole glossary ─────────────────────────────────────────────────────────

def ground_glossary(glossary: list[dict], language: str = 'en') -> list[dict]:
    """Correct a generated glossary against the real bases.

    An attested equivalent REPLACES the model's own; a term no base knows is
    left exactly as generated and simply carries no `verified` flag. The whole
    pass is best-effort: it is wrapped so that no network problem can ever stop
    a speech from being generated.
    """
    if not TERMINOLOGY_GROUNDING_ENABLED or not glossary:
        return glossary

    rows = [r for r in glossary if isinstance(r, dict)][:TERMINOLOGY_MAX_TERMS]
    if not rows:
        return glossary

    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(lookup_term, row.get('term', ''), language): row
                for row in rows if str(row.get('term', '')).strip()
            }
            for future in as_completed(futures, timeout=TERMINOLOGY_TIMEOUT * 4):
                row = futures[future]
                try:
                    found = future.result()
                except Exception:
                    continue
                if not found:
                    continue
                for field in ('arabic', 'french', 'english'):
                    value = found.get(field)
                    if value:
                        row[field] = value
                        # Drop the aliases the display falls back through, or a
                        # stale model value could resurface over the attested one.
                        for alias in _ALIASES[field]:
                            row.pop(alias, None)
                if found.get('definition') and not str(row.get('definition', '')).strip():
                    row['definition'] = found['definition']
                row['verified'] = True
                row['verified_sources'] = found.get('sources', [])
    except Exception:
        pass                    # partial grounding is fine; no grounding is fine too

    return glossary


_ALIASES = {
    'arabic':  ['Arabic', 'ar', 'AR', 'arabic_term', 'term_ar', 'arabic_translation',
                'translation_ar', 'العربية', 'عربي'],
    'french':  ['French', 'fr', 'FR', 'french_term', 'term_fr', 'french_translation',
                'translation_fr', 'français', 'francais'],
    'english': ['English', 'en', 'EN', 'english_term', 'term_en', 'english_translation',
                'translation_en'],
}
