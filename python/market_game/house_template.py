import helics as h
import json

from abc import ABC, abstractmethod

import matplotlib.pyplot as plt

from battery import Battery,check_valid,ensure_valid
# defining a house federate

class House(ABC):
    def __init__(self, name: str, connection: str = "localhost"):
        self.battery = Battery()
        self.name = name
        self.demand = [5] * 24  # Default demand profile
        self.consume = []
        self.actual_load = []
        self.prices = []
        self.actual_cost = []
        self.battery_state = []
        
        self.totalCost = 0.0
        self.current_time = 0
        self.connection = connection
        self.federate = None
        self.demand_pub = None
        self.price = None

        self.connect()

    @abstractmethod
    def compute_demand(price:float, hour:int, battery_charge:float, demand:list[float], price_history:list[float])->float:
        """Compute the demand based on the price, hour, battery charge, and demand profile."""
        pass
    
    def connect(self):
        fedinfo = h.helicsCreateFederateInfo()
        h.helicsFederateInfoSetCoreType(fedinfo, h.HELICS_CORE_TYPE_ZMQ_SS)
        h.helicsFederateInfoSetBroker(fedinfo, self.connection)
        h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 1.0)
        
        # Create the federate
        self.federate = h.helicsCreateCombinationFederate(self.name, fedinfo)
        print(f"Created federate {self.name}")
        # Register the subscription to the price
        self.price = self.federate.register_subscription("price", "$/kWh")
        
        # Register the demand publication
        self.demand_pub = self.federate.register_publication("demand", "float", "kWh")
        
        # Enter initializing mode
        self.federate.enter_initializing_mode()
        
        # Get the demand profile from the market maker
        print("getting the demand profile")
        demand_profile_json = h.helicsFederateWaitCommand(self.federate)
        self.demand = json.loads(demand_profile_json)["demand"]
        
        # Enter executing mode
        self.federate.enter_executing_mode()

    def run(self):
        
        while self.current_time<24:
            #get the current price
            current_price=h.helicsInputGetDouble(self.price)
            self.prices.append(current_price)
            #load the current consumption
            current_demand=self.demand[int(self.current_time)]
            # call the user defined consumption calculation method
            computed_demand=self.compute_demand(current_price,int(self.current_time),self.battery.current_charge(),self.demand,self.prices)
            #check if the computed demand is  valid
            warning=check_valid(computed_demand,current_demand, self.battery)
            if warning:
                #if it wasn't valid issue a warning and bound it to a the valid range
                print(f"invalid demand computed={computed_demand} warning={warning}, recalculating with new value")
                computed_demand=ensure_valid(computed_demand,current_demand, self.battery)
            self.actual_load.append(computed_demand)
            #update the battery
            self.battery.change(computed_demand-current_demand)
            #store some data
            self.battery_state.append(self.battery.current_charge())
            self.actual_cost.append(current_price*computed_demand)
            print(f"hour {int(self.current_time)}:price={current_price}, house_demand={current_demand}, load={computed_demand}, battery delta= {computed_demand-current_demand} battery charge={self.battery.current_charge()} cost={computed_demand*current_price}")
            #publish the demand and request the next step
            self.demand_pub.publish(computed_demand)
            self.current_time=self.federate.request_next_step()
    
        print(f"total load={sum(self.actual_load)}, total_cost={sum(self.actual_cost)}")
        self.federate.disconnect()
        
    def plot_results(self):
        time = list(range(24))
        figure, axis = plt.subplots(2, 2)

        # For demand
        axis[0, 0].plot(time, self.demand, color='r', label='consumption')
        axis[0, 0].plot(time, self.actual_load, color='g', label='load')
        axis[0, 0].set_title("Demand profiles")

        # For price
        axis[0, 1].plot(time, self.prices)
        axis[0, 1].set_title("prices")

        # battery state
        axis[1, 0].plot(time, self.battery_state)
        axis[1, 0].set_title("Battery State")

        # For costs
        axis[1, 1].plot(time, self.actual_cost)
        axis[1, 1].set_title("costs")

        # Combine all the operations and display
        plt.show()

    