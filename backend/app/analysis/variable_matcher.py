"""Dataset-aware variable matching with economics synonym dictionary.

Given tokens from a parsed research question and the actual columns of
an uploaded dataset, produce CandidateVariable suggestions. No external
LLM — matching is token overlap + synonym dictionary + column typing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from app.analysis.economics_synonyms import (
    ECONOMICS_SYNONYMS,
    get_concept_for_token,
)
from app.schemas.dataset import ColumnTypeInfo
from app.schemas.planning import CandidateVariable, VariableRole
from app.services.column_typing import infer_all_column_types


@dataclass
class MatchResult:
    candidates: list[CandidateVariable]
    ambiguities: list[str]


def _tokenize_column_name(name: str) -> list[str]:
    name = re.sub(r"[_\-\.]+", " ", name.lower())
    return [t for t in name.split() if len(t) > 1]


def _token_overlap_score(question_tokens: list[str], col_tokens: list[str]) -> float:
    if not question_tokens or not col_tokens:
        return 0.0
    q_set = set(question_tokens)
    c_set = set(col_tokens)
    overlap = q_set & c_set
    if not overlap:
        return 0.0
    return len(overlap) / max(len(q_set), len(c_set))


def _synonym_score(
    question_tokens: list[str], col_name_normalized: str
) -> tuple[float, str | None]:
    q_concepts: set[str] = set()
    for tok in question_tokens:
        concept = get_concept_for_token(tok)
        if concept:
            q_concepts.add(concept)

    for concept in q_concepts:
        synonyms = ECONOMICS_SYNONYMS.get(concept, [])
        for syn in synonyms:
            if syn in col_name_normalized or col_name_normalized in syn:
                return 0.8, concept

    col_tokens = _tokenize_column_name(col_name_normalized)
    for tok in col_tokens:
        concept = get_concept_for_token(tok)
        if concept and concept in q_concepts:
            return 0.7, concept

    return 0.0, None


def _role_from_hints(col_info: ColumnTypeInfo) -> VariableRole:
    hints = col_info.role_hints
    if "Possible Entity ID" in hints:
        return "entity_column"
    if "Possible Time Variable" in hints:
        return "time_column"
    if "Potential Outcome" in hints:
        return "dependent_variable"
    if "Potential Explanatory Variable" in hints:
        return "primary_independent_variable"
    if "Potential Control" in hints:
        return "control_variable"
    return "unresolved"


def match_variables(
    df: pd.DataFrame,
    question_tokens: list[str],
    preferred_outcome: str | None = None,
    preferred_primary_iv: str | None = None,
) -> MatchResult:
    col_infos = infer_all_column_types(df)
    candidates: list[CandidateVariable] = []
    ambiguities: list[str] = []

    dep_candidates: list[str] = []
    iv_candidates: list[str] = []

    for col_info in col_infos:
        col_name = col_info.name
        col_tokens = _tokenize_column_name(col_name)
        col_normalized = re.sub(r"[_\-\.]+", " ", col_name.lower()).strip()

        base_role = _role_from_hints(col_info)
        evidence: list[str] = []
        warnings: list[str] = []

        direct_score = _token_overlap_score(question_tokens, col_tokens)
        syn_score, matched_concept = _synonym_score(question_tokens, col_normalized)

        combined = max(direct_score, syn_score)

        if direct_score > 0:
            evidence.append(f"Column name tokens overlap with question ({direct_score:.0%})")
        if matched_concept:
            evidence.append(f"Matched economics concept: '{matched_concept}'")

        if base_role == "entity_column":
            evidence.append(f"Column typing suggests entity identifier ({col_info.inferred_role})")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role="entity_column",
                confidence=0.9,
                evidence=evidence,
                warnings=warnings,
            ))
            continue

        if base_role == "time_column":
            evidence.append(f"Column typing suggests time variable ({col_info.inferred_role})")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role="time_column",
                confidence=0.9,
                evidence=evidence,
                warnings=warnings,
            ))
            continue

        if col_info.inferred_role not in ("numeric", "datetime"):
            if combined < 0.3:
                continue
            warnings.append("Column is non-numeric; may need encoding or exclusion")

        if preferred_outcome and col_name.lower() == preferred_outcome.lower():
            evidence.append("User specified as preferred outcome variable")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role="dependent_variable",
                confidence=0.95,
                evidence=evidence,
                warnings=warnings,
            ))
            dep_candidates.append(col_name)
            continue

        if preferred_primary_iv and col_name.lower() == preferred_primary_iv.lower():
            evidence.append("User specified as preferred primary independent variable")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role="primary_independent_variable",
                confidence=0.95,
                evidence=evidence,
                warnings=warnings,
            ))
            iv_candidates.append(col_name)
            continue

        if combined >= 0.5:
            if base_role in ("dependent_variable", "unresolved") and not dep_candidates:
                role: VariableRole = "dependent_variable"
                dep_candidates.append(col_name)
            elif base_role in ("primary_independent_variable", "unresolved") and not iv_candidates:
                role = "primary_independent_variable"
                iv_candidates.append(col_name)
            else:
                role = "control_variable"

            evidence.append(f"High relevance score ({combined:.0%}) from question matching")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role=role,
                confidence=min(combined + 0.1, 0.95),
                evidence=evidence,
                warnings=warnings,
            ))
        elif combined >= 0.2:
            evidence.append(f"Moderate relevance ({combined:.0%}) — suggested as control")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role="control_variable",
                confidence=combined,
                evidence=evidence,
                warnings=warnings,
            ))
        elif base_role in ("dependent_variable", "primary_independent_variable", "control_variable"):
            evidence.append(f"Suggested by column typing: {', '.join(col_info.role_hints)}")
            candidates.append(CandidateVariable(
                column_name=col_name,
                role="control_variable",
                confidence=0.2,
                evidence=evidence,
                warnings=warnings,
            ))

    if len(dep_candidates) > 1:
        ambiguities.append(
            f"Multiple columns could be the dependent variable: {', '.join(dep_candidates)}. "
            "Please select one."
        )
    if not dep_candidates:
        ambiguities.append(
            "No clear dependent variable was identified from your question. "
            "Please specify which column is your outcome variable."
        )

    if len(iv_candidates) > 1:
        ambiguities.append(
            f"Multiple columns could be the primary independent variable: "
            f"{', '.join(iv_candidates)}. Please select one."
        )
    if not iv_candidates:
        ambiguities.append(
            "No clear primary independent variable was identified. "
            "Please specify which column is your main explanatory variable."
        )

    candidates.sort(key=lambda c: (-c.confidence, c.column_name))

    return MatchResult(candidates=candidates, ambiguities=ambiguities)
