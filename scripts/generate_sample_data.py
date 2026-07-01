"""Generate sample_data/world_bank_panel_sample.xlsx.

Synthetic, but structurally realistic, country-year panel data designed to
demonstrate: panel detection, missing values, outliers, log transformation,
fixed effects, two-way fixed effects, clustered standard errors, and the
Hausman test. Not real-world data.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

COUNTRIES = [
    "Alandia", "Borovia", "Casteria", "Dravonia", "Estoria",
    "Farlan", "Gornia", "Hesperia", "Ilvania", "Jovaria",
    "Kestria", "Lorenthia", "Meridia", "Norvana", "Orenthal",
    "Palterra", "Quorvia", "Rionsea", "Solvenia", "Tavaria",
]
YEARS = list(range(2005, 2020))  # 15 years


def generate() -> pd.DataFrame:
    rows = []
    for country in COUNTRIES:
        country_effect = RNG.normal(0, 0.6)
        base_gdp = RNG.uniform(2000, 15000)
        internet_growth_start = RNG.uniform(0, 15)
        for year in YEARS:
            t = year - YEARS[0]
            urbanization = np.clip(30 + t * RNG.uniform(0.5, 1.5) + RNG.normal(0, 2), 10, 95)
            internet_users = np.clip(
                internet_growth_start + t * RNG.uniform(3, 7) + RNG.normal(0, 3), 0, 99
            )
            education_spending = np.clip(RNG.normal(4.5, 1.2), 1.0, 9.0)
            employment_rate = np.clip(RNG.normal(62, 5), 40, 85)
            inflation = np.clip(RNG.normal(4, 3), -2, 40)
            trade_openness = np.clip(RNG.normal(70, 25), 10, 220)

            log_gdp = (
                np.log(base_gdp)
                + country_effect
                + 0.012 * internet_users
                + 0.01 * urbanization
                + 0.02 * education_spending
                - 0.005 * inflation
                + 0.02 * t
                + RNG.normal(0, 0.15)
            )
            gdp_per_capita = float(np.exp(log_gdp))

            rows.append(
                {
                    "country": country,
                    "year": year,
                    "gdp_per_capita": round(gdp_per_capita, 2),
                    "internet_users": round(float(internet_users), 2),
                    "urbanization": round(float(urbanization), 2),
                    "education_spending": round(float(education_spending), 2),
                    "employment_rate": round(float(employment_rate), 2),
                    "inflation": round(float(inflation), 2),
                    "trade_openness": round(float(trade_openness), 2),
                }
            )

    df = pd.DataFrame(rows)

    # Inject missing values (~3%) into a few economic columns.
    for col in ["education_spending", "employment_rate", "trade_openness"]:
        mask = RNG.random(len(df)) < 0.03
        df.loc[mask, col] = np.nan

    # Inject a handful of outliers in gdp_per_capita and inflation.
    outlier_idx = RNG.choice(df.index, size=8, replace=False)
    df.loc[outlier_idx[:4], "gdp_per_capita"] *= 4.5
    df.loc[outlier_idx[4:], "inflation"] += RNG.uniform(50, 90, size=4)

    return df


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "sample_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "world_bank_panel_sample.xlsx"
    df = generate()
    df.to_excel(out_path, index=False, sheet_name="panel_data")
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
