from typing import List, Dict

class ProteinChunkProcessor:
    def __init__(self, chunk_size=100):
        self.chunk_size = chunk_size
    
    def chunk_by_protein(self, proteins):
        chunks = []
        for i in range(0, len(proteins), self.chunk_size):
            chunks.append(proteins[i:i+self.chunk_size])
        return chunks
    
    def chunk_by_length(self, proteins):
        buckets = {"short": [], "medium": [], "long": [], "xlong": []}
        for p in proteins:
            l = p.get("length", len(p.get("sequence", "")))
            if l < 200:
                buckets["short"].append(p)
            elif l < 500:
                buckets["medium"].append(p)
            elif l < 1000:
                buckets["long"].append(p)
            else:
                buckets["xlong"].append(p)
        return [v for v in buckets.values() if v]