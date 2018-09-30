from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np
import pysal
import matplotlib.pyplot as plt

class MiningPool(Agent):
    def __init__(self, unique_id, k, m, model):
        super().__init__(unique_id, model)
        r = np.random.uniform(0.7,1) 
        # This random number is used to create variability among mining pools' hash rates
        # And to set energy consumption of each mining pool as a consequence of its hash rate
        self.hashRatePerMachine = r * self.model.maxHashRatePerMachine * k
        self.maxHashRate = self.hashRatePerMachine * m # H/s
        self.k = k # Available multiplier of the hashRatePerMachine
        self.hashRate = self.maxHashRate # H/s Mining pool uses all its available hash rate in the beginning
        self.energyConsumption = r * self.model.energyConsumptionPerMachine * m # W        
        self.costPerKWh = np.random.uniform(0.05,0.20) # Euro/KWh
        self.energyPerHash = self.energyConsumption / self.maxHashRate # J/H        
        self.hashCost = self.energyPerHash * (self.costPerKWh / 3600000) # e.g. Euro/H
        self.reward = 0 # e.g. ETH
        self.cost = 0 # e.g. Euro
        self.profit = 0 # Euro
        self.expectedProfitPerBlock = 0 # Euro
        
    def start(self):
        self.hashRate = self.maxHashRate
        print("Mining pool " + str(self.unique_id) + ' start...\n')
        
    def stop(self):
        self.hashRate = 0
        print("Mining pool " + str(self.unique_id) + ' stop...\n')
                
    def computeExpectedProfitPerBlock(self):
        # If at least one mining pool is active
        if self.model.totalHashRate > 0:
            # If this mining pool is active
            if (self.hashRate > 0):
                expectedRewardPerBlock = self.maxHashRate/self.model.totalHashRate*self.model.reward*self.model.currencyValueWrtFiat
            # If this mining pool is not active
            else:
                expectedRewardPerBlock = self.maxHashRate/(self.model.totalHashRate + self.maxHashRate)*self.model.reward*self.model.currencyValueWrtFiat              
        # If no mining pool is active
        else:
            expectedRewardPerBlock = self.model.reward
        costPerBlock = self.maxHashRate * self.model.blockTime * self.hashCost 
        self.expectedProfitPerBlock =  expectedRewardPerBlock - costPerBlock
                     
    def step(self):    
        # Init or update expectedProfit
        self.computeExpectedProfitPerBlock()
        
        # Pay energy to compute hash
        self.cost += self.hashRate * self.model.blockTime * self.hashCost 
        
        # Compute profit
        self.profit = self.reward * self.model.currencyValueWrtFiat - self.cost

        # Here all data to selected a policy are computed
        print('mining pool:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward, ',cost:', self.cost, ',profit:', self.profit, ',expectedProfitPerBlock:', self.expectedProfitPerBlock, '\n')
        
        # Mining pools' policies are executed in a random order
        # Each mining pool select a policy taking into consideration policies selected by other mining pools before him 
        if (self.hashRate == 0 and self.expectedProfitPerBlock > 0):
            self.start()
        elif (self.hashRate > 0 and self.expectedProfitPerBlock <= 0):
            self.stop()                
        
class Network(Model):
    def __init__(self, superMiningPool, numMiningPools, averageNumMachinePerMiningPool, maxHashRatePerMachine, energyConsumptionPerMachine, initialReward, blockTime, initialCurrencyValueWrtFiat):
        self.numMiningPools = numMiningPools        
        self.averageNumMachinePerMiningPool = averageNumMachinePerMiningPool
        self.maxHashRatePerMachine = maxHashRatePerMachine
        self.energyConsumptionPerMachine = energyConsumptionPerMachine # W            
        self.reward = initialReward # e.g. ETH
        self.blockTime = blockTime # s
        self.currencyValueWrtFiat = initialCurrencyValueWrtFiat # e.g. Euro/ETH 
        self.totalHashRate = 0 # H/s
        self.decentralizationIndex = 0
        self.schedule = RandomActivation(self)
                
        # Add super mining pool to scheduler
        self.schedule.add(superMiningPool(self))
        
        # Create mining pools
        for i in range(1, self.numMiningPools):
            k = 1
            percentageDeviationFromAverageNumMachinePerMiningPool = 0.7
            m = np.random.uniform(self.averageNumMachinePerMiningPool * (1 - percentageDeviationFromAverageNumMachinePerMiningPool), self.averageNumMachinePerMiningPool * (1 + percentageDeviationFromAverageNumMachinePerMiningPool))           
            a = MiningPool(i, k, m, self)
            # Add other mining pools to scheduler
            self.schedule.add(a)
        
        # Init decentralization index
        self.computeDecentralizationIndex()

        # Init totalHashRate
        self.computeTotalHashRate()         
            
        # Declare data that have to be collected            
        self.datacollector = DataCollector( model_reporters={"decentralizationIndex": "decentralizationIndex"},
                                           agent_reporters={"reward": "reward", "hashRate":"hashRate"})
    
    def powPuzzle(self):
        if self.totalHashRate > 0:        
            # Compute probability to solve pow for each mining pool        
            probabilityToSolvePowForEachMiningPool = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
            # Select the winning mining pool        
            winningMiningPoolIndex = np.random.choice(self.numMiningPools, 1, p = probabilityToSolvePowForEachMiningPool)
            # Reward the winning mining pool        
            self.schedule.agents[winningMiningPoolIndex].reward += self.reward    
    
    def computeTotalHashRate(self):
         self.totalHashRate = sum(list(map(lambda a: a.hashRate, self.schedule.agents)))
        
    def computeDecentralizationIndex(self):             
        hashRates = list(map(lambda a: a.hashRate, self.schedule.agents))   
        # As a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRates is distributed equally among mining pools 
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print('### Decentralization index: ', self.decentralizationIndex, '\n')
        
#     def computeCurrencyValueWrtFiat(self): 
#         pass
                
    def step(self):
        # Network before powPuzzle                 
        self.datacollector.collect(self)
        self.powPuzzle()       
        self.schedule.step()
        # Network after powPuzzle, mining pools may have changed strategy
        # Update totalHashRate
        self.computeTotalHashRate()
        # Update decentralization index after streategies of mining pools may have changed               
        self.computeDecentralizationIndex()
        # self.computeCurrencyValueWrtFiat()

