from mesa import Agent, Model
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
import random
import numpy as np
import pysal
#import matplotlib.pyplot as plt

class Miner(Agent):
    def __init__(self, unique_id, maxHashRate, model):
        super().__init__(unique_id, model)
        self.maxHashRate = maxHashRate # H/s
        self.hashRate = maxHashRate # H/s Miner uses all its available hashRate in the beginning
        self.hashCost = 12e-13 # e.g. Euro/H
        self.reward = 0 # e.g. BTC
        self.cost = 0 # e.g. Euro
        self.profit = 0
        
    def getExpectedProfit(self):
        expectedReward = self.maxHashRate/self.model.totalHashRate*self.model.reward*self.model.currencyValueWrtFiat
        cost = self.maxHashRate * 10 * 60 * self.hashCost 
        return expectedReward - cost
        
    def start(self):
        #print("Miner ", self.unique_id, ' start.')
        self.hashRate = self.maxHashRate
        #input("Press Enter to continue...")
        
    def stop(self):
        #print("Miner ", self.unique_id, ' stop.')
        self.hashRate = 0
        #input("Press Enter to continue...")
              
    def step(self):
        # Pay energy to compute hash
        self.cost += self.hashRate * 10 * 60 * self.hashCost 
        # Compute profit
        self.profit = self.reward * self.model.currencyValueWrtFiat - self.cost
        print('miner:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward, ',cost:', self.cost, " ,profit:", self.profit)
        
        # TODO: implement here miner policies taking into consideration (reward, cost, decentralizationIndex,  self.model.currencyValueWrtFiat)
        if (self.hashRate == 0 and self.getExpectedProfit() > 0):
            self.start()
        elif (self.hashRate > 0 and (self.getExpectedProfit() < 0 or self.profit < 0)):
            self.stop()
        
        
class Network(Model):
    def __init__(self, numMiners, technologicalMaximumHashRate, initialReward, intialCurrencyValueWrtFiat):
        self.numMiners = numMiners        
        self.reward = initialReward # e.g. BTC
        self.currencyValueWrtFiat = intialCurrencyValueWrtFiat # e.g. Euro/BTC 
        self.totalHashRate = 0 # H/s
        self.decentralizationIndex = 0
        self.schedule = BaseScheduler(self)
        
        # Create miners
        for i in range(self.numMiners):
            maxHashRate = random.randrange(0, technologicalMaximumHashRate)
            # superMiner could have much more maxHashRate with respect to others
            #if i == 0:
            #    maxHashRate *= 50  
            # TODO randomize policies
            a = Miner(i, maxHashRate, self)
            self.schedule.add(a)
        
        # Init decentralization index
        self.computeDecentralizationIndex()

        # Init totalHashRate
        self.computeTotalHashRate()         
            
        # Declare data that have to be collected            
        self.datacollector = DataCollector(agent_reporters={"reward": "reward"})
    
    def powPuzzle(self):
        # Compute probability to solve pow for each miner        
        probabilityToSolvePowForEachMiner = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
        # Select the winning miner        
        winningMinerIndex = np.random.choice(self.numMiners, 1, p = probabilityToSolvePowForEachMiner)
        # Reward the winning miner        
        self.schedule.agents[winningMinerIndex].reward += self.reward
        
    def computeDecentralizationIndex(self):
        print('compute decentralizationIndex')
        hashRates = list(map(lambda a: a.hashRate, self.schedule.agents))
        # as a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRate is distributed equally among miners 
        # TODO find a better index
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print(self.decentralizationIndex)
 
    def computeCurrencyValueWrtFiat(self):    
        print('compute currencyValueWrtFiat')
        # TODO find a reasonable relationship
        self.currencyValueWrtFiat = self.currencyValueWrtFiat * (1 + (self.decentralizationIndex - 0.6)/4320)
        print(self.currencyValueWrtFiat)

    def computeTotalHashRate(self):
         self.totalHashRate = sum(list(map(lambda a: a.hashRate, self.schedule.agents)))
                
    def step(self):
        print('network before powPuzzle')               
        # TODO: update here the reward     
        self.datacollector.collect(self)
        self.powPuzzle()
        self.schedule.step()
        print('network after powPuzzle, miner may have changed strategy')
        # Update decentralization index after streategies of miners may have changed               
        self.computeDecentralizationIndex()       
        # Update totalHashRate
        self.computeTotalHashRate()
        # Update currency value with respect to fiat
        self.computeCurrencyValueWrtFiat()

# Run the simulation
numMiners = 10
technologicalMaximumHashRate = 20e6
initialReward = 12.5
intialCurrencyValueWrtFiat = 0.1
steps = 4320 # in the case of Bitcoin each step is about 10 minutes, 4320 steps is about 1 month     
random.seed(1) # set the random seed in order to make an experiment repeatable
network = Network(numMiners, technologicalMaximumHashRate, initialReward, intialCurrencyValueWrtFiat)
for i in range(steps):
    network.step()

# Plot data regarding miners using datacollector
minersRewards = network.datacollector.get_agent_vars_dataframe()
# Plot reward of each miner for each step
for i in range(numMiners):
    oneMinerReward = minersRewards.xs(i, level="AgentID").reward
    #oneMinerReward.plot()
    
# Plot reward of each miner at the end of the simulation
endMinersRewards = minersRewards.xs(steps - 1, level="Step")["reward"]
endMinersRewards.plot()


