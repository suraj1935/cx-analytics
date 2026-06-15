from sklearn.cluster import KMeans
import pandas as pd

def cluster_agents(agent_analytics):
    features = ['Average Final Score', 'Average System Score', 'Dispute Rate', 'Parameter Failure Rate']
    X = agent_analytics[features].fillna(0)
    
    kmeans = KMeans(n_clusters=3, random_state=42)
    agent_analytics['Cluster'] = kmeans.fit_predict(X)
    
    # Bias detection: difference between avg final and system score
    agent_analytics['Bias'] = agent_analytics['Average Final Score'] - agent_analytics['Average System Score']
    bias_flags = agent_analytics[agent_analytics['Bias'].abs() > 10][['QA', 'Bias']].to_dict('records')
    
    return agent_analytics[['QA', 'Cluster', 'Bias']].to_dict('records'), bias_flags
