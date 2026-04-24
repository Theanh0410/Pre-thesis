import stanza

nlp = stanza.Pipeline('en', processors='tokenize,pos,lemma,ner,depparse')

def extract_smarthome_actions(text):
    doc = nlp(text)
    actions = []
    
    for sent in doc.sentences:
        for word in sent.words:
            if word.upos == "VERB":
                action = {
                    "action": word.lemma,
                    "object": " ".join([w.text for w in sent.words 
                                      if w.head == word.id and w.deprel in ("obj", "obl")]),
                    "category": "smart-home" if any(e.text.lower() in smart_home_devices 
                                      for e in sent.ents) else "task-allocation"
                }
                actions.append(action)
    return actions