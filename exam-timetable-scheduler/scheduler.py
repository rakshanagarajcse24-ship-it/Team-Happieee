"""Python scheduling engine for the Smart Exam Scheduler."""

from __future__ import annotations

import random
import re
import time
from typing import Any

import networkx as nx

MAX_COURSES = 100
MAX_HALLS = 100
EXACT_LIMIT_MS = 1800


class InputError(ValueError):
    """An input error with field-specific messages for the web form."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("Input validation failed")
        self.errors = errors


def parse_input(n_value: Any, r_value: Any, clashes_value: Any) -> tuple[int, int, list[tuple[int, int]]]:
    errors: dict[str, str] = {}
    try:
        n = int(n_value)
        if str(n_value).strip() != str(n):
            raise ValueError
        if n < 1:
            raise ValueError
        if n > MAX_COURSES:
            errors["n"] = f"Please use {MAX_COURSES} courses or fewer for this scheduler."
    except (ValueError, TypeError):
        n = 0
        errors["n"] = "Enter a positive whole number of courses."

    try:
        r = int(r_value)
        if str(r_value).strip() != str(r):
            raise ValueError
        if r < 1:
            raise ValueError
        if r > MAX_HALLS:
            errors["r"] = f"Please use {MAX_HALLS} halls or fewer."
    except (ValueError, TypeError):
        r = 0
        errors["r"] = "Enter a positive whole number of halls."

    source = str(clashes_value or "").strip()
    edges: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    if source and source != "0":
        for line_number, raw_line in enumerate(source.splitlines(), start=1):
            line = raw_line.strip()
            match = re.fullmatch(r"(\d+)\s*[-,]\s*(\d+)", line)
            if not match:
                errors["clash"] = f"Line {line_number}: enter a pair like 1-2, or use 0 by itself for no clashes."
                break
            a, b = map(int, match.groups())
            if not (1 <= a <= n and 1 <= b <= n):
                limit = n if n else "N"
                errors["clash"] = f"Line {line_number}: course IDs must be between 1 and {limit}."
                break
            if a == b:
                errors["clash"] = f"Line {line_number}: course {a} cannot conflict with itself."
                break
            edge = (min(a, b), max(a, b))
            if edge in seen:
                errors["clash"] = f"Line {line_number}: duplicate clash {edge[0]}-{edge[1]}."
                break
            seen.add(edge)
            edges.append(edge)

    if errors:
        raise InputError(errors)
    return n, r, edges


def build_graph(n: int, edges: list[tuple[int, int]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(1, n + 1))
    graph.add_edges_from(edges)
    return graph


def validate_timetable(graph: nx.Graph, colors: list[int], hall_limit: int) -> bool:
    if len(colors) != graph.number_of_nodes() or any(not isinstance(c, int) or c < 0 for c in colors):
        return False
    counts: dict[int, int] = {}
    for node in graph:
        color = colors[node - 1]
        counts[color] = counts.get(color, 0) + 1
        if counts[color] > hall_limit:
            return False
    return all(colors[a - 1] != colors[b - 1] for a, b in graph.edges)


def dsatur_schedule(graph: nx.Graph, hall_limit: int) -> dict[str, Any]:
    started = time.perf_counter()
    n = graph.number_of_nodes()
    colors = [-1] * n
    saturation = [set() for _ in range(n)]
    sizes: list[int] = []

    for _ in range(n):
        uncolored = [v for v in range(1, n + 1) if colors[v - 1] < 0]
        chosen = min(uncolored, key=lambda v: (-len(saturation[v - 1]), -graph.degree[v], v))
        slot = 0
        while True:
            if slot >= len(sizes):
                sizes.append(0)
            if sizes[slot] < hall_limit and all(colors[neighbor - 1] != slot for neighbor in graph[chosen]):
                break
            slot += 1
        colors[chosen - 1] = slot
        sizes[slot] += 1
        for neighbor in graph[chosen]:
            if colors[neighbor - 1] < 0:
                saturation[neighbor - 1].add(slot)

    elapsed = (time.perf_counter() - started) * 1000
    result = {"colors": colors, "count": max(colors, default=-1) + 1, "time": elapsed}
    result["valid"] = validate_timetable(graph, colors, hall_limit)
    return result


def exact_schedule(graph: nx.Graph, hall_limit: int, incumbent: dict[str, Any], limit_ms: int = EXACT_LIMIT_MS) -> dict[str, Any]:
    started = time.perf_counter()
    n = graph.number_of_nodes()
    order = sorted(graph.nodes, key=lambda v: (-graph.degree[v], v))
    best_colors = incumbent["colors"][:]
    best_count = incumbent["count"]
    nodes_searched = 0
    deadline = time.perf_counter() + limit_ms / 1000
    timed_out = False

    for slot_limit in range(1, best_count):
        colors = [-1] * n
        sizes = [0] * slot_limit

        def search(depth: int) -> bool:
            nonlocal nodes_searched, timed_out
            nodes_searched += 1
            if nodes_searched % 256 == 0 and time.perf_counter() >= deadline:
                timed_out = True
                return False
            if depth == n:
                return True
            vertex = order[depth]
            forbidden = {colors[neighbor - 1] for neighbor in graph[vertex] if colors[neighbor - 1] >= 0}
            for color in range(slot_limit):
                if sizes[color] >= hall_limit or color in forbidden:
                    continue
                colors[vertex - 1] = color
                sizes[color] += 1
                if search(depth + 1):
                    return True
                if timed_out:
                    return False
                sizes[color] -= 1
                colors[vertex - 1] = -1
            return False

        if search(0):
            best_colors = colors[:]
            best_count = slot_limit
            # Limits are checked in ascending order, so the first feasible
            # limit is the minimum and every smaller limit was ruled out.
            break
        elif timed_out:
            break

    result = {
        "colors": best_colors,
        "count": best_count,
        "time": (time.perf_counter() - started) * 1000,
        "valid": validate_timetable(graph, best_colors, hall_limit),
        "proven": not timed_out,
        "status": "incomplete" if timed_out else "optimal",
        "nodes": nodes_searched,
    }
    return result


def make_timetable(colors: list[int], hall_limit: int) -> list[list[int | None]]:
    count = max(colors, default=-1) + 1
    slots: list[list[int | None]] = [[None] * hall_limit for _ in range(count)]
    offsets = [0] * count
    for course, slot in enumerate(colors, start=1):
        slots[slot][offsets[slot]] = course
        offsets[slot] += 1
    return slots


def schedule(n: int, r: int, edges: list[tuple[int, int]]) -> dict[str, Any]:
    graph = build_graph(n, edges)
    greedy = dsatur_schedule(graph, r)
    exact = exact_schedule(graph, r, greedy)
    if not greedy["valid"] or not exact["valid"]:
        raise RuntimeError("A schedule failed verification")
    for result in (greedy, exact):
        result["timetable"] = make_timetable(result["colors"], r)
    adjacency = [[neighbor - 1 for neighbor in sorted(graph[node])] for node in graph.nodes]
    return {
        "n": n,
        "r": r,
        "edges": [list(edge) for edge in edges],
        "adj": adjacency,
        "greedy": greedy,
        "exact": exact,
    }


def benchmark(density: float, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    results = []
    for n in (10, 20, 30, 40, 50):
        edges = [(a, b) for a in range(1, n + 1) for b in range(a + 1, n + 1) if rng.random() < density]
        graph = build_graph(n, edges)
        greedy = dsatur_schedule(graph, 4)
        exact = exact_schedule(graph, 4, greedy, 1500)
        for result in (greedy, exact):
            result["timetable"] = make_timetable(result["colors"], 4)
        results.append({"n": n, "edges": len(edges), "greedy": greedy, "exact": exact})
    return {"seed": seed, "density": density, "hall_limit": 4, "results": results}
