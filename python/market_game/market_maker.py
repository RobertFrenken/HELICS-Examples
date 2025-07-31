import helics as h
from dataclasses import dataclass
import json

# defining a house federate

@dataclass
class Battery:
    charge: float=0
    
    def current_charge(self)->float:
        return self.charge
    
    def discharge(self,delta:float)->float:
        """ discharge the battery by a given value
        assumed to be in 1 hour
        """
        delta=abs(delta)
        if delta>self.charge:
            raise ValueError("requested discharge exceeds current charge level")
        if delta>5.0:
            raise ValueError("requested discharge exceeds maximum discharge rate")
        self.charge-=delta
        return self.charge
    
    def charge(self,delta:float)->float:
        """ charge the battery by a given value
        assumed to be in 1 hour
        """
        delta=abs(delta)
        if self.charge+delta>20.0:
            raise ValueError("requested charge exceeds maximum capacity")
        if delta>5.0:
            raise ValueError("requested charge rate exceeds maximum rate")
        self.charge+=delta
        return self.charge
    
    def change(self, delta:float)->float:
        """ charge(positive value) or discharge(negative value) the battery by a given value
        assumed to be in 1 hour
        """
        if delta<0.0:
            return self.discharge(delta)
        else:
            return self.charge(delta)
        

fedinfo = h.helicsCreateFederateInfo()
#depending on the setup this will need to be modified
h.helicsFederateInfoSetBroker("localhost")

h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 1.0)

#set to whatever federate name you want
federate_name="market_maker_fed"
# create the federate using the federate Info structure


broker=h.helicsCreateBroker("zmq","market_maker","--ipv4 -f2")

market_maker=h.helicsCreateCombinationFederate(federate_name,fedinfo)

# register the subscription to the price
price=market_maker.register_global_publication("price",h.HELICS_DATA_TYPE_DOUBLE,"$/kWh")

# register the demand publication, setting it up as a local publication
