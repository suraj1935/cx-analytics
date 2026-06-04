import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
from supabase import create_client
import os

def train_final_score_model(df, supabase_client):
    features = [
        'Priority_enc', 'num_failed_params', 'num_auto_fails',
        'avg_system_score', 'QA Turnaround (hrs)', 'Manager Review (hrs)',
        'agent_avg_final_score', 'agent_failure_rate'
    ]
    X = df[features].fillna(0)
    y = df['Final Score']
    
    # Time split: train on earlier, test on later
    # (simplified: use all data, split randomly; you can filter by date)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    rmse = mean_squared_error(y_test, preds, squared=False)
    r2 = r2_score(y_test, preds)
    
    # Save model to Supabase Storage
    model_bytes = joblib.dump(model, 'final_score_model.pkl')
    with open('final_score_model.pkl', 'rb') as f:
        supabase_client.storage.from_('models').upload(
            'final_score_model.pkl',
            f.read(),
            {'content-type': 'application/octet-stream'}
        )
    
    # Feature importance
    importance = dict(zip(features, model.feature_importances_))
    
    return {
        'rmse': round(rmse, 2),
        'r2': round(r2, 3),
        'top_features': sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
    }
