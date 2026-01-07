import requests

resp = requests.post(
    "http://localhost:8202/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer EMPTY"
    },
    json={
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [
            {"role": "user", "content": "Say hello in one sentence."}
        ],
        "max_tokens": 50
    }
)

print(resp.status_code)
print(resp.json()["choices"][0]["message"]["content"])
