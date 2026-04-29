from transformers import pipeline

class ProteinNER:
    def __init__(self):
        self.nlp = pipeline("ner", model="dmis-lab/biobert-base-cased-v1.1", aggregation_strategy="simple")
    
    def extract(self, text):
        entities = self.nlp(text)
        return [{"entity": e["word"], "type": e["entity_group"], "score": round(e["score"], 3)} for e in entities]