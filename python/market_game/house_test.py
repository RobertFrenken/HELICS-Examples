from house_template import House
# defining a house federate

class TestHouse(House):
    def __init__(self, name: str, connection: str = "localhost"):
        super().__init__(name, connection)

    def compute_demand(self, price: float, hour: int, battery_charge: float, demand: list[float], price_history: list[float]) -> float:
        # Implement your specific demand computation logic here
        if battery_charge == 0:
            return demand[hour] + 2
        else:
            return demand[hour] - 2

if __name__ == "__main__":
    connection_string="localhost"
    house=TestHouse("TestHouse",connection_string)
    house.run()
    house.plot_results()
    