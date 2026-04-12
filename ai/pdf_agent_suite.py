"""
╔══════════════════════════════════════════════════════════════════╗
║         📚 PDF Agent Suite — v7.2 (CS Books Edition)            ║
║   مُحسَّن لكتب CS من 100 إلى 150 صفحة                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, time, json, re, requests, warnings, argparse, unicodedata
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════
#  CONFIGURATION
# ════════════════════════════════════════════════════════════

MARKER_API_URL = "https://climatological-yamileth-parliamentarily.ngrok-free.dev"
LLM_API_URL    = "https://unsuppressive-rosily-shon.ngrok-free.dev/v1/chat/completions"
LOCAL_API_KEY  = "any-key"
MODEL_NAME     = "google/medgemma-4b-it"

# ── Tuned for 100-150 page textbooks ──────────────────────
CHUNK_SIZE            = 8      # ~8 pages per chunk ≈ 1 chapter section
MAX_TOKENS            = 1400   # enough for a solid chapter summary
SLEEP_BETWEEN         = 0.4
TRANSLATE_CHUNK_CHARS = 2500
MAX_RETRIES           = 4
OUTPUT_DIR            = "./pdf_output"
MAX_CHUNK_CHARS       = 6000   # fits a full chapter section

SYSTEM_PROMPT = (
    "You are a JSON generator for CS textbook analysis. "
    "Output ONLY a valid JSON object. "
    "No explanation, no markdown, no preamble. Just the JSON."
)


# ════════════════════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════════════════════

def log(msg, level="info"):
    icons = {"info": "▸", "ok": "✓", "warn": "⚠", "err": "✗"}
    print(f"  {icons.get(level,'▸')} {msg}")


def call_model(messages, max_tokens=MAX_TOKENS, temp=0.0,
               retries=MAX_RETRIES, use_system=True):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LOCAL_API_KEY}"
    }
    if use_system and (not messages or messages[0].get("role") != "system"):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    payload = {
        "model":       MODEL_NAME,
        "messages":    messages,
        "temperature": temp,
        "max_tokens":  max_tokens,
    }

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(
                LLM_API_URL, headers=headers,
                json=payload, timeout=300, verify=False
            )
            if r.status_code == 429:
                wait = 20 * attempt
                log(f"rate limit → waiting {wait}s", "warn")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                log(f"HTTP {r.status_code} attempt {attempt}/{retries}", "warn")
                time.sleep(5 * attempt)
                continue
            content = r.json()["choices"][0]["message"]["content"]
            return content.strip() if content else None
        except requests.Timeout:
            log(f"timeout attempt {attempt}/{retries}", "warn")
            time.sleep(8 * attempt)
        except Exception as e:
            log(f"error: {e}", "err")
            if attempt == retries:
                return None
            time.sleep(4)
    return None


# ════════════════════════════════════════════════════════════
#  JSON REPAIR — robust 8-pass extractor
# ════════════════════════════════════════════════════════════

def safe_json(raw):
    if not raw:
        return None

    # Pass 0: strip model preamble ("Sure! Here is..." etc.)
    text = re.sub(
        r'^.*?(?:here is|here\'s|output|result|json)[^\{]*',
        '', raw.strip(), flags=re.IGNORECASE | re.DOTALL
    )
    if not text.strip().startswith('{'):
        text = raw.strip()

    # Pass 1: strip markdown fences
    text = re.sub(r"^```(?:json|python|text)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE).strip()

    # Pass 2: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Pass 3: extract { ... }
    s, e = text.find('{'), text.rfind('}')
    if s != -1 and e > s:
        try:
            return json.loads(text[s:e+1])
        except json.JSONDecodeError:
            pass

    # Pass 4: fix bad backslashes
    fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
    s, e = fixed.find('{'), fixed.rfind('}')
    if s != -1 and e > s:
        try:
            return json.loads(fixed[s:e+1])
        except json.JSONDecodeError:
            pass

    # Pass 5: remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    s, e = cleaned.find('{'), cleaned.rfind('}')
    if s != -1 and e > s:
        try:
            return json.loads(cleaned[s:e+1])
        except json.JSONDecodeError:
            pass

    # Pass 6: repair truncated JSON (token limit cut mid-output)
    s = text.find('{')
    if s != -1:
        try:
            repaired = _repair_truncated(text[s:])
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    # Pass 7: line-by-line quote repair
    try:
        lines = text.split('\n')
        repaired = [re.sub(r'(?<=[^\\])"(?=[^:,\{\}\[\]\n])', r'\\"', l) for l in lines]
        attempt7 = '\n'.join(repaired)
        s, e = attempt7.find('{'), attempt7.rfind('}')
        if s != -1 and e > s:
            return json.loads(attempt7[s:e+1])
    except Exception:
        pass

    # Pass 8: regex field extraction (last resort)
    return _regex_extract(text)


def _repair_truncated(s: str) -> str:
    """Close open strings/arrays/objects left by token-limit truncation."""
    depth_brace = depth_bracket = 0
    in_string = escape_next = False
    last_good = 0

    for i, ch in enumerate(s):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
        elif not in_string:
            if   ch == '{': depth_brace   += 1
            elif ch == '}':
                depth_brace -= 1
                if depth_brace == 0:
                    last_good = i + 1
            elif ch == '[': depth_bracket += 1
            elif ch == ']': depth_bracket -= 1

    result = s[:last_good] if last_good > 0 else s
    if in_string:
        result = result.rstrip(',\n ') + '"'
    result = result.rstrip(',\n ')
    result += ']' * max(0, depth_bracket)
    result += '}' * max(0, depth_brace)
    return result


def _regex_extract(text: str):
    """Extract key fields with regex when JSON is completely broken."""
    result = {}
    m = re.search(r'"topic"\s*:\s*"([^"]+)"', text)
    if m: result["topic"] = m.group(1)
    m = re.search(r'"summary"\s*:\s*"([^"]{20,})"', text)
    if m: result["summary"] = m.group(1)
    m = re.search(r'"takeaways"\s*:\s*\[([^\]]+)\]', text, re.DOTALL)
    if m:
        items = re.findall(r'"([^"]+)"', m.group(1))
        if items: result["takeaways"] = items
    if result.get("topic") or result.get("summary"):
        for k in ["key_concepts","formulas","algorithms","code_insights","examples","connections"]:
            result.setdefault(k, [])
        result.setdefault("takeaways", [])
        result["_regex_extracted"] = True
        return result
    return None


# ════════════════════════════════════════════════════════════
#  CONTENT TYPE DETECTION
# ════════════════════════════════════════════════════════════

class ContentAnalyzer:
    CODE_PATTERNS = [
        r'def\s+\w+\s*\(', r'int\s+\w+\s*\(', r'public\s+(static\s+)?\w+',
        r'#include\s*[<"]', r'for\s*\(\s*\w+', r'while\s*\(', r'if\s*\(',
        r'return\s+', r'class\s+\w+', r'import\s+\w+', r'function\s+\w+',
        r'algorithm\s+\w+', r'procedure\s+\w+', r'BEGIN\s*$|END\s*$', r'→|←|:=',
    ]
    MATH_PATTERNS = [
        r'\$[^$]+\$', r'\$\$[\s\S]+?\$\$', r'\\[a-zA-Z]+\{',
        r'[∑∏∫∂∇∈∉⊂⊃∪∩∧∨¬∀∃≤≥≠≈]',
        r'\b(?:theorem|lemma|proof|corollary|definition)\b',
        r'\b(?:O\(|Θ\(|Ω\()', r'[a-z]\s*[=<>≤≥]\s*[a-z0-9]',
        r'\d+\s*[×÷±]\s*\d+',
    ]
    TABLE_PATTERNS = [r'^\|.+\|', r'\t.+\t', r'^\s*[-|+]{3,}']

    @classmethod
    def detect(cls, text: str) -> dict:
        lines = text.split('\n')
        code_score  = sum(1 for p in cls.CODE_PATTERNS  if re.search(p, text, re.MULTILINE | re.IGNORECASE))
        math_score  = sum(1 for p in cls.MATH_PATTERNS  if re.search(p, text, re.MULTILINE))
        table_score = sum(1 for p in cls.TABLE_PATTERNS if re.search(p, text, re.MULTILINE))
        code_score  += len(re.findall(r'```[\s\S]*?```', text)) * 3
        math_score  += len(re.findall(r'\$\$[\s\S]+?\$\$|\$[^$\n]+\$', text)) * 2
        total = code_score + math_score + table_score + 1

        content_type = "text"
        if   code_score  / total > 0.4:                   content_type = "code"
        elif math_score  / total > 0.35:                  content_type = "math"
        elif table_score / total > 0.3:                   content_type = "table"
        elif (code_score + math_score) / total > 0.4:     content_type = "mixed"

        lang = "unknown"
        if code_score > 0:
            if   re.search(r'def\s+\w+|import\s+\w+|print\s*\(', text):      lang = "Python"
            elif re.search(r'#include|int\s+main\s*\(|printf\s*\(', text):    lang = "C/C++"
            elif re.search(r'public\s+class|System\.out\.print', text):       lang = "Java"
            elif re.search(r'algorithm|procedure|begin|end', text, re.I):     lang = "Pseudocode"

        return {
            "type": content_type, "code_score": code_score,
            "math_score": math_score, "lang": lang,
            "has_arabic": bool(re.search(r'[\u0600-\u06FF]', text)),
            "line_count": len(lines), "char_count": len(text),
        }


# ════════════════════════════════════════════════════════════
#  NORMALIZER
# ════════════════════════════════════════════════════════════

class TextNormalizer:
    MATH_MAP = {
        '∑':r'\sum','∏':r'\prod','∫':r'\int','∂':r'\partial','∇':r'\nabla',
        '∞':r'\infty','∈':r'\in','∉':r'\notin','⊂':r'\subset','⊃':r'\supset',
        '∪':r'\cup','∩':r'\cap','∧':r'\land','∨':r'\lor','¬':r'\neg',
        '∀':r'\forall','∃':r'\exists','≤':r'\leq','≥':r'\geq','≠':r'\neq',
        '≈':r'\approx','≡':r'\equiv','∝':r'\propto','→':r'\rightarrow',
        '←':r'\leftarrow','↔':r'\leftrightarrow','⇒':r'\Rightarrow',
        '⇔':r'\Leftrightarrow','×':r'\times','÷':r'\div','±':r'\pm','√':r'\sqrt',
        'α':r'\alpha','β':r'\beta','γ':r'\gamma','δ':r'\delta','ε':r'\epsilon',
        'θ':r'\theta','λ':r'\lambda','μ':r'\mu','π':r'\pi','σ':r'\sigma',
        'τ':r'\tau','φ':r'\phi','ω':r'\omega','Σ':r'\Sigma','Π':r'\Pi',
        'Δ':r'\Delta','Λ':r'\Lambda','Ω':r'\Omega',
    }
    OCR_FIXES = [
        (r'\b([A-Z])\s+\(', r'\1('),
        (r'\bO\s*\(\s*n\s*\)', 'O(n)'), (r'\bO\s*\(\s*1\s*\)', 'O(1)'),
        (r'\bO\s*\(\s*n\s*log\s*n\s*\)', 'O(n log n)'),
        (r'\bO\s*\(\s*n\s*2\s*\)', 'O(n²)'), (r'\bO\s*\(\s*2\s*n\s*\)', 'O(2ⁿ)'),
        (r'(?<=[a-z])1(?=[a-z])', 'l'), (r'(?<=\s)0(?=[a-z])', 'o'),
        (r'\bFigure\s+(\d+)', r'Figure \1'), (r'\bAlgorithm\s+(\d+)', r'Algorithm \1'),
        (r'(\w)-\n(\w)', r'\1\2'), (r'([a-z])\n([a-z])', r'\1 \2'),
    ]

    @classmethod
    def normalize(cls, text: str, preserve_math: bool = True) -> str:
        text = unicodedata.normalize('NFKC', text)
        for pattern, replacement in cls.OCR_FIXES:
            text = re.sub(pattern, replacement, text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        text = re.sub(r'^(#{1,4})\s*\n\s*(.+)$', r'\1 \2', text, flags=re.MULTILINE)
        if preserve_math:
            protected = {}
            def protect_math(m):
                key = f"__MATH_{len(protected)}__"
                protected[key] = m.group(0)
                return key
            text = re.sub(r'\$\$[\s\S]+?\$\$|\$[^$\n]+\$', protect_math, text)
            for uni, latex in cls.MATH_MAP.items():
                if uni in text:
                    text = text.replace(uni, f'${latex}$')
            for key, val in protected.items():
                text = text.replace(key, val)
        text = cls._fix_code_blocks(text)
        text = cls._fix_tables(text)
        text = cls._fix_arabic(text)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE)
        return text.strip()

    @classmethod
    def _fix_code_blocks(cls, text: str) -> str:
        lines = text.split('\n')
        result, in_code = [], False
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code:
                    in_code = True
                    tag = line.strip()[3:].strip()
                    if not tag:
                        lookahead = '\n'.join(lines[i+1:i+10])
                        if re.search(r'def\s+\w+|import\s+\w+', lookahead):     line = '```python'
                        elif re.search(r'#include|int\s+main', lookahead):      line = '```cpp'
                        elif re.search(r'public\s+class', lookahead):           line = '```java'
                        elif re.search(r'algorithm|procedure', lookahead, re.I):line = '```pseudocode'
                else:
                    in_code = False
            result.append(line)
        return '\n'.join(result)

    @classmethod
    def _fix_tables(cls, text: str) -> str:
        lines = text.split('\n')
        result = []
        for i, line in enumerate(lines):
            result.append(line)
            if (line.startswith('|') and i + 1 < len(lines) and
                lines[i+1].startswith('|') and
                not re.match(r'^\|[\s\-|]+\|$', lines[i+1])):
                cols = len(re.findall(r'\|', line)) - 1
                result.append('|' + '---|' * cols)
        return '\n'.join(result)

    @classmethod
    def _fix_arabic(cls, text: str) -> str:
        text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f]', '', text)
        text = re.sub(r'\u0640', '', text)
        return text

    @classmethod
    def extract_structure(cls, text: str) -> dict:
        structure = {"chapters": [], "sections": [], "has_index": False, "has_toc": False}
        if re.search(r'table\s+of\s+contents|contents\s*\n[-\s]+', text, re.IGNORECASE):
            structure["has_toc"] = True
        if re.search(r'\bindex\b\s*\n', text[-2000:], re.IGNORECASE):
            structure["has_index"] = True
        ch_pattern = re.compile(
            r'^(?:chapter|ch\.?)\s+(\d+|[ivxlc]+)[:\s—–-]*(.+)$', re.MULTILINE | re.IGNORECASE)
        for m in ch_pattern.finditer(text):
            structure["chapters"].append({
                "num": m.group(1), "title": m.group(2).strip()[:80], "pos": m.start()})
        sec_pattern = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
        for m in sec_pattern.finditer(text):
            structure["sections"].append({"title": m.group(1).strip()[:80], "pos": m.start()})
        return structure


# ════════════════════════════════════════════════════════════
#  AGENT 1 — EXTRACTOR
# ════════════════════════════════════════════════════════════

def run_marker_extraction(pdf_path: str, out_dir: str) -> str:
    log(f"sending PDF → marker server at {MARKER_API_URL}")
    try:
        with open(pdf_path, "rb") as f:
            response = requests.post(
                f"{MARKER_API_URL}/extract",
                files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
                timeout=600,
            )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"❌ Can't connect to marker server at {MARKER_API_URL}")
    if response.status_code != 200:
        raise RuntimeError(f"❌ marker error {response.status_code}: {response.text[:300]}")

    data     = response.json()
    raw_text = data.get("markdown", "")
    log(f"received {len(raw_text):,} chars from marker")
    clean_text = TextNormalizer.normalize(raw_text)
    log(f"normalized → {len(clean_text):,} chars")
    structure  = TextNormalizer.extract_structure(clean_text)
    log(f"structure: {len(structure['chapters'])} chapters, {len(structure['sections'])} sections, "
        f"TOC={'yes' if structure['has_toc'] else 'no'}")

    out_path = os.path.join(out_dir, "EXTRACTED.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {Path(pdf_path).stem}\n\n")
        f.write(f"*Extracted: {len(clean_text):,} chars | "
                f"Chapters: {len(structure['chapters'])} | Sections: {len(structure['sections'])}*\n\n")
        if structure["chapters"]:
            f.write("## Book Structure\n")
            for ch in structure["chapters"][:30]:
                f.write(f"- Chapter {ch['num']}: {ch['title']}\n")
            f.write("\n---\n\n")
        f.write(clean_text)

    with open(os.path.join(out_dir, "STRUCTURE.json"), "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    log(f"saved → {out_path}", "ok")
    return out_path


def get_pages_from_extracted(extracted_text: str, chars_per_page: int = 4000) -> dict:
    # Method 1: Chapter boundaries (best for textbooks)
    ch_pattern = re.compile(
        r'^(?:#{1,2}\s+)?(?:chapter|ch\.?)\s+(\d+)[:\s—–-]*(.+)$', re.MULTILINE | re.IGNORECASE)
    matches = list(ch_pattern.finditer(extracted_text))
    if len(matches) >= 2:
        pages = {}
        for idx, m in enumerate(matches):
            ch_num  = int(m.group(1)) if m.group(1).isdigit() else idx + 1
            start   = m.start()
            end     = matches[idx+1].start() if idx + 1 < len(matches) else len(extracted_text)
            content = extracted_text[start:end].strip()
            if len(content) > 300:
                pages[ch_num] = content
        if pages:
            log(f"page detection: {len(pages)} chapters via chapter headings")
            return pages

    # Method 2: Explicit page markers
    pattern = re.compile(
        r'(?:<!-+\s*[Pp]age\s*(\d+)\s*-+>|^#{1,3}\s*[Pp]age\s+(\d+)\s*$)', re.MULTILINE)
    matches = list(pattern.finditer(extracted_text))
    if matches:
        pages = {}
        for idx, m in enumerate(matches):
            pg_num  = int(m.group(1) or m.group(2))
            start   = m.end()
            end     = matches[idx+1].start() if idx+1 < len(matches) else len(extracted_text)
            content = extracted_text[start:end].strip()
            if content:
                pages[pg_num] = content
        if pages:
            log(f"page detection: {len(pages)} pages via explicit markers")
            return pages

    # Method 3: Image markers
    img_pattern = re.compile(r"!\[.*?\]\(_page_(\d+)_")
    img_matches = list(img_pattern.finditer(extracted_text))
    if img_matches:
        split_points, seen = [], set()
        for m in img_matches:
            pg = int(m.group(1))
            if pg not in seen:
                seen.add(pg)
                line_start = extracted_text.rfind("\n", 0, m.start())
                split_points.append((pg, line_start if line_start != -1 else m.start()))
        split_points.sort(key=lambda x: x[1])
        pages = {}
        for i, (pg, pos) in enumerate(split_points):
            end = split_points[i+1][1] if i+1 < len(split_points) else len(extracted_text)
            content = extracted_text[pos:end].strip()
            if content and len(content) > 100:
                pages[pg] = content
        if pages:
            log(f"page detection: {len(pages)} pages via image markers")
            return pages

    # Method 4: H2/H1 headings
    for heading_re, label in [
        (re.compile(r"^## .+$", re.MULTILINE), "H2"),
        (re.compile(r"^# .+$",  re.MULTILINE), "H1"),
    ]:
        h_matches = list(heading_re.finditer(extracted_text))
        if len(h_matches) >= 2:
            pages = {}
            for i, m in enumerate(h_matches):
                end = h_matches[i+1].start() if i+1 < len(h_matches) else len(extracted_text)
                content = extracted_text[m.start():end].strip()
                if content and len(content) > 200:
                    pages[i+1] = content
            if pages:
                log(f"page detection: {len(pages)} sections via {label}")
                return pages

    # Method 5: --- separators
    parts = [p.strip() for p in re.split(r'\n---+\n', extracted_text)
             if p.strip() and len(p.strip()) > 100]
    if len(parts) > 1:
        log(f"page detection: {len(parts)} sections via separators")
        return {i+1: p for i, p in enumerate(parts)}

    # Method 6: Auto-split (for books without clear chapter markers)
    text = extracted_text.strip()
    if len(text) <= chars_per_page:
        return {1: text}
    pages, pg = {}, 1
    while text:
        if len(text) <= chars_per_page:
            pages[pg] = text; break
        cut = text.rfind('\n\n', 0, chars_per_page)
        if cut == -1: cut = text.rfind('\n', 0, chars_per_page)
        if cut == -1: cut = chars_per_page
        pages[pg] = text[:cut].strip()
        text = text[cut:].strip()
        pg += 1
    log(f"page detection: {len(pages)} auto-split chunks ({chars_per_page} chars/chunk)")
    return pages


def get_chunk_text(pages_dict: dict, chunk: list) -> str:
    parts = []
    for p in chunk:
        if p in pages_dict:
            parts.append(f"<!-- Page/Section {p} -->\n\n{pages_dict[p]}")
    return "\n\n---\n\n".join(parts)


# ════════════════════════════════════════════════════════════
#  AGENT 2 — SUMMARIZER
#  v7.2: prompts tuned for full textbook chapters
# ════════════════════════════════════════════════════════════

def _summary_prompt_simple(label: str, chunk_text: str, ctype: str, lang: str) -> str:
    """
    Simple prompt — first attempt.
    Short schema that small models can complete reliably.
    """
    if ctype == "code":
        focus = f"This is a CODE section ({lang}). Focus on: algorithms, complexity, patterns, implementation."
    elif ctype == "math":
        focus = "This is a MATH section. Focus on: formulas, theorems, proofs, and their CS applications."
    elif ctype == "table":
        focus = "This section has tables/comparisons. Focus on: what's being compared and key criteria."
    else:
        focus = "This is a CS textbook section. Focus on: core concepts, definitions, practical applications."

    return f"""You are a JSON generator. Output ONLY valid JSON, nothing else.

Task: Summarize this CS textbook section.
{focus}

--- TEXTBOOK CONTENT ---
{chunk_text[:MAX_CHUNK_CHARS]}
--- END CONTENT ---

Output this JSON (fill ALL fields with real content):
{{
  "topic": "chapter/section topic name",
  "summary": "Write 4-6 sentences. Explain the MAIN ideas, WHY they matter, and HOW they connect to each other.",
  "key_concepts": [
    {{"term": "concept name", "definition": "clear 1-2 sentence definition", "intuition": "simple analogy or example"}}
  ],
  "formulas": [
    {{"formula": "exact formula or complexity", "meaning": "what it means in plain language"}}
  ],
  "algorithms": [
    {{"name": "algorithm name", "purpose": "what it solves", "complexity": "O(?)"}}
  ],
  "takeaways": ["most important point 1", "most important point 2", "most important point 3"]
}}

Rules:
- key_concepts: 3-6 items (only real CS concepts from the text)
- formulas: list all formulas found, or []
- algorithms: list all algorithms found, or []
- takeaways: exactly 3 items — the most exam-important points
- NO text outside the JSON"""


def _summary_prompt_minimal(label: str, chunk_text: str) -> str:
    """
    Minimal fallback prompt — if even the simple one fails.
    Absolute minimum schema.
    """
    return f"""Output ONLY JSON. No text before or after.

Summarize this CS textbook content:
{chunk_text[:3000]}

JSON:
{{"topic": "topic name", "summary": "3-4 sentences summarizing the main ideas", "takeaways": ["point 1", "point 2", "point 3"]}}"""


def make_fallback_summary(label: str, raw_text: str) -> dict:
    clean = re.sub(r'\s+', ' ', (raw_text or "")).strip()[:800]
    return {
        "section": label, "topic": f"Section {label}",
        "summary": clean or "Content unavailable — check _raw file.",
        "key_concepts": [], "formulas": [], "algorithms": [],
        "code_insights": [], "examples": [], "connections": [],
        "takeaways": ["Review original content for this section."],
        "_fallback": True
    }


def render_chunk_summary_md(s: dict) -> str:
    if not s:
        return ""
    section = s.get('section', '')
    topic   = s.get('topic', '')
    lines   = [f"### 📄 {section} — {topic}"]

    badges = []
    if s.get("_fallback"):         badges.append("⚠️ fallback")
    if s.get("_regex_extracted"):  badges.append("⚡ partial")
    if badges:
        lines.append(f"*{' | '.join(badges)}*")
    lines.append("")

    if s.get("summary"):
        lines.append(s["summary"] + "\n")

    if s.get("key_concepts"):
        lines.append("**🔑 Key Concepts:**")
        for c in s["key_concepts"]:
            if isinstance(c, dict):
                intuition = f" 💡 *{c['intuition']}*" if c.get("intuition") else ""
                lines.append(f"- **{c.get('term','')}** — {c.get('definition','')}{intuition}")
        lines.append("")

    if s.get("formulas"):
        lines.append("**∑ Formulas:**")
        for f in s["formulas"]:
            if isinstance(f, dict):
                formula  = f.get("formula", f.get("formula",""))
                meaning  = f.get("meaning", f.get("variables", f.get("when_to_use","")))
                lines.append(f"- `{formula}` — {meaning}")
        lines.append("")

    if s.get("algorithms"):
        lines.append("**⚙️ Algorithms:**")
        for a in s["algorithms"]:
            if isinstance(a, dict):
                name      = a.get("name","")
                purpose   = a.get("purpose","")
                # support both complexity formats
                tc = a.get("complexity", a.get("time_complexity",""))
                sc = a.get("space_complexity","")
                badge = f" `{tc}`" if tc else ""
                badge += f" / `{sc}`" if sc else ""
                lines.append(f"- **{name}**{badge} — {purpose}")
                if a.get("steps"):
                    for step in a["steps"][:4]:
                        lines.append(f"  1. {step}")
        lines.append("")

    if s.get("code_insights"):
        lines.append("**💻 Code Insights:**")
        for c in s["code_insights"]:
            if isinstance(c, dict):
                lines.append(f"- `{c.get('snippet','')}` — {c.get('explanation','')}")
        lines.append("")

    if s.get("examples"):
        lines.append("**📝 Examples:**")
        for ex in s["examples"]:
            if isinstance(ex, dict):
                lines.append(f"- **{ex.get('problem','')}** → {ex.get('solution','')}")
        lines.append("")

    if s.get("takeaways"):
        lines.append("**✅ Key Takeaways:**")
        for t in s["takeaways"]:
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines)


def _book_overview_prompt(sections_text: str, page_range: str) -> str:
    return f"""Output ONLY a JSON object. No text before or after.

CS textbook summaries (sections {page_range}):
{sections_text[:3500]}

JSON:
{{"title":"book/chapter title","subject":"CS subfield (e.g. Data Structures, Networks, OS)","overview":"6-8 sentences: synthesize ALL topics, explain how they build on each other, what the reader learns","main_topics":["topic 1","topic 2","topic 3","topic 4"],"key_takeaways":["critical insight 1","critical insight 2","critical insight 3","critical insight 4"],"study_strategy":"3 sentences on the best way to study this material","exam_focus":"2 sentences on what topics are most likely to be examined"}}"""


def render_book_overview_md(s: dict, page_range: str) -> str:
    if not s:
        return ""
    lines = [
        f"## 📘 {s.get('title', 'Book Summary')}",
        f"*{s.get('subject', '')} | Sections {page_range}*\n",
        "### Overview", s.get("overview", "") + "\n",
    ]
    if s.get("main_topics"):
        lines.append("### Main Topics")
        for t in s["main_topics"]:
            lines.append(f"- {t}")
        lines.append("")
    if s.get("key_takeaways"):
        lines.append("### Key Takeaways")
        for k in s["key_takeaways"]:
            lines.append(f"- {k}")
        lines.append("")
    if s.get("study_strategy"):
        lines.append(f"### 📖 Study Strategy\n{s['study_strategy']}\n")
    if s.get("exam_focus"):
        lines.append(f"### 📝 Exam Focus\n{s['exam_focus']}\n")
    return "\n".join(lines)


def run_summarization_pipeline(pages_dict: dict, pages: list, out_dir: str,
                                book_name: str, chunk_size: int,
                                do_book_summary: bool = True):
    all_summaries = []
    failed = 0
    total_chunks = (len(pages) + chunk_size - 1) // chunk_size

    for idx, start in enumerate(range(0, len(pages), chunk_size)):
        chunk      = pages[start:start + chunk_size]
        label      = (f"sections {chunk[0]}-{chunk[-1]}"
                      if len(chunk) > 1 else f"section {chunk[0]}")
        chunk_text = get_chunk_text(pages_dict, chunk)

        if not chunk_text.strip():
            continue
        if len(chunk_text) > MAX_CHUNK_CHARS:
            chunk_text = chunk_text[:MAX_CHUNK_CHARS] + "\n\n[... content truncated ...]"

        content_info = ContentAnalyzer.detect(chunk_text)
        ctype        = content_info["type"]
        lang         = content_info.get("lang", "unknown")
        type_badge   = f"[{ctype.upper()}" + (f"/{lang}" if ctype == "code" else "") + "]"

        log(f"[{idx+1}/{total_chunks}] summarizing {label} {type_badge} "
            f"({len(chunk_text):,} chars)...")

        # ── Attempt 1: simple prompt ───────────────────────
        raw = call_model(
            [{"role": "user", "content": _summary_prompt_simple(label, chunk_text, ctype, lang)}],
            max_tokens=MAX_TOKENS, temp=0.0,
        )
        res = safe_json(raw)

        # ── Attempt 2: minimal prompt ──────────────────────
        if not (res and isinstance(res, dict) and (res.get("topic") or res.get("summary"))):
            log("attempt 1 failed → minimal prompt...", "warn")
            raw = call_model(
                [{"role": "user", "content": _summary_prompt_minimal(label, chunk_text)}],
                max_tokens=600, temp=0.1,
            )
            res = safe_json(raw)

        if res and isinstance(res, dict) and (res.get("topic") or res.get("summary")):
            res["section"]       = label
            res["_content_type"] = ctype
            all_summaries.append(res)
            n_concepts  = len(res.get("key_concepts", []))
            n_formulas  = len(res.get("formulas", []))
            n_algos     = len(res.get("algorithms", []))
            n_takeaways = len(res.get("takeaways", []))
            badge = "⚡partial" if res.get("_regex_extracted") else "✓"
            log(f"{badge} {res.get('topic','done')[:50]} | "
                f"concepts:{n_concepts} formulas:{n_formulas} "
                f"algos:{n_algos} takeaways:{n_takeaways}", "ok")
        else:
            failed += 1
            all_summaries.append(make_fallback_summary(label, raw))
            raw_path = os.path.join(out_dir, f"_raw_{chunk[0]}.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(raw or "")
            log(f"fallback for {label} → saved raw to {raw_path}", "warn")

        if start + chunk_size < len(pages):
            time.sleep(SLEEP_BETWEEN)

    if failed:
        log(f"{failed}/{len(all_summaries)} chunks used fallback", "warn")
    else:
        log("all chunks parsed successfully", "ok")

    # ── Book-level overview ────────────────────────────────
    book_overview = None
    if do_book_summary and len(all_summaries) >= 2:
        log("generating book-level overview...")
        stext = ""
        for s in all_summaries:
            stext += f"\n### {s.get('section','')}\nTopic: {s.get('topic','')}\n"
            stext += f"{s.get('summary','')}\n"
            if s.get("takeaways"):
                stext += "Key points: " + " | ".join(str(t) for t in s["takeaways"][:3]) + "\n"
        raw = call_model(
            [{"role": "user", "content": _book_overview_prompt(stext, f"{pages[0]}-{pages[-1]}")}],
            max_tokens=700, temp=0.1
        )
        book_overview = safe_json(raw)
        if book_overview:
            log("book overview generated", "ok")
        else:
            log("book overview parse failed — skipping", "warn")

    # ── Write SUMMARY.md ──────────────────────────────────
    out_path    = os.path.join(out_dir, "SUMMARY.md")
    plain_parts = []
    fallback_note = f" | ⚠️ {failed} fallbacks" if failed else ""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Summary\n\n")
        f.write(f"*{len(pages)} pages | {len(all_summaries)} chunks processed{fallback_note}*\n\n---\n\n")
        if book_overview and isinstance(book_overview, dict):
            bmd = render_book_overview_md(book_overview, f"{pages[0]}-{pages[-1]}")
            f.write(bmd + "\n\n---\n\n## 📑 Section-by-Section Summaries\n\n")
            plain_parts.append(bmd)
        else:
            f.write("## 📑 Section-by-Section Summaries\n\n")
        for s in all_summaries:
            md = render_chunk_summary_md(s)
            if md:
                f.write(md + "\n\n---\n\n")
                plain_parts.append(md)

    log(f"saved → {out_path}", "ok")
    return out_path, "\n\n".join(plain_parts)


# ════════════════════════════════════════════════════════════
#  AGENT 3 — QUESTIONS
# ════════════════════════════════════════════════════════════

def _questions_prompt(label: str, chunk_text: str, content_info: dict, lang: str) -> str:
    lang_rule = {
        "ar":   "Write ALL questions and answers in Arabic.",
        "en":   "Write ALL questions and answers in English.",
        "auto": "Use the same language as the content.",
    }.get(lang, "Use the same language as the content.")

    ctype = content_info["type"]
    if ctype == "code":
        q_hint = "Include: mcq (concepts), trace (give code, ask output), complexity (ask Big-O)"
    elif ctype == "math":
        q_hint = "Include: mcq (theory), calculate (apply formula to numbers), concept (explain theorem)"
    else:
        q_hint = "Include: mcq (facts), concept (explain + compare), design (design a solution)"

    return f"""Output ONLY a JSON object. No text before or after.
{lang_rule}
{q_hint}

CS Textbook content (section {label}):
{chunk_text[:MAX_CHUNK_CHARS]}

Generate 5 exam questions covering different Bloom's levels. JSON:
{{"section":"{label}","topic":"topic","total_marks":17,"questions":[
{{"id":1,"type":"mcq","bloom_level":"L1_remember","question":"Define or identify [concept from content]?","options":["A) opt1","B) opt2","C) opt3","D) opt4"],"answer":"B) opt2","explanation":"why correct and why others are wrong","marks":2,"common_mistake":"typical error"}},
{{"id":2,"type":"concept","bloom_level":"L2_understand","question":"Explain [concept] and compare it to [related concept]?","options":[],"answer":"full explanation with comparison","explanation":"key distinction","marks":3,"common_mistake":"confusion between the two"}},
{{"id":3,"type":"trace","bloom_level":"L4_analyze","question":"Trace through [algorithm/process from content] with input [X]. Show each step.","options":[],"answer":"step-by-step trace","explanation":"what happens at each step","marks":4,"common_mistake":"skipping a step"}},
{{"id":4,"type":"complexity","bloom_level":"L5_evaluate","question":"Analyze the time and space complexity of [algorithm]. Justify your answer.","options":[],"answer":"O(?) with justification","explanation":"how to derive it","marks":4,"common_mistake":"wrong case analysis"}},
{{"id":5,"type":"design","bloom_level":"L6_create","question":"Design [data structure/algorithm/system] to solve [problem from content].","options":[],"answer":"complete design with justification","explanation":"design decisions","marks":4,"common_mistake":"ignoring edge cases"}}
]}}

IMPORTANT: Replace every placeholder with REAL content from the text above."""


def render_questions_md(qdata: dict) -> str:
    if not qdata or not qdata.get("questions"):
        return ""
    type_icons = {
        "mcq":"🔤","concept":"💡","truefalse":"✅","trace":"🔍","debug":"🐛",
        "complexity":"⏱","design":"🏗","prove":"📐","calculate":"🧮",
        "compare":"⚖️","modify":"✏️","scenario":"🌍","open":"🧠"
    }
    bloom_colors = {
        "L1_remember":"🔵","L2_understand":"🟢","L3_apply":"🟡",
        "L4_analyze":"🟠","L5_evaluate":"🔴","L6_create":"🟣"
    }
    total_marks = qdata.get("total_marks", sum(q.get("marks",0) for q in qdata["questions"]))
    lines = [
        f"### {qdata.get('section','')} — {qdata.get('topic','')}",
        f"*Total: {total_marks} marks | {len(qdata['questions'])} questions*\n"
    ]
    for q in qdata["questions"]:
        icon  = type_icons.get(q.get("type",""), "❓")
        bloom = bloom_colors.get(q.get("bloom_level",""), "⚪")
        ms    = f"`{q.get('marks','')}m`" if q.get("marks") else ""
        lines.append(f"**Q{q['id']}** {icon} {bloom} {ms} `{q.get('type','')}` `{q.get('bloom_level','')}`")
        lines.append(f"\n> {q['question']}\n")
        for opt in q.get("options", []):
            lines.append(f"> {opt}")
        if q.get("options"):
            lines.append("")
        if q.get("answer"):
            details  = f"\n**Answer:** {str(q['answer']).strip()}\n"
            if q.get("explanation"):
                details += f"\n**Explanation:** {str(q['explanation']).strip()}\n"
            if q.get("common_mistake"):
                details += f"\n**⚠️ Common mistake:** {str(q['common_mistake']).strip()}\n"
            lines.append(f"<details><summary>✔ Model Answer</summary>{details}</details>\n")
    return "\n".join(lines)


def run_questions_pipeline(pages_dict: dict, pages: list, out_dir: str,
                            book_name: str, chunk_size: int, lang: str = "auto") -> str:
    all_chunks, failed, all_q_count, total_marks_sum = [], 0, 0, 0
    total_chunks = (len(pages) + chunk_size - 1) // chunk_size

    for idx, start in enumerate(range(0, len(pages), chunk_size)):
        chunk      = pages[start:start + chunk_size]
        label      = (f"sections {chunk[0]}-{chunk[-1]}"
                      if len(chunk) > 1 else f"section {chunk[0]}")
        chunk_text = get_chunk_text(pages_dict, chunk)
        if not chunk_text.strip():
            continue
        if len(chunk_text) > MAX_CHUNK_CHARS:
            chunk_text = chunk_text[:MAX_CHUNK_CHARS] + "\n\n[truncated]"

        content_info = ContentAnalyzer.detect(chunk_text)
        log(f"[{idx+1}/{total_chunks}] questions for {label} [{content_info['type'].upper()}]...")

        raw = call_model(
            [{"role": "user", "content": _questions_prompt(label, chunk_text, content_info, lang)}],
            max_tokens=1200, temp=0.0,
        )
        res = safe_json(raw)

        if res and isinstance(res, dict) and res.get("questions"):
            all_chunks.append(res)
            qcount = len(res["questions"])
            marks  = res.get("total_marks", sum(q.get("marks",0) for q in res["questions"]))
            all_q_count    += qcount
            total_marks_sum += marks
            log(f"✓ {qcount} questions | {marks} marks", "ok")
        else:
            failed += 1
            log(f"parse failed for {label}", "warn")
            if raw:
                with open(os.path.join(out_dir, f"_qraw_{chunk[0]}.txt"), "w", encoding="utf-8") as fb:
                    fb.write(raw)

        if start + chunk_size < len(pages):
            time.sleep(SLEEP_BETWEEN)

    type_count  = defaultdict(int)
    bloom_count = defaultdict(int)
    for chunk in all_chunks:
        for q in chunk.get("questions", []):
            type_count[q.get("type","?")]        += 1
            bloom_count[q.get("bloom_level","?")] += 1

    out_path = os.path.join(out_dir, "QUESTIONS.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Question Bank\n\n")
        f.write(f"*{all_q_count} questions | {total_marks_sum} total marks | {failed} failed chunks*\n\n")
        if type_count:
            f.write("### By Question Type\n| Type | Count |\n|------|-------|\n")
            for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
                f.write(f"| {t} | {c} |\n")
            f.write("\n")
        if bloom_count:
            f.write("### By Bloom's Level\n| Level | Count |\n|-------|-------|\n")
            for bl, c in sorted(bloom_count.items()):
                f.write(f"| {bl} | {c} |\n")
            f.write("\n---\n\n")
        for chunk in all_chunks:
            md = render_questions_md(chunk)
            if md:
                f.write(md + "\n\n---\n\n")
    log(f"saved → {out_path} ({all_q_count} questions, {total_marks_sum} marks)", "ok")
    return out_path


# ════════════════════════════════════════════════════════════
#  AGENT 4 — TRANSLATOR (Egyptian Arabic)
# ════════════════════════════════════════════════════════════

TRANSLATE_SYSTEM = """أنت بتترجم محتوى كتب Computer Science للعامية المصرية البسيطة.

قواعد صارمة:
١. اكتب بالعامية المصرية الكلامية — مش فصحى ولا إنجليزي خالص
٢. المصطلحات التقنية: خليها بالإنجليزي كما هي (algorithm, pointer, stack, etc.)
٣. المعادلات والأكواد: حافظ عليها كما هي بالضبط، واشرحها بالعامية بعدها
٤. حافظ على تنسيق Markdown بالكامل (##, **, -, `code`, etc.)
٥. ابدأ مباشرة بدون "بالتأكيد" أو "بكل سرور" أو أي مقدمة
٦. لما تشرح concept صعب، استخدم تشبيه من الحياة اليومية
٧. كود: ترجم التعليقات بس، الكود نفسه متلمسوش
٨. لو الجزء ده كبير، ركّز على الـ summary والـ takeaways"""


def _validate_translation(original: str, translated: str) -> str:
    if not translated:
        return original
    issues = []
    for eq in set(re.findall(r'\$\$[\s\S]+?\$\$|\$[^$\n]+\$', original)):
        if eq not in translated:
            issues.append(f"missing equation: {eq[:40]}")
    for code_block in set(re.findall(r'```[\s\S]+?```', original)):
        if code_block not in translated:
            issues.append("code block modified")
            break
    if issues:
        prefix = "\n".join(f"<!-- ⚠️ {w} -->" for w in issues)
        return f"{prefix}\n\n{translated}"
    return translated


def _split_text(text: str, max_chars: int = TRANSLATE_CHUNK_CHARS) -> list:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text); break
        cut = text.rfind("\n\n", 0, max_chars)
        if cut == -1: cut = text.rfind("\n", 0, max_chars)
        if cut == -1: cut = max_chars
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    return [c for c in chunks if c.strip()]


def run_translation_pipeline(summary_text: str, out_dir: str, book_name: str) -> str:
    if not summary_text.strip():
        out_path = os.path.join(out_dir, "TRANSLATED.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {book_name} — ملخص بالعامية المصرية\n\n*لا يوجد محتوى.*\n")
        return out_path

    chunks = _split_text(summary_text, max_chars=TRANSLATE_CHUNK_CHARS)
    log(f"translating {len(chunks)} chunk(s)...")
    parts = []

    for i, chunk in enumerate(chunks, 1):
        log(f"chunk {i}/{len(chunks)} ({len(chunk):,} chars)...")
        messages = [
            {"role": "system", "content": TRANSLATE_SYSTEM},
            {"role": "user",   "content": f"ترجم ملخص الـ CS ده للعامية المصرية:\n\n---\n{chunk}\n---"},
        ]
        translated = call_model(messages, max_tokens=1600, temp=0.0, use_system=False)

        if translated:
            # Anti-repetition filter
            lines = translated.split('\n')
            clean_lines, prev, rep = [], None, 0
            for line in lines:
                stripped = line.strip()
                if stripped and stripped == prev:
                    rep += 1
                    if rep > 2: break
                else:
                    rep = 0
                clean_lines.append(line)
                prev = stripped
            parts.append(_validate_translation(chunk, '\n'.join(clean_lines)))
        else:
            log(f"chunk {i} failed — using original", "warn")
            parts.append(chunk)

        if i < len(chunks):
            time.sleep(SLEEP_BETWEEN)

    out_path = os.path.join(out_dir, "TRANSLATED.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — ملخص بالعامية المصرية\n\n")
        f.write("*ملاحظة: المصطلحات التقنية محفوظة بالإنجليزي | المعادلات والكود محفوظين كما هم*\n\n---\n\n")
        f.write("\n\n---\n\n".join(parts))
    log(f"saved → {out_path}", "ok")
    return out_path


# ════════════════════════════════════════════════════════════
#  AGENT 5 — CONCEPT MAP
# ════════════════════════════════════════════════════════════

def _concept_map_prompt(all_summaries: list) -> str:
    topics = []
    for s in all_summaries:
        concepts = [c.get("term","") for c in s.get("key_concepts",[]) if isinstance(c, dict)]
        algos    = [a.get("name","")  for a in s.get("algorithms",[])   if isinstance(a, dict)]
        topics.append({
            "section":  s.get("section",""),
            "topic":    s.get("topic",""),
            "concepts": concepts[:5],
            "algos":    algos[:3],
        })
    return f"""Output ONLY a JSON object. No text before or after.

Topics from a CS textbook ({len(topics)} sections):
{json.dumps(topics, ensure_ascii=False)[:2500]}

Build a concept dependency map. JSON:
{{"central_concepts":["most important concept 1","concept 2","concept 3","concept 4"],
"learning_order":["learn first","then","then","finally"],
"concept_map":[{{"concept":"name","depends_on":["prereqs"],"difficulty":"beginner|intermediate|advanced","category":"data_structure|algorithm|math|theory|system|language"}}],
"study_plan":{{"week1":["concepts"],"week2":["concepts"],"week3":["concepts"],"week4":["concepts"]}}}}"""


def run_concept_map(all_summaries: list, out_dir: str, book_name: str) -> str:
    if len(all_summaries) < 2:
        return None
    log("building concept dependency map...")
    raw  = call_model(
        [{"role": "user", "content": _concept_map_prompt(all_summaries)}],
        max_tokens=800, temp=0.0
    )
    data = safe_json(raw)
    if not data:
        log("concept map parse failed", "warn")
        return None

    out_path = os.path.join(out_dir, "CONCEPT_MAP.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Concept Map\n\n")
        if data.get("central_concepts"):
            f.write("## 🌟 Central Concepts\n")
            for c in data["central_concepts"]:
                f.write(f"- **{c}**\n")
            f.write("\n")
        if data.get("learning_order"):
            f.write("## 📚 Recommended Learning Order\n")
            for i, c in enumerate(data["learning_order"], 1):
                f.write(f"{i}. {c}\n")
            f.write("\n")
        if data.get("study_plan"):
            f.write("## 📅 Study Plan\n")
            for week, concepts in data["study_plan"].items():
                f.write(f"**{week.replace('week','Week ')}:** {', '.join(concepts)}\n\n")
        if data.get("concept_map"):
            f.write("## 🗺️ Concept Dependencies\n\n")
            f.write("| Concept | Category | Difficulty | Depends On |\n")
            f.write("|---------|----------|------------|------------|\n")
            for item in data["concept_map"]:
                deps = ", ".join(item.get("depends_on", [])[:3])
                f.write(f"| **{item.get('concept','')}** | "
                        f"{item.get('category','')} | "
                        f"{item.get('difficulty','')} | {deps} |\n")
    log(f"saved → {out_path}", "ok")
    return out_path


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    global MARKER_API_URL, LLM_API_URL

    parser = argparse.ArgumentParser(
        description="PDF Agent Suite v7.2 — CS Textbooks (100-150 pages)")
    parser.add_argument("--pdf",             required=True,  help="Path to PDF file")
    parser.add_argument("--mode",            default="all",
                        choices=["extract","summarize","questions","translate","concept-map","all"])
    parser.add_argument("--lang",            default="auto", choices=["ar","en","auto"])
    parser.add_argument("--page-from",       type=int, default=None)
    parser.add_argument("--page-to",         type=int, default=None)
    parser.add_argument("--chunk-size",      type=int, default=CHUNK_SIZE,
                        help=f"Pages per chunk (default: {CHUNK_SIZE} ≈ 1 chapter section)")
    parser.add_argument("--no-book-summary", action="store_true")
    parser.add_argument("--output-dir",      default=OUTPUT_DIR)
    parser.add_argument("--marker-url",      default=MARKER_API_URL)
    parser.add_argument("--llm-url",         default=LLM_API_URL,
                        help="Full LLM API URL e.g. https://xxxx.ngrok-free.dev/v1/chat/completions")
    args = parser.parse_args()

    MARKER_API_URL = args.marker_url.rstrip('/')
    LLM_API_URL    = args.llm_url

    if not os.path.exists(args.pdf):
        print(f"❌ File not found: {args.pdf}")
        sys.exit(1)

    pdf_name   = Path(args.pdf).stem
    out_dir    = os.path.join(args.output_dir, pdf_name)
    chunk_size = args.chunk_size
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'━'*62}")
    print(f"  📚 PDF Agent Suite v7.2 — CS Textbooks (100-150 pages)")
    print(f"{'━'*62}")
    print(f"  PDF        : {args.pdf}")
    print(f"  Output     : {out_dir}")
    print(f"  Mode       : {args.mode} | Lang: {args.lang} | Chunk: {chunk_size} pages")
    print(f"  Marker URL : {MARKER_API_URL}")
    print(f"  LLM URL    : {LLM_API_URL}")
    print(f"{'━'*62}\n")

    extracted_path = os.path.join(out_dir, "EXTRACTED.md")
    pages_dict, pages, summary_text, all_summaries = {}, [], "", []

    # ── EXTRACTION ──────────────────────────────────────────
    if args.mode in ("extract","summarize","questions","translate","concept-map","all"):
        print(f"\n{'━'*50}")
        print("  📝 AGENT 1 — EXTRACTION + NORMALIZATION")
        print(f"{'━'*50}")
        if not os.path.exists(extracted_path):
            run_marker_extraction(args.pdf, out_dir)
        else:
            log("EXTRACTED.md exists — skipping extraction (delete to re-extract)")

        full_text  = open(extracted_path, encoding="utf-8").read()
        pages_dict = get_pages_from_extracted(full_text)
        all_nums   = sorted(pages_dict.keys())
        pages = [p for p in all_nums
                 if (args.page_from is None or p >= args.page_from)
                 and (args.page_to   is None or p <= args.page_to)]
        if not pages:
            print("❌ No sections found!")
            sys.exit(1)
        total_chunks = (len(pages) + chunk_size - 1) // chunk_size
        log(f"{len(pages)} page(s)/section(s) → {total_chunks} chunk(s) of ~{chunk_size}", "ok")

    # ── SUMMARIZATION ────────────────────────────────────────
    if args.mode in ("summarize","all","translate","concept-map"):
        print(f"\n{'━'*50}")
        print("  📚 AGENT 2 — CONTENT-AWARE SUMMARIZATION")
        print(f"{'━'*50}")
        _, summary_text = run_summarization_pipeline(
            pages_dict, pages, out_dir, pdf_name, chunk_size,
            do_book_summary=not args.no_book_summary,
        )

    # ── QUESTIONS ────────────────────────────────────────────
    if args.mode in ("questions","all"):
        print(f"\n{'━'*50}")
        print("  ❓ AGENT 3 — BLOOM'S TAXONOMY QUESTIONS")
        print(f"{'━'*50}")
        run_questions_pipeline(pages_dict, pages, out_dir, pdf_name, chunk_size, args.lang)

    # ── TRANSLATION ──────────────────────────────────────────
    if args.mode in ("translate","all"):
        print(f"\n{'━'*50}")
        print("  🌍 AGENT 4 — EGYPTIAN ARABIC TRANSLATION")
        print(f"{'━'*50}")
        if not summary_text:
            sp = os.path.join(out_dir, "SUMMARY.md")
            if os.path.exists(sp):
                summary_text = open(sp, encoding="utf-8").read()
            else:
                print("❌ Run --mode summarize first")
                sys.exit(1)
        run_translation_pipeline(summary_text, out_dir, pdf_name)

    # ── CONCEPT MAP ──────────────────────────────────────────
    if args.mode in ("concept-map","all"):
        print(f"\n{'━'*50}")
        print("  🗺️  AGENT 5 — CONCEPT DEPENDENCY MAP")
        print(f"{'━'*50}")
        fake_summaries = []
        for start in range(0, len(pages), chunk_size):
            chunk = pages[start:start+chunk_size]
            label = (f"sections {chunk[0]}-{chunk[-1]}"
                     if len(chunk) > 1 else f"section {chunk[0]}")
            ct    = get_chunk_text(pages_dict, chunk)
            info  = ContentAnalyzer.detect(ct)
            fake_summaries.append({
                "section":      label,
                "topic":        label,
                "key_concepts": [],
                "_content_type": info["type"],
            })
        run_concept_map(fake_summaries, out_dir, pdf_name)

    print(f"\n{'━'*62}")
    print(f"  ✅ Done! Output files in: {out_dir}/")
    print(f"  📄 EXTRACTED.md   — normalized full text")
    print(f"  📚 SUMMARY.md     — chapter-by-chapter summary")
    print(f"  ❓ QUESTIONS.md   — Bloom's taxonomy questions")
    print(f"  🌍 TRANSLATED.md  — Egyptian Arabic summary")
    print(f"  🗺️  CONCEPT_MAP.md — concept dependencies")
    print(f"{'━'*62}\n")


if __name__ == "__main__":
    main()