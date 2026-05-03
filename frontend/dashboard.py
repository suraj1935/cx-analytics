"""
CX Analytics Platform – Streamlit Dashboard
============================================
Run locally:
    streamlit run frontend/dashboard.py

Configure backend URL via environment variable or .streamlit/secrets.toml:
    API_URL = "https://your-backend.railway.app/api"
"""
import io
import os
import logging

import pandas as pd
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
# Priority: env var → Streamlit secrets → default localhost
def _get_api_url() -> str:
    if "API_URL" in os.environ:
        return os.environ["API_URL"].rstrip("/")
    try:
        return st.secrets["API_URL"].rstrip("/")
    except Exception:
        return "http://localhost:8000/api"


API_BASE = _get_api_url()
TIMEOUT = 15

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(path: str, params: dict = None) -> dict | None:
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at `{API_BASE}`. Is the backend running?")
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out.")
    except requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        st.error(f"API {exc.response.status_code}: {detail}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
    return None


def _upload_csv(file_bytes: bytes, filename: str) -> dict | None:
    url = f"{API_BASE}/upload/"
    try:
        r = requests.post(
            url,
            files={"file": (filename, io.BytesIO(file_bytes), "text/csv")},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at `{API_BASE}`.")
    except requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        st.error(f"Upload failed {exc.response.status_code}: {detail}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
    return None


# ── Gauge colour helper ────────────────────────────────────────────────────────

def _csat_label(pct: float) -> str:
    if pct >= 70:
        return "🟢 Good"
    if pct >= 40:
        return "🟡 Fair"
    return "🔴 Poor"


def _nps_label(score: float) -> str:
    if score >= 50:
        return "🟢 Excellent"
    if score >= 0:
        return "🟡 Needs work"
    return "🔴 Critical"


# ── Sidebar: upload ───────────────────────────────────────────────────────────

def sidebar_upload():
    st.sidebar.header("📤 Upload Data")
    st.sidebar.markdown(
        "Upload a CSV with **`score`** (0–10) and **`feedback`** (text) columns."
    )
    uploaded = st.sidebar.file_uploader("Choose CSV", type=["csv"])

    if uploaded:
        file_bytes = uploaded.read()
        try:
            preview = pd.read_csv(io.BytesIO(file_bytes))
            st.sidebar.markdown(f"**Preview** ({len(preview)} rows)")
            st.sidebar.dataframe(preview.head(3), use_container_width=True)
        except Exception:
            st.sidebar.warning("Could not preview file.")

        if st.sidebar.button("🚀 Upload & Process"):
            with st.sidebar:
                with st.spinner("Uploading…"):
                    result = _upload_csv(file_bytes, uploaded.name)
            if result:
                st.sidebar.success(
                    f"✅ {result['message']}\n\n"
                    f"**{result['rows_accepted']} rows** accepted."
                )
                # Invalidate cached data so the main panel refreshes
                for key in ["summary", "rca"]:
                    st.session_state.pop(key, None)

    st.sidebar.divider()
    st.sidebar.markdown(f"**API:** `{API_BASE}`")
    # Live health check
    try:
        h = requests.get(
            API_BASE.replace("/api", "") + "/health", timeout=3
        )
        if h.status_code == 200:
            st.sidebar.success("✅ API Online")
        else:
            st.sidebar.warning("⚠️ API Degraded")
    except Exception:
        st.sidebar.error("❌ API Offline")


# ── Analytics panel ───────────────────────────────────────────────────────────

def panel_analytics():
    st.header("📊 CSAT & NPS Metrics")

    col_refresh, _ = st.columns([1, 5])
    if col_refresh.button("🔄 Refresh"):
        st.session_state.pop("summary", None)

    if "summary" not in st.session_state:
        with st.spinner("Fetching analytics…"):
            data = _get("/analytics/summary")
        if not data:
            return
        st.session_state["summary"] = data

    data = st.session_state["summary"]
    csat = data["csat"]
    nps = data["nps"]
    dist = data["score_distribution"]

    # ── Top-level KPIs ────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "😊 CSAT",
        f"{csat['satisfaction_pct']}%",
        help=f"Responses with score ≥ {csat['threshold']}",
    )
    k2.metric(
        "⭐ Avg Score",
        f"{csat['avg_score']} / 10",
    )
    k3.metric(
        "📣 NPS",
        f"{nps['nps_score']}",
        help="Promoter% − Detractor%",
    )
    k4.metric(
        "📋 Records",
        data["total_records"],
    )

    st.caption(
        f"{_csat_label(csat['satisfaction_pct'])}  |  NPS: {_nps_label(nps['nps_score'])}"
    )
    st.divider()

    # ── Two-column layout ─────────────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("CSAT Detail")
        c1, c2 = st.columns(2)
        c1.metric("Satisfied", csat["satisfied_count"])
        c2.metric("Total", csat["total_count"])

        st.subheader("Score Distribution")
        if dist:
            dist_df = (
                pd.DataFrame(
                    {"Score": list(dist.keys()), "Count": list(dist.values())}
                )
                .sort_values("Score")
                .set_index("Score")
            )
            st.bar_chart(dist_df, use_container_width=True)
        else:
            st.info("No distribution data.")

    with right:
        st.subheader("NPS Breakdown")
        n1, n2, n3 = st.columns(3)
        n1.metric("🟢 Promoters",  f"{nps['promoter_pct']}%",  f"{nps['promoter_count']} resp.")
        n2.metric("🟡 Passives",   f"{nps['passive_pct']}%",   f"{nps['passive_count']} resp.")
        n3.metric("🔴 Detractors", f"{nps['detractor_pct']}%", f"{nps['detractor_count']} resp.")

        st.subheader("NPS Segments")
        seg_df = pd.DataFrame(
            {
                "Segment": ["Promoters", "Passives", "Detractors"],
                "Count": [
                    nps["promoter_count"],
                    nps["passive_count"],
                    nps["detractor_count"],
                ],
            }
        ).set_index("Segment")
        st.bar_chart(seg_df, use_container_width=True)


# ── RCA panel ─────────────────────────────────────────────────────────────────

def panel_rca():
    st.header("🔍 Root Cause Analysis – Keyword Engine")
    st.markdown(
        "Scans feedback for negative keywords to surface the most common pain points."
    )

    if st.button("▶️ Run RCA"):
        st.session_state.pop("rca", None)

    if "rca" not in st.session_state:
        with st.spinner("Running RCA…"):
            data = _get("/rca/keyword", params={"limit": 500})
        if not data:
            return
        st.session_state["rca"] = data

    data = st.session_state["rca"]
    kw_counts = data.get("keyword_counts", {})
    records = data.get("matching_records", [])
    total_matches = data.get("total_matches", 0)
    total_records = data.get("total_records", 0)
    keywords_used = data.get("keywords_used", [])

    # ── Summary metrics ───────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("🚨 Affected Rows", total_matches)
    m2.metric("📋 Total Rows",    total_records)
    impact = round((total_matches / total_records) * 100, 1) if total_records else 0
    m3.metric("📉 Impact Rate",   f"{impact}%")

    st.caption(f"Keywords monitored: `{'`, `'.join(keywords_used)}`")
    st.divider()

    # ── Keyword frequency bar chart ───────────────────────────────────────────
    st.subheader("Top Negative Keyword Hits")
    if kw_counts:
        kw_df = (
            pd.DataFrame(
                {"Keyword": list(kw_counts.keys()), "Hits": list(kw_counts.values())}
            )
            .sort_values("Hits", ascending=False)
            .set_index("Keyword")
        )
        st.bar_chart(kw_df, use_container_width=True)
    else:
        st.success("No negative keywords detected in the current dataset. 🎉")

    # ── Matching feedback table ───────────────────────────────────────────────
    st.subheader(f"Matching Feedback Rows ({total_matches})")
    if records:
        records_df = pd.DataFrame(records)
        # Reorder columns: score first if present
        cols = []
        if "score" in records_df.columns:
            cols.append("score")
        cols += ["feedback", "matched_keywords"]
        records_df = records_df[[c for c in cols if c in records_df.columns]]

        st.dataframe(records_df, use_container_width=True, height=400)

        csv_bytes = records_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Matching Records",
            data=csv_bytes,
            file_name="rca_keyword_results.csv",
            mime="text/csv",
        )
    else:
        st.info("No matching records found.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="CX Analytics Platform",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    sidebar_upload()

    page = st.sidebar.radio(
        "Navigate",
        ["📊 Analytics", "🔍 Root Cause Analysis"],
        index=0,
    )

    if page == "📊 Analytics":
        panel_analytics()
    elif page == "🔍 Root Cause Analysis":
        panel_rca()


if __name__ == "__main__":
    main()