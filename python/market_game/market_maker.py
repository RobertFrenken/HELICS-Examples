import helics as h
from dataclasses import dataclass,field
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
        
@dataclass
class SubFed:
    battery:Battery=field(default_factory=Battery)
    input:h.HelicsInput=None
    totalCost:float=0
    
    demand:list[float]=field(default_factory=lambda: [5] * 24)
    consume:list[float]=field(default_factory=list)
    name:str=""

def compute_new_price(total:float, feds:int)->float:
    M=total/feds
    if M<3.0:
        price=0.1
    elif M<6.0:
        price=0.1+0.03*(M-3.0)
    elif M<9.0:
        price=0.19+0.1*(M-6.0)
    elif M<13.0:
        price=0.49+0.25*(M-9.0)
    else:
        price=1.49+1.0*(M-13.0)
    return price

fedinfo = h.helicsCreateFederateInfo()
#depending on the setup this will need to be modified
h.helicsFederateInfoSetBroker(fedinfo,"localhost")

h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 1.0)

#set to whatever federate name you want
federate_name="market_maker_fed"
# create the federate using the federate Info structure


broker=h.helicsCreateBroker("zmq","market_maker","--ipv4 -f1")

market_maker=h.helicsCreateCombinationFederate(federate_name,fedinfo)

# register the price publication
price=market_maker.register_global_publication("price",h.HELICS_DATA_TYPE_DOUBLE,"$/kWh")

fedQuery=h.helicsCreateQuery("federation","federates")

while True:
    results=h.helicsQueryBrokerExecute(fedQuery,broker)
    index=0
    for fed in results:
        print(f"fed {index}:{fed}")
        index+=1
    res = input("enter i to start initialization: ")
    if res and res[0]=='i':
        break

# Now enter initializing mode iterative
h.helicsFederateEnterInitializingModeIterative(market_maker)

results=h.helicsQueryBrokerExecute(fedQuery,broker)
feds=[]
for fed in results:
    if fed==federate_name:
        continue
    print(f"fed {index}:{fed}")
    sf=SubFed(name=fed)
    sf.input=h.helicsFederateRegisterSubscription(market_maker,sf.name+"/demand","kWh")
    h.helicsFederateSendCommand(market_maker,sf.name,json.dumps({"demand":sf.demand}))
    feds.append(sf)

h.helicsFederateEnterInitializingMode(market_maker)
num_feds=len(feds)
current_price=0.5
price.publish(current_price)
h.helicsFederateEnterExecutingMode(market_maker)
current_time=0
while current_time<=24:
    total_load=0
    
    if current_time>0:
        hour=int(current_time)
        for fed in feds:
            load=h.helicsInputGetDouble(fed.input)
            if load>fed.demand[hour-1]+5:
                h.helicsFederateGlobalError(market_maker,120,f"federate {fed.name} listed demand exceeds limits")
            if load<fed.demand[hour-1]-5:
                h.helicsFederateGlobalError(market_maker,121,f"federate {fed.name} listed demand invalid")
            if fed.demand[hour-1]-load>fed.battery.current_charge():
                h.helicsFederateGlobalError(market_maker,122,f"federate {fed.name} insufficient battery energy")
            fed.battery.change(load-fed.demand[hour-1])
            fed.consume.append(load)
            print(f"hr {hour}: federate {fed.name} using {load} scheduled {fed.demand[hour-1]} battery at {fed.battery.energy} ")
        total_load+=load
    current_price=compute_new_price(total_load,num_feds)
    print(f"hr {hour}: total load {total_load} new  price = {current_price} ")
    price.publish(current_price)
    current_time=market_maker.request_next_step()
    
h.helicsFederateDisconnect(market_maker)

h.helicsBrokerDisconnect(broker)
