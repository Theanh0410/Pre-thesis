import stanza

# Initialize pipeline (download models if first run)
stanza.download('en')  # Only need to run once
nlp = stanza.Pipeline('en', processors='tokenize,pos,lemma,ner,depparse')

# Define your smart home devices vocabulary
smart_home_devices = {
    'lights', 'bulbs', 'thermostat', 'music', 'player', 
    'speaker', 'curtain', 'door', 'fan', 'purifier',
    'heater', 'tv', 'plug', 'machine'
}

def extract_smarthome_actions(text):
    doc = nlp(text)
    actions = []
    
    for sent in doc.sentences:  # Fixed typo: sentences not sentences
        for word in sent.words:
            if word.upos == "VERB":
                # Extract object
                obj_words = [
                    w.text for w in sent.words 
                    if w.head == word.id and 
                    w.deprel in ("obj", "obl", "nmod", "compound")
                ]
                obj_text = " ".join(obj_words) if obj_words else ""
                
                # Determine category
                category = "smart-home" if any(
                    device in obj_text.lower() or 
                    device in word.text.lower()
                    for device in smart_home_devices
                ) else "task-allocation"
                
                # Only add meaningful actions
                if obj_text or category == "smart-home":
                    actions.append({
                        "action": word.lemma,
                        "object": obj_text,
                        "category": category
                    })
    
    return actions

# Test
text = """To start, I'll turn on the lights in the living room by adjusting the smart bulbs..."""
print(extract_smarthome_actions(text))