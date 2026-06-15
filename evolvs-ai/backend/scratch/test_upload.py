import requests

url = "http://localhost:8000/api/upload/"
files = {"file": open("data/uploads/20260608_223926_bpo-qa (1).xlsx", "rb")}

try:
    response = requests.post(url, files=files)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
