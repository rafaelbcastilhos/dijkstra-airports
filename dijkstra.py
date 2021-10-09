import collections
import csv
import functools
import haversine
import heapq
import sys

Airport = collections.namedtuple('Airport', 'code name country latitude longitude')
Flight = collections.namedtuple('Flight', 'origin destination')
Route = collections.namedtuple('Route', 'price path')


class Heap(object):
    def __init__(self):
        self._values = []

    def push(self, value):
        heapq.heappush(self._values, value)

    def pop(self):
        return heapq.heappop(self._values)

    def __len__(self):
        return len(self._values)


def get_airports(path='airports.dat'):
    with open(path, 'rt') as fd:
        reader = csv.reader(fd)
        for row in reader:
            name = row[1]
            country = row[3]
            code = row[4]
            latitude = float(row[6])
            longitude = float(row[7])
            yield Airport(code, name, country, latitude, longitude)


AIRPORTS = {airport.code: airport for airport in get_airports()}


def get_flights(path='flights.dat'):
    with open(path, 'rt') as fd:
        reader = csv.reader(fd)
        for row in reader:
            origin = row[2]
            destination = row[4]
            nstops = int(row[7])
            if not nstops:
                yield Flight(origin, destination)


class Graph(object):
    def __init__(self):
        self._neighbors = collections.defaultdict(set)

    def connect(self, node1, node2):
        self._neighbors[node1].add(node2)
        self._neighbors[node2].add(node1)

    def neighbors(self, node):
        yield from self._neighbors[node]

    @classmethod
    def load(cls):
        world = cls()
        for flight in get_flights():
            try:
                origin = AIRPORTS[flight.origin]
                destination = AIRPORTS[flight.destination]
                world.connect(origin, destination)
            except KeyError:
                continue
        return world

    @staticmethod
    @functools.lru_cache()
    # Return the cheapest flight without stops
    def get_price(origin, destination, cents_per_km=0.1):
        # Haversine distance, in kilometers
        point1 = origin.latitude, origin.longitude,
        point2 = destination.latitude, destination.longitude
        distance = haversine.haversine(point1, point2)
        return distance * cents_per_km

    # Dijkstra's find the cheapest path
    def dijkstra(self, origin, destination):
        routes = Heap()
        for neighbor in self.neighbors(origin):
            price = self.get_price(origin, neighbor)
            routes.push(Route(price=price, path=[origin, neighbor]))

        visited = set()
        visited.add(origin)

        while routes:
            price, path = routes.pop()
            airport = path[-1]
            if airport in visited:
                continue

            if airport is destination:
                return price, path

            # Tentative distances to all the unvisited neighbors
            for neighbor in self.neighbors(airport):
                if neighbor not in visited:
                    new_price = price + self.get_price(airport, neighbor)
                    new_path = path + [neighbor]
                    routes.push(Route(new_price, new_path))

            visited.add(airport)

        return sys.maxsize


if __name__ == "__main__":
    world = Graph.load()
    source_location = input("Enter source prefix: ")
    destination_location = input("Enter destination prefix: ")

    price, path = world.dijkstra(AIRPORTS[source_location], AIRPORTS[destination_location])
    for index, airport in enumerate(path):
        print(index, '|', airport[0], '-', airport[1], '-', airport[2])

    print(price, '€')
