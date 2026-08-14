# URL Shortener

A simple, self-contained URL shortener built with Flask and SQLite.

## Features

- Shorten any URL to a random 6-character code, or pick your own custom code
- Redirect from the short URL to the original
- Click tracking per link
- Simple web UI + JSON API
- Recent links table on the homepage

## Setup

1. **Install dependencies** (Python 3.8+ required):

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**

   ```bash
   python app.py
   ```

3. Open your browser to **http://127.0.0.1:5000**

The SQLite database (`urls.db`) is created automatically in the project folder on first run.

## Usage (Web UI)

- Paste a URL into the box and click **Shorten**.
- Optionally provide a custom short code (letters/numbers only).
- Click on the short link to visit the original site (this also increments the click counter).
- Click on the click count to see stats for that link.

## Usage (JSON API)

**Create a short link:**

```bash
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/some/long/path"}'
```

Response:

```json
{
  "short_code": "aZ3xQ1",
  "short_url": "http://127.0.0.1:5000/aZ3xQ1",
  "original_url": "http://example.com/some/long/path"
}
```

Optionally include a custom code:

```bash
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "custom_code": "mylink"}'
```

**Get stats for a link:**

```bash
curl http://127.0.0.1:5000/api/stats/aZ3xQ1
```

Response:

```json
{
  "short_code": "aZ3xQ1",
  "original_url": "http://example.com/some/long/path",
  "created_at": "2026-08-14T12:00:00.000000",
  "clicks": 3
}
```

## Project structure

```
url_shortener/
├── app.py               # Flask application (routes, DB logic)
├── requirements.txt      # Python dependencies
├── templates/
│   ├── base.html          # Shared layout & styling
│   ├── index.html         # Homepage: shorten form + recent links
│   ├── stats.html         # Per-link stats page
│   └── 404.html           # Not-found page
└── urls.db               # SQLite database (created on first run)
```

## Notes

- This is a development server (`debug=True`). For production, run it behind a real WSGI server (e.g. `gunicorn app:app`) and set `debug=False`.
- Short codes are 6 characters from `[A-Za-z0-9]`, giving ~56 billion combinations, and collisions are checked against the database before saving.
- To reset all data, just delete `urls.db` and restart the app.
