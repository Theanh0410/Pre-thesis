import spacy
import re
from typing import List, Dict

nlp = spacy.load("en_core_web_sm")

def ner_after_rag(text: str) -> List[Dict]:
    """Trích xuất thực thể smarthome từ input (dùng regex + SpaCy)."""
    patterns = {
        "turn on": r"(turn on|switch on|activate)\s(the\s)?(?P<device>.+?)\s(in the\s)?(?P<location>.+?)(?=\s|$)",
        "turn off": r"(turn off|switch off|deactivate)\s(the\s)?(?P<device>.+?)\s(in the\s)?(?P<location>.+?)(?=\s|$)",
        "adjust": r"(adjust|set|change)\s(the\s)?(?P<device>.+?)\s(to\s)?(?P<value>.+?)(?=\s|$)",
    }
    
    entities = []
    for action, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append({
                "action": action,
                "device": match.group("device").strip(),
                "location": match.group("location").strip() if "location" in match.groupdict() else None,
                "value": match.group("value").strip() if "value" in match.groupdict() else None,
                "source": "NER-after-RAG"
            })
    
    # Bổ sung bằng SpaCy NER
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"] and "thermostat" in ent.text.lower():
            entities.append({
                "action": "adjust",
                "device": "thermostat",
                "value": None,
                "source": "SpaCy-NER"
            })
    
    return entities