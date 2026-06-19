from dotenv import load_dotenv
import os
import requests

load_dotenv()
or_token = os.getenv('OPENROUTER')
deepseek_model = "deepseek/deepseek-r1-0528:free"
devstral_model = "mistralai/devstral-2512:free"
gemma_model="google/gemma-3n-e4b-it:free"

"""
Notice:
If it wasn't obvious, all of these models are free models via openrouter
For scaling purposes, an upgraded model with a fairly low cost could be utilized.
However, for all current purposes, these lightweight models are more than enough.
"""

def chat_deepseek(prompt, model=f"{deepseek_model}"):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {or_token}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def chat_devstral(prompt):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {or_token}",
        },
        json={
            "model": f"{devstral_model}",
            "messages": [
                {"role": "user", "content": prompt}
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def chat_gemma(prompt):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {or_token}",
        },
        json={
            "model": f"{gemma_model}",
            "messages": [
                {"role": "user", "content": prompt}
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]