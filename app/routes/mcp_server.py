 @mcp.tool()
async def train_final_score_model(excel_url: str) -> str:
    """Train an XGBoost model to predict Final Score from the BPO audit Excel file."""
    from ml.data_loader import load_excel
    from ml.features import build_audit_features
    from ml.train import train_final_score_model
    drill, params, agents, _ = load_excel(excel_url)
    df = build_audit_features(drill, params, agents)
    result = train_final_score_model(df, supabase)
    return json.dumps(result)

@mcp.tool()
async def predict_final_score(audit_data: dict) -> str:
    """Predict the Final Score for a new audit given features as JSON."""
    # Load model from Supabase storage
    # ... implementation ...
    pass

@mcp.tool()
async def run_failure_reason_topics(excel_url: str) -> str:
    """Identify topics from audit failure reasons."""
    from ml.data_loader import load_excel
    from ml.rca_nlp import topic_modeling_on_reasons
    _, params, _, _ = load_excel(excel_url)
    topics, dist = topic_modeling_on_reasons(params)
    return json.dumps({"topics": topics, "distribution": dist})

@mcp.tool()
async def analyze_agent_calibration(excel_url: str) -> str:
    """Cluster QA agents and flag scoring bias."""
    from ml.data_loader import load_excel
    from ml.agent_calibration import cluster_agents
    _, _, agents, _ = load_excel(excel_url)
    clusters, bias = cluster_agents(agents)
    return json.dumps({"clusters": clusters, "bias_flags": bias})
