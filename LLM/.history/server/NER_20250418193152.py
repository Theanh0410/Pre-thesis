import os
import requests
import json
import re

# Ollama API
OLLAMA_URL = "http://localhost:11434/api/generate"  # Modify this if your Ollama server URL is different.
MODEL_NAME = "llama3.2"

# Function to call Llama API (Ollama)
def generate_with_llm(prompt: str) -> str:
    """Call Llama 3.2 (via Ollama API) to generate the assistant's response."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False  # No need to stream if you want the full response at once
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # Check if the response is successful

        # Parse response and return the content
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

# Function to extract entities (Action, Object, Value)
def extract_entities(text: str):
    """
    Extract actions, objects, and values from the LLM response using simple rules and regex.
    This is done after receiving the LLM response from the `generate_with_llm()` function.
    """
    entities = []

    # Regex patterns for action extraction (can be customized further)
    action_patterns = [
        (r"turn on the (.*)", "Turn on", "smart-home"),
        (r"turn off the (.*)", "Turn off", "smart-home"),
        (r"adjust the (.*) to (.*)", "Adjust", "smart-home"),
        (r"play (.*) music", "Play", "music"),
        (r"bring (.*) to (.*)", "Bring", "task-allocation"),
        (r"prepare (.*) for (.*)", "Prepare", "task-allocation"),
        (r"get (.*)", "Get", "task-allocation"),
    ]

    # Look for matches using regex and capture entities
    for pattern, action, category in action_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            entities.append({
                "action": action,
                "object": match.group(1).strip(),
                "value": match.group(2) if len(match.groups()) > 1 else None,
                "category": category,
                "source": "NER-after-LLM"
            })

    return entities

# Example usage
user_prompt = "I just go home and I feel tired, can you prepare the living room for me?"

# Generate the assistant's response using Llama 3.2 via Ollama
llm_response = generate_with_llm(user_prompt)
print("LLM Response:", llm_response)

# Extract the entities from the LLM response
entities = extract_entities(llm_response)
print("Extracted Entities:", entities)
