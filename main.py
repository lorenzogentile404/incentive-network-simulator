from mesa import Agent, Model
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
import random
import numpy as np
import pysal
#import matplotlib.pyplot as plt

class Miner(Agent):
    def __init__(self, unique_id, hashRate, model):
        super().__init__(unique_id, model)
        self.hashRate = hashRate # H/s
        self.hashCost = 1 # e.g. Euro/H
        self.reward = 0 # e.g. BTC
        self.cost = 0 # e.g. Euro       

    def step(self):
        # Pay energy to compute hash
        self.cost += self.hashRate * 10 * 60 * self.hashCost        
        print('miner:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward, ',cost:', self.cost)
        # TODO: implement here miner policies taking into consideration (reward, cost, decentralizationIndex)
        
class Network(Model):
    def __init__(self, numMiners, maxHashRatePerMiner, initialReward, intialCurrencyValueWrtFiat):
        self.numMiners = numMiners        
        self.reward = initialReward # e.g. BTC
        self.currencyValueWrtFiat = intialCurrencyValueWrtFiat # e.g. Euro        
        self.totalHashRate = 0 # H/s
        self.decentralizationIndex = 0
        self.schedule = BaseScheduler(self)
        
        # Create miners
        for i in range(self.numMiners):
            hashRate = random.randrange(maxHashRatePerMiner)
            # superMiner could have much more hashRate with respect to others
            #if i == 0:
            #    hashRate *= 1   
            self.totalHashRate += hashRate
            a = Miner(i, hashRate, self)
            self.schedule.add(a)
        
        # Init decentralization index
        self.computeDecentralizationIndex()         
            
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
        print('update decentralizationIndex')
        hashRates = list(map(lambda a: a.hashRate, network.schedule.agents))
        # as a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRate is distributed equally among miners 
        # TODO find a better index
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print(self.decentralizationIndex)
 
    def computeCurrencyValueWrtFiat(self):    
        print('update currencyValueWrtFiat')
        # TODO find a reasonable relationship
        self.currencyValueWrtFiat = self.currencyValueWrtFiat * (1 + (self.decentralizationIndex - 0.6)/4320)
        print(self.currencyValueWrtFiat)        
                
    def step(self):
        print('network before powPuzzle')               
        # TODO: update here the reward     
        self.datacollector.collect(self)
        self.powPuzzle()
        self.schedule.step()
        print('network after powPuzzle, miner may have changed strategy')
        # Update decentralization index after streategies of miners may have changed               
        self.computeDecentralizationIndex()       
        # Update currency value with respect to fiat
        self.computeCurrencyValueWrtFiat()

# Run the simulation
numMiners = 10
maxHashRatePerMiner = 100
initialReward = 1
intialCurrencyValueWrtFiat = 1
steps = 4320 # in the case of Bitcoin each step is about 10 minutes, 4320 steps is about 1 month     
network = Network(numMiners, maxHashRatePerMiner, initialReward, intialCurrencyValueWrtFiat)
for i in range(steps):
    network.step()

# Plot data regarding miners using datacollector
minersRewards = network.datacollector.get_agent_vars_dataframe()
# Plot reward of each miner for each step
for i in range(numMiners):
    oneMinerReward = minersRewards.xs(i, level="AgentID")
    #oneMinerReward.reward.plot()
    
# Plot reward of each miner at the end of the simulation
endMinersRewards = minersRewards.xs(steps - 1, level="Step")["reward"]
endMinersRewards.plot()

