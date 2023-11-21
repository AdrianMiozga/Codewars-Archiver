import json

import requests

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

USERNAME = config["username"]
_SESSION_ID = config["_session_id"]

cookies = {
    "_session_id": _SESSION_ID,
}

headers = {
    "user-agent": """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36""",
    "x-requested-with": "XMLHttpRequest",
}

params = {
    "page": "1",
}

response = requests.get(
    f"https://www.codewars.com/users/{USERNAME}/completed_solutions",
    params=params,
    cookies=cookies,
    headers=headers,
    timeout=5,
)

print(response.url)

with open("output/output.html", "w", encoding="utf-8") as file:
    file.write(response.text)
