import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama3",
    "prompt": "What is 2 + 2?",
    "stream": False
}

try:
    response = requests.post(url, json=payload)
    print("✅ Status Code:", response.status_code)
    print("🤖 AI Reply:", response.json()['response'])
except Exception as e:
    print("❌ Error:", e)