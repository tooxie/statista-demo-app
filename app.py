from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import sqlite3
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import io
import time

# Initialize FastAPI app
app = FastAPI()

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Database setup
def init_db():
    conn = sqlite3.connect('statistics.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS statistics
                 (id INTEGER PRIMARY KEY,
                  title TEXT,
                  subject TEXT,
                  description TEXT,
                  link TEXT,
                  date TEXT,
                  teaser_image_url TEXT,
                  embedding BLOB)''')
    conn.commit()
    conn.close()

# Load data and create embeddings
def load_data():
    with open('statistics.json', 'r') as f:
        data = json.load(f)

    conn = sqlite3.connect('statistics.db')
    c = conn.cursor()

    # Check if data is already loaded
    c.execute("SELECT COUNT(*) FROM statistics")
    if c.fetchone()[0] == 0:
        for item in data:
            # Create embedding for search
            text = f"{item['title']} {item['subject']} {item['description']}"
            embedding = model.encode(text)

            # Store in database
            c.execute('''INSERT INTO statistics
                        (id, title, subject, description, link, date, teaser_image_url, embedding)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (item['id'], item['title'], item['subject'], item['description'],
                      item['link'], item['date'], item['teaser_image_url'],
                      embedding.tobytes()))

    conn.commit()
    conn.close()

# Initialize database and load data
init_db()
load_data()

# Create FAISS index
def create_faiss_index():
    conn = sqlite3.connect('statistics.db')
    c = conn.cursor()

    # Get all embeddings
    c.execute("SELECT id, embedding FROM statistics")
    results = c.fetchall()

    if not results:
        return None

    # Create FAISS index
    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)

    # Add vectors to index
    ids = []
    vectors = []
    for id_, embedding_bytes in results:
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        vectors.append(embedding)
        ids.append(id_)

    vectors = np.array(vectors)
    index.add(vectors)

    conn.close()
    return index, ids

# Create FAISS index
index, ids = create_faiss_index()

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

@app.get("/")
async def root():
    return {"message": "Welcome to the Statistics Search API"}

@app.get("/health")
async def shallow_health():
    """This is a shallow health check endpoint. It simply makes sure that the
    app is up and running. Since this is a very cheap operation, kubernetes
    can hit this endpoint constantly as part of the liveness and readiness
    probes."""

    return {"message": "OK"}

@app.get("/health/deep")
async def deep_health():
    """This is the deep health check endpoint. It should test that all the
    system's dependencies are reachable and healthy. This not only means
    pinging the database, but also making sure that the credentials work.

    This is a more expensive endpoint, it should not be queried constantly.
    Not only it could incur in extra costs but it can affect performance of the
    overall application if it gets invoked too often. Instead, we should use
    this as part of the startup probe."""

    try:
        # Test database connection
        conn = sqlite3.connect('statistics.db')
        conn.close()

        # Here we should add all necessary checks. For example if we depend on
        # an external service, we should make sure that it's reachable and able
        # to handle our requests.
    except Exception as e:
        # For demo purposes we can return the error message, but in production
        # we should be careful to not leak sensitive information.
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return {"message": "OK"}

@app.post("/find")
async def find_statistics(query: SearchQuery):
    if not index:
        raise HTTPException(status_code=500, detail="Search index not initialized")

    # Encode query
    query_embedding = model.encode(query.query)

    # Search in FAISS index
    k = min(query.limit, len(ids))
    distances, indices = index.search(np.array([query_embedding]), k)

    # Get results from database
    conn = sqlite3.connect('statistics.db')
    c = conn.cursor()

    results = []
    for idx in indices[0]:
        c.execute("SELECT * FROM statistics WHERE id = ?", (ids[idx],))
        result = c.fetchone()
        if result:
            results.append({
                "id": result[0],
                "title": result[1],
                "subject": result[2],
                "description": result[3],
                "link": result[4],
                "date": result[5],
                "teaser_image_url": result[6]
            })

    conn.close()
    return results

@app.post("/stream/find")
async def stream_find_statistics(query: SearchQuery):
    if not index:
        raise HTTPException(status_code=500, detail="Search index not initialized")

    # Encode query
    query_embedding = model.encode(query.query)

    # Search in FAISS index
    k = min(10, len(ids))  # Always return top 10 for streaming
    distances, indices = index.search(np.array([query_embedding]), k)

    # Get results from database
    conn = sqlite3.connect('statistics.db')
    c = conn.cursor()

    async def generate():
        for idx in indices[0]:
            c.execute("SELECT * FROM statistics WHERE id = ?", (ids[idx],))
            result = c.fetchone()
            if result:
                item = {
                    "id": result[0],
                    "title": result[1],
                    "subject": result[2],
                    "description": result[3],
                    "link": result[4],
                    "date": result[5],
                    "teaser_image_url": result[6]
                }
                yield f"data: {json.dumps(item)}\n\n"
                time.sleep(0.1)  # Small delay to demonstrate streaming

    conn.close()
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)