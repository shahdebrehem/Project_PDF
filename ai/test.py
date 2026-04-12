"""
╔══════════════════════════════════════════════════════════════════╗
║         📚 PDF Agent Suite — v12.1 "Universal"                  ║
║   Any content type | English summary | Egyptian Arabic          ║
╠══════════════════════════════════════════════════════════════════╣
║  5 Agents:                                                       ║
║  1. EXTRACTION    → EXTRACTED.md   (Marker API + cleanup)        ║
║  2. SUMMARIZE     → SUMMARY.md     (English, adaptive format)    ║
║  3. QUESTIONS     → QUESTIONS.md   (4 questions, Bloom levels)   ║
║  4. TRANSLATE     → TRANSLATED.md  (Egyptian Arabic)             ║
║  5. CONCEPT MAP   → CONCEPT_MAP.md                               ║
║                                                                  ║
║  Supported content types (auto-detected):                        ║
║  • Pure text / concept explanations                              ║
║  • SQL queries (SELECT, mysql>, CREATE TABLE...)                  ║
║  • Python / C / C++ / Java code                                  ║
║  • Pseudocode / algorithm notation                               ║
║  • LaTeX math / theorems / proofs                                ║
║  • Data tables and comparison grids                              ║
║  • Any mix of the above                                          ║
║                                                                  ║
║  Splitter never cuts inside a code block or $$ math block.       ║
║                                                                  ║
║  Usage:                                                          ║
║  python3 pdf_agent_suite.py --pdf book.pdf --mode all \          ║
║    --llm-url "https://YOUR.trycloudflare.com/v1/chat/completions"║
║                                                                  ║
║  For dense books (lots of code/math per page):                   ║
║    add --chunk-size 4                                            ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, time, json, re, requests, warnings, argparse, unicodedata
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

warnings.filterwarnings("ignore")


# ════════════════════════════════════════════════════════════
#  CONFIGURATION
# ════════════════════════════════════════════════════════════

MARKER_API_URL    = "https://climatological-yamileth-parliamentarily.ngrok-free.dev"
LLM_API_URL       = "https://YOUR_QWEN_URL.trycloudflare.com/v1/chat/completions"
LOCAL_API_KEY     = "any-key"
MODEL_NAME        = "Qwen/Qwen2.5-7B-Instruct"
OUTPUT_DIR        = "./pdf_output"
CHUNK_SIZE        = 6      # pages per chunk — lower for dense books (3-4)
MAX_CHARS_PER_SUB = 4500   # hard cap per sub-chunk regardless of page size


# ════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════

def log(msg: str, level: str = "info"):
    sym = {"ok":"✓","warn":"⚠","err":"✗","progress":"◈"}.get(level, "▸")
    print(f"  {sym} {msg}")


# ════════════════════════════════════════════════════════════
#  CHUNK PROFILER
# ════════════════════════════════════════════════════════════

@dataclass
class ChunkProfile:
    char_count:       int   = 0
    word_count:       int   = 0
    concept_density:  float = 0.0
    formula_count:    int   = 0
    code_lines:       int   = 0
    has_code:         bool  = False
    has_math:         bool  = False
    has_tables:       bool  = False
    lang:             str   = "unknown"
    complexity_score: float = 0.0
    size_bucket:      str   = "medium"


_TECH_TERMS = re.compile(
    r'\b(?:algorithm|complexity|theorem|proof|lemma|corollary|definition|'
    r'polynomial|recursion|iteration|binary|hash|tree|graph|stack|queue|heap|'
    r'sort|search|pointer|buffer|cache|protocol|encryption|compression|'
    r'bandwidth|latency|throughput|sampling|quantization|integral|derivative|'
    r'convergence|kernel|operator|matrix|vector|eigenvalue)\b', re.IGNORECASE
)


def profile_chunk(text: str) -> ChunkProfile:
    p = ChunkProfile()
    p.char_count = len(text)
    p.word_count = len(text.split())

    # ── detect CODE / PSEUDOCODE ─────────────────────────────
    # fenced code blocks count heavily
    code_signals  = len(re.findall(r'```[\s\S]*?```', text)) * 4
    # actual programming constructs
    code_signals += len(re.findall(
        r'def\s+\w+\s*\(|int\s+\w+\s*\(|#include|for\s*\(|while\s*\(|'
        r'return\s+\w|class\s+\w+|import\s+\w+|printf\s*\(|cout\s*<<', text))
    # SQL queries — mysql> prompt, SQL clauses at line start, MySQL output borders
    code_signals += len(re.findall(
        r'mysql>\s*\w|'                          # mysql> prompt
        r'->\s+(?:FROM|WHERE|JOIN|AND|OR)\b|'    # -> continuation lines
        r'(?:^|\n)\s*(?:SELECT|FROM|WHERE|'
        r'INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|OUTER\s+JOIN|'
        r'ORDER\s+BY|GROUP\s+BY|HAVING|'
        r'INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|'
        r'CREATE\s+TABLE|DROP\s+TABLE|ALTER\s+TABLE|CREATE\s+INDEX)\s|'
        r'(?:^|\n)\+[-+]+\+',                    # MySQL +---+---+ table border
        text, re.IGNORECASE | re.MULTILINE))
    # pseudocode / algorithm notation — common in CS textbooks
    code_signals += len(re.findall(
        r'\bAlgorithm\s+\w+|'           # Algorithm BubbleSort
        r'\bProcedure\s+\w+|'           # Procedure Merge
        r'\bFunction\s+\w+|'            # Function Search
        r'(?:^|\n)\s{2,}\w+\s*:=\s*|'  # x := value (indented assignment)
        r'(?:^|\n)\s*for\s+\w+\s*=|'   # for i = 0 to n
        r'(?:^|\n)\s*if\s+\w+.*then|'  # if condition then
        r'(?:^|\n)\s*while\s+\w+.*do|' # while cond do
        r'(?:^|\n)\s*return\s+\w',      # return value (indented)
        text, re.IGNORECASE | re.MULTILINE))
    p.has_code   = code_signals >= 2    # >= not > — 2 strong signals is enough
    p.code_lines = len([l for l in text.split('\n')
                        if re.search(r'^\s{4,}|\t', l) or '```' in l])
    # lang detection — SQL checked first (most specific prompt)
    if p.has_code:
        if   re.search(r'mysql>\s*\w|^\s*(?:SELECT|INSERT|UPDATE|DELETE)\s',
                       text, re.IGNORECASE | re.MULTILINE):                p.lang = "SQL"
        elif re.search(r'def\s+\w+|import\s+\w+|print\s*\(', text):      p.lang = "Python"
        elif re.search(r'#include|int\s+main\s*\(|printf', text):         p.lang = "C/C++"
        elif re.search(r'public\s+class|System\.out', text):              p.lang = "Java"
        elif re.search(r'\bAlgorithm\b|\bProcedure\b|\bbegin\b|\bend\b',
                       text, re.IGNORECASE):                               p.lang = "Pseudocode"

    # ── detect TABLES (must be before math — affects complexity_math) ──────
    p.has_tables = len(re.findall(r'^\|.+\|', text, re.MULTILINE)) > 3

    # ── detect MATH / THEOREMS ──────────────────────────────
    latex_math = len(re.findall(r'\$[^$]+\$|\$\$[\s\S]+?\$\$', text))
    latex_cmds = len(re.findall(
        r'\\(?:int|sum|prod|frac|sqrt|partial|nabla|infty|forall|exists|'
        r'leq|geq|neq|approx|equiv|rightarrow|Rightarrow|alpha|beta|gamma|'
        r'lambda|mu|pi|sigma|phi|omega|Sigma|Delta|Omega|phi|theta|'
        r'lim|max|min|sup|inf)\b', text))
    unicode_math   = len(re.findall(r'[∑∏∫∂∇∈∧∨¬∀∃≤≥≠≈∞]', text))
    norm_notation  = len(re.findall(r'\|\|[^|]+\|\|', text))
    theorem_blocks = len(re.findall(
        r'(?:^|\n)(?:Theorem|Lemma|Proof|Corollary|Definition|Proposition)\s*[\d.]*\s*[.:]',
        text, re.IGNORECASE | re.MULTILINE))
    recurrence     = len(re.findall(r'T\s*\(\s*n[^)]*\)\s*=', text))
    # O() counts as math only outside tables (tables just compare, not derive)
    complexity_math = (min(len(re.findall(r'O\s*\([^)]+\)', text)), 3)
                       if not p.has_tables else 0)
    math_signals = (latex_math + latex_cmds + unicode_math + norm_notation +
                    theorem_blocks * 2 + recurrence + complexity_math)
    p.has_math      = math_signals >= 2
    p.formula_count = latex_math  # only $ formulas for token budget

    # ── complexity score ────────────────────────────────────
    if p.word_count > 0:
        p.concept_density = (len(_TECH_TERMS.findall(text)) / p.word_count) * 100

    p.complexity_score = min(
        min(p.concept_density / 15.0, 1.0)                          * 0.35 +
        min((p.formula_count + theorem_blocks) / 10.0, 1.0)         * 0.30 +
        min(p.code_lines                        / 50.0, 1.0)         * 0.20 +
        (0.15 if (p.has_code and p.has_math) else
         0.10 if (p.has_code or  p.has_math) else 0.0),
        1.0)

    if   p.char_count < 1000:  p.size_bucket = "tiny"
    elif p.char_count < 3000:  p.size_bucket = "small"
    elif p.char_count < 7000:  p.size_bucket = "medium"
    elif p.char_count < 15000: p.size_bucket = "large"
    else:                       p.size_bucket = "huge"

    return p


# ════════════════════════════════════════════════════════════
#  PROCESSING STRATEGY
# ════════════════════════════════════════════════════════════

@dataclass
class ProcessingStrategy:
    sub_chunk_size: int = 4500
    overlap:        int = 400
    max_tokens:     int = 1800
    content_limit:  int = 3000


def decide_strategy(profile: ChunkProfile, task: str = "summarize") -> ProcessingStrategy:
    s = ProcessingStrategy()
    c = profile.complexity_score

    raw_size = {
        "tiny":  profile.char_count,
        "small": 3500,
        "medium":4000 if c < 0.4 else 3000,
        "large": 3500 if c < 0.5 else 2800,
        "huge":  3000 if c < 0.6 else 2500,
    }.get(profile.size_bucket, 3500)
    s.sub_chunk_size = min(raw_size, MAX_CHARS_PER_SUB)

    # bigger overlap for technical/dense content — preserves context across splits
    s.overlap = int(300 + c * 350)

    if task == "summarize":
        # math and code need more tokens to reproduce equations/code verbatim
        type_bonus   = 300 if (profile.has_code and profile.has_math) else \
                       200 if profile.has_code else \
                       200 if profile.has_math else 0
        s.max_tokens = min(1600 + int(c * 500) + type_bonus, 2800)
    else:  # questions
        s.max_tokens    = min(1200 + int(c * 400), 2000)
        s.content_limit = min(int(2000 + c * 1500), s.sub_chunk_size - 200)

    return s


# ════════════════════════════════════════════════════════════
#  PROMPT BUILDER
# ════════════════════════════════════════════════════════════

class PromptBuilder:

    SUMMARY_SYSTEM = (
        "You are a student who deeply understands the subject and explains it clearly to peers. "
        "Write summaries in plain, flowing English — like explaining to a friend, not a textbook. "
        "Build ideas gradually: start with the big picture, then go deeper step by step. "
        "Keep all technical terms, code, equations, and proofs exactly as they appear in the source. "
        "Only include what is in the source text — never add, never omit."
    )

    TRANSLATE_SYSTEM = (
        "انت طالب شاطر بتترجم ملخصات إنجليزي للعامية المصرية لصحابك يذاكروا منها. "
        "الأسلوب: عامية مصرية سلسة — مش ترجمة حرفية. "
        "المصطلحات التقنية الإنجليزية خليها زي ما هي. "
        "الأكواد والمعادلات والإثباتات الرياضية انقلها كما هي بدون أي تغيير. "
        "قايمة 'Key Exam Points' ترجمها: '⚠️ مهم للامتحان:'. "
        "بس اللي في الملخص — مش تزيد ولا تحذف."
    )

    JSON_SYSTEM = (
        "You are a precise JSON generator. "
        "Output ONLY valid JSON starting with { and ending with }."
    )

    # ── Universal summary prompt — model decides the format ──

    SUMMARY_FORMAT = (
        "Write the summary in this format — adapt the structure based on what is actually in the source:\n\n"
        "Start with a clear flowing explanation in plain English.\n"
        "Build gradually: explain the big idea first, then go into details.\n"
        "Connect ideas naturally: 'This means that...', 'Because of this...', 'Notice that...'\n"
        "If there is a comparison in the source, make it: 'The difference between X and Y is...'\n"
        "If there is an example in the source, include it: 'For example, in the source...'\n\n"
        "THEN — only include the sections that actually exist in the source:\n\n"
        "If the source contains CODE or PSEUDOCODE:\n"
        "**Code:**\n"
        "```\n[paste the code or pseudocode exactly — no changes at all]\n```\n"
        "[explain what the code does step by step]\n"
        "[state the time and space complexity if the source mentions it]\n\n"
        "If the source contains EQUATIONS or FORMULAS:\n"
        "**Equations:**\n"
        "[each equation exactly as it appears] — [what it means in plain English]\n\n"
        "If the source contains THEOREMS or PROOFS:\n"
        "**Theorem/Proof:**\n"
        "[the theorem statement exactly] — [what it means and why it matters]\n\n"
        "Always end with:\n"
        "Key Exam Points:\n"
        "- [point 1 — drawn from the source]\n"
        "- [point 2]\n"
        "- [at least 2, more if the source warrants it]"
    )

    @staticmethod
    def summary(text: str, profile: ChunkProfile,
                part_n: int = 1, total_parts: int = 1) -> str:
        part_note = (f"\n\n[Part {part_n} of {total_parts} — summarize only this part]"
                     if total_parts > 1 else "")

        # give the model a heads-up about what's in the text
        content_hints = []
        if profile.has_code:
            lang = f" ({profile.lang})" if profile.lang != "unknown" else ""
            content_hints.append(f"code/pseudocode{lang}")
        if profile.has_math:
            content_hints.append("equations/formulas/theorems")
        if profile.has_tables:
            content_hints.append("tables/comparisons")
        hint_line = (f"Note: this section contains {', '.join(content_hints)}. "
                     f"Preserve all of it verbatim.\n\n") if content_hints else ""

        return (
            f"You are summarizing a textbook section for students. "
            f"Write a clear English summary of the text below.\n\n"
            f"{hint_line}"
            f"{PromptBuilder.SUMMARY_FORMAT}\n\n"
            f"Strict rules:\n"
            f"- Only what is in the source — do not add or invent anything\n"
            f"- Paste all code, equations, and theorem statements verbatim — no paraphrasing\n"
            f"- Always end with 'Key Exam Points:' with at least 2 bullet points{part_note}\n\n"
            f"Source text:\n{'─'*60}\n{text}\n{'─'*60}\n\n"
            f"Write the summary now:"
        )

    @staticmethod
    def summary_fallback(text: str, attempt: int) -> str:
        if attempt == 2:
            return (
                f"Summarize this text clearly in plain English.\n\n"
                f"Include any code, equations, or theorems exactly as they appear.\n"
                f"End with:\nKey Exam Points:\n- [point]\n- [point]\n\n"
                f"Source:\n{text[:4000]}\n\nSummary:"
            )
        return (
            f"Write a 2-paragraph summary of this text.\n"
            f"End with:\nKey Exam Points:\n- ...\n- ...\n\n"
            f"Source:\n{text[:2000]}\n\nSummary:"
        )

    @staticmethod
    def synthesis(parts: list, profile: ChunkProfile) -> str:
        combined = "\n\n---\n\n".join(parts[:4])
        preserve_note = ""
        if profile.has_code or profile.has_math:
            preserve_note = (
                "\nIMPORTANT: Any code, equations, theorems, or proofs that appear in the "
                "sub-summaries MUST be preserved verbatim in the merged summary — do not paraphrase them.\n"
            )
        return (
            f"Merge these sub-summaries of the same textbook section into one cohesive summary.\n"
            f"{preserve_note}\n"
            f"Format: flowing explanation first, then any code/equations/theorems, then:\n"
            f"Key Exam Points:\n- [all important points from all parts combined]\n- [...]\n\n"
            f"Rule: only what is in the summaries below — do not add anything.\n\n"
            f"Sub-summaries:\n{combined[:3500]}\n\n"
            f"Write the merged summary now:"
        )

    @staticmethod
    def book_overview(snippets: str) -> str:
        return (
            f"You have summaries of sections from a textbook.\n"
            f"Write a 2-3 paragraph overview in plain English.\n"
            f"Tell the reader what the book covers and how the topics connect.\n"
            f"End with: 'Most important for exams: ...' — drawn from the summaries.\n"
            f"Only what is in the summaries — nothing extra.\n\n"
            f"{snippets[:4500]}\n\nWrite the overview now:"
        )

    @staticmethod
    def translate(chunk: str) -> str:
        return (
            f"ترجم الملخص الإنجليزي ده للعامية المصرية.\n\n"
            f"القواعد:\n"
            f"- عامية مصرية سلسة — مش ترجمة حرفية\n"
            f"- المصطلحات التقنية الإنجليزية خليها كما هي\n"
            f"- الأكواد والمعادلات والإثباتات انقلها كما هي بدون أي تغيير\n"
            f"- قايمة 'Key Exam Points' ترجمها: '⚠️ مهم للامتحان:' وخلي النقط كما هي\n"
            f"- بس اللي في الملخص — مش تزيد ولا تحذف\n\n"
            f"الملخص:\n{'─'*60}\n{chunk}\n{'─'*60}\n\n"
            f"اكتب الترجمة دلوقتي:"
        )

    @staticmethod
    def questions(text: str, label: str, profile: ChunkProfile,
                  lang_rule: str) -> str:
        # question type based on actual content, not pre-assumed category
        if profile.has_code and profile.has_math:
            hint = ("Include: (1) mcq on a key concept, (2) trace/apply an equation or code, "
                    "(3) analyze complexity or prove a property, (4) design or derive a solution.")
        elif profile.has_code:
            hint = ("Include: (1) mcq on syntax/output, (2) trace real code step by step, "
                    "(3) complexity analysis, (4) design a similar algorithm.")
        elif profile.has_math:
            hint = ("Include: (1) mcq on a definition or theorem, (2) apply a formula with numbers, "
                    "(3) prove a property or show a derivation, (4) compare two approaches.")
        else:
            hint = ("Include: (1) mcq on a concept, (2) explain and compare two ideas, "
                    "(3) analyze a process step by step, (4) design a solution.")

        marks = 13 if profile.complexity_score < 0.5 else 15
        m_hi  = "5" if marks == 15 else "4"
        src   = text[:getattr(profile, '_content_limit', 2500)]
        return (
            f"Output ONLY valid JSON starting with {{. {lang_rule}\n\n{hint}\n\n"
            f"Textbook section \"{label}\" "
            f"(complexity={profile.complexity_score:.2f}):\n{src}\n\n"
            f"Generate 4 exam questions using REAL content — no placeholders.\n\n"
            f'{{"section":"{label}","topic":"REAL topic","total_marks":{marks},"questions":['
            f'{{"id":1,"type":"mcq","bloom_level":"L1_remember","question":"REAL mcq?",'
            f'"options":["A) real","B) real","C) real","D) real"],"answer":"A/B/C/D",'
            f'"explanation":"why correct","marks":2,"common_mistake":"real error"}},'
            f'{{"id":2,"type":"concept","bloom_level":"L2_understand","question":"Explain REAL concept?",'
            f'"options":[],"answer":"full explanation","explanation":"key point","marks":3,"common_mistake":"real confusion"}},'
            f'{{"id":3,"type":"apply","bloom_level":"L4_analyze","question":"REAL application question.",'
            f'"options":[],"answer":"step-by-step answer","explanation":"why each step","marks":{m_hi},"common_mistake":"real error"}},'
            f'{{"id":4,"type":"design","bloom_level":"L6_create","question":"REAL design/derivation question.",'
            f'"options":[],"answer":"complete answer","explanation":"why it works","marks":{m_hi},"common_mistake":"real mistake"}}'
            f']}}'
        )

    @staticmethod
    def concept_map(topics: list) -> str:
        return (
            f"Output ONLY a JSON object starting with {{.\n\n"
            f"Textbook — {len(topics)} sections with their key concepts:\n"
            f"{json.dumps(topics, ensure_ascii=False)[:3500]}\n\n"
            f'{{"central_concepts":["c1","c2","c3","c4","c5"],'
            f'"learning_order":["first","then","then","then","finally"],'
            f'"exam_high_priority":["p1","p2","p3"],'
            f'"concept_map":[{{"concept":"name","depends_on":["prereq"],'
            f'"required_by":["consumer"],"difficulty":"beginner|intermediate|advanced",'
            f'"category":"data_structure|algorithm|math|theory|system|other"}}],'
            f'"study_plan":{{"week1":["foundations"],"week2":["intermediate"],'
            f'"week3":["advanced"],"week4":["exam prep"]}}}}'
        )


# ════════════════════════════════════════════════════════════
#  LLM INTERFACE
# ════════════════════════════════════════════════════════════

def call_model(messages: list, max_tokens: int = 1800, temp: float = 0.0,
               retries: int = 3, timeout: int = 300,
               system: str = None) -> Optional[str]:
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {LOCAL_API_KEY}"}
    sys_msg = system or PromptBuilder.SUMMARY_SYSTEM
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": sys_msg}] + messages
    payload = {"model": MODEL_NAME, "messages": messages,
               "temperature": temp, "max_tokens": max_tokens}
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(LLM_API_URL, headers=headers, json=payload,
                              timeout=timeout, verify=False)
            if r.status_code == 429:
                wait = 20 * attempt
                log(f"rate limit - waiting {wait}s", "warn")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                log(f"HTTP {r.status_code} (attempt {attempt}/{retries})", "warn")
                time.sleep(5 * attempt)
                continue
            content = r.json()["choices"][0]["message"]["content"]
            return content.strip() if content else None
        except requests.Timeout:
            log(f"timeout (attempt {attempt}/{retries})", "warn")
            time.sleep(8 * attempt)
        except Exception as e:
            log(f"error: {e}", "err")
            if attempt == retries:
                return None
            time.sleep(4)
    return None


# ════════════════════════════════════════════════════════════
#  JSON PARSER  (questions + concept map only)
# ════════════════════════════════════════════════════════════

@dataclass
class ParseResult:
    data:    Optional[dict] = None
    quality: float          = 0.0


def _repair_json(s: str) -> str:
    db = dbr = 0
    in_str = esc = False
    last = 0
    for i, ch in enumerate(s):
        if esc:    esc = False; continue
        if ch == '\\' and in_str: esc = True; continue
        if ch == '"': in_str = not in_str
        elif not in_str:
            if   ch == '{': db  += 1
            elif ch == '}': db  -= 1; last = i + 1 if db == 0 else last
            elif ch == '[': dbr += 1
            elif ch == ']': dbr -= 1
    res = s[:last] if last else s
    if in_str: res = res.rstrip(',\n ') + '"'
    return res.rstrip(',\n ') + ']' * max(0, dbr) + '}' * max(0, db)


def parse_json(raw: str, task: str = "questions") -> ParseResult:
    result = ParseResult()
    if not raw:
        return result
    text = raw.strip()
    text = re.sub(r"^```(?:json|python|text)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE).strip()
    s = text.find('{')
    if s == -1:
        return result
    text = text[s:]
    for candidate in [text,
                      re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text),
                      _repair_json(text)]:
        try:
            d = json.loads(candidate)
            result.data = d
            if task == "questions":
                qs = d.get("questions", [])
                real = sum(1 for q in qs
                           if "REAL" not in q.get("question", "")
                           and len(q.get("question", "")) > 20)
                result.quality = (min(len(qs)/4, 1.0)*0.5 +
                                  (real/len(qs)*0.5 if qs else 0))
            else:
                result.quality = 0.8
            return result
        except Exception:
            pass
    return result


# ════════════════════════════════════════════════════════════
#  SUMMARY QUALITY SCORER
# ════════════════════════════════════════════════════════════

# patterns that indicate "Key Exam Points" section exists
_EXAM_PATTERNS = re.compile(
    r'Key\s+Exam\s+Points|Important\s+for\s+exam|Exam\s+notes|'
    r'Remember\s*:|Key\s+points\s*:|Summary\s+points\s*:',
    re.IGNORECASE
)


def _score_summary(text: str, profile: ChunkProfile) -> float:
    if not text or len(text.strip()) < 60:
        return 0.0
    t = text.strip()

    # length relative to source
    expected = max(150, min(profile.char_count * 0.08, 1000))
    len_sc   = min(len(t) / expected, 1.0) * 0.40

    # has exam list (flexible pattern)
    exam_sc  = 0.30 if _EXAM_PATTERNS.search(t) else 0.0

    # code/equations preserved if source had them
    preserve_sc = 0.0
    if profile.has_code and ('```' in t or 'Code:' in t):
        preserve_sc += 0.10
    if profile.has_math and ('Equations:' in t or '$' in t or 'Theorem' in t or 'Proof' in t):
        preserve_sc += 0.10
    # if source has neither, give full preserve score
    if not profile.has_code and not profile.has_math:
        preserve_sc = 0.20

    # not starting with model preamble
    clean_sc = 0.10 if not re.match(
        r'^(Sure|Of course|Here|Certainly|Below|The following)',
        t, re.IGNORECASE
    ) else 0.0

    return min(len_sc + exam_sc + preserve_sc + clean_sc, 1.0)


def _clean(raw: str) -> str:
    if not raw:
        return ""
    t = raw.strip()
    t = re.sub(r"^```[\w]*\n?", "", t)
    t = re.sub(r"\n?```$",      "", t)
    t = re.sub(
        r"^(Sure[,!]?\s*|Of course[,!]?\s*|Here(?:'s| is)[,:]?\s*|"
        r"Certainly[,!]?\s*|Below is\s*|The following is\s*|"
        r"بالتأكيد[،,]?\s*|طبعاً[،,]?\s*|حاضر[،,]?\s*)",
        "", t, flags=re.IGNORECASE
    )
    return t.strip()


# ════════════════════════════════════════════════════════════
#  POST-PROCESSOR — ensure exam list exists
# ════════════════════════════════════════════════════════════

def _ensure_exam_list(text: str, source: str, profile: ChunkProfile) -> str:
    """
    If exam list is missing, try via model call.
    Fallback extracts meaningful sentences from the summary — not just keywords.
    """
    if _EXAM_PATTERNS.search(text):
        return text

    log("exam list missing - adding", "warn")
    raw = call_model(
        [{"role": "user", "content": (
            f"This summary needs a 'Key Exam Points' section.\n"
            f"Add 3-5 bullet points at the end.\n"
            f"Each point must be a complete, meaningful statement — not just a term.\n"
            f"Draw only from what is already in the summary below.\n\n"
            f"Summary:\n{text}\n\n"
            f"Rewrite the full summary with 'Key Exam Points:' appended at the end:"
        )}],
        max_tokens=min(len(text)//2 + 500, 1000), temp=0.0, retries=1
    )
    result = _clean(raw)
    if result and _EXAM_PATTERNS.search(result) and len(result) > len(text) * 0.5:
        return result

    # fallback: extract complete sentences from the summary that sound important
    important_pat = re.compile(
        r'[A-Z][^.!?\n]{20,}(?:is|are|means|defined|works|used|complexity|O\(|'
        r'must|cannot|always|never|difference|unlike|better|worse)[^.!?\n]*[.!?]',
        re.IGNORECASE)
    candidates = important_pat.findall(text)
    if not candidates:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        candidates = [s.strip() for s in sentences
                      if len(s.strip()) > 40
                      and re.search(
                          r'\b(?:time|space|complexity|O\(|must|cannot|'
                          r'difference|important|key|note|always|never)\b',
                          s, re.IGNORECASE)][:5]

    if candidates:
        points = "\n".join(f"- {c.strip()}" for c in candidates[:5])
        return text + f"\n\nKey Exam Points:\n{points}"

    return text + "\n\nKey Exam Points:\n- Review this section carefully for the exam"


# ════════════════════════════════════════════════════════════
#  ADAPTIVE CHUNKER
# ════════════════════════════════════════════════════════════

def split_adaptive(text: str, strategy: ProcessingStrategy) -> list:
    """
    Split text at natural boundaries.
    Critical: never split inside a fenced code block or a $$ math block.
    """
    if len(text) <= strategy.sub_chunk_size:
        return [text]

    # pre-compute protected zones: ranges that must not be cut through
    protected_ranges = []
    for pat in [r'```[\s\S]+?```',     # fenced code blocks
                r'\$\$[\s\S]+?\$\$']:  # display math $$...$$
        for m in re.finditer(pat, text, re.IGNORECASE):
            protected_ranges.append((m.start(), m.end()))
    protected_ranges.sort(key=lambda x: x[0])

    def is_safe_pos(pos: int) -> bool:
        """True if position is not inside a protected block."""
        return not any(start < pos < end for start, end in protected_ranges)

    def safe_next_pos(pos: int) -> int:
        """If pos lands inside a protected block, jump past it."""
        for start, end in protected_ranges:
            if start <= pos < end:
                return end
        return pos

    chunks, pos = [], 0
    while pos < len(text):
        end = pos + strategy.sub_chunk_size
        if end >= len(text):
            chunks.append(text[pos:])
            break

        # try to cut at a natural boundary that's not inside a protected block
        cut = -1
        for sep in ['\n\n', '.\n', '. ', '\n']:
            candidate = text.rfind(sep, pos, end)
            if candidate != -1 and is_safe_pos(candidate):
                cut = candidate
                break

        if cut == -1:
            # no safe cut found in window — extend past any protected block
            cut = end
            for start, finish in protected_ranges:
                if start < cut <= finish:
                    cut = finish
                    break

        chunks.append(text[pos:cut].strip())
        # next pos: overlap back from cut, but never land inside a protected block
        next_pos = max(pos + 1, cut - strategy.overlap)
        pos = safe_next_pos(next_pos)

        if len(chunks) >= 12:
            chunks.append(text[pos:])
            break

    return [c for c in chunks if c.strip()]


# ════════════════════════════════════════════════════════════
#  TEXT NORMALIZER
# ════════════════════════════════════════════════════════════

class TextNormalizer:
    _MATH_MAP = {
        '∑':r'\sum','∏':r'\prod','∫':r'\int','∂':r'\partial','∇':r'\nabla',
        '∞':r'\infty','∈':r'\in','∉':r'\notin','⊂':r'\subset','⊃':r'\supset',
        '∪':r'\cup','∩':r'\cap','∧':r'\land','∨':r'\lor','¬':r'\neg',
        '∀':r'\forall','∃':r'\exists','≤':r'\leq','≥':r'\geq','≠':r'\neq',
        '≈':r'\approx','≡':r'\equiv','→':r'\rightarrow','⇒':r'\Rightarrow',
        '⇔':r'\Leftrightarrow','×':r'\times','÷':r'\div','±':r'\pm','√':r'\sqrt',
        'α':r'\alpha','β':r'\beta','γ':r'\gamma','δ':r'\delta','ε':r'\epsilon',
        'θ':r'\theta','λ':r'\lambda','μ':r'\mu','π':r'\pi','σ':r'\sigma',
        'φ':r'\phi','ω':r'\omega','Σ':r'\Sigma','Δ':r'\Delta','Ω':r'\Omega',
    }
    _OCR = [
        (r'\bO\s*\(\s*n\s*\)',              'O(n)'),
        (r'\bO\s*\(\s*1\s*\)',              'O(1)'),
        (r'\bO\s*\(\s*n\s*log\s*n\s*\)',    'O(n log n)'),
        (r'\bO\s*\(\s*n\s*2\s*\)',          'O(n²)'),
        (r'\bO\s*\(\s*2\s*n\s*\)',          'O(2ⁿ)'),
        (r'\bO\s*\(\s*log\s*n\s*\)',        'O(log n)'),
        (r'(\w)-\n(\w)',                    r'\1\2'),
        (r'([a-z])\n([a-z])',               r'\1 \2'),
    ]

    @classmethod
    def normalize(cls, text: str) -> str:
        text = unicodedata.normalize('NFKC', text)
        for p, r in cls._OCR:
            text = re.sub(p, r, text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        # protect existing math before substituting unicode
        protected = {}
        def protect(m):
            k = f"__M{len(protected)}__"
            protected[k] = m.group(0)
            return k
        text = re.sub(r'\$\$[\s\S]+?\$\$|\$[^$\n]+\$', protect, text)
        for uni, latex in cls._MATH_MAP.items():
            if uni in text:
                text = text.replace(uni, f'${latex}$')
        for k, v in protected.items():
            text = text.replace(k, v)
        text = cls._fix_code_blocks(text)
        text = cls._fix_tables(text)
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE)
        return text.strip()

    @classmethod
    def _fix_code_blocks(cls, text: str) -> str:
        lines, result, in_code = text.split('\n'), [], False
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code:
                    in_code = True
                    if not line.strip()[3:].strip():
                        look = '\n'.join(lines[i+1:i+8])
                        if   re.search(r'SELECT\s|INSERT\s|mysql>', look, re.I):  line = '```sql'
                        elif re.search(r'def\s+\w+|import\s+\w+', look):          line = '```python'
                        elif re.search(r'#include|int\s+main', look):             line = '```cpp'
                        elif re.search(r'public\s+class', look):                  line = '```java'
                        elif re.search(r'algorithm|procedure', look, re.I):       line = '```pseudocode'
                else:
                    in_code = False
            result.append(line)
        return '\n'.join(result)

    @classmethod
    def _fix_tables(cls, text: str) -> str:
        lines, result = text.split('\n'), []
        for i, line in enumerate(lines):
            result.append(line)
            if (line.startswith('|') and i+1 < len(lines)
                    and lines[i+1].startswith('|')
                    and not re.match(r'^\|[\s\-|]+\|$', lines[i+1])):
                cols = len(re.findall(r'\|', line)) - 1
                result.append('|' + '---|' * cols)
        return '\n'.join(result)

    @classmethod
    def extract_structure(cls, text: str) -> dict:
        chapters, sections = [], []
        ch_pat = re.compile(
            r'^(?:chapter|ch\.?)\s+(\d+|[ivxlc]+)[:\s\u2014\u2013-]*(.+)$',
            re.MULTILINE | re.IGNORECASE)
        for m in ch_pat.finditer(text):
            chapters.append({"num": m.group(1),
                             "title": m.group(2).strip()[:80],
                             "pos": m.start()})
        for m in re.finditer(r'^#{2,3}\s+(.+)$', text, re.MULTILINE):
            sections.append({"title": m.group(1).strip()[:80], "pos": m.start()})
        return {"chapters": chapters, "sections": sections}


# ════════════════════════════════════════════════════════════
#  AGENT 1 — EXTRACTION
# ════════════════════════════════════════════════════════════

def run_extraction(pdf_path: str, out_dir: str) -> str:
    log("sending PDF to Marker API...")
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(
                f"{MARKER_API_URL}/extract",
                files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
                timeout=600)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Cannot connect to Marker at {MARKER_API_URL}")
    if r.status_code != 200:
        raise RuntimeError(f"Marker error {r.status_code}: {r.text[:200]}")

    raw    = r.json().get("markdown", "")
    clean  = TextNormalizer.normalize(raw)
    struct = TextNormalizer.extract_structure(clean)
    log(f"extracted {len(clean):,} chars | "
        f"{len(struct['chapters'])} chapters | {len(struct['sections'])} sections", "ok")

    out = os.path.join(out_dir, "EXTRACTED.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {Path(pdf_path).stem}\n\n*{len(clean):,} chars*\n\n")
        if struct["chapters"]:
            f.write("## Structure\n")
            for ch in struct["chapters"][:30]:
                f.write(f"- Chapter {ch['num']}: {ch['title']}\n")
            f.write("\n---\n\n")
        f.write(clean)
    with open(os.path.join(out_dir, "STRUCTURE.json"), "w", encoding="utf-8") as f:
        json.dump(struct, f, ensure_ascii=False, indent=2)
    log(f"saved -> {out}", "ok")
    return out


def _split_into_sections(text: str, chars_per_page: int = 4000) -> dict:
    """Split extracted text into processable sections."""

    # 1: Chapter headings
    pat = re.compile(
        r'^(?:#{1,2}\s+)?(?:chapter|ch\.?)\s+(\d+)[:\s\u2014\u2013-]*(.+)$',
        re.MULTILINE | re.IGNORECASE)
    ms = list(pat.finditer(text))
    if len(ms) >= 2:
        pages = {}
        for i, m in enumerate(ms):
            num = int(m.group(1)) if m.group(1).isdigit() else i + 1
            end = ms[i+1].start() if i+1 < len(ms) else len(text)
            c   = text[m.start():end].strip()
            if len(c) > 300: pages[num] = c
        if pages: log(f"detected {len(pages)} chapters"); return pages

    # 2: Explicit page markers
    pat2 = re.compile(
        r'(?:<!-+\s*[Pp]age\s*(\d+)\s*-+>|^#{1,3}\s*[Pp]age\s+(\d+)\s*$)',
        re.MULTILINE)
    ms2 = list(pat2.finditer(text))
    if ms2:
        pages = {}
        for i, m in enumerate(ms2):
            num = int(m.group(1) or m.group(2))
            end = ms2[i+1].start() if i+1 < len(ms2) else len(text)
            c   = text[m.end():end].strip()
            if c: pages[num] = c
        if pages: log(f"detected {len(pages)} page markers"); return pages

    # 3: Marker API image markers  _page_N_
    img_ms = list(re.finditer(r"!\[.*?\]\(_page_(\d+)_", text))
    if img_ms:
        pts, seen = [], set()
        for m in img_ms:
            pg = int(m.group(1))
            if pg not in seen:
                seen.add(pg)
                ls = text.rfind("\n", 0, m.start())
                pts.append((pg, ls if ls != -1 else m.start()))
        pts.sort(key=lambda x: x[1])
        pages = {}
        for i, (pg, pos) in enumerate(pts):
            end = pts[i+1][1] if i+1 < len(pts) else len(text)
            c   = text[pos:end].strip()
            if c and len(c) > 100: pages[pg] = c
        if pages: log(f"detected {len(pages)} image-marker pages"); return pages

    # 4: H2 sections
    hs = list(re.finditer(r"^## .+$", text, re.MULTILINE))
    if len(hs) >= 2:
        pages = {}
        for i, m in enumerate(hs):
            end = hs[i+1].start() if i+1 < len(hs) else len(text)
            c   = text[m.start():end].strip()
            if len(c) > 200: pages[i+1] = c
        if pages: log(f"detected {len(pages)} H2 sections"); return pages

    # 5: H1 sections
    hs1 = list(re.finditer(r"^# .+$", text, re.MULTILINE))
    if len(hs1) >= 2:
        pages = {}
        for i, m in enumerate(hs1):
            end = hs1[i+1].start() if i+1 < len(hs1) else len(text)
            c   = text[m.start():end].strip()
            if len(c) > 200: pages[i+1] = c
        if pages: log(f"detected {len(pages)} H1 sections"); return pages

    # 6: Horizontal rules
    parts = [p.strip() for p in re.split(r'\n---+\n', text) if len(p.strip()) > 100]
    if len(parts) > 1:
        log(f"detected {len(parts)} separator sections")
        return {i+1: p for i, p in enumerate(parts)}

    # 7: Auto-split at natural boundaries
    body, pg, pages = text.strip(), 1, {}
    while body:
        if len(body) <= chars_per_page:
            pages[pg] = body
            break
        cut = body.rfind('\n\n', 0, chars_per_page)
        if cut == -1: cut = body.rfind('\n', 0, chars_per_page)
        if cut == -1: cut = chars_per_page
        pages[pg] = body[:cut].strip()
        body = body[cut:].strip()
        pg  += 1
    log(f"auto-split -> {len(pages)} sections")
    return pages


def _chunk_text(pages: dict, keys: list) -> str:
    parts = [f"<!-- Section {k} -->\n\n{pages[k]}" for k in keys if k in pages]
    return "\n\n---\n\n".join(parts)


# ════════════════════════════════════════════════════════════
#  AGENT 2 — SUMMARIZATION
# ════════════════════════════════════════════════════════════

_QUALITY_THRESHOLD = 0.45


def _summarize_subchunk(text: str, source: str, profile: ChunkProfile,
                         strategy: ProcessingStrategy,
                         part_n: int, total: int) -> str:
    prompt = PromptBuilder.summary(text, profile, part_n, total)
    best, best_q = "", 0.0

    for attempt, (use_fb, temp) in enumerate(
            [(False, 0.0), (False, 0.2), (True, 0.1)], 1):
        p   = PromptBuilder.summary_fallback(text, attempt) if use_fb else prompt
        raw = call_model([{"role": "user", "content": p}],
                         max_tokens=strategy.max_tokens, temp=temp, retries=1)
        out = _clean(raw)
        q   = _score_summary(out, profile)
        if q > best_q:
            best, best_q = out, q
        if out and q >= _QUALITY_THRESHOLD:
            break
        if attempt < 3:
            log(f"  part {part_n}: q={q:.2f} -> retry #{attempt+1}", "warn")

    result = best if best.strip() else "[Processing failed for this section]"
    return _ensure_exam_list(result, source, profile)


def _merge_subchunks(parts: list, profile: ChunkProfile) -> str:
    valid = [s for s in parts if s and "Processing failed" not in s]
    if not valid:
        return "[Processing failed]"
    if len(valid) == 1:
        return valid[0]
    raw    = call_model(
        [{"role": "user", "content": PromptBuilder.synthesis(valid, profile)}],
        max_tokens=1000, temp=0.0)
    merged = _clean(raw)
    if merged and len(merged.strip()) > 100:
        return _ensure_exam_list(merged, "\n\n".join(valid), profile)
    return "\n\n".join(valid)


def summarize_chunk(chunk_text: str, label: str) -> dict:
    profile  = profile_chunk(chunk_text)
    strategy = decide_strategy(profile, "summarize")

    content_flags = []
    if profile.has_code: content_flags.append(f"code({profile.lang})")
    if profile.has_math: content_flags.append("math")
    if profile.has_tables: content_flags.append("tables")
    log(f"  [{' + '.join(content_flags) or 'text'} | "
        f"c={profile.complexity_score:.2f} | {profile.size_bucket} | "
        f"tokens={strategy.max_tokens}]")

    subs  = split_adaptive(chunk_text, strategy)
    total = len(subs)
    if total > 1:
        log(f"  -> {total} sub-chunks", "progress")

    results = []
    for i, sub in enumerate(subs, 1):
        sub_p = profile_chunk(sub)
        if total > 1:
            log(f"  -> sub {i}/{total} ({len(sub):,} chars)", "progress")
        results.append(_summarize_subchunk(sub, chunk_text, sub_p, strategy, i, total))
        if i < total:
            time.sleep(0.3)

    return {
        "section":       label,
        "summary_text":  _merge_subchunks(results, profile),
        "_has_code":     profile.has_code,
        "_has_math":     profile.has_math,
        "_complexity":   round(profile.complexity_score, 2),
        "_sub_count":    total,
        "_raw_terms":    list(dict.fromkeys(
            re.findall(r'\b[A-Z][a-zA-Z]{3,}(?:\s[A-Z][a-zA-Z]+)?\b', chunk_text)
        ))[:8],
    }


def run_summarization(pages: dict, keys: list, out_dir: str,
                       book_name: str, chunk_size: int,
                       do_overview: bool = True) -> tuple:
    summaries, failed = [], 0
    n = (len(keys) + chunk_size - 1) // chunk_size

    for idx, start in enumerate(range(0, len(keys), chunk_size)):
        batch      = keys[start:start+chunk_size]
        label      = f"Sections {batch[0]}-{batch[-1]}" if len(batch)>1 else f"Section {batch[0]}"
        chunk_text = _chunk_text(pages, batch)
        if not chunk_text.strip():
            continue

        log(f"[{idx+1}/{n}] {label} ({len(chunk_text):,} chars)", "progress")
        res = summarize_chunk(chunk_text, label)
        summaries.append(res)

        txt = res.get("summary_text", "")
        if not txt or "Processing failed" in txt:
            failed += 1
            log(f"failed: {label}", "warn")
        else:
            flags = []
            if res.get("_has_code"):  flags.append("code")
            if res.get("_has_math"):  flags.append("math")
            sub = f" ({res['_sub_count']} parts)" if res.get("_sub_count",1)>1 else ""
            log(f"{label}{sub} [{'/'.join(flags) or 'text'}] | {len(txt):,} chars", "ok")

        if start + chunk_size < len(keys):
            time.sleep(0.3)

    log(f"{failed}/{len(summaries)} failed" if failed else "all sections done", "warn" if failed else "ok")

    # book overview
    overview = None
    if do_overview and len(summaries) >= 2:
        log("writing book overview...", "progress")
        snippets = "\n\n---\n\n".join(
            f"[{s['section']}]\n{s.get('summary_text','')[:300]}"
            for s in summaries if s.get("summary_text"))
        raw      = call_model(
            [{"role":"user","content":PromptBuilder.book_overview(snippets)}],
            max_tokens=600, temp=0.1)
        overview = _clean(raw)
        log("overview done" if overview else "overview failed",
            "ok" if overview else "warn")

    out  = os.path.join(out_dir, "SUMMARY.md")
    txts = []
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Study Summary\n\n")
        f.write(f"*{len(keys)} sections | v12.0*\n\n")
        f.write("> Read the explanation first to understand the concept,\n")
        f.write("> then review **Key Exam Points** before your exam.\n\n---\n\n")
        if overview:
            f.write("## What is this book about?\n\n")
            f.write(overview + "\n\n---\n\n")
            txts.append(overview)
        f.write("## Detailed Summaries\n\n")
        for s in summaries:
            txt = s.get("summary_text","").strip()
            f.write(f"### {s['section']}\n\n")
            if s.get("_sub_count",1) > 1:
                f.write(f"*Merged from {s['_sub_count']} parts*\n\n")
            f.write((txt if txt else "*Processing failed.*") + "\n\n---\n\n")
            txts.append(txt)

    log(f"saved -> {out}", "ok")
    return out, "\n\n".join(txts), summaries


# ════════════════════════════════════════════════════════════
#  AGENT 3 — QUESTIONS
# ════════════════════════════════════════════════════════════

def run_questions(pages: dict, keys: list, out_dir: str,
                   book_name: str, chunk_size: int, lang: str = "auto") -> str:
    lang_rule  = {"ar":"Write ALL in Arabic.","en":"Write ALL in English.",
                  "auto":"Use same language as content."}.get(lang,"Use same language as content.")
    all_chunks = []
    total_q = total_m = failed = 0
    n = (len(keys) + chunk_size - 1) // chunk_size

    for idx, start in enumerate(range(0, len(keys), chunk_size)):
        batch      = keys[start:start+chunk_size]
        label      = f"sections {batch[0]}-{batch[-1]}" if len(batch)>1 else f"section {batch[0]}"
        chunk_text = _chunk_text(pages, batch)
        if not chunk_text.strip():
            continue

        profile  = profile_chunk(chunk_text)
        strategy = decide_strategy(profile, "questions")
        log(f"[{idx+1}/{n}] questions: {label}...")

        subs, results = split_adaptive(chunk_text, strategy), []
        for si, sub in enumerate(subs):
            sub_p = profile_chunk(sub)
            sub_p.__dict__['_content_limit'] = strategy.content_limit
            lbl   = f"{label} p{si+1}" if len(subs)>1 else label
            for temp in [0.0, 0.15]:
                raw = call_model(
                    [{"role":"user","content":PromptBuilder.questions(sub, lbl, sub_p, lang_rule)}],
                    max_tokens=strategy.max_tokens, temp=temp,
                    system=PromptBuilder.JSON_SYSTEM)
                res = parse_json(raw, "questions")
                if res.data and res.data.get("questions") and res.quality > 0.3:
                    results.append(res.data)
                    break
                log(f"  sub {si+1} q={res.quality:.2f} -> retry","warn")
            else:
                log(f"  sub {si+1} failed","warn")
                if raw:
                    with open(os.path.join(out_dir,f"_qraw_{batch[0]}_{si}.txt"),
                              "w",encoding="utf-8") as fb:
                        fb.write(raw)

        if results:
            if len(results) == 1:
                merged = results[0]
            else:
                merged = {"section":label,"topic":results[0].get("topic",label),
                          "questions":[],"total_marks":0}
                for qid, q in enumerate((q for r in results for q in r.get("questions",[])),1):
                    q["id"] = qid
                    merged["questions"].append(q)
                    merged["total_marks"] += q.get("marks",0)
                merged["questions"]   = merged["questions"][:6]
                merged["total_marks"] = sum(q.get("marks",0) for q in merged["questions"])
            all_chunks.append(merged)
            qc = len(merged["questions"]); mk = merged.get("total_marks",0)
            total_q += qc; total_m += mk
            log(f"{qc} questions | {mk} marks","ok")
        else:
            failed += 1
            log(f"failed: {label}","warn")

        if start + chunk_size < len(keys):
            time.sleep(0.3)

    icons  = {"mcq":"🔤","concept":"💡","apply":"🔍","trace":"🔍","debug":"🐛",
               "design":"🏗","prove":"📐","calculate":"🧮","compare":"⚖️"}
    blooms = {"L1_remember":"🔵","L2_understand":"🟢","L3_apply":"🟡",
               "L4_analyze":"🟠","L5_evaluate":"🔴","L6_create":"🟣"}

    out = os.path.join(out_dir, "QUESTIONS.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Question Bank\n\n")
        f.write(f"*{total_q} questions | {total_m} marks | v12.0*\n\n---\n\n")
        for ch in all_chunks:
            if not ch.get("questions"): continue
            mk = ch.get("total_marks", sum(q.get("marks",0) for q in ch["questions"]))
            f.write(f"### {ch.get('section','')} — {ch.get('topic','')}\n")
            f.write(f"*{mk} marks | {len(ch['questions'])} questions*\n\n")
            for q in ch["questions"]:
                f.write(f"**Q{q['id']}** {icons.get(q.get('type',''),'❓')} "
                        f"{blooms.get(q.get('bloom_level',''),'⚪')} "
                        f"`{q.get('marks','')}m`\n\n")
                f.write(f"> {q['question']}\n\n")
                for opt in q.get("options",[]): f.write(f"> {opt}\n")
                if q.get("options"): f.write("\n")
                if q.get("answer"):
                    body = f"\n**Answer:** {str(q['answer']).strip()}\n"
                    if q.get("explanation"):
                        body += f"\n**Explanation:** {str(q['explanation']).strip()}\n"
                    if q.get("common_mistake"):
                        body += f"\n**Common mistake:** {str(q['common_mistake']).strip()}\n"
                    f.write(f"<details><summary>Model Answer</summary>{body}</details>\n\n")
            f.write("---\n\n")

    log(f"saved -> {out} ({total_q} questions, {total_m} marks)","ok")
    return out


# ════════════════════════════════════════════════════════════
#  AGENT 4 — TRANSLATION  (English -> Egyptian Arabic)
# ════════════════════════════════════════════════════════════

def _split_for_translation(text: str, max_chars: int = 3000) -> list:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text)
            break
        # cut at section boundaries first
        cut = -1
        for sep in ['\n### ', '\n## ', '\n\n', '\n']:
            cut = text.rfind(sep, 0, max_chars)
            if cut != -1: break
        if cut == -1: cut = max_chars
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    return [c for c in chunks if c.strip()]


def run_translation(summary_text: str, out_dir: str, book_name: str) -> str:
    if not summary_text.strip():
        out = os.path.join(out_dir, "TRANSLATED.md")
        with open(out,"w",encoding="utf-8") as f:
            f.write(f"# {book_name} - ملخص بالعامية المصرية\n\n*لا يوجد محتوى.*\n")
        return out

    chunks = _split_for_translation(summary_text, max_chars=3000)
    log(f"translating {len(chunks)} chunks...")
    parts  = []

    for i, chunk in enumerate(chunks, 1):
        log(f"  chunk {i}/{len(chunks)} ({len(chunk):,} chars)", "progress")
        raw        = call_model(
            [{"role":"user","content":PromptBuilder.translate(chunk)}],
            max_tokens=2400, temp=0.0, retries=2, timeout=580,
            system=PromptBuilder.TRANSLATE_SYSTEM)
        translated = _clean(raw)

        if translated and len(translated.strip()) > 50:
            # verify code blocks survived — re-inject if lost
            for code in re.findall(r'```[\s\S]+?```', chunk):
                if code not in translated:
                    log(f"  chunk {i}: code block lost - restoring","warn")
                    translated += f"\n\n{code}"
            parts.append(translated)
        else:
            log(f"  chunk {i}: translation failed - keeping English","warn")
            parts.append(chunk)

        if i < len(chunks):
            time.sleep(0.3)

    out = os.path.join(out_dir, "TRANSLATED.md")
    with open(out,"w",encoding="utf-8") as f:
        f.write(f"# {book_name} - ملخص بالعامية المصرية\n\n")
        f.write(f"*v12.0 | المصطلحات التقنية بالإنجليزي | الأكواد والمعادلات محفوظة*\n\n---\n\n")
        f.write("\n\n".join(parts))
    log(f"saved -> {out}","ok")
    return out


# ════════════════════════════════════════════════════════════
#  AGENT 5 — CONCEPT MAP
# ════════════════════════════════════════════════════════════

def run_concept_map(summaries: list, out_dir: str, book_name: str) -> Optional[str]:
    if len(summaries) < 2:
        return None
    log("building concept map...")

    topics = [{"section":  s.get("section",""),
               "concepts": s.get("_raw_terms",[])}
              for s in summaries]

    raw    = call_model(
        [{"role":"user","content":PromptBuilder.concept_map(topics)}],
        max_tokens=1200, temp=0.0, system=PromptBuilder.JSON_SYSTEM)
    result = parse_json(raw, "concept_map")
    data   = result.data
    if not data:
        log("concept map failed","warn")
        return None

    out = os.path.join(out_dir, "CONCEPT_MAP.md")
    with open(out,"w",encoding="utf-8") as f:
        f.write(f"# {book_name} — Concept Map\n\n")
        if data.get("central_concepts"):
            f.write("## Central Concepts\n")
            for c in data["central_concepts"]: f.write(f"- **{c}**\n")
            f.write("\n")
        if data.get("learning_order"):
            f.write("## Recommended Learning Order\n")
            for i,c in enumerate(data["learning_order"],1): f.write(f"{i}. {c}\n")
            f.write("\n")
        if data.get("exam_high_priority"):
            f.write("## High Priority for Exams\n")
            for c in data["exam_high_priority"]: f.write(f"- **{c}**\n")
            f.write("\n")
        if data.get("study_plan"):
            f.write("## Study Plan\n")
            for week, concepts in data["study_plan"].items():
                f.write(f"**{week}:** {', '.join(concepts)}\n\n")
        if data.get("concept_map"):
            f.write("## Concept Dependencies\n\n")
            f.write("| Concept | Category | Difficulty | Depends On | Required By |\n")
            f.write("|---------|----------|------------|------------|-------------|\n")
            for item in data["concept_map"]:
                deps   = ", ".join(item.get("depends_on",[])[:3])
                req_by = ", ".join(item.get("required_by",[])[:2])
                f.write(f"| **{item.get('concept','')}** | {item.get('category','')} | "
                        f"{item.get('difficulty','')} | {deps} | {req_by} |\n")
    log(f"saved -> {out}","ok")
    return out


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    global MARKER_API_URL, LLM_API_URL

    parser = argparse.ArgumentParser(description="PDF Agent Suite v12.0 - Universal")
    parser.add_argument("--pdf",         required=True,  help="path to PDF")
    parser.add_argument("--mode",        default="all",
                        choices=["extract","summarize","translate","questions",
                                 "concept-map","all"])
    parser.add_argument("--lang",        default="auto", choices=["ar","en","auto"],
                        help="question language")
    parser.add_argument("--page-from",   type=int, default=None)
    parser.add_argument("--page-to",     type=int, default=None)
    parser.add_argument("--chunk-size",  type=int, default=CHUNK_SIZE,
                        help=f"pages per chunk (default {CHUNK_SIZE}, use 3-4 for dense)")
    parser.add_argument("--no-overview", action="store_true")
    parser.add_argument("--output-dir",  default=OUTPUT_DIR)
    parser.add_argument("--marker-url",  default=MARKER_API_URL)
    parser.add_argument("--llm-url",     default=LLM_API_URL)
    args = parser.parse_args()

    MARKER_API_URL = args.marker_url.rstrip('/')
    LLM_API_URL    = args.llm_url

    if not os.path.exists(args.pdf):
        print(f"File not found: {args.pdf}"); sys.exit(1)

    name       = Path(args.pdf).stem
    out_dir    = os.path.join(args.output_dir, name)
    chunk_size = args.chunk_size
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*62}")
    print(f"  PDF Agent Suite v12.0 — Universal Content Handling")
    print(f"{'='*62}")
    print(f"  PDF       : {args.pdf}")
    print(f"  Output    : {out_dir}")
    print(f"  Mode      : {args.mode} | Lang: {args.lang} | Chunk: {chunk_size}")
    print(f"  Sub-chunk : max {MAX_CHARS_PER_SUB:,} chars")
    print(f"  Model     : {MODEL_NAME}")
    print(f"  LLM       : {LLM_API_URL}")
    print(f"{'='*62}\n")

    extracted  = os.path.join(out_dir, "EXTRACTED.md")
    pages_dict, page_keys, summaries, summary_text = {}, [], [], ""

    # Agent 1
    if args.mode in ("extract","summarize","translate","questions","concept-map","all"):
        print("--- AGENT 1: EXTRACTION ---")
        if not os.path.exists(extracted):
            run_extraction(args.pdf, out_dir)
        else:
            log("EXTRACTED.md found - skipping")

        full   = open(extracted, encoding="utf-8").read()
        pages_dict = _split_into_sections(full)
        all_k  = sorted(pages_dict.keys())
        page_keys = [k for k in all_k
                     if (args.page_from is None or k >= args.page_from)
                     and (args.page_to   is None or k <= args.page_to)]
        if not page_keys:
            print("No sections found!"); sys.exit(1)

        total_c = sum(len(pages_dict[k]) for k in page_keys)
        avg_c   = total_c // len(page_keys)
        fp      = profile_chunk(full)
        flags   = []
        if fp.has_code: flags.append(f"code({fp.lang})")
        if fp.has_math: flags.append("math")
        if fp.has_tables: flags.append("tables")
        density = "DENSE" if avg_c > 5000 else ("NORMAL" if avg_c > 2000 else "LIGHT")

        print(f"\n  Document : {len(page_keys)} sections | {total_c:,} chars")
        print(f"  Avg/sect : {avg_c:,} chars [{density}]")
        print(f"  Content  : {', '.join(flags) or 'text'} | complexity={fp.complexity_score:.2f}")
        print()

    # Agent 2
    if args.mode in ("summarize","translate","all","concept-map"):
        print("--- AGENT 2: SUMMARIZATION (English) ---")
        _, summary_text, summaries = run_summarization(
            pages_dict, page_keys, out_dir, name, chunk_size,
            do_overview=not args.no_overview)
        print()

    # Agent 3
    if args.mode in ("questions","all"):
        print("--- AGENT 3: QUESTIONS ---")
        run_questions(pages_dict, page_keys, out_dir, name, chunk_size, args.lang)
        print()

    # Agent 4
    if args.mode in ("translate","all"):
        print("--- AGENT 4: TRANSLATION (Egyptian Arabic) ---")
        if not summary_text:
            sp = os.path.join(out_dir, "SUMMARY.md")
            if os.path.exists(sp):
                summary_text = open(sp, encoding="utf-8").read()
            else:
                print("Run --mode summarize first"); sys.exit(1)
        run_translation(summary_text, out_dir, name)
        print()

    # Agent 5
    if args.mode in ("concept-map","all"):
        print("--- AGENT 5: CONCEPT MAP ---")
        if not summaries:
            for start in range(0, len(page_keys), chunk_size):
                batch = page_keys[start:start+chunk_size]
                lbl   = f"sections {batch[0]}-{batch[-1]}" if len(batch)>1 else f"section {batch[0]}"
                ct    = _chunk_text(pages_dict, batch)
                terms = list(dict.fromkeys(
                    re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', ct)))[:8]
                summaries.append({"section":lbl,"summary_text":"","_raw_terms":terms})
        run_concept_map(summaries, out_dir, name)
        print()

    # Done
    print(f"{'='*62}")
    print(f"  Done!  Output: {out_dir}/")
    print(f"{'='*62}")
    for fname, desc in [
        ("EXTRACTED.md",   "raw extracted text"),
        ("SUMMARY.md",     "English summary"),
        ("QUESTIONS.md",   "exam questions"),
        ("TRANSLATED.md",  "Egyptian Arabic translation"),
        ("CONCEPT_MAP.md", "concept dependency map"),
    ]:
        path = os.path.join(out_dir, fname)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        mark = "v" if size > 0 else "o"
        info = f"{size//1024}KB" if size > 0 else "not generated"
        print(f"  {mark} {fname:<24} {desc} [{info}]")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    main()