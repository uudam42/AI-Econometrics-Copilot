"""Parse and normalize natural-language research questions.

Detects causal vs. association intent, extracts variable-like tokens,
and normalizes the question for downstream matching. No external LLM —
all logic is rule-based pattern matching.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.planning import AnalysisIntent

_CAUSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bcause[sd]?\b", re.IGNORECASE),
    re.compile(r"\bcausal\b", re.IGNORECASE),
    re.compile(r"\bcausation\b", re.IGNORECASE),
    re.compile(r"\blead[s]?\s+to\b", re.IGNORECASE),
    re.compile(r"\beffect\s+of\b", re.IGNORECASE),
    re.compile(r"\baffect[s]?\b", re.IGNORECASE),
    re.compile(r"\bimpact[s]?\s+(of|on)\b", re.IGNORECASE),
    re.compile(r"\bdrive[s]?\b", re.IGNORECASE),
    re.compile(r"\bdetermine[s]?\b", re.IGNORECASE),
    re.compile(r"\binfluence[s]?\b", re.IGNORECASE),
]

_ASSOCIATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bassociat(ed|ion)\b", re.IGNORECASE),
    re.compile(r"\bcorrelat(ed|ion)\b", re.IGNORECASE),
    re.compile(r"\brelat(ed|ionship)\b", re.IGNORECASE),
    re.compile(r"\blinked?\b", re.IGNORECASE),
    re.compile(r"\bconnect(ed|ion)\b", re.IGNORECASE),
    re.compile(r"\bco-?move\b", re.IGNORECASE),
    re.compile(r"\bpredict[s]?\b", re.IGNORECASE),
]

_EXPLORATORY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bexplor(e|atory)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(factors|variables|explains?)\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(factors|variables)\b", re.IGNORECASE),
    re.compile(r"\bdescri(be|ptive)\b", re.IGNORECASE),
]

_STOPWORDS = frozenset(
    "a an the is are was were do does did have has had be been being "
    "of in on at to for with by from as into through during per between "
    "and or but not if then than so that this these those it its "
    "i we you they he she my our their "
    "how what which where when who whom why whether there "
    "can could will would shall should may might must "
    "across over among about".split()
)


@dataclass
class ParsedQuestion:
    original: str
    normalized: str
    detected_intent: AnalysisIntent
    causal_keywords_found: list[str] = field(default_factory=list)
    extracted_tokens: list[str] = field(default_factory=list)
    causal_warning: str = ""


def _normalize(text: str) -> str:
    text = text.strip().rstrip("?").strip()
    text = re.sub(r"[''`]", "'", text)
    text = re.sub(r"[""„]", '"', text)
    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def _extract_content_tokens(normalized: str) -> list[str]:
    words = normalized.split()
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _detect_intent(
    normalized: str,
) -> tuple[AnalysisIntent, list[str]]:
    causal_found: list[str] = []
    for pat in _CAUSAL_PATTERNS:
        match = pat.search(normalized)
        if match:
            causal_found.append(match.group(0).lower())

    association_found = any(pat.search(normalized) for pat in _ASSOCIATION_PATTERNS)
    exploratory_found = any(pat.search(normalized) for pat in _EXPLORATORY_PATTERNS)

    if causal_found and not association_found:
        return "causal_claim_requested", causal_found
    if causal_found and association_found:
        return "causal_claim_requested", causal_found
    if association_found:
        return "association", causal_found
    if exploratory_found:
        return "exploratory", causal_found
    if not causal_found and not association_found and not exploratory_found:
        return "unclear", causal_found
    return "association", causal_found


_CAUSAL_WARNING = (
    "Your question uses causal language ({keywords}). "
    "This platform identifies statistical associations only. "
    "Establishing causal effects requires additional identification "
    "assumptions (e.g. instrumental variables, regression discontinuity, "
    "difference-in-differences) that are beyond the scope of the models "
    "offered here. Results will be framed as associations."
)

_NO_CAUSAL_WARNING = (
    "This analysis identifies statistical associations and does not "
    "establish causal effects unless additional identification "
    "assumptions are justified."
)


def parse_research_question(question: str) -> ParsedQuestion:
    if not question or not question.strip():
        return ParsedQuestion(
            original=question,
            normalized="",
            detected_intent="unclear",
            causal_warning=_NO_CAUSAL_WARNING,
        )

    normalized = _normalize(question)
    intent, causal_kws = _detect_intent(normalized)
    tokens = _extract_content_tokens(normalized)

    if intent == "causal_claim_requested" and causal_kws:
        warning = _CAUSAL_WARNING.format(keywords=", ".join(sorted(set(causal_kws))))
    else:
        warning = _NO_CAUSAL_WARNING

    return ParsedQuestion(
        original=question,
        normalized=normalized,
        detected_intent=intent,
        causal_keywords_found=causal_kws,
        extracted_tokens=tokens,
        causal_warning=warning,
    )
