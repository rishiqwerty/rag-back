from fastapi import FastAPI
from .services.ingestion import chunk_text
app = FastAPI()

@app.get("/")
def read_root():

    from sentence_transformers import SentenceTransformer
    import time

    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    start = time.time()
    vec = model.encode("Whistleblower here.")
    print(len(vec))  # should be 768
    print(f"Time taken: {time.time() - start:.3f} seconds")
    chunk=chunk_text()
    # print(len(chunk))
    return {"status": f"{chunk}"}

def doc_upload():
    pass
