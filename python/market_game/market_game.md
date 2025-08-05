# Market game

The market game example is meant as a test case for a multi-user cosimulation.   It is meant more as a teaching tool than a real simulation, but is meant to be fun in a group.  The idea is that there are a number of houses in a neighborhood. they are all consuming power but have a battery which can charge or discharge depending on the price.  How much power is consumed affects the price in the next interval.   

## House specifications

Each house consumes power in a little different profile, but all consume the same amount of power during a given day.   This is measured in KWh. The total consumption of each house is 120KWh per day averaging 5 kWh per hour.  Each house also has a battery that can store 20kWh.   The battery starts out empty in a day.  The maximum charge rate of the battery is 5kWh/hr. The maximum discharge rate of the battery is 10kWh/hr.  The battery rate of charge/discharge can change to any level from 1 hour to the next with the limits.  The battery is 100% efficient in charge and discharge.

## Market maker

The Market maker federate is the controller.  It sets the price per KWh.   The price is a function of demand.   If demand is below `N*3 kW` the price is set at $0.10/kWh.  N is the number of houses connected. Above that the price rises for the next hour.  The market maker is pretty dumb so the price lags an hours.   The function for the price is a piecewise linear function.    A multiplier `M` is computed as `M=total demand/N`.  The price is a function of `M`.    M<3.0  price is $0.10 per kilowatt-hour.   Above that it begins to rise.   From `3.0<M<6.0` price = 0.1+0.03*(M-3).   From `6.0<M<9.0`  price=0.19+0.1*(M-6.0).  From `9.0<M<13.0`  price=0.49+0.25*(M-9.0).  For M>13.0, price is 1.49+1.0*(M-13.0).   

## The game

Each hour the market maker will send a price for the next hour, Each federate needs to compute how much power they want to consume and send it back to the market maker.  This will then be used to compute the price for the next hour and so on.    The game is whoever spends the least amount of money in the 24 hours and still powers their house.   

## The federates

The Market maker will publish a price each time step.   Each house federate subscribes to this price.  Each house federate publishes a consumption.  This continues for 24 steps representing each hour starting at midnight.  Each house is free to define the algorihthm or methods used to adjust the battery charging/discharging and modulate the demand used by the house as a function of price.   The federate also knows the load profile used by the house and the current state of charge of the battery.    

Given it is a game the market maker also generates the demand curves for each federate so it knows the demand curve and will be monitoring the state of charge of the battery for each federate to compute the score at the end of the game.   And ensure no one is cheating.   Penalty costs will be assessed if the returned load is invalid.  Which means it exceeds the battery charge/discharge rates or the available capacity.  The penalty is $10 per kWh exceeding the allowed battery specification.  
