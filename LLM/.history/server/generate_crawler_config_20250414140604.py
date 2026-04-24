import json
from pathlib import Path

crawler_config = {
    "max_depth": 3,
    "valid_path_keywords": [
        "article", "advice", "guide", "topics", "mental", "health", "support"
    ],
    "skip_keywords": [
        "login", "signup", "account", "privacy", "terms", "index"
    ],
    "skip_extensions": [
        ".pdf", ".zip", ".jpg", ".jpeg", ".png", ".svg", ".webp", ".doc", ".docx"
    ]
}

config_path = Path("crawler_config.json")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(crawler_config, f, ensure_ascii=False, indent=2)

print("✅ File crawler_config.json created!")
