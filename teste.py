import requests
url = "https://lobatofranca.app.n8n.cloud/webhook-test/fe320849-b3a4-4a70-bf78-7e1b09463b5d"
payload = {"message": "Teste do chatbot via n8n"}
headers = {"Content-Type": "application/json"}
response = requests.post(url, json=payload, headers=headers)
print(response.status_code)
print(response.text)