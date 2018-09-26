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
        self.decentralizationIndexOtherMiners = 0
        
    def start(self):
        print("Miner ", self.unique_id, ' start.')
        self.hashRate = self.maxHashRate
        input("Press Enter to continue...\n")
        
    def stop(self):
        print("Miner ", self.unique_id, ' stop.')
        self.hashRate = 0
        input("Press Enter to continue...\n")
        
#    def computeDecentralizationIndexOtherMiners(self):
#        otherMiners = list(filter(lambda a: a.unique_id != self.unique_id and a.hashRate > 0, self.model.schedule.agents))
#        if len(otherMiners) > 0:
#            hashRates = list(map(lambda a: a.hashRate, otherMiners))
#            # as a decentralizationIndex 1 - gini indix is used
#            # the higher it is, the more the hashRate is distributed equally among miners 
#            self.decentralizationIndexOtherMiners = 1 - pysal.inequality.gini.Gini(hashRates).g
#            print(hashRates)            
#        else:
#            print('Miner ', self.unique_id,' is the only one.')
#            input("Press Enter to continue...")
              
    def step(self):
        # Init or update decentralization index other miners
        # Note that if this index is used step of the miners should be executed at the same time
        #self.computeDecentralizationIndexOtherMiners()  
        
        # Pay energy to compute hash
        self.cost += self.hashRate * 10 * 60 * self.hashCost 

        print('miner:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward, ',cost:', self.cost, '\n')
        
        # TODO: implement here miner policies taking into consideration decentralizationIndex        
        if (self.hashRate == 0 and self.model.decentralizationIndex >= 0.6):
            self.start()
        elif (self.hashRate > 0 and self.model.decentralizationIndex < 0.6):
            self.stop()
        
        
class Network(Model):
    def __init__(self, superMiner, numMiners, technologicalMaximumHashRate, initialReward):
        self.numMiners = numMiners        
        self.reward = initialReward # e.g. BTC
        self.totalHashRate = 0 # H/s
        self.decentralizationIndex = 0
        self.schedule = BaseScheduler(self)
                
        # Add super miner to scheduler
        self.schedule.add(superMiner(self))
        
        # Create miners
        for i in range(1, self.numMiners):
            maxHashRate = random.randrange(0, technologicalMaximumHashRate)
            a = Miner(i, maxHashRate, self)
            # Add other miners to scheduler
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
        activeMiners = list(filter(lambda a: a.hashRate > 0, self.schedule.agents))          
        hashRates = list(map(lambda a: a.hashRate, activeMiners))   
        # as a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRate is distributed equally among miners 
        # TODO find a better index
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print(self.decentralizationIndex)

    def computeTotalHashRate(self):
         self.totalHashRate = sum(list(map(lambda a: a.hashRate, self.schedule.agents)))
                
    def step(self):
        print('network before powPuzzle')               
        # TODO: update here the reward     
        self.datacollector.collect(self)
        self.powPuzzle()       
        self.schedule.step()
        print('network after powPuzzle, miner may have changed strategy')
        # Update totalHashRate
        self.computeTotalHashRate()
        # Update decentralization index after streategies of miners may have changed               
        self.computeDecentralizationIndex()       

# Run the simulation
numMiners = 10
technologicalMaximumHashRate = 20e6
initialReward = 12.5
steps = 2 #4320 # in the case of Bitcoin each step is about 10 minutes, 4320 steps is about 1 month     
random.seed(1) # set the random seed in order to make an experiment repeatable
k = 2 # hash rate multiplier available to super miner
# superMiner parameters are changed in order to simulate different scenarios
# note that a lambda is used because in order to initialize an agent its model is required
superMiner = lambda model: Miner(0, technologicalMaximumHashRate * k, model)
network = Network(superMiner, numMiners, technologicalMaximumHashRate, initialReward)
for i in range(steps):
    print('### Step ', i, '\n')
    network.step()
    if network.totalHashRate == 0:
        print('There is no more hash rate in the network.')
        break


