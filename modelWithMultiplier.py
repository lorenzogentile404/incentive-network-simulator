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
        self.singleMachineHashRate = r * self.model.technologicalMaximumHashRate * k
        self.maxCumulativeHashRate = self.singleMachineHashRate * m # H/s
        self.k = k # Available multiplier of the singleMachineHashRate
        self.cumulativeHashRate = self.maxCumulativeHashRate # H/s Mining pool uses all its available hashRate in the beginning
        self.energyConsumption = r * 1400 * m # W         
        self.costPerKWh = np.random.uniform(0.05,0.20) # Euro/KWh
        self.energyPerHash = self.energyConsumption / self.maxCumulativeHashRate # J/H        
        self.hashCost = self.energyPerHash * (self.costPerKWh / 3600000) # e.g. Euro/H
        self.reward = 0 # e.g. ETH
        self.cost = 0 # e.g. Euro
        self.profit = 0 # Euro
        self.expectedProfitPerBlock = 0 # Euro
        
    def start(self):
        self.cumulativeHashRate = self.maxCumulativeHashRate
        print("Mining pool " + str(self.unique_id) + ' start...\n')
        
    def stop(self):
        self.cumulativeHashRate = 0
        print("Mining pool " + str(self.unique_id) + ' stop...\n')
                
    def computeExpectedProfitPerBlock(self):
        # If at least one mining pool is active
        if self.model.totalHashRate > 0:
            # If this mining pool is active
            if (self.cumulativeHashRate > 0):
                expectedRewardPerBlock = self.maxCumulativeHashRate/self.model.totalHashRate*self.model.reward*self.model.currencyValueWrtFiat
            # If this mining pool is not active
            else:
                expectedRewardPerBlock = self.maxCumulativeHashRate/(self.model.totalHashRate + self.maxCumulativeHashRate)*self.model.reward*self.model.currencyValueWrtFiat              
        # If no mining pool is active
        else:
            expectedRewardPerBlock = self.model.reward
        costPerBlock = self.maxCumulativeHashRate * 15 * self.hashCost 
        self.expectedProfitPerBlock =  expectedRewardPerBlock - costPerBlock
                     
    def step(self):    
        # Init or update expectedProfit
        self.computeExpectedProfitPerBlock()
        
        # Pay energy to compute hash
        self.cost += self.cumulativeHashRate * 15 * self.hashCost 
        
        # Compute profit
        self.profit = self.reward * self.model.currencyValueWrtFiat - self.cost

        # Here all data to selected a policy are computed
        print('mining pool:', self.unique_id, ',cumulativeHashRate:', self.cumulativeHashRate, ',reward:', self.reward, ',cost:', self.cost, ',profit:', self.profit, ',expectedProfitPerBlock:', self.expectedProfitPerBlock, '\n')
        
        # Mining pools' policies are executed in a random order
        # Each mining pool select a policy taking into consideration policies selected by other mining pools before him 
        if (self.cumulativeHashRate == 0 and self.expectedProfitPerBlock > 0):
            self.start()
        elif (self.cumulativeHashRate > 0 and self.expectedProfitPerBlock <= 0):
            self.stop()                
        
class Network(Model):
    def __init__(self, superMiningPool, numMiningPools, technologicalMaximumHashRate, initialReward, initialCurrencyValueWrtFiat):
        self.numMiningPools = numMiningPools
        self.technologicalMaximumHashRate = technologicalMaximumHashRate        
        self.reward = initialReward # e.g. ETH
        self.currencyValueWrtFiat = initialCurrencyValueWrtFiat # e.g. Euro/ETH 
        self.totalHashRate = 0 # H/s
        self.decentralizationIndex = 0
        self.schedule = RandomActivation(self)
                
        # Add super mining pool to scheduler
        self.schedule.add(superMiningPool(self))
        
        # Create mining pools
        for i in range(1, self.numMiningPools):            
            a = MiningPool(i, 1, np.random.uniform(45000, 135000), self)
            # Add other mining pools to scheduler
            self.schedule.add(a)
        
        # Init decentralization index
        self.computeDecentralizationIndex()

        # Init totalHashRate
        self.computeTotalHashRate()         
            
        # Declare data that have to be collected            
        self.datacollector = DataCollector( model_reporters={"decentralizationIndex": "decentralizationIndex"},
                                           agent_reporters={"reward": "reward", "cumulativeHashRate":"cumulativeHashRate"})
    
    def powPuzzle(self):
        if self.totalHashRate > 0:        
            # Compute probability to solve pow for each mining pool        
            probabilityToSolvePowForEachMiningPool = list(map(lambda a: a.cumulativeHashRate/self.totalHashRate, self.schedule.agents))
            # Select the winning mining pool        
            winningMiningPoolIndex = np.random.choice(self.numMiningPools, 1, p = probabilityToSolvePowForEachMiningPool)
            # Reward the winning mining pool        
            self.schedule.agents[winningMiningPoolIndex].reward += self.reward    
    
    def computeTotalHashRate(self):
         self.totalHashRate = sum(list(map(lambda a: a.cumulativeHashRate, self.schedule.agents)))
        
    def computeDecentralizationIndex(self):             
        cumulativeHashRates = list(map(lambda a: a.cumulativeHashRate, self.schedule.agents))   
        # As a decentralizationIndex 1 - gini indix is used
        # the higher it is, the more the cumulativeHashRates is distributed equally among mining pools 
        self.decentralizationIndex = 1 - pysal.inequality.gini.Gini(cumulativeHashRates).g
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
        # TODO Update currency value with respect to fiat
        # self.computeCurrencyValueWrtFiat()

# number of machines super mining pool could decide to use
for m in (100, 1000, 10000, 100000, 1000000):
    # hash rate multiplier available to super mining pool
    for k in (1, 10, 100, 1000):
        # Run the simulation
        # https://etherscan.io/chart/hashrate
        # 28/09/2018 totalHashRate = 266 TH/s 
        # if 10 mining pools, 26.6 TH/s in average each
        # if technologicalMaximumHashRate = 300 MH/s
        # numMachines in average is 90000
        numMiningPools = 10
        technologicalMaximumHashRate = 300e6 # 30 MH/s per 10 units
        initialReward = 3 # ETH
        initialCurrencyValueWrtFiat = 200 # Euro
        steps = 10 #172800 # in the case of Ethereum each step is about 15 seconds, 172800 steps is about 1 month     
        np.random.seed(1) # set the random seed in order to make an experiment repeatable
        # superMiningPool parameters are changed in order to simulate different scenarios
        # note that a lambda is used because in order to initialize an agent its model is required
        superMiningPool = lambda model: MiningPool(0, k, m, model)
        network = Network(superMiningPool, numMiningPools, technologicalMaximumHashRate, initialReward, initialCurrencyValueWrtFiat)
        for i in range(steps):
            print('Step ' + str(i) + '...\n')
            network.step()
            # Print active mining pools
            print('Active mining pools: ', str(list(map(lambda a: a.unique_id, list(filter(lambda a: a.cumulativeHashRate > 0, network.schedule.agents))))))
            if network.totalHashRate == 0:
                print('There is no more hash rate in the network.')
        
        # Plot hash rates by step and mining pool
        miningPoolsInfo = network.datacollector.get_agent_vars_dataframe()
        ind = np.arange(steps) # The x locations for the groups
        width = 0.35 # The width of the bars: can also be len(x) sequence
        bottom = () # Useful to stake bars
        p = [0] * numMiningPools # Useful to create legend
        
        plt.title('Cumulative hash rates by step and mining pool, m = ' + str(m) + ', k = ' + str(k))
        plt.xlabel('Step')
        plt.ylabel('Cumulative hash rates')
        plt.xticks(ind, np.asarray(list(map(lambda e: str(e), ind))))
        
        for i in range(numMiningPools):
            oneMiningPoolCumulativeHashRate = miningPoolsInfo.xs(i, level="AgentID").cumulativeHashRate
            if (i == 0):      
                bottom = np.array(oneMiningPoolCumulativeHashRate)
                p[i] = plt.bar(ind, oneMiningPoolCumulativeHashRate, width, color=str(i/numMiningPools))
            else:
                p[i] = plt.bar(ind, oneMiningPoolCumulativeHashRate, width, color=str(i/numMiningPools), bottom=bottom)
                bottom += np.array(oneMiningPoolCumulativeHashRate)
        
        plt.legend(np.asarray(list(map(lambda el: el[0], p))),np.asarray(list(map(lambda e: 'Mining pool ' +  str(e), ind))),bbox_to_anchor=(1.4, 0.8))
                   
        plt.savefig('plots/Cumulative hash rates by step and mining pool, m = ' + str(m) + ', k = ' + str(k),bbox_inches='tight')
        plt.clf()           
                   
        # Plot reward per mining pool at simulation\'s end
        eachMiningPoolRewardEndSimulation = miningPoolsInfo.xs(steps - 1, level="Step")["reward"]
        plt.title('Reward per mining pool at simulation\'s end, m = ' + str(m) + ', k = ' + str(k))
        plt.xlabel('Mining pool')
        plt.ylabel('Reward')
        plt.plot(eachMiningPoolRewardEndSimulation)
        
        plt.savefig('plots/Reward per mining pool at simulation\'s end, m = ' + str(m) + ', k = ' + str(k))
        plt.clf()   
        
        # Plot decentralizationIndex per step
        networkInfo = network.datacollector.get_model_vars_dataframe()
        decentralizationIndexPerStep = networkInfo.decentralizationIndex
        plt.title('decentralizationIndex per step, m = ' + str(m) + ', k = ' + str(k))
        plt.xlabel('Step')
        plt.ylabel('decentralizationIndex')
        plt.ylim(0,1)
        plt.plot(decentralizationIndexPerStep)
        
        plt.savefig('plots/decentralizationIndex per step, m = ' + str(m) + ', k = ' + str(k))
        plt.clf()   
        
        # Plot number of active mining pools per step
        numActiveMiningPoolsPerStep = list(map(lambda step: sum(miningPoolsInfo.xs(step, level="Step")["cumulativeHashRate"] > 0), range(0, steps)))
        plt.title('Number active mining pools per step, m = ' + str(m) + ', k = ' + str(k))
        plt.xlabel('Step')
        plt.ylabel('Number of active mining pools')
        plt.ylim(0,numMiningPools)
        plt.plot(numActiveMiningPoolsPerStep)
        
        plt.savefig('plots/Number active mining pools per step, m = ' + str(m) + ', k = ' + str(k))
        plt.clf()   


