from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd

def topic_modeling_on_reasons(audit_params):
    reasons = audit_params['Reason'].dropna().astype(str)
    vect = CountVectorizer(max_features=500, stop_words='english')
    X = vect.fit_transform(reasons)
    
    lda = LatentDirichletAllocation(n_components=5, random_state=42)
    lda.fit(X)
    
    # Top words per topic
    feature_names = vect.get_feature_names_out()
    topics = {}
    for topic_idx, topic in enumerate(lda.components_):
        top_words = [feature_names[i] for i in topic.argsort()[-10:]]
        topics[f'Topic {topic_idx+1}'] = top_words
    
    # Assign dominant topic to each reason
    topic_assignments = lda.transform(X).argmax(axis=1)
    audit_params['dominant_topic'] = topic_assignments
    
    # Trend analysis: count topics by month (if date available)
    # For simplicity, return cluster distribution
    return topics, audit_params['dominant_topic'].value_counts().to_dict()
