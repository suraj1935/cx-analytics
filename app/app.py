cat > frontend/app.py << 'EOF'
import streamlit as st
import requests
import pandas as pd

# 🔗 Hardcoded live backend – no secrets needed
API_URL = "https://cx-analytics-1zb2.onrender.com/api"

st.set_page_config(page_title="CX Analytics MVP", layout="wide")
st.title("📊 Customer Experience Analytics Dashboard")

# Sidebar: Upload CSV
st.sidebar.header("📤 Upload Data")
st.sidebar.markdown("Upload a CSV with **`score`** (0–10) and **`feedback`** (text) columns.")
uploaded_file = st.sidebar.file_uploader("Choose CSV", type="csv")
if uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
    try:
        resp = requests.post(f"{API_URL}/upload/", files=files)
        if resp.status_code == 200:
            st.sidebar.success(f"✅ Uploaded {resp.json()['rows_accepted']} rows")
        else:
            st.sidebar.error(resp.json().get("detail", "Upload failed"))
    except Exception:
        st.sidebar.warning("Backend not reachable")

st.sidebar.divider()
st.sidebar.markdown(f"**API:** `{API_URL}`")
try:
    health = requests.get(API_URL.replace("/api", "") + "/health", timeout=10)
    if health.status_code == 200:
        st.sidebar.success("✅ API Online")
    else:
        st.sidebar.warning("⚠️ API Degraded")
except Exception:
    st.sidebar.error("❌ API Offline")

# Navigation
page = st.sidebar.radio("Navigate", ["📊 Analytics", "🔍 Root Cause Analysis"], index=0)

# Analytics page
def show_analytics():
    st.header("📊 CSAT & NPS Metrics")
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

    if "summary" not in st.session_state:
        try:
            r = requests.get(f"{API_URL}/analytics/summary")
            if r.status_code == 200:
                st.session_state["summary"] = r.json()
        except Exception:
            st.error("Cannot fetch analytics. Backend may be waking up…")
            return

    data = st.session_state["summary"]
    csat = data["csat"]
    nps = data["nps"]
    dist = data.get("score_distribution", {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("😊 CSAT", f"{csat['satisfaction_pct']}%",
                help=f"Satisfied (score ≥ {csat['threshold']}): {csat['satisfied_count']}/{csat['total_count']}")
    col2.metric("⭐ Avg Score", f"{csat['avg_score']:.1f} / 10")
    col3.metric("📣 NPS", nps['nps_score'],
                help=f"Promoters: {nps['promoter_pct']}%, Passives: {nps['passive_pct']}%, Detractors: {nps['detractor_pct']}%")
    col4.metric("📋 Records", data["total_records"])

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("CSAT Detail")
        c1, c2 = st.columns(2)
        c1.metric("Satisfied", csat["satisfied_count"])
        c2.metric("Total", csat["total_count"])
        st.subheader("Score Distribution")
        if dist:
            dist_df = pd.DataFrame({"Score": list(dist.keys()), "Count": list(dist.values())}).sort_values("Score").set_index("Score")
            st.bar_chart(dist_df)
        else:
            st.info("No distribution data.")
    with right:
        st.subheader("NPS Breakdown")
        n1, n2, n3 = st.columns(3)
        n1.metric("🟢 Promoters", f"{nps['promoter_pct']}%", f"{nps['promoter_count']} resp.")
        n2.metric("🟡 Passives", f"{nps['passive_pct']}%", f"{nps['passive_count']} resp.")
        n3.metric("🔴 Detractors", f"{nps['detractor_pct']}%", f"{nps['detractor_count']} resp.")

# RCA page
def show_rca():
    st.header("🔍 Root Cause Analysis – Keyword Engine")
    if st.button("▶️ Run RCA"):
        st.cache_data.clear()
        st.session_state.pop("rca", None)

    if "rca" not in st.session_state:
        try:
            r = requests.get(f"{API_URL}/rca/keyword?limit=50")
            if r.status_code == 200:
                st.session_state["rca"] = r.json()
        except Exception:
            st.error("Cannot run RCA. Backend may be waking up…")
            return

    data = st.session_state["rca"]
    kw_counts = data.get("keyword_counts", {})
    records = data.get("matching_records", [])
    total_matches = data.get("total_matches", 0)
    total_records = data.get("total_records", 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("🚨 Affected Rows", total_matches)
    col2.metric("📋 Total Rows", total_records)
    impact = round((total_matches / total_records) * 100, 1) if total_records else 0
    col3.metric("📉 Impact Rate", f"{impact}%")

    st.subheader("Top Negative Keyword Hits")
    if kw_counts:
        kw_df = pd.DataFrame({"Keyword": list(kw_counts.keys()), "Hits": list(kw_counts.values())}).set_index("Keyword")
        st.bar_chart(kw_df)
    else:
        st.success("No negative keywords detected. 🎉")

    st.subheader(f"Matching Feedback Rows ({total_matches})")
    if records:
        rec_df = pd.DataFrame(records)
        st.dataframe(rec_df, use_container_width=True, height=400)
    else:
        st.info("No matching records found.")

# Page routing
if page == "📊 Analytics":
    show_analytics()
else:
    show_rca()
EOF
