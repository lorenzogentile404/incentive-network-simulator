from mesa import Agent, Model
from mesa.time import BaseScheduler
import random
import numpy as np
#import matplotlib.pyplot as plt

class Miner(Agent):
    def __init__(self, unique_id, hashRate, model):
        super().__init__(unique_id, model)
        self.hashRate = hashRate
        self.reward = 0

    def step(self):
        print('miner:', self.unique_id, ', hashRate:', self.hashRate, ' reward:', self.reward)

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

    def step(self):
        print('network')
        # print(list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents)))
        probabilityToSolvePowForEachMiner = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
        winningMinerIndex = np.random.choice(self.numMiners, 1, p = probabilityToSolvePowForEachMiner)
        self.schedule.agents[winningMinerIndex].reward += self.reward     
        self.schedule.step()

numMiners = 10
maxHashRate = 100
initialReward = 1     
network = Network(numMiners, maxHashRate, initialReward)
for i in range(100):
    network.step()


