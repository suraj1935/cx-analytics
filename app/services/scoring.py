"""
CSAT and NPS scoring services.
All functions accept a pandas DataFrame and return plain dicts.
Gracefully handles missing columns and non-numeric data.
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# ── CSAT ──────────────────────────────────────────────────────────────────────

def compute_csat(df: pd.DataFrame, threshold: float = 7.0) -> dict:
    """
    Compute CSAT metrics.

    Satisfied = score >= threshold (default 7).
    Returns:
        satisfaction_pct : float  – % of satisfied respondents
        avg_score        : float  – mean score across all respondents
        satisfied_count  : int
        total_count      : int
        threshold        : float
    """
    default = {
        "satisfaction_pct": 0.0,
        "avg_score": 0.0,
        "satisfied_count": 0,
        "total_count": 0,
        "threshold": threshold,
    }

    if df is None or df.empty:
        return default

    if "score" not in df.columns:
        logger.warning("compute_csat: 'score' column missing")
        return default

    scores = pd.to_numeric(df["score"], errors="coerce").dropna()
    if scores.empty:
        return default

    total = len(scores)
    satisfied = int((scores >= threshold).sum())
    satisfaction_pct = round((satisfied / total) * 100, 2)
    avg_score = round(float(scores.mean()), 2)

    return {
        "satisfaction_pct": satisfaction_pct,
        "avg_score": avg_score,
        "satisfied_count": satisfied,
        "total_count": total,
        "threshold": threshold,
    }


# ── NPS ───────────────────────────────────────────────────────────────────────

def _nps_segment(score: float) -> str:
    if score >= 9:
        return "Promoter"
    if score >= 7:
        return "Passive"
    return "Detractor"


def compute_nps(df: pd.DataFrame) -> dict:
    """
    Compute NPS metrics.

    Promoters  : score 9-10
    Passives   : score 7-8
    Detractors : score 0-6
    NPS = (promoters% - detractors%)

    Returns:
        nps_score          : float
        promoter_pct       : float
        passive_pct        : float
        detractor_pct      : float
        promoter_count     : int
        passive_count      : int
        detractor_count    : int
        total_count        : int
    """
    default = {
        "nps_score": 0.0,
        "promoter_pct": 0.0,
        "passive_pct": 0.0,
        "detractor_pct": 0.0,
        "promoter_count": 0,
        "passive_count": 0,
        "detractor_count": 0,
        "total_count": 0,
    }

    if df is None or df.empty:
        return default

    if "score" not in df.columns:
        logger.warning("compute_nps: 'score' column missing")
        return default

    scores = pd.to_numeric(df["score"], errors="coerce").dropna()
    if scores.empty:
        return default

    total = len(scores)
    segments = scores.apply(_nps_segment)
    counts = segments.value_counts()

    promoters   = int(counts.get("Promoter",  0))
    passives    = int(counts.get("Passive",   0))
    detractors  = int(counts.get("Detractor", 0))

    promoter_pct  = round((promoters  / total) * 100, 2)
    passive_pct   = round((passives   / total) * 100, 2)
    detractor_pct = round((detractors / total) * 100, 2)
    nps_score     = round(promoter_pct - detractor_pct, 2)

    return {
        "nps_score": nps_score,
        "promoter_pct": promoter_pct,
        "passive_pct": passive_pct,
        "detractor_pct": detractor_pct,
        "promoter_count": promoters,
        "passive_count": passives,
        "detractor_count": detractors,
        "total_count": total,
    }


# ── Score distribution ────────────────────────────────────────────────────────

def score_distribution(df: pd.DataFrame) -> dict:
    """Return {score_value: count} for all integer scores present."""
    if df is None or df.empty or "score" not in df.columns:
        return {}
    scores = pd.to_numeric(df["score"], errors="coerce").dropna().astype(int)
    return {int(k): int(v) for k, v in scores.value_counts().sort_index().items()}