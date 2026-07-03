"""Configurable economics synonym dictionary for variable matching.

Each key is a semantic concept. Values are lowercase token patterns that may
appear in column names. The matcher normalizes column names by replacing
separators with spaces and lowercasing, then checks token overlap.

This dictionary is intentionally broad enough for typical development-
economics datasets (World Bank, Penn World Table, WHO, etc.) but should be
extended for domain-specific work.
"""
from __future__ import annotations

ECONOMICS_SYNONYMS: dict[str, list[str]] = {
    # ── Outcome / dependent variable candidates ──
    "gdp_per_capita": [
        "gdp_per_capita", "gdppc", "income_per_capita", "per_capita_income",
        "gdp_pc", "percapita_gdp", "real_gdp_per_capita", "gdp_capita",
    ],
    "gdp": [
        "gdp", "gross_domestic_product", "real_gdp", "nominal_gdp",
        "gdp_current", "gdp_constant",
    ],
    "gdp_growth": [
        "gdp_growth", "growth_rate", "economic_growth", "gdp_growth_rate",
    ],
    "life_expectancy": [
        "life_expectancy", "life_exp", "lifeexp", "expected_lifespan",
    ],
    "infant_mortality": [
        "infant_mortality", "infant_death_rate", "under5_mortality",
        "child_mortality", "neonatal_mortality",
    ],
    "poverty": [
        "poverty", "poverty_rate", "poverty_headcount", "poor", "gini",
        "inequality",
    ],

    # ── Explanatory variable candidates ──
    "internet_penetration": [
        "internet_users", "internet_use", "internet_penetration",
        "internet_access", "internet_usage", "internet_adoption",
        "internet_subscribers", "broadband",
    ],
    "trade_openness": [
        "trade_openness", "trade", "exports", "imports", "trade_share",
        "trade_gdp", "openness",
    ],
    "inflation": [
        "inflation", "cpi", "consumer_price_index", "inflation_rate",
        "price_level",
    ],
    "population": [
        "population", "pop", "total_population", "pop_total",
    ],
    "population_growth": [
        "population_growth", "pop_growth", "pop_growth_rate",
    ],

    # ── Common control variable candidates ──
    "education": [
        "education_spending", "education_expenditure", "public_education_spending",
        "education", "school_enrollment", "enrollment", "literacy",
        "literacy_rate", "years_schooling", "mean_schooling",
    ],
    "urbanization": [
        "urbanization", "urban_population_share", "urban_rate", "urban",
        "urban_pop", "urban_population",
    ],
    "employment": [
        "employment_rate", "employment", "labor_force_participation",
        "unemployment", "unemployment_rate", "labor_force", "labour_force",
    ],
    "health_spending": [
        "health_spending", "health_expenditure", "health_exp",
        "public_health_spending",
    ],
    "investment": [
        "investment", "gross_capital_formation", "fdi", "foreign_direct_investment",
        "capital_formation", "gfcf",
    ],
    "government_spending": [
        "government_spending", "gov_spending", "gov_expenditure",
        "fiscal_spending", "public_spending",
    ],

    # ── Entity identifiers ──
    "country": [
        "country", "country_name", "country_code", "iso3", "iso2",
        "nation", "economy",
    ],
    "region": [
        "region", "state", "province", "district", "county",
    ],
    "firm": [
        "firm", "company", "firm_id", "company_id", "ticker", "entity",
    ],
    "individual": [
        "individual", "person", "respondent", "household", "hh_id",
    ],

    # ── Time identifiers ──
    "year": [
        "year", "yr", "fiscal_year", "calendar_year",
    ],
    "date": [
        "date", "time", "period", "quarter", "month",
    ],
}


# Reverse index: token → concept
_TOKEN_TO_CONCEPT: dict[str, str] = {}
for concept, tokens in ECONOMICS_SYNONYMS.items():
    for token in tokens:
        _TOKEN_TO_CONCEPT[token] = concept


def get_concept_for_token(token: str) -> str | None:
    """Return the semantic concept for a normalized token, or None."""
    return _TOKEN_TO_CONCEPT.get(token.lower().strip())


def get_tokens_for_concept(concept: str) -> list[str]:
    """Return all known synonym tokens for a concept."""
    return ECONOMICS_SYNONYMS.get(concept, [])


def all_concepts() -> list[str]:
    return list(ECONOMICS_SYNONYMS.keys())
