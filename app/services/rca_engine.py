"""
Keyword-based Root Cause Analysis engine.
Scans the 'feedback' column for negative keywords and returns
aggregated counts and the matching rows.
"""
import logging
import re
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)

NEGATIVE_KEYWORDS: List[str] = [
    "slow", "bug", "error", "crash", "bad", "terrible",
    "broken", "frustrated", "useless", "poor",
]


def _build_pattern(keywords: List[str]) -> re.Pattern:
    """Compile a single regex that matches any keyword as a whole word."""
    escaped = [re.escape(kw) for kw in keywords]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


def run_keyword_rca(
    df: pd.DataFrame,
    keywords: List[str] = None,
) -> dict:
    """
    Scan feedback text for negative keywords.

    Parameters
    ----------
    df       : cleaned DataFrame with at least a 'feedback' column.
    keywords : override the default NEGATIVE_KEYWORDS list.

    Returns
    -------
    {
        "keyword_counts"   : {keyword: hit_count, ...},
        "matching_records" : [ {score, feedback, matched_keywords}, ... ],
        "total_matches"    : int,
        "total_records"    : int,
    }
    """
    empty_result = {
        "keyword_counts": {},
        "matching_records": [],
        "total_matches": 0,
        "total_records": 0,
    }

    if df is None or df.empty:
        return empty_result

    if "feedback" not in df.columns:
        logger.warning("run_keyword_rca: 'feedback' column missing")
        return empty_result

    kw_list = keywords if keywords else NEGATIVE_KEYWORDS
    pattern = _build_pattern(kw_list)

    # Per-keyword frequency
    keyword_counts: dict = {kw: 0 for kw in kw_list}

    matching_rows = []
    feedback_series = df["feedback"].fillna("").astype(str)

    for idx, text in feedback_series.items():
        found = pattern.findall(text)
        if not found:
            continue
        # Normalise to lowercase and deduplicate within a row
        unique_found = list({f.lower() for f in found})
        for kw in unique_found:
            if kw in keyword_counts:
                keyword_counts[kw] += 1

        row_data: dict = {"feedback": text, "matched_keywords": ", ".join(unique_found)}
        if "score" in df.columns:
            row_data["score"] = df.at[idx, "score"]
        matching_rows.append(row_data)

    # Remove keywords with zero hits for a cleaner response
    keyword_counts = {k: v for k, v in keyword_counts.items() if v > 0}
    # Sort descending by count
    keyword_counts = dict(
        sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "keyword_counts": keyword_counts,
        "matching_records": matching_rows,
        "total_matches": len(matching_rows),
        "total_records": len(df),
    }
