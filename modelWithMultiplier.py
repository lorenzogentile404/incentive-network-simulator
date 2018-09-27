from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import random
import numpy as np
import pysal
#import matplotlib.pyplot as plt

class Miner(Agent):
    def __init__(self, unique_id, technologicalMaximumHashRate, model):
        super().__init__(unique_id, model)
        r = np.random.uniform(0.7,1) 
        # This random number is used to create variability among miners' hash rates
        # And to set energy consumption of each miner as a consequence of its hash rate
        self.maxHashRate = r * technologicalMaximumHashRate # H/s
        self.hashRate = self.maxHashRate # H/s Miner uses all its available hashRate in the beginning
        self.energyConsumption = r * 140 # W         
        self.costPerKWh = np.random.uniform(0.05,0.20) # Euro/KWh               
        self.energyPerHash = self.energyConsumption / self.maxHashRate # J/H        
        self.hashCost = self.energyPerHash * (self.costPerKWh / 3600000) # e.g. Euro/H
        self.reward = 0 # e.g. BTC
        self.cost = 0 # e.g. Euro
        # DecentralizationIndexOn is the decentralizationIndex of the network
        # if this miner is on. In case this miner is already on, then it is equal to 
        # decentralizationIndex
        self.decentralizationIndexOn = 0
        # DecentralizationIndexOff is the decentralizationIndex of the network
        # if this miner is off. In case this miner is already off, then it is equal to 
        # decentralizationIndex
        self.decentralizationIndexOff = 0
        
    def start(self):
        self.hashRate = self.maxHashRate
        input("Miner " + str(self.unique_id) + ' start...\n')
        
    def stop(self):
        self.hashRate = 0
        input("Miner " + str(self.unique_id) + ' stop...\n')
        
    def computeDecentralizationIndexOnOff(self):
        otherMiners = list(filter(lambda a: a.unique_id != self.unique_id and a.hashRate > 0, self.model.schedule.agents))
        if len(otherMiners) > 0:
            hashRatesOff = list(map(lambda a: a.hashRate, otherMiners))
            self.decentralizationIndexOff = 1 - pysal.inequality.gini.Gini(hashRatesOff).g 
                   
            hashRatesOn = hashRatesOff + [self.maxHashRate]
            self.decentralizationIndexOn = 1 - pysal.inequality.gini.Gini(hashRatesOn).g              
        else:
            input('Miner ' + str(self.unique_id) + ' is the only one...\n')
              
    def step(self):
        # Init or update decentralization index other miners
        self.computeDecentralizationIndexOnOff()  
        
        # Pay energy to compute hash
        self.cost += self.hashRate * 10 * 60 * self.hashCost 

        # Here all data to selected a policy are computed
        print('miner:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward, ',cost:', self.cost, ',decentralizationIndexOn:',  self.decentralizationIndexOn, ',decentralizationIndexOff:',  self.decentralizationIndexOff,'\n')
                
    def advance(self):
        # Miners' policies are executed "at the same time"
        # Each miner does not selected a policy taking into consideration the policies selected by others
        if (self.hashRate == 0 and self.decentralizationIndexOn >= 0.6):
            self.start()
        elif (self.hashRate > 0 and (self.model.decentralizationIndex < 0.6 and self.decentralizationIndexOff < 0.6 or len(list(filter(lambda a: a.unique_id != self.unique_id and a.hashRate > 0, self.model.schedule.agents))) == 0)):
            self.stop()
        
class Network(Model):
    def __init__(self, superMiner, numMiners, technologicalMaximumHashRate, initialReward):
        self.numMiners = numMiners        
        self.reward = initialReward # e.g. BTC
        self.totalHashRate = 0 # H/s
        self.decentralizationIndex = 0
        self.schedule = SimultaneousActivation(self)
                
        # Add super miner to scheduler
        self.schedule.add(superMiner(self))
        
        # Create miners
        for i in range(1, self.numMiners):            
            a = Miner(i, technologicalMaximumHashRate, self)
            # Add other miners to scheduler
            self.schedule.add(a)
        
        # Init decentralization index
        self.computeDecentralizationIndex()

        # Init totalHashRate
        self.computeTotalHashRate()         
            
        # Declare data that have to be collected            
        self.datacollector = DataCollector(agent_reporters={"reward": "reward", "hashRate":"hashRate"})
    
    def powPuzzle(self):
        # Compute probability to solve pow for each miner        
        probabilityToSolvePowForEachMiner = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
        # Select the winning miner        
        winningMinerIndex = np.random.choice(self.numMiners, 1, p = probabilityToSolvePowForEachMiner)
        # Reward the winning miner        
        self.schedule.agents[winningMinerIndex].reward += self.reward
        
    def computeDecentralizationIndex(self):    
        activeMiners = list(filter(lambda a: a.hashRate > 0, self.schedule.agents))          
        hashRates = list(map(lambda a: a.hashRate, activeMiners))   
        # As a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRate is distributed equally among miners 
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print('### Decentralization index: ', self.decentralizationIndex, '\n')

    def computeTotalHashRate(self):
         self.totalHashRate = sum(list(map(lambda a: a.hashRate, self.schedule.agents)))
                
    def step(self):
        # Network before powPuzzle                 
        self.datacollector.collect(self)
        self.powPuzzle()       
        self.schedule.step()
        # Network after powPuzzle, miner may have changed strategy
        # Update totalHashRate
        self.computeTotalHashRate()
        # Update decentralization index after streategies of miners may have changed               
        self.computeDecentralizationIndex()       

# Run the simulation
numMiners = 10
technologicalMaximumHashRate = 20e6
initialReward = 12.5
steps = 10 #4320 # in the case of Bitcoin each step is about 10 minutes, 4320 steps is about 1 month     
random.seed(1) # set the random seed in order to make an experiment repeatable
k = 10 # hash rate multiplier available to super miner
# superMiner parameters are changed in order to simulate different scenarios
# note that a lambda is used because in order to initialize an agent its model is required
superMiner = lambda model: Miner(0, technologicalMaximumHashRate * k, model)
network = Network(superMiner, numMiners, technologicalMaximumHashRate, initialReward)
for i in range(steps):
    input('Step ' + str(i) + '...\n')
    network.step()
    # Print active miners
    print('Active miners: ', str(list(map(lambda a: a.unique_id, list(filter(lambda a: a.hashRate > 0, network.schedule.agents))))))
    if network.totalHashRate == 0:
        print('There is no more hash rate in the network.')
        break

# Plot data regarding miners using datacollector
minersHashRates = network.datacollector.get_agent_vars_dataframe()
# Plot hashRate of each miner for each step
for i in range(numMiners):
    oneMinerHashRate = minersHashRates.xs(i, level="AgentID")
    oneMinerHashRate.hashRate.plot()

