import requests

url = "http://localhost:8000/dashboard/chat"
data = {"message": "Привет, как дела?"}
response = requests.post(url, data=data)
print("Ответ модели:", response.json())
