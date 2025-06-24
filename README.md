# Statistics Search API

A FastAPI application that provides semantic search capabilities over a collection of statistics data. The application uses SQLite for data storage, FAISS for efficient similarity search, and sentence-transformers for generating embeddings.

## Features

- Semantic search over statistics data
- Two search endpoints:
  - `/find`: Returns top-5 most related results (configurable)
  - `/stream/find`: Streams top-10 most related results progressively
- Uses modern NLP techniques for accurate search results

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the server:
```bash
python app.py
```

The server will start on `http://localhost:8000`

## API Usage

### Regular Search
```bash
curl -X POST "http://localhost:8000/find" \
     -H "Content-Type: application/json" \
     -d '{"query": "AI unicorns", "limit": 5}'
```

### Streaming Search
```bash
curl -X POST "http://localhost:8000/stream/find" \
     -H "Content-Type: application/json" \
     -d '{"query": "AI unicorns"}'
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Data Structure

The application expects a `statistics.json` file in the root directory with the following structure:
```json
[
  {
    "id": 123,
    "title": "Example Title",
    "subject": "Example Subject",
    "description": "Example Description",
    "link": "https://example.com",
    "date": "2024-01-01 12:00:00+00:00",
    "teaser_image_url": "https://example.com/image.jpg"
  }
]
```

## Load Testing

The `loadtesting.py` script simulates, in a very dummy way, concurrent users.

First the test dependencies must be installed:
```bash
pip install -r requirements.load.txt
```

Once the dependencies are installed the script can be invoked as follows:
```bash
python loadtesting.py --url <URL_TO_STRESS>
```

By default it will issue 100 concurrent requests. This can be configured using the `--requests` argument:
```bash
python loadtesting.py --url <URL_TO_STRESS> --requests <DESIRED_CONCURRENT_REQUESTS>
```

Due to time constraints the script has the following limitations that would not be admissible in a real-world scenario:
* For security reasons it shouldn't allow for any arbitrary URL to be queried, only `localhost`.
* It is not possible to set a fixed number of concurrent requests, all requests will be issued at once.
* Most importantly, it's not possible to send body (POST) parameters.

## Notes

- The first time you run the application, it will:
  1. Create a SQLite database
  2. Load data from statistics.json
  3. Generate embeddings for all entries
  4. Build a FAISS index for efficient search
- Subsequent runs will use the existing database and index
