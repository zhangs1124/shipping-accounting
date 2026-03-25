import requests
url = "http://localhost:8000/voyage-tasks/create"
data = {"ship_name": "WAN-HAI-301", "voyage_no": "WH-2024-033"}
r = requests.post(url, data=data)
print(r.status_code)
print(r.url)
