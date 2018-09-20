from mesa import Agent, Model
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
import random
import numpy as np
#import matplotlib.pyplot as plt

class Miner(Agent):
    def __init__(self, unique_id, hashRate, model):
        super().__init__(unique_id, model)
        self.hashRate = hashRate
        self.reward = 0

    def step(self):
        print('miner:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward)
        # TODO: implement here miner policies
        
class Network(Model):
    def __init__(self, numMiners, maxHashRate, initialReward):
        self.numMiners = numMiners
        self.schedule = BaseScheduler(self)
        self.totalHashRate = 0
        self.reward = initialReward
        
        # Create miners
        for i in range(self.numMiners):
            hashRate = random.randrange(100)
            self.totalHashRate += hashRate
            a = Miner(i, hashRate, self)
            self.schedule.add(a)
            
        # Declare data that have to be collected            
        self.datacollector = DataCollector(agent_reporters={"reward": "reward"})
        
    def step(self):
        print('network')
        # TODO: update here reward, difficulty        
        
        self.datacollector.collect(self)
        # Compute probability to solve pow for each miner        
        probabilityToSolvePowForEachMiner = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
        # Select the winning miner        
        winningMinerIndex = np.random.choice(self.numMiners, 1, p = probabilityToSolvePowForEachMiner)
        # Reward the winning miner        
        self.schedule.agents[winningMinerIndex].reward += self.reward     
        self.schedule.step()

# Run the simulation
numMiners = 10
maxHashRate = 100
initialReward = 1     
network = Network(numMiners, maxHashRate, initialReward)
for i in range(100):
    network.step()

# Plot data regarding miners using datacollector
minersRewards = network.datacollector.get_agent_vars_dataframe()
# Plot reward of each miner for each step
for i in range(10):
    oneMinerReward = minersRewards.xs(i, level="AgentID")
    #oneMinerReward.reward.plot()
    
# Plot reward of each miner at the end of the simulation
endMinersRewards = minersRewards.xs(99, level="Step")["reward"]
endMinersRewards.plot()


