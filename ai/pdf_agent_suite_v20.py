"""
╔══════════════════════════════════════════════════════════════════╗
║         📚 PDF Agent Suite — v20.0 "CS & Math Edition"          ║
║   All v19.0 — accuracy-safe speed (removed unsafe parallel)     ║
╠══════════════════════════════════════════════════════════════════╣
║  F1-F9: OCR, LaTeX, MySQL, Pseudo, SmartChunk, MathPrompt,      ║
║         ExamQA, TermProtect, AutoChunk (v13-v14)                ║
║                                                                  ║
║  NEW in v15.0 — AI logic fixes:                                  ║
║  [G1] Hierarchical synthesis  — no more parts[:4] loss          ║
║  [G2] Adaptive question types — matches actual content          ║
║  [G3] Overview from Key Exam Points, not raw [:300]             ║
║  [G4] Concept map from summaries, not raw_terms regex           ║
║  [G5] Adaptive quality threshold — scales with complexity       ║
║  [G6] Translation marks untranslated chunks clearly             ║
║  [G7] Exam fallback uses summary text, not raw source           ║
║  [G8] Context thread — each chunk sees prev section headline    ║
║                                                                  ║
║  NEW in v16.0 — Agent 6: RAG Chat                               ║
║  [R1] Vector index built from summary chunks (TF-IDF + BM25)    ║
║  [R2] Top-K retrieval with section-aware reranking              ║
║  [R3] Grounded answers — cites section names, never hallucinates ║
║  [R4] Conversation memory — follows up on prev questions        ║
║  [R5] Interactive CLI chat loop (--mode chat)                   ║
║                                                                  ║
║  NEW in v17.0 — Source-first redesign:                          ║
║  [S1] RAG index built on EXTRACTED.md (raw text, not summary)   ║
║  [S2] Questions generated from raw source pages                 ║
║  [S3] Translation from raw source (verbatim preservation)       ║
║  [S4] Arabic chat with verbatim source quotes in answers        ║
║  [S5] Index hash — detects stale index automatically            ║
║  [S6] avgdl cached in RAGIndex — not recomputed per query       ║
║                                                                  ║
║  NEW in v18.0 — Semantic RAG:                                   ║
║  [M1] TF-IDF sklearn vectors → cosine similarity (semantic)     ║
║  [M2] Hybrid score = 0.6×semantic + 0.4×BM25                   ║
║  [M3] Arabic↔English query expansion (synonym mapping)          ║
║  [M4] Score threshold — never returns irrelevant chunks         ║
║  [M5] TF-IDF matrix stored in index — instant query             ║
║                                                                  ║
║  NEW in v19.0 — Speed optimizations:                            ║
║  [P1] ThreadPoolExecutor — parallel chunk summarization         ║
║  [P2] Removed time.sleep(0.3) — replaced with smart backoff     ║
║  [P3] Adaptive retries — fast fail on small chunks              ║
║  [P4] Dynamic max_tokens — scales to actual content size        ║
║  [P5] _ensure_exam_list skips LLM call when score is close      ║
║  [P6] BM25 df_cache precomputed once at index build time        ║
║                                                                  ║
║  v20.0 — Accuracy fixes:                                        ║
║  [A1] Removed unsafe parallel — G8 context thread restored      ║
║  [A2] PromptBuilder._prev_context race condition fixed          ║
║  [A3] Parallel questions only (safe — no shared state)          ║
║  [A4] Streaming max_tokens detection — no silent truncation     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, time, json, re, requests, warnings, argparse, unicodedata
import math, heapq, pickle
import concurrent.futures
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from collections import defaultdict, Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")


# ════════════════════════════════════════════════════════════
#  CONFIGURATION
# ════════════════════════════════════════════════════════════

MARKER_API_URL    = "https://climatological-yamileth-parliamentarily.ngrok-free.dev"
LLM_API_URL       = "https://YOUR_QWEN_URL.trycloudflare.com/v1/chat/completions"
LOCAL_API_KEY     = "any-key"
MODEL_NAME        = "Qwen/Qwen2.5-7B-Instruct"
OUTPUT_DIR        = "./pdf_output"
CHUNK_SIZE        = 6
MAX_CHARS_PER_SUB = 4500

# Speed configuration  [P1]
MAX_PARALLEL_CHUNKS = 3   # threads for parallel summarization
                          # keep ≤3 to avoid LLM rate limits
MIN_SLEEP_BETWEEN   = 0.0 # seconds between sequential calls (was 0.3)
FAST_FAIL_CHARS     = 800 # chunks smaller than this get retries=1


# ════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════

def log(msg: str, level: str = "info"):
    sym = {"ok": "✓", "warn": "⚠", "err": "✗", "progress": "◈"}.get(level, "▸")
    print(f"  {sym} {msg}")


# ════════════════════════════════════════════════════════════
#  [F8] TECHNICAL TERM PROTECTION (Translation)
# ════════════════════════════════════════════════════════════

CS_PROTECTED_TERMS = {
    # Data Structures
    "stack", "queue", "heap", "tree", "graph", "hash", "array", "linked list",
    "binary tree", "AVL tree", "B-tree", "trie", "hash table", "hash map",
    "deque", "priority queue", "adjacency list", "adjacency matrix",
    # Algorithms
    "sorting", "searching", "BFS", "DFS", "dynamic programming", "greedy",
    "divide and conquer", "backtracking", "memoization", "recursion",
    "merge sort", "quick sort", "heap sort", "bubble sort", "insertion sort",
    "selection sort", "radix sort", "counting sort",
    "Dijkstra", "Bellman-Ford", "Floyd-Warshall", "Prim", "Kruskal",
    # Complexity
    "Big O", "Big Theta", "Big Omega", "time complexity", "space complexity",
    "amortized", "worst case", "best case", "average case",
    # Math / CS Theory
    "theorem", "lemma", "corollary", "proof", "induction", "invariant",
    "recurrence", "master theorem", "substitution method",
    "NP-hard", "NP-complete", "polynomial", "logarithm",
    # Database
    "SELECT", "FROM", "WHERE", "JOIN", "INNER JOIN", "LEFT JOIN",
    "PRIMARY KEY", "FOREIGN KEY", "index", "transaction", "ACID",
    "normalization", "schema", "tuple", "relation",
    # Systems / Networks
    "cache", "buffer", "pointer", "register", "pipeline", "thread", "process",
    "semaphore", "mutex", "deadlock", "race condition",
    "TCP", "UDP", "HTTP", "DNS", "IP", "MAC",
    # ML / AI
    "gradient descent", "backpropagation", "neural network", "loss function",
    "epoch", "batch", "overfitting", "underfitting", "regularization",
    # Steganography / Security — ADDED v21
    "steganography", "steganalysis", "steganographic",
    "stego", "stego object", "cover image", "cover video", "cover message",
    "LSB", "DCT", "DWT", "spread spectrum",
    "I-frame", "P-frame", "B-frame", "keyframe", "intra-frame", "inter-frame",
    "RGB", "YUV", "YCbCr", "luma", "chroma", "chrominance", "luminance",
    "chroma subsampling", "pixel", "blob", "frame rate", "bit rate",
    "fps", "bps", "Mbps", "SD", "HD", "UHD", "4K",
    "aspect ratio", "resolution", "codec", "multiplexing", "muxing",
    "interlaced", "progressive scan", "A/V sync",
    "lossless", "lossy", "spatial compression", "temporal compression",
    "macroblock", "DCT block", "transform domain", "spatial domain",
    "HDMI", "DVI", "analog", "digital",
    "metadata", "timestamp", "container",
}


def protect_technical_terms(text: str) -> tuple:
    """
    [F8] Replaces technical terms with placeholders before translation.
    Returns (modified_text, mapping_dict).
    Sorts by length descending to avoid partial replacements.
    """
    protected = {}
    result = text
    sorted_terms = sorted(CS_PROTECTED_TERMS, key=len, reverse=True)
    for i, term in enumerate(sorted_terms):
        placeholder = f"__TERM_{i:04d}__"
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        if pattern.search(result):
            protected[placeholder] = term
            result = pattern.sub(placeholder, result)
    return result, protected


def restore_technical_terms(text: str, protected: dict) -> str:
    """[F8] Restores protected terms after translation."""
    for placeholder, term in protected.items():
        text = text.replace(placeholder, term)
    return text


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
    has_proofs:       bool  = False   # [F4] NEW
    theorem_count:    int   = 0       # [F4] NEW
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

# [F4] Stronger pseudocode patterns
_PSEUDOCODE_PATTERNS = re.compile(
    r'\b(?:Algorithm|Procedure|Function)\s+\w+|'
    r'(?:^|\n)\s*(?:Input|Output|Require|Ensure)\s*:|'
    r'(?:^|\n)\s*\d+[:.]\s+\w|'
    r'(?:^|\n)\s*(?:end\s+(?:if|for|while|procedure|algorithm|function))\b|'
    r'\bnil\b|\bNIL\b|'
    r'(?:^|\n)\s*\w+\s*:=\s*\w',
    re.MULTILINE | re.IGNORECASE
)


def profile_chunk(text: str) -> ChunkProfile:
    p = ChunkProfile()
    p.char_count = len(text)
    p.word_count = len(text.split())

    # ── detect CODE / PSEUDOCODE ─────────────────────────────
    code_signals  = len(re.findall(r'```[\s\S]*?```', text)) * 4
    code_signals += len(re.findall(
        r'def\s+\w+\s*\(|int\s+\w+\s*\(|#include|for\s*\(|while\s*\(|'
        r'return\s+\w|class\s+\w+|import\s+\w+|printf\s*\(|cout\s*<<', text))
    code_signals += len(re.findall(
        r'mysql>\s*\w|'
        r'->\s+(?:FROM|WHERE|JOIN|AND|OR)\b|'
        r'(?:^|\n)\s*(?:SELECT|FROM|WHERE|'
        r'INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|OUTER\s+JOIN|'
        r'ORDER\s+BY|GROUP\s+BY|HAVING|'
        r'INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|'
        r'CREATE\s+TABLE|DROP\s+TABLE|ALTER\s+TABLE|CREATE\s+INDEX)\s|'
        r'(?:^|\n)\+[-+]+\+',
        text, re.IGNORECASE | re.MULTILINE))
    code_signals += len(re.findall(
        r'\bAlgorithm\s+\w+|'
        r'\bProcedure\s+\w+|'
        r'\bFunction\s+\w+|'
        r'(?:^|\n)\s{2,}\w+\s*:=\s*|'
        r'(?:^|\n)\s*for\s+\w+\s*=|'
        r'(?:^|\n)\s*if\s+\w+.*then|'
        r'(?:^|\n)\s*while\s+\w+.*do|'
        r'(?:^|\n)\s*return\s+\w',
        text, re.IGNORECASE | re.MULTILINE))

    # [F4] Extra pseudocode signals
    pseudo_hits = len(_PSEUDOCODE_PATTERNS.findall(text))
    if pseudo_hits >= 3:
        code_signals += pseudo_hits

    p.has_code   = code_signals >= 2
    p.code_lines = len([l for l in text.split('\n')
                        if re.search(r'^\s{4,}|\t', l) or '```' in l])

    if p.has_code:
        if   re.search(r'mysql>\s*\w|^\s*(?:SELECT|INSERT|UPDATE|DELETE)\s',
                       text, re.IGNORECASE | re.MULTILINE):            p.lang = "SQL"
        elif re.search(r'def\s+\w+|import\s+\w+|print\s*\(', text):  p.lang = "Python"
        elif re.search(r'#include|int\s+main\s*\(|printf', text):     p.lang = "C/C++"
        elif re.search(r'public\s+class|System\.out', text):          p.lang = "Java"
        elif re.search(r'\bAlgorithm\b|\bProcedure\b|\bbegin\b|\bend\b|'
                       r'\bInput:\b|\bOutput:\b',
                       text, re.IGNORECASE):                           p.lang = "Pseudocode"

    # ── detect TABLES ──────────────────────────────────────
    p.has_tables = len(re.findall(r'^\|.+\|', text, re.MULTILINE)) > 3

    # ── detect MATH / THEOREMS ─────────────────────────────
    latex_math     = len(re.findall(r'\$[^$]+\$|\$\$[\s\S]+?\$\$', text))
    latex_cmds     = len(re.findall(
        r'\\(?:int|sum|prod|frac|sqrt|partial|nabla|infty|forall|exists|'
        r'leq|geq|neq|approx|equiv|rightarrow|Rightarrow|alpha|beta|gamma|'
        r'lambda|mu|pi|sigma|phi|omega|Sigma|Delta|Omega|phi|theta|'
        r'lim|max|min|sup|inf)\b', text))
    unicode_math   = len(re.findall(r'[∑∏∫∂∇∈∧∨¬∀∃≤≥≠≈∞□]', text))
    norm_notation  = len(re.findall(r'\|\|[^|]+\|\|', text))

    # [F4] Theorem/proof block detection
    p.theorem_count = len(re.findall(
        r'(?:^|\n)(?:Theorem|Lemma|Proof|Corollary|Definition|Proposition|Claim|Remark)\s*[\d.]*\s*[.:]',
        text, re.IGNORECASE | re.MULTILINE
    ))
    p.has_proofs = p.theorem_count >= 1

    recurrence     = len(re.findall(r'T\s*\(\s*n[^)]*\)\s*=', text))
    complexity_math = (min(len(re.findall(r'O\s*\([^)]+\)', text)), 3)
                       if not p.has_tables else 0)
    math_signals = (latex_math + latex_cmds + unicode_math + norm_notation +
                    p.theorem_count * 2 + recurrence + complexity_math)
    p.has_math      = math_signals >= 2
    p.formula_count = latex_math

    # ── complexity score ────────────────────────────────────
    if p.word_count > 0:
        p.concept_density = (len(_TECH_TERMS.findall(text)) / p.word_count) * 100

    # [F4] Proofs increase complexity score
    p.complexity_score = min(
        min(p.concept_density / 15.0, 1.0)                               * 0.28 +
        min((p.formula_count + p.theorem_count) / 8.0, 1.0)              * 0.30 +
        min(p.code_lines / 50.0, 1.0)                                    * 0.20 +
        min(p.theorem_count / 5.0, 1.0)                                  * 0.12 +
        (0.10 if (p.has_code and p.has_math) else
         0.06 if (p.has_code or p.has_math) else 0.0),
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

    s.overlap = int(300 + c * 350)
    # [F4] Proofs need more overlap to keep theorem + proof together
    if profile.has_proofs:
        s.overlap = min(s.overlap + 200, 800)

    if task == "summarize":
        type_bonus   = 300 if (profile.has_code and profile.has_math) else \
                       200 if profile.has_code else \
                       200 if profile.has_math else 0
        proof_bonus  = 300 if profile.has_proofs else 0
        base_tokens  = 1600 + int(c * 500) + type_bonus + proof_bonus
        # [P4] Cap tokens to actual content size — no need for 2800 on a 500-char chunk
        content_cap  = max(400, min(profile.char_count // 3, 2800))
        s.max_tokens = min(base_tokens, content_cap, 2800)
    else:
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

    # [F6] NEW: dedicated system prompt for math/proof-heavy content
    MATH_SYSTEM = (
        "You are a mathematics and CS teaching assistant specializing in making proofs and algorithms clear. "
        "When summarizing proofs: state the theorem verbatim, identify the KEY INSIGHT "
        "(the clever step that makes the proof work), then trace the logic step by step. "
        "Never say 'the proof shows that...' without explaining HOW each step follows. "
        "For algorithms: copy the pseudocode verbatim, trace it with a small concrete example, "
        "then derive the time complexity step by step. "
        "Keep all LaTeX notation, recurrences, and Big-O expressions exactly as written."
    )

    TRANSLATE_SYSTEM = (
        "انت مترجم متخصص بتترجم محتوى تقني إنجليزي للعامية المصرية. "
        "قواعد صارمة لازم تتبعها:\n"
        "1. اكتب بالعربية أو الإنجليزية فقط — ممنوع تماماً أي لغة تانية.\n"
        "   مثال صح: 'الـ frame هو صورة واحدة من الفيديو'\n"
        "   مثال غلط: '帧是视频的一个画面' (صيني ممنوع)\n"
        "2. أي كلمة شكلها __TERM_XXXX__: اكتبها كما هي بالضبط.\n"
        "3. المصطلحات دي خليها إنجليزي: steganography, steganalysis, pixel, frame, codec, "
        "LSB, DCT, DWT, RGB, YUV, YCbCr, I-frame, P-frame, B-frame, fps, bps, HDMI, DVI.\n"
        "4. الأكواد والمعادلات: انقلها كما هي.\n"
        "5. لو مش قادر تترجم جملة بالعربي، اكتبها بالإنجليزي — مش بصيني أو غيره.\n"
        "6. عامية مصرية سلسة — مش ترجمة حرفية.\n"
        "7. بس اللي في النص — مش تزيد ولا تحذف."
    )

    JSON_SYSTEM = (
        "You are a precise JSON generator. "
        "Output ONLY valid JSON starting with { and ending with }."
    )

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
        "[the theorem statement exactly] — [what it means and why it matters]\n"
        "[KEY INSIGHT: the clever step that makes the proof work]\n"
        "[trace the proof logic: 'We start with X, then show Y, therefore Z']\n\n"
        "Always end with:\n"
        "Key Exam Points:\n"
        "- [specific fact with number/formula/algorithm name from the source]\n"
        "- [another specific fact]\n"
        "- [at least 2, more if the source warrants it]"
    )

    @staticmethod
    def summary(text: str, profile: ChunkProfile,
                part_n: int = 1, total_parts: int = 1) -> str:
        part_note = (f"\n\n[Part {part_n} of {total_parts} — summarize only this part]"
                     if total_parts > 1 else "")

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

        # [F6] Extra instructions for proofs
        proof_instruction = ""
        if profile.has_proofs:
            proof_instruction = (
                "\n\nFor THEOREMS and PROOFS:\n"
                "1. State the theorem EXACTLY as written — do not paraphrase it\n"
                "2. Identify the KEY INSIGHT — the one clever step that makes the proof work\n"
                "3. Trace the proof: 'We start with X... then we show Y... therefore Z'\n"
                "4. State WHY this theorem matters (what it enables or proves)\n"
                "Do NOT just write 'the proof shows that...' — explain the HOW.\n"
            )

        # [F6] Extra instructions for algorithms
        algo_instruction = ""
        if profile.has_code and profile.lang in ("Pseudocode", "Python", "C/C++"):
            algo_instruction = (
                "\n\nFor ALGORITHMS:\n"
                "1. Copy the pseudocode/code VERBATIM — no changes\n"
                "2. Trace it with a small concrete example (e.g. array of 4 elements)\n"
                "3. Derive the time complexity step by step (not just state it)\n"
                "4. State the key invariant the algorithm maintains\n"
            )

        # [G8] Inject previous section context if available
        context_line = ""
        # prev_context is passed in via summarize_chunk; we access it via closure
        # We use a module-level variable set by summarize_chunk before calling prompt builder
        _prev = getattr(PromptBuilder, "_prev_context", "")
        if _prev:
            context_line = (
                f"CONTEXT: The previous section covered: {_prev}\n"
                f"Connect ideas naturally where relevant (e.g. 'Building on X...')\n\n"
            )

        return (
            f"You are summarizing a textbook section for students. "
            f"Write a clear English summary of the text below.\n\n"
            f"{context_line}"
            f"{hint_line}"
            f"{proof_instruction}"
            f"{algo_instruction}"
            f"{PromptBuilder.SUMMARY_FORMAT}\n\n"
            f"Strict rules:\n"
            f"- Only what is in the source — do not add or invent anything\n"
            f"- Paste all code, equations, and theorem statements verbatim\n"
            f"- Key Exam Points must contain SPECIFIC facts (numbers, formulas, names) — "
            f"never generic advice like 'study this section'{part_note}\n\n"
            f"Source text:\n{'─'*60}\n{text}\n{'─'*60}\n\n"
            f"Write the summary now:"
        )

    @staticmethod
    def summary_fallback(text: str, attempt: int) -> str:
        if attempt == 2:
            return (
                f"Summarize this text clearly in plain English.\n\n"
                f"Include any code, equations, or theorems exactly as they appear.\n"
                f"End with:\nKey Exam Points:\n- [specific fact]\n- [specific fact]\n\n"
                f"Source:\n{text[:4000]}\n\nSummary:"
            )
        return (
            f"Write a 2-paragraph summary of this text.\n"
            f"End with:\nKey Exam Points:\n- ...\n- ...\n\n"
            f"Source:\n{text[:2000]}\n\nSummary:"
        )

    @staticmethod
    def synthesis(parts: list, profile: ChunkProfile) -> str:
        """
        [G1] Hierarchical synthesis — never drops sub-chunks.
        If parts > 4, we do a two-level merge: batch into groups of 3,
        merge each group, then merge the group-summaries into one final.
        This ensures EVERY part contributes to the final summary.
        """
        preserve_note = ""
        if profile.has_code or profile.has_math:
            preserve_note = (
                "\nIMPORTANT: Any code, equations, theorems, or proofs that appear in the "
                "sub-summaries MUST be preserved verbatim in the merged summary.\n"
            )

        def _merge_prompt(subs: list) -> str:
            combined = "\n\n---\n\n".join(subs)
            return (
                f"Merge these sub-summaries of the same textbook section into one cohesive summary.\n"
                f"{preserve_note}\n"
                f"Format: flowing explanation first, then any code/equations/theorems, then:\n"
                f"Key Exam Points:\n- [specific facts with numbers/formulas]\n- [...]\n\n"
                f"Rule: only what is in the summaries below — do not add anything.\n\n"
                f"Sub-summaries:\n{combined[:3800]}\n\n"
                f"Write the merged summary now:"
            )

        # [G1] If ≤ 4 parts, merge directly
        if len(parts) <= 4:
            return _merge_prompt(parts)

        # [G1] If > 4 parts, hierarchical: batch into groups of 3 first
        # We return the prompt for the FINAL merge; caller handles the intermediate calls
        # We embed all parts as a structured list with clear separators
        all_combined = "\n\n===PART BREAK===\n\n".join(parts)
        return (
            f"Merge ALL these sub-summaries (there are {len(parts)} parts) "
            f"of the same textbook section into one cohesive summary.\n"
            f"{preserve_note}\n"
            f"IMPORTANT: Every part contains unique content — do NOT skip any part.\n"
            f"Parts are separated by '===PART BREAK==='\n\n"
            f"Format: flowing explanation first, then any code/equations/theorems, then:\n"
            f"Key Exam Points:\n- [collect ALL important points from ALL parts]\n- [...]\n\n"
            f"Sub-summaries:\n{all_combined[:4500]}\n\n"
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
        """[S3] Translation prompt — zero tolerance for non-Arabic."""
        return (
            f"ترجم النص الإنجليزي التالي للعامية المصرية.\n\n"
            f"⛔ ممنوع تماماً: الصيني، الياباني، الكوري، الروسي، أو أي لغة غير العربية والإنجليزية.\n"
            f"✅ لو مش قادر تترجم جملة: اكتبها بالإنجليزي — مش بصيني أو غيره.\n\n"
            f"القواعد:\n"
            f"1. عربي أو إنجليزي فقط — zero tolerance لأي لغة تانية\n"
            f"2. __TERM_XXXX__ → اكتبها كما هي بالضبط\n"
            f"3. المصطلحات دي إنجليزي: steganography, steganalysis, pixel, frame, codec,"
            f" LSB, DCT, DWT, RGB, YUV, I-frame, P-frame, B-frame, fps, bps, HDMI, DVI\n"
            f"4. الأكواد والمعادلات → انقلها كما هي\n"
            f"5. عامية مصرية سلسة — مش ترجمة حرفية\n"
            f"6. بس اللي في النص — مش تزيد ولا تحذف\n\n"
            f"النص:\n{'─'*60}\n{chunk}\n{'─'*60}\n\n"
            f"الترجمة:"
        )
    @staticmethod
    def questions(text: str, label: str, profile: ChunkProfile,
                  lang_rule: str) -> str:
        """
        [G2] Adaptive question types — detects what the section actually contains
        and builds question types that match. No more forced 'design' questions
        on a section that only has definitions.
        """
        # Detect what's actually in the text
        has_complexity  = bool(re.search(r'O\s*\(|Θ\s*\(|Ω\s*\(|time complexity|space complexity', text, re.IGNORECASE))
        has_definitions = bool(re.search(r'(?:Definition|define|is defined as|we say that)', text, re.IGNORECASE))
        has_examples    = bool(re.search(r'(?:Example|for instance|consider|suppose|given)', text, re.IGNORECASE))
        has_comparison  = bool(re.search(r'(?:vs\.|versus|compared to|difference between|unlike|whereas)', text, re.IGNORECASE))

        if profile.has_code and profile.has_math:
            q3_type = "trace the code AND apply the equation with a concrete example"
            q4_type = "derive the time complexity step-by-step OR design a variant" if has_complexity else "design a solution using both the code pattern and the formula"
        elif profile.has_code:
            q3_type = "trace the algorithm step-by-step with a small input (e.g., array of 4 items)"
            q4_type = "analyze time+space complexity with justification" if has_complexity else "design a modified version that handles an edge case"
        elif profile.has_proofs:
            q3_type = "identify the KEY INSIGHT of the proof and explain why it works"
            q4_type = "apply the theorem to a new case OR find a counterexample to a variant"
        elif profile.has_math:
            q3_type = "apply the formula/method to a numerical example step-by-step"
            q4_type = "compare two approaches OR prove a property from the section"
        elif has_comparison:
            q3_type = "compare and contrast the two approaches with a specific scenario"
            q4_type = "decide which approach fits a given situation and justify"
        elif has_definitions:
            q3_type = "give a concrete example that satisfies the definition AND one that does not"
            q4_type = "explain why the definition requires each condition (what breaks without it)"
        else:
            q3_type = "analyze a process step by step using content from this section"
            q4_type = "design a solution to a new problem using ideas from this section"

        q2_type = "compare two key concepts" if has_comparison else "explain the main concept in your own words with an example"

        marks = 13 if profile.complexity_score < 0.5 else 15
        m_hi  = "5" if marks == 15 else "4"
        hint  = (
            f"Q1: mcq testing recall of a specific fact from the section.\n"
            f"Q2: {q2_type}.\n"
            f"Q3: {q3_type}.\n"
            f"Q4: {q4_type}."
        )
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
        """[G4] Concept map — forces REAL names, not placeholders."""
        topics_json = json.dumps(topics, ensure_ascii=False)[:3500]
        schema = json.dumps({
            "central_concepts": ["Video Steganography", "I-frame", "P-frame", "B-frame", "Steganalysis"],
            "learning_order": ["first real topic", "second real topic", "third"],
            "exam_high_priority": ["first real priority", "second", "third"],
            "concept_map": [{"concept": "REAL name", "depends_on": ["real prereq"],
                             "required_by": ["real consumer"],
                             "difficulty": "beginner", "category": "theory"}],
            "study_plan": {"week1": ["real topic"], "week2": ["real topic"],
                           "week3": ["real topic"], "week4": ["real review"]}
        })
        return (
            f"Build a concept dependency map from these textbook sections.\n"
            f"Use REAL concept names from the content — NOT placeholders like c1, p1.\n\n"
            f"Sections:\n{topics_json}\n\n"
            f"Output ONLY valid JSON. Replace ALL placeholder values with REAL names from the content.\n"
            f"Follow this schema exactly: {schema}"
        )
# ════════════════════════════════════════════════════════════
#  LLM INTERFACE
# ════════════════════════════════════════════════════════════

# [P2] Thread-local session — reuses TCP connection, saves handshake time
_session_local = threading.local()

def _get_session() -> requests.Session:
    """Returns a per-thread requests.Session (reuses connections)."""
    if not hasattr(_session_local, "session"):
        s = requests.Session()
        s.verify = False
        s.headers.update({
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {LOCAL_API_KEY}",
        })
        _session_local.session = s
    return _session_local.session


def call_model(messages: list, max_tokens: int = 1800, temp: float = 0.0,
               retries: int = 3, timeout: int = 300,
               system: str = None) -> Optional[str]:
    """
    [P2] Uses persistent session — no TCP reconnect per call.
    [P3] Exponential backoff only on 429/timeout — immediate on other errors.
    """
    sys_msg = system or PromptBuilder.SUMMARY_SYSTEM
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": sys_msg}] + messages
    payload = {"model": MODEL_NAME, "messages": messages,
               "temperature": temp, "max_tokens": max_tokens}
    session = _get_session()

    for attempt in range(1, retries + 1):
        try:
            r = session.post(LLM_API_URL, json=payload, timeout=timeout)

            if r.status_code == 429:
                # [P3] Rate limit — exponential backoff only here
                wait = min(10 * attempt, 60)
                log(f"rate limit — waiting {wait}s", "warn")
                time.sleep(wait)
                continue

            if r.status_code != 200:
                log(f"HTTP {r.status_code} (attempt {attempt}/{retries})", "warn")
                if attempt < retries:
                    time.sleep(2 * attempt)  # [P3] shorter than before (was 5×)
                continue

            content = r.json()["choices"][0]["message"]["content"]
            return content.strip() if content else None

        except requests.Timeout:
            log(f"timeout (attempt {attempt}/{retries})", "warn")
            if attempt < retries:
                time.sleep(4 * attempt)  # [P3] was 8×
        except Exception as e:
            log(f"error: {e}", "err")
            if attempt == retries:
                return None
            time.sleep(2)  # [P3] was 4s flat
    return None


# ════════════════════════════════════════════════════════════
#  JSON PARSER
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

_EXAM_PATTERNS = re.compile(
    r'Key\s+Exam\s+Points|Important\s+for\s+exam|Exam\s+notes|'
    r'Remember\s*:|Key\s+points\s*:|Summary\s+points\s*:|'
    r'مهم للامتحان',
    re.IGNORECASE
)

# [F7] Generic phrases that indicate low-quality exam points
_GENERIC_EXAM_PHRASES = [
    'review this section', 'study carefully', 'important for exam',
    'remember this', 'key concept', 'understand this',
    'pay attention', 'make sure to', 'be familiar with',
    'this is important', 'note that', 'keep in mind'
]


def validate_exam_points(text: str) -> bool:
    """
    [F7] Checks that Key Exam Points are specific, not generic.
    Returns True if points are acceptable quality.
    """
    exam_match = re.search(
        r'Key\s+Exam\s+Points[:\s]*([\s\S]+?)(?:\n\n|\Z)',
        text, re.IGNORECASE
    )
    if not exam_match:
        return False

    points_text = exam_match.group(1)
    bullets = re.findall(r'[-•*]\s*(.+)', points_text)

    if len(bullets) < 2:
        return False

    good_points = 0
    for bullet in bullets:
        bullet_lower = bullet.lower().strip()
        is_generic = any(phrase in bullet_lower for phrase in _GENERIC_EXAM_PHRASES)
        # A good point has: numbers, formulas, algorithm names, or complexity notation
        has_substance = bool(re.search(
            r'O\([^)]+\)|Θ\([^)]+\)|Ω\([^)]+\)|\d+|'
            r'\b(?:algorithm|theorem|lemma|proof|sort|search|hash|tree|graph|'
            r'complexity|time|space|BFS|DFS|DP|greedy|recurrence)\b',
            bullet, re.IGNORECASE
        ))
        if not is_generic and (has_substance or len(bullet) > 40):
            good_points += 1

    return good_points >= 2


def _score_summary(text: str, profile: ChunkProfile) -> float:
    if not text or len(text.strip()) < 60:
        return 0.0
    t = text.strip()

    expected = max(150, min(profile.char_count * 0.08, 1000))
    len_sc   = min(len(t) / expected, 1.0) * 0.35

    # [F7] Use validate_exam_points for stricter scoring
    exam_sc  = (0.30 if validate_exam_points(t) else
                0.15 if _EXAM_PATTERNS.search(t) else 0.0)

    preserve_sc = 0.0
    if profile.has_code and ('```' in t or 'Code:' in t):
        preserve_sc += 0.10
    if profile.has_math and ('Equations:' in t or '$' in t or 'Theorem' in t or 'Proof' in t):
        preserve_sc += 0.10
    # [F4] Proof preservation check
    if profile.has_proofs and re.search(r'KEY INSIGHT|key insight|Proof:|proof:', t):
        preserve_sc += 0.05
    if not profile.has_code and not profile.has_math:
        preserve_sc = 0.20

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
    t = t.strip()

    # [A4] Detect silent truncation — output cut mid-sentence
    # Signs: ends without punctuation, or ends mid-code-block
    if t:
        last_char = t[-1]
        open_fences = t.count("```") % 2 != 0   # odd = unclosed code block
        mid_sentence = (last_char not in ".!?:،؟\n`"
                        and not t.endswith("---")
                        and len(t) > 100)
        if open_fences:
            log("output truncated mid-code-block — appending closure", "warn")
            t += "\n```"
        elif mid_sentence and len(t) > 1200:
            # Only warn if genuinely long AND ends mid-English-word (likely cut)
            last_line = t.rstrip().split("\n")[-1].strip()
            is_list_ending   = last_line.startswith(("-", "❑", "❖", "➢", "•", "*", "►"))
            is_short_ending  = len(last_line) < 80
            is_arabic_ending = bool(re.search(r'[\u0600-\u06ff]', last_line[-5:])) if last_line else False
            ends_mid_word    = bool(re.search(r'[a-zA-Z]$', last_line))
            if ends_mid_word and not (is_list_ending or is_short_ending or is_arabic_ending):
                log("possible truncation detected (no terminal punctuation)", "warn")

    return t


# ════════════════════════════════════════════════════════════
#  POST-PROCESSOR — ensure exam list exists and is high quality
# ════════════════════════════════════════════════════════════

def _ensure_exam_list(text: str, source: str, profile: ChunkProfile) -> str:
    """
    [F7] Ensures Key Exam Points exist AND are specific/high quality.
    """
    has_section  = _EXAM_PATTERNS.search(text)
    is_good      = validate_exam_points(text) if has_section else False

    if has_section and is_good:
        return text

    # [P5] If section exists and text is long enough, skip LLM regeneration
    # The extra call costs 5-15 seconds — not worth it for borderline cases
    if has_section and len(text) > 300:
        bullets = re.findall(r'[-•*]\s*(.+)', text)
        if len(bullets) >= 2 and any(len(b) > 30 for b in bullets):
            return text  # good enough — skip regeneration

    reason = "generic points" if has_section else "missing exam list"
    log(f"exam list {reason} — regenerating", "warn")

    raw = call_model(
        [{"role": "user", "content": (
            f"Add a 'Key Exam Points' section to this summary.\n\n"
            f"RULES — each bullet point MUST:\n"
            f"  1. Be a complete sentence (not just a term)\n"
            f"  2. Contain a SPECIFIC fact: a number, formula, algorithm name, or complexity\n"
            f"  3. Come directly from the source text below\n\n"
            f"GOOD examples:\n"
            f"  - BFS runs in O(V+E) time where V=vertices and E=edges\n"
            f"  - The merge step in Merge Sort always takes Θ(n) time\n"
            f"  - Dijkstra's algorithm fails on graphs with negative edge weights\n\n"
            f"BAD examples (rejected — too generic):\n"
            f"  - Understand BFS and DFS\n"
            f"  - Study the sorting algorithms carefully\n\n"
            f"Summary to improve:\n{text}\n\n"
            f"Source (for reference):\n{source[:1500]}\n\n"
            f"Rewrite the full summary with improved 'Key Exam Points:' at the end:"
        )}],
        max_tokens=min(len(text)//2 + 600, 1200), temp=0.0, retries=2
    )
    result = _clean(raw)
    if result and validate_exam_points(result) and len(result) > len(text) * 0.5:
        return result

    # Fallback: extract substance-rich sentences from source
    substance_pat = re.compile(
        r'[A-Z][^.!?\n]{20,}(?:'
        r'O\s*\(|Θ\s*\(|Ω\s*\('
        r'|runs in|takes|requires|costs'
        r'|algorithm|theorem|lemma|proof'
        r'|complexity|always|never|if and only if'
        r')[^.!?\n]*[.!?]',
        re.IGNORECASE
    )
    # [G7] Search summary text FIRST (consistent with what was written),
    # only fall back to raw source if summary has no substance-rich sentences.
    search_texts = [text, source]  # text = summary, source = raw chunk
    candidates = []
    for search_in in search_texts:
        candidates = substance_pat.findall(search_in)
        if not candidates:
            sentences = re.split(r'(?<=[.!?])\s+', search_in)
            candidates = [s.strip() for s in sentences
                          if len(s.strip()) > 50 and re.search(
                              r'\b(?:O\(|Θ\(|complexity|algorithm|theorem|'
                              r'sort|search|time|space|proof|always|never)\b',
                              s, re.IGNORECASE)][:5]
        if candidates:
            break  # found good candidates in summary, don't need raw source

    if candidates:
        points = "\n".join(f"- {c.strip()}" for c in candidates[:5])
        return text + f"\n\nKey Exam Points:\n{points}"

    return text + "\n\nKey Exam Points:\n- Review this section carefully for the exam"


# ════════════════════════════════════════════════════════════
#  [F1] [F2] [F3] TEXT NORMALIZER — with CS/Math fixes
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
        '□':r'\square',  # end-of-proof marker
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
        # [F1] Recover code that OCR missed
        text = cls._recover_orphan_code(text)
        # [F2] Fix LaTeX / math notation
        text = cls._fix_latex_math(text)
        # [F3] Fix MySQL tables
        text = cls._fix_mysql_tables(text)
        text = cls._fix_tables(text)
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE)
        # Fix Marker OCR artifacts: standalone FROM/WHERE
        text = re.sub(r'(?<![A-Z])FROM(?![A-Z_])', 'from', text)
        return text.strip()

    @classmethod
    def _recover_orphan_code(cls, text: str) -> str:
        """[F1] Wrap un-fenced code blocks that OCR failed to fence."""
        lines = text.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            # Skip if already inside a fenced block
            in_fence = '```' in '\n'.join(result[-5:]) and result.count('```') % 2 == 1

            if not in_fence and re.match(
                r'^(?:def |class |import |from |#include|int main|'
                r'public class|Algorithm |Procedure |Function )',
                stripped
            ):
                # Collect the block
                code_block = [line]
                j = i + 1
                while j < len(lines) and (
                    lines[j].startswith('    ') or
                    lines[j].startswith('\t') or
                    lines[j].strip() == ''
                ):
                    code_block.append(lines[j])
                    j += 1

                # Only wrap if block is at least 2 lines
                if j > i + 1:
                    lang = 'python'
                    if stripped.startswith('#include') or 'int main' in stripped:
                        lang = 'cpp'
                    elif stripped.startswith('public class'):
                        lang = 'java'
                    elif re.match(r'^(?:Algorithm|Procedure|Function)\b', stripped, re.IGNORECASE):
                        lang = 'pseudocode'
                    result.append(f'```{lang}')
                    result.extend(code_block)
                    result.append('```')
                    i = j
                    continue

            result.append(line)
            i += 1
        return '\n'.join(result)

    @classmethod
    def _fix_latex_math(cls, text: str) -> str:
        """[F2] Fix common LaTeX patterns that OCR mangles."""
        # Recurrence relations: T(n) = ... wrap in $...$
        recurrence_pat = re.compile(
            r'(?<!\$)(T\s*\(\s*n(?:/\d+)?\s*\)\s*=\s*[\dT()\s/+*-]+(?:\+\s*(?:n|Θ|O)\([^)]+\))?)(?!\$)',
            re.MULTILINE
        )
        text = recurrence_pat.sub(r'$\1$', text)

        # Bare O() / Θ() / Ω() outside math context
        for notation in [r'O\s*\([^)]+\)', r'Θ\s*\([^)]+\)', r'Ω\s*\([^)]+\)']:
            text = re.sub(
                r'(?<!\$)(' + notation + r')(?!\$)',
                r'$\1$', text
            )

        # Fix split fractions: "a\n─\nb" -> "$\frac{a}{b}$"
        text = re.sub(
            r'(\w+)\s*\n\s*[─━—]+\s*\n\s*(\w+)',
            r'$\\frac{\1}{\2}$', text
        )

        return text

    @classmethod
    def _fix_mysql_tables(cls, text: str) -> str:
        """[F3] Repair MySQL output tables that OCR corrupted."""
        lines = text.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Detect a MySQL border row that OCR might have garbled
            # Original: +------+------+
            # OCR might produce: |------+------| or similar
            if re.match(r'^[|+][-+|─━]+[|+]$', line.strip()):
                # Normalize to standard MySQL border
                cols = len(re.findall(r'[|+]', line)) - 1
                normalized = '+' + '+'.join(['------'] * cols) + '+'
                result.append(normalized)
            else:
                result.append(line)
            i += 1
        return '\n'.join(result)

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
#  [F9] AUTO CHUNK-SIZE DETECTION
# ════════════════════════════════════════════════════════════

_DENSITY_TO_CHUNK = [
    (12, 2),
    (9,  3),
    (6,  4),
    (3,  5),
    (0,  6),
]


def auto_detect_chunk_size(pages: dict, keys: list) -> int:
    """
    [F9] Analyses a sample of the book and returns the optimal chunk-size.

    Sampling strategy: first 5 + middle 5 + last 5 sections.
    Scoring factors (density_score 0-16) -> chunk_size (2-6).
    Manual --chunk-size still overrides this when explicitly provided.
    """
    if not keys:
        return 6

    mid         = len(keys) // 2
    sample_keys = list(dict.fromkeys(
        keys[:5] +
        keys[max(0, mid - 2) : mid + 3] +
        keys[-5:]
    ))
    sample_keys = [k for k in sample_keys if k in pages]
    if not sample_keys:
        return 6

    char_counts = [len(pages[k]) for k in sample_keys]
    avg_chars   = sum(char_counts) / len(char_counts)
    max_chars   = max(char_counts)

    sample_text   = "\n\n".join(pages[k] for k in sample_keys)
    profile       = profile_chunk(sample_text)
    density_score = 0

    # Factor 1: section size
    if   avg_chars > 6000: density_score += 3
    elif avg_chars > 4000: density_score += 2
    elif avg_chars > 2000: density_score += 1

    # Factor 2: code type
    if profile.has_code:
        if   profile.lang in ("Pseudocode", "C/C++"): density_score += 3
        elif profile.lang in ("Python", "Java"):       density_score += 2
        else:                                           density_score += 1

    # Factor 3: proofs / theorems
    if profile.has_proofs:       density_score += 3
    elif profile.theorem_count:  density_score += 1

    # Factor 4: math formulas
    if profile.has_math: density_score += 2

    # Factor 5: comparison tables
    if profile.has_tables: density_score += 1

    # Factor 6: overall complexity
    density_score += int(profile.complexity_score * 4)

    # Lookup
    chunk_size = 6
    for threshold, size in _DENSITY_TO_CHUNK:
        if density_score >= threshold:
            chunk_size = size
            break

    # Safety: any section > 8 000 chars needs an extra reduction
    if max_chars > 8000:
        chunk_size = max(2, chunk_size - 1)

    book_type = {
        2: "extremely dense (CLRS / pure math)",
        3: "very dense (algorithms + proofs)",
        4: "dense (CS with code)",
        5: "moderate (CS concepts)",
        6: "light (prose / introductory)",
    }.get(chunk_size, "unknown")

    log(
        f"auto chunk-size = {chunk_size}  [{book_type}]  "
        f"avg={avg_chars:.0f}c  density={density_score}  "
        f"complexity={profile.complexity_score:.2f}",
        "ok"
    )
    return chunk_size


# ════════════════════════════════════════════════════════════
#  AGENT 1 — EXTRACTION
# ════════════════════════════════════════════════════════════

def _detect_language(text: str) -> str:
    """
    Detect dominant language of the document.
    Returns: 'arabic', 'english', or 'mixed'
    Used to avoid stripping Arabic content from Arabic books.
    """
    sample   = text[:3000]
    arabic   = len(re.findall(r'[\u0600-\u06ff]', sample))
    latin    = len(re.findall(r'[a-zA-Z]', sample))
    total    = max(arabic + latin, 1)
    ar_ratio = arabic / total
    if ar_ratio > 0.6:
        return 'arabic'
    if ar_ratio < 0.15:
        return 'english'
    return 'mixed'


def _deep_clean(text: str) -> str:
    """
    Deep cleaning pipeline — runs AFTER TextNormalizer.normalize().

    Smart rules:
    1. Detect book language first — never drop content that matches book language
    2. Skip garbage check inside code blocks and math blocks
    3. Remove lines >25% CJK/Cyrillic (unless book is Arabic → safe)
    4. Fix FROM/WHERE only OUTSIDE code blocks (SQL safety)
    5. Remove leftover artifacts (__TERM_, INFORMATION__, etc.)
    6. Normalize separator lines → clean ---
    7. Collapse blank lines
    """
    book_lang = _detect_language(text)

    _cjk_pat = re.compile(
        r'[\u4e00-\u9fff'   # CJK unified
        r'\u3040-\u30ff'    # Hiragana + Katakana
        r'\u3400-\u4dbf'    # CJK extension A
        r'\u0400-\u04ff'    # Cyrillic
        r'\u0900-\u097f]'   # Devanagari
    )

    # ── Step 1: Line-by-line garbage removal ─────────────────────
    lines      = text.split("\n")
    result     = []
    in_code    = False   # inside ```...``` block
    in_math    = False   # inside $$...$$ block
    dropped    = 0

    for line in lines:
        stripped = line.strip()

        # Track code block state
        fence_count = stripped.count("```")
        if fence_count % 2 == 1:
            in_code = not in_code

        # Track math block state
        math_count = stripped.count("$$")
        if math_count % 2 == 1:
            in_math = not in_math

        # Inside code or math — NEVER touch, pass through as-is
        if in_code or in_math:
            result.append(line)
            continue

        # Remove pure image placeholder lines (no caption value)
        if re.match(r'^!\[\]\([^)]*\)\s*$', stripped):
            continue

        # Collapse long separator lines → clean ---
        if re.match(r'^[─—━=\-]{8,}\s*$', stripped):
            # Only add one --- between content (skip duplicates)
            if result and result[-1].strip() != '---':
                result.append('---')
            continue

        # Garbage check — skip if book language matches line content
        if stripped:
            garbage = len(_cjk_pat.findall(stripped))
            ratio   = garbage / max(len(stripped), 1)

            # Check if line has useful math/formula content
            has_math = bool(re.search(
                r'[\u0391-\u03c9\u0398\u03a9\u03b1-\u03c9]'  # Greek
                r'|T\(n\)|O\(|Θ\(|Ω\(', stripped))

            if ratio > 0.25 and not has_math:
                # For Arabic books: if line has mostly Arabic, keep it
                if book_lang == 'arabic':
                    ar_chars = len(re.findall(r'[\u0600-\u06ff]', stripped))
                    if ar_chars / max(len(stripped), 1) > 0.3:
                        result.append(line)
                        continue
                dropped += 1
                continue   # Drop pure garbage
            elif ratio > 0.05 and not has_math:
                # Partial garbage — strip bad chars, keep the rest
                cleaned_line = _cjk_pat.sub('', line).strip()
                if cleaned_line:
                    result.append(cleaned_line)
                continue

        result.append(line)

    if dropped:
        log(f"  [clean] removed {dropped} garbage lines from Marker OCR", "warn")

    text = "\n".join(result)

    # ── Step 2: Fix FROM/WHERE only OUTSIDE code blocks ──────────
    def _fix_sql_artifacts(txt: str) -> str:
        """Replace standalone FROM/WHERE only outside code blocks."""
        parts   = re.split(r'(```[\s\S]*?```)', txt)
        cleaned = []
        for part in parts:
            if part.startswith('```'):
                cleaned.append(part)   # code block — leave untouched
            else:
                # Only replace standalone FROM/WHERE (not inside identifiers)
                part = re.sub(r'(?<![A-Za-z_])FROM(?![A-Za-z_0-9(])', 'from', part)
                part = re.sub(r'(?<![A-Za-z_])WHERE(?![A-Za-z_0-9(])', 'where', part)
                cleaned.append(part)
        return ''.join(cleaned)

    text = _fix_sql_artifacts(text)

    # ── Step 3: Remove leftover artifacts ────────────────────────
    text = re.sub(r'__TERM_\d{4}__', '', text)
    text = re.sub(r'INFORMATION__\w*', '', text)
    text = re.sub(r'FORMAT\w*__\w*', '', text)
    text = re.sub(r'FORMATION__\w*', '', text)

    # ── Step 4: Normalize whitespace ─────────────────────────────
    text = "\n".join(l.rstrip() for l in text.split("\n"))
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text.strip()


def run_extraction(pdf_path: str, out_dir: str) -> str:
    """
    Pipeline:
      1. Marker API  → raw markdown
      2. normalize() → fix OCR, LaTeX, tables
      3. _deep_clean()→ remove garbage, fix artifacts
      4. Save EXTRACTED_RAW.md (post-normalize, pre-clean) for debugging
      5. Save EXTRACTED.md (fully clean) — ALL agents use this
    """
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

    # Step 1: get raw markdown from Marker
    raw = r.json().get("markdown", "")
    log(f"  Marker returned {len(raw):,} chars", "ok")

    # Step 2: normalize (fix OCR patterns, LaTeX, tables, code blocks)
    normalized = TextNormalizer.normalize(raw)
    log(f"  after normalize: {len(normalized):,} chars", "ok")

    # Step 3: deep clean (remove garbage, fix artifacts)
    book_lang = _detect_language(normalized)
    log(f"  detected language: {book_lang}", "ok")
    clean = _deep_clean(normalized)
    log(f"  after clean: {len(clean):,} chars", "ok")

    struct = TextNormalizer.extract_structure(clean)
    log(f"  {len(struct['chapters'])} chapters | {len(struct['sections'])} sections", "ok")

    # Step 4: save raw (for debugging / manual inspection)
    raw_out = os.path.join(out_dir, "EXTRACTED_RAW.md")
    with open(raw_out, "w", encoding="utf-8") as f:
        f.write(f"# {Path(pdf_path).stem} — RAW (debug)\n\n")
        f.write(f"*{len(normalized):,} chars — post-normalize, pre-clean*\n\n---\n\n")
        f.write(normalized)
    log(f"  raw  -> {raw_out}", "ok")

    # Step 5: save clean — this is what ALL agents use
    pdf_hash = _file_hash(pdf_path)
    out = os.path.join(out_dir, "EXTRACTED.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {Path(pdf_path).stem}\n\n")
        f.write(f"*{len(clean):,} chars | pdf_hash={pdf_hash} | v25.0*\n\n")
        if struct["chapters"]:
            f.write("## Structure\n")
            for ch in struct["chapters"][:30]:
                f.write(f"- Chapter {ch['num']}: {ch['title']}\n")
            f.write("\n---\n\n")
        f.write(clean)
    with open(os.path.join(out_dir, "STRUCTURE.json"), "w", encoding="utf-8") as f:
        json.dump(struct, f, ensure_ascii=False, indent=2)

    log(f"  clean-> {out}", "ok")
    return out


def _split_into_sections(text: str, chars_per_page: int = 4000) -> dict:
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

    hs = list(re.finditer(r"^## .+$", text, re.MULTILINE))
    if len(hs) >= 2:
        pages = {}
        for i, m in enumerate(hs):
            end = hs[i+1].start() if i+1 < len(hs) else len(text)
            c   = text[m.start():end].strip()
            if len(c) > 200: pages[i+1] = c
        if pages: log(f"detected {len(pages)} H2 sections"); return pages

    hs1 = list(re.finditer(r"^# .+$", text, re.MULTILINE))
    if len(hs1) >= 2:
        pages = {}
        for i, m in enumerate(hs1):
            end = hs1[i+1].start() if i+1 < len(hs1) else len(text)
            c   = text[m.start():end].strip()
            if len(c) > 200: pages[i+1] = c
        if pages: log(f"detected {len(pages)} H1 sections"); return pages

    parts = [p.strip() for p in re.split(r'\n---+\n', text) if len(p.strip()) > 100]
    if len(parts) > 1:
        log(f"detected {len(parts)} separator sections")
        return {i+1: p for i, p in enumerate(parts)}

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
#  [F5] SMART ADAPTIVE CHUNKER
# ════════════════════════════════════════════════════════════

def find_logical_boundaries(text: str) -> list:
    """
    [F5] Returns positions that are safe to cut at.
    Prioritizes: end-of-proof markers, end-of-algorithm markers,
    section headings, then paragraph breaks.
    """
    boundaries = []

    boundary_patterns = [
        # End of proof (highest priority — never cut inside a proof)
        (r'(?:□|∎|QED|\\qed|\\blacksquare)\s*\n', 10),
        (r'(?:^|\n)(?:End\s+of\s+[Pp]roof|Proof\s+complete)\s*[.\n]', 10),
        # End of algorithm block
        (r'(?:^|\n)(?:end\s+(?:procedure|algorithm|function|for|while|if))\s*\n',  8),
        (r'(?:^|\n)(?:End\s+Algorithm|End\s+Procedure)\s*\n', 8),
        # Section/chapter headings
        (r'(?:^|\n)#{1,3}\s+\w', 6),
        (r'(?:^|\n)(?:Chapter|Section)\s+\d', 6),
        # After a complete theorem statement (before its proof)
        (r'(?:^|\n)Proof[.:\s]', 4),
        # Double newline after a sentence (paragraph break)
        (r'\.\s*\n\n', 2),
    ]

    for pattern, priority in boundary_patterns:
        for m in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            boundaries.append((m.end(), priority))

    # Sort by position, keep highest priority for each nearby position
    boundaries.sort(key=lambda x: x[0])
    # Deduplicate positions within 50 chars of each other
    deduped = []
    last_pos = -100
    for pos, pri in boundaries:
        if pos - last_pos > 50:
            deduped.append(pos)
            last_pos = pos

    return deduped


def split_adaptive(text: str, strategy: ProcessingStrategy) -> list:
    """
    [F5] Smart chunker that respects logical boundaries.
    Never splits inside: fenced code blocks, $$ math blocks,
    theorem proofs, or algorithm bodies.
    """
    if len(text) <= strategy.sub_chunk_size:
        return [text]

    # Protected zones: code blocks and display math
    protected_ranges = []
    for pat in [r'```[\s\S]+?```', r'\$\$[\s\S]+?\$\$']:
        for m in re.finditer(pat, text, re.IGNORECASE):
            protected_ranges.append((m.start(), m.end()))
    protected_ranges.sort(key=lambda x: x[0])

    def is_safe_pos(pos: int) -> bool:
        return not any(start < pos < end for start, end in protected_ranges)

    def safe_next_pos(pos: int) -> int:
        for start, end in protected_ranges:
            if start <= pos < end:
                return end
        return pos

    # [F5] Get logical boundaries
    logical_bounds = find_logical_boundaries(text)

    chunks, pos = [], 0
    while pos < len(text):
        end = pos + strategy.sub_chunk_size
        if end >= len(text):
            chunks.append(text[pos:])
            break

        # Priority 1: logical boundary within window
        best_cut = -1
        for bound in logical_bounds:
            if pos < bound <= end and is_safe_pos(bound):
                best_cut = bound  # Take the latest one in window

        # Priority 2: natural text boundary
        if best_cut == -1:
            for sep in ['\n\n', '.\n', '. ', '\n']:
                candidate = text.rfind(sep, pos, end)
                if candidate != -1 and is_safe_pos(candidate):
                    best_cut = candidate
                    break

        # Priority 3: extend past protected block
        if best_cut == -1:
            best_cut = end
            for start, finish in protected_ranges:
                if start < best_cut <= finish:
                    best_cut = finish
                    break

        chunks.append(text[pos:best_cut].strip())
        next_pos = max(pos + 1, best_cut - strategy.overlap)
        pos = safe_next_pos(next_pos)

        if len(chunks) >= 12:
            chunks.append(text[pos:])
            break

    return [c for c in chunks if c.strip()]


# ════════════════════════════════════════════════════════════
#  AGENT 2 — SUMMARIZATION
# ════════════════════════════════════════════════════════════

# [G5] Quality threshold is adaptive — complex sections need higher quality.
# Base is 0.38; add up to 0.15 based on complexity_score.
# This is a module-level default; _adaptive_threshold() is called per-chunk.
_QUALITY_THRESHOLD = 0.40

def _adaptive_threshold(profile: ChunkProfile) -> float:
    """[G5] Returns quality threshold scaled to content complexity."""
    base      = 0.35
    c_bonus   = profile.complexity_score * 0.15   # 0.0 – 0.15
    proof_add = 0.05 if profile.has_proofs else 0.0
    return min(base + c_bonus + proof_add, 0.55)


def _summarize_subchunk(text: str, source: str, profile: ChunkProfile,
                         strategy: ProcessingStrategy,
                         part_n: int, total: int) -> str:
    prompt = PromptBuilder.summary(text, profile, part_n, total)

    # [F6] Choose system prompt based on content type
    if profile.has_proofs or (profile.has_math and profile.theorem_count > 0):
        system = PromptBuilder.MATH_SYSTEM
    else:
        system = PromptBuilder.SUMMARY_SYSTEM

    best, best_q = "", 0.0

    for attempt, (use_fb, temp) in enumerate(
            [(False, 0.0), (False, 0.2), (True, 0.1)], 1):
        p   = PromptBuilder.summary_fallback(text, attempt) if use_fb else prompt
        raw = call_model([{"role": "user", "content": p}],
                         max_tokens=strategy.max_tokens, temp=temp,
                         retries=1, system=system)  # [F6] pass system
        out = _clean(raw)
        q   = _score_summary(out, profile)
        if q > best_q:
            best, best_q = out, q
        if out and q >= _adaptive_threshold(profile):  # [G5]
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


def summarize_chunk(chunk_text: str, label: str,
                    prev_context: str = "") -> dict:
    """
    [G8] prev_context: a short headline from the previous section summary.
    This gives the model a thread so it can write 'building on X from the
    previous section' instead of treating every chunk as an isolated island.
    """
    profile  = profile_chunk(chunk_text)
    strategy = decide_strategy(profile, "summarize")

    content_flags = []
    if profile.has_code:    content_flags.append(f"code({profile.lang})")
    if profile.has_math:    content_flags.append("math")
    if profile.has_proofs:  content_flags.append(f"proofs({profile.theorem_count})")  # [F4]
    if profile.has_tables:  content_flags.append("tables")
    log(f"  [{' + '.join(content_flags) or 'text'} | "
        f"c={profile.complexity_score:.2f} | {profile.size_bucket} | "
        f"tokens={strategy.max_tokens}]")

    subs  = split_adaptive(chunk_text, strategy)
    total = len(subs)
    if total > 1:
        log(f"  -> {total} sub-chunks", "progress")

    # [A2] Pass prev_context as instance variable scoped to this call only.
    # Using class attribute caused race condition when parallel was attempted.
    # Now stored as a thread-local on the current call stack.
    PromptBuilder._prev_context = prev_context  # single-threaded — safe

    results = []
    for i, sub in enumerate(subs, 1):
        sub_p = profile_chunk(sub)
        if total > 1:
            log(f"  -> sub {i}/{total} ({len(sub):,} chars)", "progress")
        results.append(_summarize_subchunk(sub, chunk_text, sub_p, strategy, i, total))
        if i < total:
            time.sleep(0.3)

    summary_txt = _merge_subchunks(results, profile)

    # [G8] Extract headline for next chunk: first sentence of the summary
    headline = ""
    if summary_txt:
        first_sent = re.split(r'(?<=[.!?])\s+', summary_txt.strip())
        headline   = first_sent[0][:120] if first_sent else ""

    return {
        "section":       label,
        "summary_text":  summary_txt,
        "_headline":     headline,   # [G8] passed to next chunk as prev_context
        "_has_code":     profile.has_code,
        "_has_math":     profile.has_math,
        "_has_proofs":   profile.has_proofs,    # [F4]
        "_theorem_count":profile.theorem_count,  # [F4]
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

    # [A1] Sequential summarization — preserves G8 context thread correctly.
    # Parallel was removed because:
    #   1. PromptBuilder._prev_context is shared state → race condition [A2]
    #   2. G8 context thread requires sequential order to pass headlines
    # Speed gains come from P2 (session reuse), P3 (faster retries),
    # P4 (dynamic tokens), P5 (skip LLM when not needed) instead.

    for idx, start in enumerate(range(0, len(keys), chunk_size)):
        batch      = keys[start:start+chunk_size]
        label      = f"Sections {batch[0]}-{batch[-1]}" if len(batch)>1 else f"Section {batch[0]}"
        chunk_text = _chunk_text(pages, batch)
        if not chunk_text.strip():
            continue

        log(f"[{idx+1}/{n}] {label} ({len(chunk_text):,} chars)", "progress")
        # [G8] Pass previous section headline as context (safe — sequential)
        prev_ctx = summaries[-1].get("_headline", "") if summaries else ""
        res = summarize_chunk(chunk_text, label, prev_context=prev_ctx)
        summaries.append(res)

        txt = res.get("summary_text", "")
        if not txt or "Processing failed" in txt:
            failed += 1
            log(f"failed: {label}", "warn")
        else:
            flags = []
            if res.get("_has_code"):   flags.append("code")
            if res.get("_has_math"):   flags.append("math")
            if res.get("_has_proofs"): flags.append(f"proofs({res.get('_theorem_count',0)})")
            sub = f" ({res['_sub_count']} parts)" if res.get("_sub_count",1)>1 else ""
            log(f"{label}{sub} [{'/'.join(flags) or 'text'}] | {len(txt):,} chars", "ok")

    log(f"{failed}/{len(summaries)} failed" if failed else "all sections done",
        "warn" if failed else "ok")

    overview = None
    if do_overview and len(summaries) >= 2:
        log("writing book overview...", "progress")
        # [G3] Use Key Exam Points from each section, not raw first-300-chars.
        # Key Exam Points are the densest signal of what each section actually covers.
        snippet_parts = []
        for s in summaries:
            txt = s.get("summary_text", "")
            if not txt:
                continue
            # Extract Key Exam Points block if present
            exam_match = re.search(
                r'Key\s+Exam\s+Points[:\s]*([\s\S]+?)(?:\n\n|\Z)',
                txt, re.IGNORECASE
            )
            if exam_match:
                points = exam_match.group(1).strip()[:400]
                snippet_parts.append(f"[{s['section']}]\nKey points:\n{points}")
            else:
                # Fallback: last 300 chars tends to be more conclusive than first 300
                snippet_parts.append(f"[{s['section']}]\n{txt[-300:].strip()}")
        snippets = "\n\n---\n\n".join(snippet_parts)
        raw      = call_model(
            [{"role":"user","content":PromptBuilder.book_overview(snippets)}],
            max_tokens=700, temp=0.1)
        overview = _clean(raw)
        log("overview done" if overview else "overview failed",
            "ok" if overview else "warn")

    out  = os.path.join(out_dir, "SUMMARY.md")
    txts = []
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Study Summary\n\n")
        f.write(f"*{len(keys)} sections | v25.0*\n\n")
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

    # [A3] Questions are safe to parallelize — each batch is fully independent.
    # No shared state, no context thread needed.
    def _gen_questions_batch(args):
        """Fully self-contained — safe to run in parallel."""
        idx, batch, label, chunk_text = args
        profile  = profile_chunk(chunk_text)
        strategy = decide_strategy(profile, "questions")
        log(f"[{idx+1}/{n}] questions: {label}...")
        subs, results = split_adaptive(chunk_text, strategy), []
        for si, sub in enumerate(subs):
            sub_p = profile_chunk(sub)
            sub_p.__dict__['_content_limit'] = strategy.content_limit
            lbl   = f"{label} p{si+1}" if len(subs) > 1 else label
            raw   = None
            for temp in [0.0, 0.15]:
                raw = call_model(
                    [{"role":"user","content":PromptBuilder.questions(sub, lbl, sub_p, lang_rule)}],
                    max_tokens=strategy.max_tokens, temp=temp,
                    system=PromptBuilder.JSON_SYSTEM)
                res = parse_json(raw, "questions")
                if res.data and res.data.get("questions") and res.quality > 0.3:
                    results.append(res.data)
                    break
                log(f"  sub {si+1} q={res.quality:.2f} -> retry", "warn")
            else:
                log(f"  sub {si+1} failed", "warn")
                if raw:
                    with open(os.path.join(out_dir, f"_qraw_{batch[0]}_{si}.txt"),
                              "w", encoding="utf-8") as fb:
                        fb.write(raw)
        return idx, label, batch, results

    # Build batch list
    q_batches = []
    for idx, start in enumerate(range(0, len(keys), chunk_size)):
        batch      = keys[start:start+chunk_size]
        label      = f"sections {batch[0]}-{batch[-1]}" if len(batch) > 1 else f"section {batch[0]}"
        chunk_text = _chunk_text(pages, batch)
        if chunk_text.strip():
            q_batches.append((idx, batch, label, chunk_text))

    # Run parallel
    q_results_map = {}
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_PARALLEL_CHUNKS) as executor:
        futs = {executor.submit(_gen_questions_batch, b): b for b in q_batches}
        for fut in concurrent.futures.as_completed(futs):
            try:
                idx, label, batch, results = fut.result()
                q_results_map[idx] = (label, batch, results)
            except Exception as e:
                log(f"questions batch error: {e}", "err")

    # Merge in order
    for idx in sorted(q_results_map.keys()):
        label, batch, results = q_results_map[idx]
        if results:
            if len(results) == 1:
                merged = results[0]
            else:
                merged = {"section": label, "topic": results[0].get("topic", label),
                          "questions": [], "total_marks": 0}
                for qid, q in enumerate(
                        (q for r in results for q in r.get("questions", [])), 1):
                    q["id"] = qid
                    merged["questions"].append(q)
                    merged["total_marks"] += q.get("marks", 0)
                merged["questions"]   = merged["questions"][:6]
                merged["total_marks"] = sum(q.get("marks", 0)
                                            for q in merged["questions"])
            all_chunks.append(merged)
            qc = len(merged["questions"]); mk = merged.get("total_marks", 0)
            total_q += qc; total_m += mk
            log(f"{qc} questions | {mk} marks", "ok")
        else:
            failed += 1
            log(f"failed: {label}", "warn")

    icons  = {"mcq":"🔤","concept":"💡","apply":"🔍","trace":"🔍","debug":"🐛",
               "design":"🏗","prove":"📐","calculate":"🧮","compare":"⚖️"}
    blooms = {"L1_remember":"🔵","L2_understand":"🟢","L3_apply":"🟡",
               "L4_analyze":"🟠","L5_evaluate":"🔴","L6_create":"🟣"}

    out = os.path.join(out_dir, "QUESTIONS.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {book_name} — Question Bank\n\n")
        f.write(f"*{total_q} questions | {total_m} marks | v25.0*\n\n---\n\n")
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
        cut = -1
        for sep in ['\n### ', '\n## ', '\n\n', '\n']:
            cut = text.rfind(sep, 0, max_chars)
            if cut != -1: break
        if cut == -1: cut = max_chars
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    return [c for c in chunks if c.strip()]


def run_translation(summary_text: str, out_dir: str, book_name: str,
                    pages: dict = None, keys: list = None) -> str:
    """
    [S3] Translation now works on raw source pages when available.
    Falls back to summary_text if pages not provided.
    Using source text means technical definitions and code stay verbatim.
    """
    # [S3] Prefer raw source text — richer and more accurate than summary
    if pages and keys:
        source_text = "\n\n---\n\n".join(
            pages[k] for k in keys if k in pages
        )
        log("translating from raw source text", "ok")
    else:
        source_text = summary_text
        log("translating from summary (no source pages provided)", "warn")

    if not source_text.strip():
        out = os.path.join(out_dir, "TRANSLATED.md")
        with open(out,"w",encoding="utf-8") as f:
            f.write(f"# {book_name} - ترجمة بالعامية المصرية\n\n*لا يوجد محتوى.*\n")
        return out

    chunks = _split_for_translation(source_text, max_chars=1500)
    log(f"translating {len(chunks)} chunks...")
    parts  = []

    for i, chunk in enumerate(chunks, 1):
        log(f"  chunk {i}/{len(chunks)} ({len(chunk):,} chars)", "progress")

        # Clean Marker OCR artifacts before protecting terms
        # "FROM" appearing as standalone word is a Marker extraction glitch
        clean_chunk = re.sub(r'\bFROM\b', 'من', chunk)
        clean_chunk = re.sub(r'\bWHERE\b(?!\s+[A-Z])', 'حيث', clean_chunk)

        # [F8] Protect technical terms before translation
        protected_chunk, term_map = protect_technical_terms(clean_chunk)

        raw        = call_model(
            [{"role":"user","content":PromptBuilder.translate(protected_chunk)}],
            max_tokens=2000, temp=0.0, retries=3, timeout=400,
            system=PromptBuilder.TRANSLATE_SYSTEM)
        translated = _clean(raw)

        if translated and len(translated.strip()) > 50:
            # [F8] Restore technical terms
            translated = restore_technical_terms(translated, term_map)

            # ── Non-Arabic detection + aggressive retry loop ────────────
            _non_arab_pat = re.compile(
                r'[\u4e00-\u9fff'  # Chinese
                r'\u3040-\u309f'   # Hiragana
                r'\u30a0-\u30ff'   # Katakana
                r'\u0400-\u04ff'   # Cyrillic
                r'\u0900-\u097f'   # Devanagari
                r']')

            def _non_arab_ratio(txt):
                return len(_non_arab_pat.findall(txt)) / max(len(txt), 1)

            def _strip_non_arab(txt):
                """Remove non-Arabic/English characters entirely."""
                return _non_arab_pat.sub('', txt).strip()

            ratio = _non_arab_ratio(translated)

            if ratio > 0.01:   # even 1% is unacceptable
                log(f"  chunk {i}: non-Arabic {ratio:.0%} — retrying (up to 3x)", "warn")
                best_t, best_r = translated, ratio

                for attempt in range(1, 4):
                    retry_prompt = (
                        f"⚠️ اكتب بالعربية فقط. ممنوع الصيني أو أي لغة غير العربية.\n"
                        f"لو مش قادر تترجم جملة، اكتبها بالإنجليزي مش بأي لغة تانية.\n\n"
                        f"{PromptBuilder.translate(protected_chunk)}"
                    )
                    raw2 = call_model(
                        [{"role": "user", "content": retry_prompt}],
                        max_tokens=3500, temp=0.1 * attempt, retries=2, timeout=700,
                        system=PromptBuilder.TRANSLATE_SYSTEM
                    )
                    t2 = _clean(raw2)
                    if t2 and len(t2.strip()) > 50:
                        t2 = restore_technical_terms(t2, term_map)
                        r2 = _non_arab_ratio(t2)
                        if r2 < best_r:
                            best_t, best_r = t2, r2
                        if best_r < 0.01:
                            break

                # Last resort: strip the offending characters
                if best_r > 0.01:
                    log(f"  chunk {i}: still {best_r:.0%} after retries — stripping chars", "warn")
                    best_t = _strip_non_arab(best_t)

                translated = best_t

            # Verify code blocks survived — re-inject if lost
            for code in re.findall(r'```[\s\S]+?```', chunk):
                if code not in translated:
                    log(f"  chunk {i}: code block lost - restoring", "warn")
                    translated += f"\n\n{code}"
            parts.append(translated)
        else:
            # [G6] Mark untranslated chunks visibly so user knows what happened
            log(f"  chunk {i}: translation failed - keeping English with notice", "warn")
            notice = (
                "\n\n> ⚠️ **ملاحظة:** الجزء ده اتحفظ بالإنجليزي لأن الترجمة فشلت.\n\n"
            )
            parts.append(notice + chunk)

    out = os.path.join(out_dir, "TRANSLATED.md")
    with open(out,"w",encoding="utf-8") as f:
        f.write(f"# {book_name} - ملخص بالعامية المصرية\n\n")
        f.write(f"*v25.0 | المصطلحات التقنية بالإنجليزي | الأكواد والمعادلات محفوظة*\n\n---\n\n")
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

    # [G4] Extract Key Exam Points from summaries instead of raw_terms regex.
    # Key Exam Points are actual content; raw_terms are just capitalized words.
    def _extract_key_concepts(summary_text: str, raw_terms: list) -> list:
        if not summary_text:
            return raw_terms[:8]
        # Pull bullet points from Key Exam Points section
        exam_match = re.search(
            r'Key\s+Exam\s+Points[:\s]*([\s\S]+?)(?:\n\n|\Z)',
            summary_text, re.IGNORECASE
        )
        if exam_match:
            bullets = re.findall(r'[-•*]\s*(.+)', exam_match.group(1))
            # Shorten each bullet to first 60 chars for the concept map prompt
            concepts = [b.strip()[:60] for b in bullets if len(b.strip()) > 10]
            if concepts:
                return concepts[:6]
        # Fallback: raw_terms
        return raw_terms[:8]

    topics = [{"section":  s.get("section",""),
               "concepts": _extract_key_concepts(
                   s.get("summary_text",""),
                   s.get("_raw_terms",[])
               )}
              for s in summaries]

    raw    = call_model(
        [{"role":"user","content":PromptBuilder.concept_map(topics)}],
        max_tokens=1800, temp=0.1, system=PromptBuilder.JSON_SYSTEM)
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


# ════════════════════════════════════════════════════════════
#  AGENT 6 — RAG CHAT (zero external dependencies)
# ════════════════════════════════════════════════════════════
#
#  Architecture (v18 — Semantic Hybrid):
#    Build:  EXTRACTED.md → chunks → sklearn TF-IDF matrix + BM25 → INDEX.pkl
#    Query:  question → Arabic expansion → hybrid score → top-K → LLM answer
#
#  Hybrid score = 0.6 × cosine(TF-IDF) + 0.4 × BM25  [M2]
#  Query expansion maps Arabic terms to English synonyms [M3]
#  Only numpy + sklearn needed — no FAISS, no ChromaDB, no internet
# ════════════════════════════════════════════════════════════

# ── RAG Configuration ────────────────────────────────────────
RAG_TOP_K       = 5     # عدد الـ chunks اللي بنجيبهم
RAG_MAX_CONTEXT = 3000  # max chars بنبعتهم للنموذج
RAG_INDEX_FILE  = "INDEX.pkl"

RAG_SYSTEM = (
    "You are a helpful study assistant for a CS/Math textbook. "
    "Answer questions using ONLY the provided context sections. "
    "Always cite which section your answer comes from. "
    "If the answer is not in the context, say: "
    "'This topic is not covered in the sections I have access to.' "
    "Keep answers clear and student-friendly. "
    "For code or math, preserve it exactly as it appears in the context."
)


# ── Data structures ───────────────────────────────────────────

@dataclass
class RAGChunk:
    """Single retrievable unit — one section or sub-section."""
    chunk_id:   int
    section:    str          # e.g. "Sections 3-4"
    text:       str          # the summary text
    char_count: int = 0
    has_code:   bool = False
    has_math:   bool = False

    def __post_init__(self):
        self.char_count = len(self.text)
        self.has_code   = bool(re.search(r'```|def |int main', self.text))
        self.has_math   = bool(re.search(r'\$|theorem|proof|O\(', self.text, re.IGNORECASE))


@dataclass
class RAGIndex:
    """Full index for one book."""
    book_name:  str
    chunks:     List[RAGChunk]
    vocab:      Dict[str, int]          # term → global index
    idf:        Dict[str, float]        # term → IDF score
    tf_matrix:  Dict[int, Dict[str, float]]  # chunk_id → {term: tf}
    built_at:   str = ""
    avgdl:        float = 0.0        # [S6] cached avg doc length
    source_hash:  str  = ""          # [S5] hash of source file
    tfidf_matrix: object = None      # [M5] sklearn sparse matrix
    tfidf_vectorizer: object = None  # [M5] fitted TfidfVectorizer
    df_cache: Dict[str, int] = None  # [P6] precomputed document frequencies

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self, f)
        log(f"RAG index saved → {path}  ({len(self.chunks)} chunks)", "ok")

    @staticmethod
    def load(path: str) -> "RAGIndex":
        with open(path, "rb") as f:
            idx = pickle.load(f)
        log(f"RAG index loaded ← {path}  ({len(idx.chunks)} chunks)", "ok")
        return idx


# ── Text preprocessing ────────────────────────────────────────

def _rag_tokenize(text: str) -> List[str]:
    """
    Simple tokenizer for TF-IDF.
    Lowercases, removes punctuation, keeps technical terms intact.
    e.g. "O(n log n)" → ["o", "n", "log", "n"]
         "BFS algorithm" → ["bfs", "algorithm"]
    """
    # Preserve code identifiers: snake_case, camelCase
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)   # camelCase → camel Case
    text = text.lower()
    text = re.sub(r'[^a-z0-9_\s]', ' ', text)
    tokens = text.split()
    # Remove very short tokens and pure numbers
    tokens = [t for t in tokens if len(t) > 1 and not t.isdigit()]
    return tokens


_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "this", "that", "these", "those", "it", "its", "we", "our", "they",
    "their", "he", "she", "his", "her", "you", "your", "i", "my",
    "in", "on", "at", "by", "for", "with", "about", "from", "to", "of",
    "and", "or", "but", "not", "so", "yet", "both", "either", "neither",
    "if", "then", "than", "as", "into", "through", "during", "before",
    "after", "above", "below", "between", "each", "more", "most",
    "such", "no", "only", "same", "also", "very", "just", "section",
    "chapter", "page", "note", "example", "following", "shown", "given",
}

def _rag_terms(text: str) -> List[str]:
    """Tokenize + remove stopwords."""
    return [t for t in _rag_tokenize(text) if t not in _STOPWORDS]


# ── Index builder ─────────────────────────────────────────────

def _file_hash(path: str) -> str:
    """[S5] Fast hash of a file for stale-index detection."""
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()[:12]


def build_rag_index(source_path: str, out_dir: str, book_name: str) -> "RAGIndex":
    """
    [S1] Builds RAG index from EXTRACTED.md (raw source), NOT SUMMARY.md.
    Using raw text means the index contains every fact in the book —
    nothing is lost to summarization.

    [S5] Saves a hash of the source file in the index so we can detect
    when the index is stale and needs rebuilding.

    [S6] Computes and caches avgdl once at build time — not per query.
    """
    import datetime
    log("building RAG index from source text...", "progress")

    if not os.path.exists(source_path):
        log(f"source file not found: {source_path}", "err")
        return None

    text        = open(source_path, encoding="utf-8").read()
    source_hash = _file_hash(source_path)

    # ── Split EXTRACTED.md into retrievable chunks ────────────
    # Strategy: use the same _split_into_sections logic so chunk
    # boundaries match the summarization pipeline exactly.
    pages_dict = _split_into_sections(text)
    if not pages_dict:
        log("could not split source into sections", "err")
        return None

    keys = sorted(pages_dict.keys())
    log(f"  {len(keys)} sections from source", "ok")

    # Group into chunks of RAG_CHUNK_PAGES pages for retrieval granularity
    RAG_CHUNK_PAGES = 3   # smaller than summarization chunks → finer retrieval
    raw_chunks = []
    for start in range(0, len(keys), RAG_CHUNK_PAGES):
        batch   = keys[start : start + RAG_CHUNK_PAGES]
        label   = (f"Sections {batch[0]}-{batch[-1]}"
                   if len(batch) > 1 else f"Section {batch[0]}")
        body    = "\n\n".join(pages_dict[k] for k in batch if k in pages_dict)
        if body.strip():
            raw_chunks.append((label, body.strip()))

    if not raw_chunks:
        log("no content found in source", "err")
        return None

    log(f"  {len(raw_chunks)} retrieval chunks built", "ok")

    # ── Build RAGChunk objects ────────────────────────────────
    chunks = [
        RAGChunk(chunk_id=i, section=sec, text=body)
        for i, (sec, body) in enumerate(raw_chunks)
    ]

    # ── Compute TF-IDF ────────────────────────────────────────
    N  = len(chunks)
    df: Dict[str, int] = defaultdict(int)
    chunk_terms: List[List[str]] = []

    for chunk in chunks:
        terms = _rag_terms(chunk.text)
        chunk_terms.append(terms)
        for t in set(terms):
            df[t] += 1

    idf: Dict[str, float] = {
        t: math.log((N + 1) / (d + 1)) + 1.0
        for t, d in df.items()
    }

    tf_matrix: Dict[int, Dict[str, float]] = {}
    all_lengths = []
    for i, terms in enumerate(chunk_terms):
        all_lengths.append(len(terms))
        if not terms:
            tf_matrix[i] = {}
            continue
        counts = Counter(terms)
        total  = len(terms)
        tf_matrix[i] = {t: c / total for t, c in counts.items()}

    vocab  = {t: idx for idx, t in enumerate(sorted(idf.keys()))}
    avgdl  = sum(all_lengths) / max(N, 1)

    # [M5] Fit sklearn TF-IDF vectorizer on all chunk texts
    # Uses the same expanded tokenizer so Arabic queries work
    log("  fitting semantic TF-IDF vectorizer...", "progress")
    chunk_texts_expanded = [
        _expand_query(chunk.text) for chunk in chunks
    ]
    try:
        vectorizer = TfidfVectorizer(
            analyzer      = "word",
            token_pattern = r"[a-zA-Z؀-ۿ_]{2,}",
            min_df        = 1,
            max_df        = 0.95,
            sublinear_tf  = True,   # log(1+tf) — better for long docs
            max_features  = 50000,
        )
        tfidf_mat = vectorizer.fit_transform(chunk_texts_expanded)
        log(f"  TF-IDF matrix: {tfidf_mat.shape[0]}×{tfidf_mat.shape[1]}", "ok")
    except Exception as e:
        log(f"  TF-IDF vectorizer failed: {e} — falling back to BM25 only", "warn")
        vectorizer = None
        tfidf_mat  = None

    # [P6] Precompute document frequencies for BM25 — saves recomputing per query
    df_cache: Dict[str, int] = defaultdict(int)
    for chunk in chunks:
        for t in set(index_tf := index_tf if False else _rag_terms(chunk.text)):
            df_cache[t] += 1
    # Simpler: rebuild from tf_matrix
    df_cache2: Dict[str, int] = defaultdict(int)
    for chunk_tf in tf_matrix.values():
        for t in chunk_tf:
            df_cache2[t] += 1

    index = RAGIndex(
        book_name        = book_name,
        chunks           = chunks,
        vocab            = vocab,
        idf              = idf,
        tf_matrix        = tf_matrix,
        built_at         = datetime.datetime.now().isoformat()[:16],
        avgdl            = avgdl,
        source_hash      = source_hash,
        tfidf_matrix     = tfidf_mat,
        tfidf_vectorizer = vectorizer,
        df_cache         = dict(df_cache2),
    )

    idx_path = os.path.join(out_dir, RAG_INDEX_FILE)
    index.save(idx_path)
    log(f"  vocab={len(vocab):,} terms | avgdl={avgdl:.0f} | hash={source_hash}", "ok")
    return index


# ── Retrieval ─────────────────────────────────────────────────

# ── [M3] Arabic ↔ English query expansion ────────────────────
# Maps Arabic question terms to English equivalents so BM25
# can match even when the book is in English.
_AR_EN_SYNONYMS: Dict[str, List[str]] = {
    # Data Structures
    "مصفوفة":      ["array", "list"],
    "قائمة":       ["list", "linked list", "queue"],
    "مكدس":        ["stack", "LIFO"],
    "طابور":       ["queue", "FIFO"],
    "شجرة":        ["tree", "binary tree", "BST"],
    "رسم بياني":   ["graph", "directed", "undirected"],
    "جدول تجزئة": ["hash table", "hash map", "dictionary"],
    "كومة":        ["heap", "priority queue"],
    # Algorithms
    "خوارزمية":    ["algorithm", "procedure"],
    "ترتيب":       ["sort", "sorting"],
    "بحث":         ["search", "searching", "find"],
    "تعقيد":       ["complexity", "Big O", "time complexity"],
    "تكرار":       ["recursion", "recursive", "iteration"],
    "ديناميكي":    ["dynamic programming", "DP", "memoization"],
    "جشع":         ["greedy", "greedy algorithm"],
    "فرق وسد":     ["divide and conquer", "merge sort"],
    # Math / CS Theory
    "نظرية":       ["theorem", "lemma", "corollary"],
    "إثبات":       ["proof", "prove", "derivation"],
    "تعريف":       ["definition", "define"],
    "معادلة":      ["equation", "formula", "expression"],
    "تكرارية":     ["recurrence", "recurrence relation"],
    "احتمال":      ["probability", "random", "expected"],
    # DB
    "قاعدة بيانات": ["database", "SQL", "relation"],
    "استعلام":     ["query", "SELECT", "JOIN"],
    # General
    "شرح":         ["explain", "description", "definition"],
    "مثال":        ["example", "instance", "case"],
    "فرق":         ["difference", "compare", "versus", "vs"],
    "أفضل":        ["best", "optimal", "efficient"],
    "أسوأ":        ["worst", "inefficient"],
    "وقت":         ["time", "complexity", "performance"],
    "مساحة":       ["space", "memory", "storage"],
}

# Reverse map: English → Arabic (for completeness)
_EN_AR_SYNONYMS: Dict[str, List[str]] = {}
for ar, en_list in _AR_EN_SYNONYMS.items():
    for en in en_list:
        _EN_AR_SYNONYMS.setdefault(en, []).append(ar)


def _expand_query(question: str) -> str:
    """
    [M3] Expand query with Arabic↔English synonyms.
    Returns enriched query string for TF-IDF vectorizer.
    """
    tokens   = _rag_tokenize(question)
    expanded = list(tokens)

    for token in tokens:
        # Arabic term → English synonyms
        if token in _AR_EN_SYNONYMS:
            expanded.extend(_AR_EN_SYNONYMS[token])
        # English term → any Arabic synonyms (helps cross-lingual)
        if token in _EN_AR_SYNONYMS:
            expanded.extend(_EN_AR_SYNONYMS[token])

    # Also try multi-word Arabic phrases
    q_lower = question.lower()
    for ar_phrase, en_list in _AR_EN_SYNONYMS.items():
        if ar_phrase in q_lower:
            expanded.extend(en_list)

    return " ".join(dict.fromkeys(expanded))  # dedup, preserve order


# ── [M1] Semantic cosine scoring ─────────────────────────────

def _semantic_score(query: str, index: RAGIndex) -> np.ndarray:
    """
    [M1] Computes cosine similarity between query TF-IDF vector
    and all chunk TF-IDF vectors using sklearn.
    Returns array of scores, one per chunk.
    """
    if index.tfidf_vectorizer is None or index.tfidf_matrix is None:
        return np.zeros(len(index.chunks))

    try:
        q_vec  = index.tfidf_vectorizer.transform([query])
        scores = cosine_similarity(q_vec, index.tfidf_matrix)[0]
        return scores
    except Exception:
        return np.zeros(len(index.chunks))


# ── [R2] BM25 scoring (kept for hybrid) ──────────────────────

def _bm25_score(query_terms: List[str], chunk: RAGChunk,
                index: RAGIndex,
                k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 scoring with [S6] cached avgdl."""
    tf    = index.tf_matrix.get(chunk.chunk_id, {})
    N     = len(index.chunks)
    avgdl = index.avgdl if index.avgdl > 0 else 1.0
    dl    = len(_rag_terms(chunk.text))

    score = 0.0
    for t in query_terms:
        if t not in index.idf:
            continue
        # [P6] Use precomputed df_cache — O(1) instead of O(chunks)
        df_val  = (index.df_cache or {}).get(t, 0) if index.df_cache else \
                  sum(1 for c in index.chunks
                      if t in index.tf_matrix.get(c.chunk_id, {}))
        idf_val = math.log((N - df_val + 0.5) / (df_val + 0.5) + 1)
        tf_raw  = tf.get(t, 0.0) * dl
        bm25    = idf_val * (tf_raw * (k1 + 1)) / (
                  tf_raw + k1 * (1 - b + b * dl / max(avgdl, 1)))
        score  += bm25
    return score


# ── [M2] Hybrid retrieval ─────────────────────────────────────

# Minimum score to return a chunk — prevents irrelevant results [M4]
_MIN_HYBRID_SCORE = 0.02

def retrieve(question: str, index: RAGIndex,
             top_k: int = RAG_TOP_K) -> List[Tuple[float, RAGChunk]]:
    """
    [M2] Hybrid semantic + BM25 retrieval.

    Score = 0.6 × cosine_similarity(TF-IDF) + 0.4 × BM25_normalized

    Why hybrid?
    - Semantic (TF-IDF cosine): catches meaning even with different words
      e.g. "ترتيب" matches "sorting" after query expansion
    - BM25: catches exact technical terms that must match precisely
      e.g. "Dijkstra" must appear verbatim

    [M3] Query is expanded with Arabic↔English synonyms before scoring.
    [M4] Chunks below _MIN_HYBRID_SCORE are filtered out.
    """
    if not question.strip():
        return []

    # [M3] Expand query with synonyms
    expanded_query = _expand_query(question)
    q_terms        = _rag_terms(expanded_query)

    if not q_terms and not question.strip():
        return []

    # [M1] Semantic scores for all chunks at once (vectorized)
    sem_scores = _semantic_score(expanded_query, index)

    # Normalize semantic scores to [0, 1]
    sem_max = float(sem_scores.max()) if sem_scores.max() > 0 else 1.0
    sem_norm = sem_scores / sem_max

    # BM25 scores per chunk
    bm25_raw = np.array([
        _bm25_score(q_terms, chunk, index)
        for chunk in index.chunks
    ])
    bm25_max  = float(bm25_raw.max()) if bm25_raw.max() > 0 else 1.0
    bm25_norm = bm25_raw / bm25_max

    # [M2] Weighted hybrid
    hybrid = 0.6 * sem_norm + 0.4 * bm25_norm

    # Content-type bonus (unchanged from v17)
    q_lower = question.lower()
    for i, chunk in enumerate(index.chunks):
        if chunk.has_code and any(w in q_lower for w in
            ["code", "algorithm", "function", "implement",
             "complexity", "pseudocode", "كود", "خوارزمية"]):
            hybrid[i] *= 1.25
        if chunk.has_math and any(w in q_lower for w in
            ["theorem", "proof", "formula", "equation", "prove",
             "derive", "نظرية", "معادلة", "إثبات"]):
            hybrid[i] *= 1.25

    # [M4] Filter below minimum threshold
    scored = [
        (float(hybrid[i]), index.chunks[i])
        for i in range(len(index.chunks))
        if float(hybrid[i]) >= _MIN_HYBRID_SCORE
    ]

    return heapq.nlargest(top_k, scored, key=lambda x: x[0])


# ── Answer generation ─────────────────────────────────────────

def _build_context(retrieved: List[Tuple[float, RAGChunk]],
                   max_chars: int = RAG_MAX_CONTEXT) -> str:
    """Assembles retrieved chunks into a context string for the LLM."""
    parts = []
    total = 0
    for score, chunk in retrieved:
        header = f"[{chunk.section}]"
        body   = chunk.text[:max_chars - total - len(header) - 10]
        if not body.strip():
            break
        parts.append(f"{header}\n{body}")
        total += len(body) + len(header)
        if total >= max_chars:
            break
    return "\n\n---\n\n".join(parts)


# [S4] Arabic-first system prompt for chat
RAG_ARABIC_SYSTEM = (
    "أنت مساعد مذاكرة ذكي متخصص في شرح محتوى الكتب الدراسية. "
    "قواعد الإجابة:"
    "\n1. أجب دائماً بالعربية الفصحى أو العامية المصرية حسب طريقة السؤال."
    "\n2. استخدم فقط المعلومات الموجودة في النص المُقدَّم — لا تضف أي معلومات من عندك."
    "\n3. لو السؤال عن كود أو معادلة، انقل النص الأصلي verbatim ثم اشرحه."
    "\n4. اذكر رقم الـ section اللي جبت منه الإجابة."
    "\n5. لو المعلومة مش موجودة في النص، قول: 'الموضوع ده مش موجود في الأجزاء اللي عندي من الكتاب.'"
    "\n6. لو السؤال عن كود: اكتب الكود كما هو بالضبط في code block، ثم اشرح كل سطر."
    "\n7. لو السؤال عن نظرية أو إثبات: اكتب نص النظرية أولاً ثم اشرح الفكرة الأساسية."
)


def answer_question(question: str, index: RAGIndex,
                    history: List[Dict] = None) -> Tuple[str, List[str]]:
    """
    [S4] Arabic-first Q&A with verbatim source quotes.
    Retrieves from raw source text → LLM answers in Arabic
    with exact quotes from the book when relevant.
    """
    retrieved = retrieve(question, index)
    if not retrieved:
        return (
            "الموضوع ده مش موجود في الأجزاء اللي عندي من الكتاب. "
            "حاول تعيد صياغة السؤال أو اسأل عن موضوع تاني.", []
        )

    context      = _build_context(retrieved)
    cited        = [chunk.section for _, chunk in retrieved]
    cited_unique = list(dict.fromkeys(cited))

    # [R4] Conversation memory — last 6 exchanges
    messages = []
    if history:
        messages.extend(history[-6:])

    # [S4] Prompt forces Arabic response + verbatim quotes
    messages.append({"role": "user", "content": (
        f"النص من الكتاب (استخدم فقط هذا النص للإجابة):\n"
        f"{'─'*50}\n{context}\n{'─'*50}\n\n"
        f"السؤال: {question}\n\n"
        f"تعليمات:\n"
        f"- أجب بالعربية\n"
        f"- لو فيه كود أو معادلة في النص، انقلها كما هي بالضبط ثم اشرحها\n"
        f"- اذكر في نهاية إجابتك: 'المصدر: [اسم الـ section]'"
    )})

    raw = call_model(
        messages,
        max_tokens=900,
        temp=0.15,
        system=RAG_ARABIC_SYSTEM,
        retries=2
    )
    answer = _clean(raw) if raw else "عذراً، حصل خطأ في توليد الإجابة. حاول تاني."

    return answer, cited_unique


# ── Interactive CLI chat loop ─────────────────────────────────

def run_chat(out_dir: str, book_name: str):
    """
    [R5] Interactive chat loop in the terminal.
    Builds or loads the RAG index, then starts Q&A session.
    """
    idx_path        = os.path.join(out_dir, RAG_INDEX_FILE)
    extracted_path  = os.path.join(out_dir, "EXTRACTED.md")

    # [S5] Load index, but rebuild if source file changed
    index = None
    if os.path.exists(idx_path):
        loaded = RAGIndex.load(idx_path)
        if (os.path.exists(extracted_path) and
                loaded.source_hash and
                loaded.source_hash != _file_hash(extracted_path)):
            log("source file changed — rebuilding index", "warn")
        else:
            index = loaded

    # [S1] Build from EXTRACTED.md (raw source), not SUMMARY.md
    if index is None:
        if os.path.exists(extracted_path):
            index = build_rag_index(extracted_path, out_dir, book_name)
            if not index:
                print("  ✗ Failed to build index.")
                return
        else:
            print("  ✗ EXTRACTED.md not found. Run --mode extract first.")
            return

    print(f"\n{'='*64}")
    print(f"  RAG Chat — {book_name}")
    print(f"  {len(index.chunks)} sections indexed | built {index.built_at}")
    print(f"{'='*64}")
    print("  اكتب سؤالك بالعربي أو الإنجليزي.")
    print("  اكتب 'خروج' أو 'quit' للخروج.")
    print("  اكتب 'مسح' أو 'clear' لمسح تاريخ المحادثة.")
    print(f"{'='*64}\n")

    history: List[Dict] = []
    q_count = 0

    while True:
        try:
            question = input("  سؤالك: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  وداعاً!")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "خروج", "bye"):
            print("  وداعاً! ربنا يوفقك في الامتحان 🎓")
            break

        if question.lower() in ("clear", "مسح", "reset"):
            history = []
            q_count = 0
            print("  ✓ تاريخ المحادثة اتمسح\n")
            continue

        q_count += 1
        log(f"Q{q_count}: retrieving...", "progress")

        answer, cited = answer_question(question, index, history)

        print(f"\n  {'─'*60}")
        print(f"  الإجابة:\n")
        # Word-wrap at 70 chars for readability
        for line in answer.split("\n"):
            print(f"    {line}")

        if cited:
            print(f"\n  المصادر: {' | '.join(cited)}")
        print(f"  {'─'*60}\n")

        # [R4] Update conversation history
        history.append({"role": "user",      "content": question})
        history.append({"role": "assistant", "content": answer})

    # Save chat log
    if q_count > 0:
        log_path = os.path.join(out_dir, "CHAT_LOG.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# {book_name} — Chat Log\n\n")
            for i in range(0, len(history), 2):
                q = history[i]["content"]
                a = history[i+1]["content"] if i+1 < len(history) else ""
                f.write(f"**Q:** {q}\n\n**A:** {a}\n\n---\n\n")
        log(f"chat log saved → {log_path}", "ok")


def main():
    global MARKER_API_URL, LLM_API_URL

    parser = argparse.ArgumentParser(description="PDF Agent Suite v25.0 - CS & Math Edition")
    parser.add_argument("--pdf",         required=True,  help="path to PDF")
    parser.add_argument("--mode",        default="all",
                        choices=["extract","summarize","translate","questions",
                                 "concept-map","chat","all"])
    parser.add_argument("--lang",        default="auto", choices=["ar","en","auto"])
    parser.add_argument("--page-from",   type=int, default=None)
    parser.add_argument("--page-to",     type=int, default=None)
    parser.add_argument("--chunk-size",  type=int, default=CHUNK_SIZE,
                        help=f"pages per chunk (default {CHUNK_SIZE}; use 3-4 for CLRS/dense books)")
    parser.add_argument("--no-overview", action="store_true")
    parser.add_argument("--output-dir",  default=OUTPUT_DIR)
    parser.add_argument("--marker-url",  default=MARKER_API_URL)
    parser.add_argument("--llm-url",     default=LLM_API_URL)
    args = parser.parse_args()

    MARKER_API_URL = args.marker_url.rstrip('/')
    LLM_API_URL    = args.llm_url

    if not os.path.exists(args.pdf):
        print(f"File not found: {args.pdf}"); sys.exit(1)

    name    = Path(args.pdf).stem
    out_dir = os.path.join(args.output_dir, name)
    os.makedirs(out_dir, exist_ok=True)

    # chunk_size is resolved later after extraction (needs pages_dict)
    # args.chunk_size == CHUNK_SIZE means "user didn't touch it" -> auto-detect
    _manual_chunk_size = (args.chunk_size if args.chunk_size != CHUNK_SIZE else None)

    print(f"\n{'='*64}")
    print(f"  PDF Agent Suite v25.0 — CS & Math Edition")
    print(f"{'='*64}")
    print(f"  PDF       : {args.pdf}")
    print(f"  Output    : {out_dir}")
    print(f"  Mode      : {args.mode} | Lang: {args.lang}")
    print(f"  Chunk     : {'manual=' + str(_manual_chunk_size) if _manual_chunk_size else 'auto-detect'}")
    print(f"  Sub-chunk : max {MAX_CHARS_PER_SUB:,} chars")
    print(f"  Model     : {MODEL_NAME}")
    print(f"  Fixes     : F1-F8 (v13) + F9 auto-chunk (v14)")
    print(f"{'='*64}\n")

    extracted  = os.path.join(out_dir, "EXTRACTED.md")
    pages_dict, page_keys, summaries, summary_text = {}, [], [], ""

    if args.mode in ("extract","summarize","translate","questions","concept-map","all"):
        print("--- AGENT 1: EXTRACTION ---")
        _need_extract = True
        if os.path.exists(extracted):
            # Smart skip: only reuse if same PDF (hash check)
            try:
                existing = open(extracted, encoding="utf-8").read(500)
                pdf_hash = _file_hash(args.pdf)
                if f"pdf_hash={pdf_hash}" in existing:
                    log(f"EXTRACTED.md up-to-date (hash match) — skipping", "ok")
                    _need_extract = False
                else:
                    log("EXTRACTED.md found but PDF changed — re-extracting", "warn")
            except Exception:
                pass
        if _need_extract:
            run_extraction(args.pdf, out_dir)

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
        if fp.has_code:   flags.append(f"code({fp.lang})")
        if fp.has_math:   flags.append("math")
        if fp.has_proofs: flags.append(f"proofs({fp.theorem_count})")
        if fp.has_tables: flags.append("tables")
        density = "DENSE" if avg_c > 5000 else ("NORMAL" if avg_c > 2000 else "LIGHT")

        print(f"\n  Document : {len(page_keys)} sections | {total_c:,} chars")
        print(f"  Avg/sect : {avg_c:,} chars [{density}]")
        print(f"  Content  : {', '.join(flags) or 'text'} | complexity={fp.complexity_score:.2f}")

        # [F9] Resolve chunk_size — manual overrides auto-detect
        print()
        print("--- CHUNK-SIZE DETECTION ---")
        if _manual_chunk_size:
            chunk_size = _manual_chunk_size
            log(f"manual override: chunk-size = {chunk_size}", "ok")
        else:
            chunk_size = auto_detect_chunk_size(pages_dict, page_keys)
        print()

    if args.mode in ("summarize","translate","all","concept-map"):
        print("--- AGENT 2: SUMMARIZATION (English) ---")
        _, summary_text, summaries = run_summarization(
            pages_dict, page_keys, out_dir, name, chunk_size,
            do_overview=not args.no_overview)
        print()

    if args.mode in ("questions","all"):
        print("--- AGENT 3: QUESTIONS ---")
        run_questions(pages_dict, page_keys, out_dir, name, chunk_size, args.lang)
        print()

    if args.mode in ("translate","all"):
        print("--- AGENT 4: TRANSLATION (Egyptian Arabic) ---")
        if not summary_text:
            sp = os.path.join(out_dir, "SUMMARY.md")
            if os.path.exists(sp):
                summary_text = open(sp, encoding="utf-8").read()
            else:
                print("Run --mode summarize first"); sys.exit(1)
        run_translation(summary_text, out_dir, name,
                         pages=pages_dict, keys=page_keys)  # [S3]
        print()

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

    if args.mode in ("chat",):
        print("--- AGENT 6: RAG CHAT ---")
        run_chat(out_dir, name)
        return

    # [S1] Auto-build RAG index from EXTRACTED.md after full pipeline
    if args.mode == "all":
        extracted_path = os.path.join(out_dir, "EXTRACTED.md")
        if os.path.exists(extracted_path):
            print("--- AGENT 6: RAG INDEX (from source) ---")
            build_rag_index(extracted_path, out_dir, name)
            print()

    print(f"{'='*64}")
    print(f"  Done!  Output: {out_dir}/")
    print(f"{'='*64}")
    for fname, desc in [
        ("EXTRACTED_RAW.md","raw from Marker (debug)"),
        ("EXTRACTED.md",   "clean text — used by all agents"),
        ("SUMMARY.md",     "English summary"),
        ("QUESTIONS.md",   "exam questions"),
        ("TRANSLATED.md",  "Egyptian Arabic translation"),
        ("CONCEPT_MAP.md", "concept dependency map"),
        ("INDEX.pkl",      "RAG search index"),
        ("CHAT_LOG.md",    "chat session log"),
    ]:
        path = os.path.join(out_dir, fname)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        mark = "v" if size > 0 else "o"
        info = f"{size//1024}KB" if size > 0 else "not generated"
        print(f"  {mark} {fname:<24} {desc} [{info}]")
    print(f"{'='*64}\n")


if __name__ == "__main__":
    main()