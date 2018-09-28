from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import numpy as np
import pysal
import matplotlib.pyplot as plt

class Miner(Agent):
    def __init__(self, unique_id, technologicalMaximumHashRate, model):
        super().__init__(unique_id, model)
        r = np.random.uniform(0.7,1) 
        # This random number is used to create variability among miners' hash rates
        # And to set energy consumption of each miner as a consequence of its hash rate
        self.maxHashRate = r * technologicalMaximumHashRate # H/s
        self.hashRate = self.maxHashRate # H/s Miner uses all its available hashRate in the beginning
        self.energyConsumption = r * 140 # W         
        self.costPerKWh = np.random.uniform(0.05,0.20*10) # Euro/KWh TODO remove * 10, it has been added for testing purposes          
        self.energyPerHash = self.energyConsumption / self.maxHashRate # J/H        
        self.hashCost = self.energyPerHash * (self.costPerKWh / 3600000) # e.g. Euro/H
        self.reward = 0 # e.g. ETH
        self.cost = 0 # e.g. Euro
        self.profit = 0 # Euro
        self.expectedProfitPerBlock = 0 # Euro
        
    def start(self):
        self.hashRate = self.maxHashRate
        print("Miner " + str(self.unique_id) + ' start...\n')
        
    def stop(self):
        self.hashRate = 0
        print("Miner " + str(self.unique_id) + ' stop...\n')
            
    def computeExpectedProfitPerBlock(self):
        if self.model.totalHashRate > 0:
            expectedRewardPerBlock = self.maxHashRate/self.model.totalHashRate*self.model.reward*self.model.currencyValueWrtFiat
        else:
            expectedRewardPerBlock = self.model.reward
        costPerBlock = self.maxHashRate * 10 * 60 * self.hashCost 
        self.expectedProfitPerBlock =  expectedRewardPerBlock - costPerBlock
                     
    def step(self):    
        # Init or update expectedProfit
        self.computeExpectedProfitPerBlock()
        
        # Pay energy to compute hash
        self.cost += self.hashRate * 10 * 60 * self.hashCost 
        
        # Compute profit
        self.profit = self.reward * self.model.currencyValueWrtFiat - self.cost

        # Here all data to selected a policy are computed
        print('miner:', self.unique_id, ',hashRate:', self.hashRate, ',reward:', self.reward, ',cost:', self.cost, ',profit:', self.profit, ',expectedProfitPerBlock:', self.expectedProfitPerBlock, '\n')
                
    def advance(self):
        # Miners' policies are executed "at the same time"
        # Each miner does not selected a policy taking into consideration the policies selected by others
        if (self.hashRate == 0 and self.expectedProfitPerBlock > 0):
            self.start()
        elif (self.hashRate > 0 and (self.expectedProfitPerBlock <= 0 or len(list(filter(lambda a: a.unique_id != self.unique_id and a.hashRate > 0, self.model.schedule.agents))) == 0)):
            self.stop()
        
class Network(Model):
    def __init__(self, superMiner, numMiners, technologicalMaximumHashRate, initialReward, initialCurrencyValueWrtFiat):
        self.numMiners = numMiners        
        self.reward = initialReward # e.g. ETH
        self.currencyValueWrtFiat = initialCurrencyValueWrtFiat # e.g. Euro/ETH 
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
        if self.totalHashRate > 0:        
            # Compute probability to solve pow for each miner        
            probabilityToSolvePowForEachMiner = list(map(lambda a: a.hashRate/self.totalHashRate, self.schedule.agents))
            # Select the winning miner        
            winningMinerIndex = np.random.choice(self.numMiners, 1, p = probabilityToSolvePowForEachMiner)
            # Reward the winning miner        
            self.schedule.agents[winningMinerIndex].reward += self.reward    
    
    def computeTotalHashRate(self):
         self.totalHashRate = sum(list(map(lambda a: a.hashRate, self.schedule.agents)))
        
    def computeDecentralizationIndex(self):    
        activeMiners = list(filter(lambda a: a.hashRate > 0, self.schedule.agents))          
        hashRates = list(map(lambda a: a.hashRate, activeMiners))   
        # As a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the hashRate is distributed equally among miners 
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(hashRates).g
        print('### Decentralization index: ', self.decentralizationIndex, '\n')
        
#     def computeCurrencyValueWrtFiat(self): 
#         pass
                
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
        # TODO Update currency value with respect to fiat
        # self.computeCurrencyValueWrtFiat()

        

# Run the simulation
# https://etherscan.io/chart/hashrate
# 28/09/2018 totalHashRate = 266 GH/s
numMiners = 10
technologicalMaximumHashRate = 20e6
initialReward = 3 # ETH
initialCurrencyValueWrtFiat = 0.1 # Euro
steps = 10 #172800 # in the case of Ethereum each step is about 15 seconds, 172800 steps is about 1 month     
np.random.seed(1) # set the random seed in order to make an experiment repeatable
k = 70 # hash rate multiplier available to super miner (20, 59, 60. 70)
# superMiner parameters are changed in order to simulate different scenarios
# note that a lambda is used because in order to initialize an agent its model is required
superMiner = lambda model: Miner(0, technologicalMaximumHashRate * k, model)
network = Network(superMiner, numMiners, technologicalMaximumHashRate, initialReward, initialCurrencyValueWrtFiat)
for i in range(steps):
    print('Step ' + str(i) + '...\n')
    network.step()
    # Print active miners
    print('Active miners: ', str(list(map(lambda a: a.unique_id, list(filter(lambda a: a.hashRate > 0, network.schedule.agents))))))
    if network.totalHashRate == 0:
        print('There is no more hash rate in the network.')



# Plot data regarding miners using datacollector
minersHashRates = network.datacollector.get_agent_vars_dataframe()

ind = np.arange(steps) # The x locations for the groups
width = 0.35 # The width of the bars: can also be len(x) sequence
bottom = () # Useful to stake bars
p = [0] * numMiners # Useful to create legend

plt.ylabel('Hash rates')
plt.title('Hash rates by step and miner')
plt.xticks(ind, np.asarray(list(map(lambda e: str(e), ind))))

# Plot hashRate of each miner for each step
for i in range(numMiners):
    oneMinerHashRate = minersHashRates.xs(i, level="AgentID").hashRate
    if (i == 0):      
        bottom = np.array(oneMinerHashRate)
        p[i] = plt.bar(ind, oneMinerHashRate, width, color=str(i/numMiners))
    else:
        p[i] = plt.bar(ind, oneMinerHashRate, width, color=str(i/numMiners), bottom=bottom)
        bottom += np.array(oneMinerHashRate)

plt.legend(np.asarray(list(map(lambda el: el[0], p))),np.asarray(list(map(lambda e: 'Min. ' +  str(e), ind))),bbox_to_anchor=(1.125, 0.8))
            
# Plot hashRate of each miner at the end of the simulation
# for i in range(steps):
#    oneStepMinersHashRates = minersHashRates.xs(i, level="Step")["hashRate"]
#    plt.pie(oneStepMinersHashRates)


