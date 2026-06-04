def build_audit_features(drilldown, audit_params, agent_analytics):
    # Aggregate from Audit Parameters per audit
    param_agg = audit_params.groupby('Audit ID').agg(
        num_failed_params = ('Threshold Passed', lambda x: (x == 'No').sum()),
        num_auto_fails = ('Auto Fail', lambda x: (x == 'Yes').sum()),
        avg_system_score = ('System Score', 'mean'),
        avg_qa_score = ('QA Score', 'mean'),
        std_qa_score = ('QA Score', 'std')
    ).reset_index()
    
    # Merge with drilldown
    df = drilldown.merge(param_agg, on='Audit ID', how='left')
    
    # Time features
    df['QA Turnaround (hrs)'] = (df['Submitted At'] - df['Assigned At']).dt.total_seconds() / 3600
    df['Manager Review (hrs)'] = (df['Reviewed At'] - df['Submitted At']).dt.total_seconds() / 3600
    df['Lifecycle (hrs)'] = (df['Closed At'] - df['Created At']).dt.total_seconds() / 3600
    
    # Merge agent-level stats (use last historical data to avoid data leakage)
    # For simplicity, we'll use current snapshot; in production use time-based split
    agent_stats = agent_analytics[['QA', 'Average Final Score', 'Parameter Failure Rate', 'Dispute Rate']]
    agent_stats.columns = ['QA', 'agent_avg_final_score', 'agent_failure_rate', 'agent_dispute_rate']
    df = df.merge(agent_stats, on='QA', how='left')
    
    # Encode categoricals
    df['Priority_enc'] = df['Priority'].map({'Low':0, 'Medium':1, 'High':2, 'Critical':3})
    
    return df
