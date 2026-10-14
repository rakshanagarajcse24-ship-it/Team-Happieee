# Smart Exam Scheduler

A browser dashboard backed by a Python FastAPI scheduling engine. NetworkX builds the course conflict graph; Python implements DSatur, capacity-aware exact backtracking, timetable verification, and seeded benchmarks. The existing HTML/CSS/JavaScript interface handles rendering, graph drawing, charts, and CSV downloads.

## Run locally

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000> in your browser. The page must be served by FastAPI (opening `index.html` as a local file will not provide the Python API).

## API

- `POST /api/schedule` accepts `{"n": 6, "r": 3, "clashes": "1-6\n2-5"}`.
- `POST /api/benchmark` accepts `{"density": 0.25, "seed": 2026}`.
- `GET /api/health` reports the active Python/NetworkX backend.

Exact search has an 1.8 second time limit for a schedule. It returns its best valid incumbent and marks optimality unproven if the search limit is reached.
