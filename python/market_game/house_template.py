import helics as h
from dataclasses import dataclass
import json

# defining a house federate

@dataclass
class Battery:
    energy: float=0
    
    def current_charge(self)->float:
        return self.energy
    
    def discharge(self,delta:float)->float:
        """ discharge the battery by a given value
        assumed to be in 1 hour
        """
        delta=abs(delta)
        if delta>self.energy:
            raise ValueError("requested discharge exceeds current charge level")
        if delta>5.0:
            raise ValueError("requested discharge exceeds maximum discharge rate")
        self.energy-=delta
        return self.energy
    
    def charge(self,delta:float)->float:
        """ charge the battery by a given value
        assumed to be in 1 hour
        """
        delta=abs(delta)
        if self.energy+delta>20.0:
            raise ValueError("requested charge exceeds maximum capacity")
        if delta>5.0:
            raise ValueError("requested charge rate exceeds maximum rate")
        self.energy+=delta
        return self.energy
    
    def change(self, delta:float)->float:
        """ charge(positive value) or discharge(negative value) the battery by a given value
        assumed to be in 1 hour
        """
        if delta<0.0:
            return self.discharge(delta)
        else:
            return self.charge(delta)
        

def compute_demand(price:float, hour:int, battery_charge:float, demand:list[float])->float:
    #this is where you get to do something interesting
    
    #the least interesting thing is just return the current demand
    return demand[hour]


fedinfo = h.helicsCreateFederateInfo()
#depending on the setup this will need to be modified
h.helicsFederateInfoSetBroker(fedinfo, "localhost")

h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 1.0)

#set to whatever federate name you want
federate_name="XXXXX"
# create the federate using the federate Info structure
fed=h.helicsCreateCombinationFederate(federate_name,fedinfo)

# register the subscription to the price
price=fed.register_subscription("price","$/kWh")

# register the demand publication, setting it up as a local publication
demand=fed.register_publication("demand","float","kWh")
#enter initializing mode
fed.enter_initializing_mode()

# get a demand profile,   this comes from the market maker it will come in json format using the command interface
print("getting the demand profile")
demand_profile_json=h.helicsFederateWaitCommand(fed)

demand_profile=json.loads(demand_profile_json)["demand"]
print(f"got demand profile={demand_profile}, type={str(type(demand_profile))} length={len(demand_profile)}")
#initialize the battery
battery=Battery()
fed.enter_executing_mode()
current_time=0

while current_time<24:
    current_price=h.helicsInputGetDouble(price)
    current_demand=demand_profile[int(current_time)]
    computed_demand=compute_demand(current_price,int(current_time),battery.current_charge(),demand_profile)
    battery.change(computed_demand-current_demand)
    print(f"hour {current_time}:price={current_price}, house_demand={current_demand}, load={computed_demand}, battery delta= {computed_demand-current_demand} batter charge={battery.current_charge}")
    demand.publish(computed_demand)
    current_time=fed.request_next_step()
    
fed.disconnect()
    