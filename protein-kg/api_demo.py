from fastapi import FastAPI
from pydantic import BaseModel
import pickle, time, random

app = FastAPI(title="Protein Search Demo")

# 加载数据
with open("data/cleaned_cache.pkl", "rb") as fh:
    proteins = pickle.load(fh)
print(f"Loaded: {len(proteins)} proteins")

class Search(BaseModel):
    sequence: str = ""
    top_k: int = 10

@app.post("/search")
async def search(req: Search):
    t0 = time.time()
    r = [{"id": p["id"], "name": p["name"][:60]} 
         for p in random.sample(proteins, min(req.top_k, len(proteins)))]
    return {"results": r, "latency_ms": round((time.time()-t0)*1000, 2)}

@app.get("/health")
async def health():
    return {"status": "ok", "total": len(proteins)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)