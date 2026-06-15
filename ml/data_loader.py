import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

def load_excel(url: str):
    # If URL is a Supabase signed URL or direct link
    resp = requests.get(url)
    resp.raise_for_status()
    xls = pd.ExcelFile(BytesIO(resp.content))
    
    drilldown = pd.read_excel(xls, sheet_name='Drilldown')
    audit_params = pd.read_excel(xls, sheet_name='Audit Parameters')
    agent_analytics = pd.read_excel(xls, sheet_name='Agent Analytics')
    param_analytics = pd.read_excel(xls, sheet_name='Parameter Analytics')
    
    # Clean timestamps (remove :60 issue)
    for col in ['Created At', 'Assigned At', 'Submitted At']:
        if col in drilldown.columns:
            drilldown[col] = drilldown[col].astype(str).str.replace(r':60$', ':59', regex=True)
            drilldown[col] = pd.to_datetime(drilldown[col], errors='coerce')
    
    return drilldown, audit_params, agent_analytics, param_analytics
