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
    def __init__(self, numMiners, maxHashRate, initialReward):
        self.numMiners = numMiners
        self.schedule = BaseScheduler(self)
        self.totalHashRate = 0
        self.reward = initialReward
        self.decentralizationIndex = 0
        
        # Create miners
        for i in range(self.numMiners):
            hashRate = random.randrange(maxHashRate)
            # superMiner could have much more hashRate with respect to others
            #if i == 0:
            #    hashRate *= 10   
            self.totalHashRate += hashRate
            a = Miner(i, hashRate, self)
            self.schedule.add(a)
            
        # Declare data that have to be collected            
        self.datacollector = DataCollector(agent_reporters={"reward": "reward"})
    
    def powPuzzle(self):
        # Compute probability to solve pow for each miner        
        probabilityToSolvePowForEachMiner = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
        # Select the winning miner        
        winningMinerIndex = np.random.choice(self.numMiners, 1, p = probabilityToSolvePowForEachMiner)
        # Reward the winning miner        
        self.schedule.agents[winningMinerIndex].reward += self.reward
        
    def updateDecentralizationIndex(self):
        print('update decentralizationIndex')
        hashRates = list(map(lambda a: a.hashRate, network.schedule.agents))
        # as a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRate is distributed equally among miners 
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print(self.decentralizationIndex)         
                
    def step(self):
        print('network before powPuzzle')               
        # TODO: update here reward     
        self.datacollector.collect(self)
        self.powPuzzle()
        self.schedule.step()
        print('network after powPuzzle, miner may have changed strategy')              
        self.updateDecentralizationIndex()         

# Run the simulation
numMiners = 10
maxHashRate = 100
initialReward = 1
steps = 100     
network = Network(numMiners, maxHashRate, initialReward)
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

