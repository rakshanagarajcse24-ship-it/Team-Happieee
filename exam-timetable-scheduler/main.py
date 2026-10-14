"""FastAPI web server and JSON API for Smart Exam Scheduler."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scheduler import InputError, benchmark, parse_input, schedule

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Smart Exam Scheduler", version="1.0.0")


class ScheduleRequest(BaseModel):
    n: object
    r: object
    clashes: str


class BenchmarkRequest(BaseModel):
    density: float
    seed: int = 2026


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.post("/api/schedule")
def create_schedule(request: ScheduleRequest):
    try:
        n, r, edges = parse_input(request.n, request.r, request.clashes)
        return schedule(n, r, edges)
    except InputError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc


@app.post("/api/benchmark")
def create_benchmark(request: BenchmarkRequest):
    if not 0.01 <= request.density <= 0.95:
        raise HTTPException(status_code=422, detail={"density": "Choose an edge density from 1% to 95%."})
    if not 0 <= request.seed <= 2**32 - 1:
        raise HTTPException(status_code=422, detail={"seed": "Seed must be between 0 and 4294967295."})
    return benchmark(request.density, request.seed)


@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "python", "graph_library": "networkx"}
