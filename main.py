import csv
import heapq
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Flight:
    source: int
    destination: int
    price: int


def read_graph_from_console():
    n, m = map(int, input("Enter N M: ").split())
    k, coupons = map(int, input("Enter K C: ").split())
    flights = []
    print(f"Enter {m} flights as: source destination price")
    for _ in range(m):
        u, v, price = map(int, input().split())
        flights.append(Flight(u, v, price))
    return n, k, coupons, flights


def read_graph_from_csv(path):
    flights = []
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("CSV needs a header row: source,destination,price")
        headers = {name.strip().lower(): name for name in reader.fieldnames}
        required = {"source", "destination", "price"}
        if not required.issubset(headers):
            raise ValueError("CSV needs columns: source,destination,price")
        for row in reader:
            flights.append(Flight(
                int(row[headers["source"]]),
                int(row[headers["destination"]]),
                int(row[headers["price"]]),
            ))
    if not flights:
        raise ValueError("CSV contains no flights.")
    n = int(input("Enter number of cities N: "))
    k, coupons = map(int, input("Enter K C: ").split())
    return n, k, coupons, flights


def generate_graph():
    n = int(input("Enter number of cities N (at least 2): "))
    k, coupons = map(int, input("Enter K C: ").split())
    if n < 2:
        raise ValueError("N must be at least 2.")
    route_flights = random.randint(1, min(max(k, 0) + 1, n - 1))
    middle = list(range(2, n))
    random.shuffle(middle)
    route = [1] + middle[:route_flights - 1] + [n]
    flights = []
    used = set()
    for u, v in zip(route, route[1:]):
        flights.append(Flight(u, v, random.randint(50, 1000)))
        used.add((u, v))
    max_edges = n * (n - 1)
    target = random.randint(len(flights), min(max_edges, max(len(flights), n * 3)))
    while len(flights) < target:
        u, v = random.sample(range(1, n + 1), 2)
        if (u, v) not in used:
            used.add((u, v))
            flights.append(Flight(u, v, random.randint(50, 1000)))
    return n, k, coupons, flights


def cheapest_route(n, k, coupon_count, flights):
    if n < 1 or k < 0 or coupon_count < 0:
        raise ValueError("N must be positive; K and C cannot be negative.")
    graph = [[] for _ in range(n + 1)]
    for flight in flights:
        if not (1 <= flight.source <= n and 1 <= flight.destination <= n):
            raise ValueError("Flight city IDs must be between 1 and N.")
        if flight.price < 0:
            raise ValueError("Flight prices cannot be negative.")
        graph[flight.source].append(flight)

    # At most K intermediate stops means at most K+1 flights.
    max_flights = k + 1
    start = (1, 0, 0)  # city, flights taken, coupons used
    best = {start: 0}
    parent = {}
    queue = [(0, 1, 0, 0)]

    while queue:
        cost, city, used_flights, used_coupons = heapq.heappop(queue)
        state = (city, used_flights, used_coupons)
        if cost != best.get(state):
            continue
        if city == n:
            path = []
            while state != start:
                previous, flight, coupon_used = parent[state]
                path.append((flight, coupon_used))
                state = previous
            path.reverse()
            return cost, path
        if used_flights == max_flights:
            continue

        for flight in graph[city]:
            next_flights = used_flights + 1
            next_state = (flight.destination, next_flights, used_coupons)
            next_cost = cost + flight.price
            if next_cost < best.get(next_state, float("inf")):
                best[next_state] = next_cost
                parent[next_state] = (state, flight, False)
                heapq.heappush(queue, (next_cost, *next_state))

            if used_coupons < coupon_count:
                coupon_state = (
                    flight.destination, next_flights, used_coupons + 1
                )
                coupon_cost = cost + flight.price // 2
                if coupon_cost < best.get(coupon_state, float("inf")):
                    best[coupon_state] = coupon_cost
                    parent[coupon_state] = (state, flight, True)
                    heapq.heappush(queue, (coupon_cost, *coupon_state))

    return -1, []


def write_result_csv(flights, path, output_path):
    # Include an occurrence index so duplicate identical flights are marked correctly.
    selected = {}
    for flight, coupon_used in path:
        key = (flight.source, flight.destination, flight.price)
        selected.setdefault(key, []).append(coupon_used)

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "source", "destination", "price", "on_path",
            "coupon_used", "price_paid",
        ])
        for flight in flights:
            key = (flight.source, flight.destination, flight.price)
            marked = bool(selected.get(key))
            coupon_used = selected[key].pop(0) if marked else False
            paid = flight.price // 2 if coupon_used else flight.price
            writer.writerow([
                flight.source, flight.destination, flight.price,
                "x" if marked else "", "x" if marked and coupon_used else "",
                paid if marked else "",
            ])


def animate_route(n, k, flights, path, total_cost):
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
        from matplotlib.animation import FuncAnimation
    except ImportError as exc:
        print("Visualization libraries missing. Install with: pip install -r requirements.txt")
        print(exc)
        return

    graph = nx.MultiDiGraph()
    graph.add_nodes_from(range(1, n + 1))
    for index, flight in enumerate(flights):
        graph.add_edge(flight.source, flight.destination, key=index, price=flight.price)
    positions = nx.spring_layout(graph, seed=7)
    route_edges = [(f.source, f.destination, i) for i, (f, _) in enumerate(path)]
    route_nodes = [1] + [f.destination for f, _ in path]
    fig, ax = plt.subplots(figsize=(10, 7))

    def draw(frame):
        ax.clear()
        ax.axis("off")
        ax.set_title("Budget Traveller with Coupons")
        colors = ["green" if node == 1 else "red" if node == n else
                  "orange" if node in route_nodes else "skyblue"
                  for node in graph.nodes]
        nx.draw_networkx_nodes(graph, positions, node_color=colors, node_size=800, ax=ax)
        nx.draw_networkx_labels(graph, positions, ax=ax)
        nx.draw_networkx_edges(graph, positions, edge_color="gray", arrows=True,
                               connectionstyle="arc3,rad=0.08", ax=ax)
        labels = {(u, v, key): data["price"] for u, v, key, data in graph.edges(keys=True, data=True)}
        nx.draw_networkx_edge_labels(graph, positions, edge_labels=labels, font_size=8, ax=ax)

        count = min(frame, len(path))
        for i, (flight, coupon_used) in enumerate(path[:count]):
            edge = route_edges[i]
            nx.draw_networkx_edges(
                graph, positions, edgelist=[edge],
                edge_color="gold" if coupon_used else "dodgerblue",
                width=4, arrows=True, connectionstyle="arc3,rad=0.08", ax=ax,
            )
        running_cost = sum(f.price // 2 if coupon else f.price
                           for f, coupon in path[:count])
        coupons_used = sum(coupon for _, coupon in path[:count])
        message = (f"Running cost: {running_cost} | Stops used: {max(0, count - 1)}/{k}"
                   f" | Coupons used: {coupons_used}")
        if count and path[count - 1][1]:
            price = path[count - 1][0].price
            message += f" | Coupon: {price} → {price // 2}"
        if frame > len(path):
            message += f" | Final cost: {total_cost}"
        ax.text(0.5, -0.08, message, transform=ax.transAxes, ha="center")

    animation = FuncAnimation(fig, draw, frames=max(2, len(path) + 2), interval=1000, repeat=False)
    fig._route_animation = animation
    plt.tight_layout()
    plt.show()


def main():
    print("Budget Traveller with Coupons")
    print("1. Enter graph manually")
    print("2. Read graph from CSV")
    print("3. Generate a random graph")
    option = input("Choose option (1/2/3): ").strip()

    if option == "1":
        n, k, coupons, flights = read_graph_from_console()
    elif option == "2":
        csv_path = input("Enter input CSV path [sample_flights.csv]: ").strip()
        csv_path = csv_path or "sample_flights.csv"
        n, k, coupons, flights = read_graph_from_csv(csv_path)
    elif option == "3":
        n, k, coupons, flights = generate_graph()
        with open("generated_flights.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["source", "destination", "price"])
            writer.writerows((f.source, f.destination, f.price) for f in flights)
        print("Generated graph saved to generated_flights.csv")
    else:
        raise ValueError("Choose option 1, 2, or 3.")

    cost, path = cheapest_route(n, k, coupons, flights)
    print(f"Minimum cost: {cost}")
    if cost == -1:
        print("No valid route from city 1 to city N.")
    else:
        cities = [1] + [flight.destination for flight, _ in path]
        print("Route: " + " -> ".join(map(str, cities)))
        for flight, coupon_used in path:
            suffix = f" (coupon: {flight.price} -> {flight.price // 2})" if coupon_used else ""
            print(f"  {flight.source} -> {flight.destination}: {flight.price}{suffix}")

    write_result_csv(flights, path, "result.csv")
    print("Path-marked CSV saved to result.csv")
    animate_route(n, k, flights, path, cost)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, csv.Error) as error:
        print(f"Error: {error}")
