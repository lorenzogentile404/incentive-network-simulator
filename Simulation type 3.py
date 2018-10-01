from modelWithMultiplierAndNumberOfMachines import *

mBreakdown = [] 
kBreakdown = []


for k in range(1,50,2):
    m = 1000
    while True:
        # Run the simulation
        # https://etherscan.io/chart/hashrate
        # 28/09/2018 total hash rate of Ethereum is equal to 266 TH/s 
        targetTotalHashRate = 266e12 # H/s e.g. totat hash rate of Ethereum        
        numMiningPools = 10                    
        averageMaxHashRatePerMiningPool = targetTotalHashRate / numMiningPools # H/s Sum of the hash rates of all units of all machines of all mining pools
        
        technologicalMaximumHashRatePerUnit = 30e6 # H/s   
        energyConsumptionPerUnit = 140 # W  
        unitsPerMachine = 10
        energyConsumptionPerMachine = energyConsumptionPerUnit * unitsPerMachine
        maxHashRatePerMachine = technologicalMaximumHashRatePerUnit * unitsPerMachine # H/s each machine contains 'unitPerMachine' units with an hash rate of 'technologicalMaximumHashRatePerUnit'
        
        averageNumMachinePerMiningPool = averageMaxHashRatePerMiningPool / maxHashRatePerMachine

        initialReward = 3 # ETH
        blockTime = 15 # s
        initialCurrencyValueWrtFiat = 200 # Euro        
        steps = 10 # In the case of Ethereum each step is about 15 seconds, 172800 steps is about 1 month     
        #np.random.seed(1) # TODO Investigate why plots with seed equal to 1 and 2 have different shape for low k
        # superMiningPool parameters are changed in order to simulate different scenarios
        # note that a lambda is used because in order to initialize an agent its model is required
        superMiningPool = lambda model: MiningPool(0, k, m, model)
        network = Network(superMiningPool, numMiningPools, averageNumMachinePerMiningPool, maxHashRatePerMachine, energyConsumptionPerMachine, initialReward, blockTime, initialCurrencyValueWrtFiat)
        for i in range(steps):
            network.step()          
            if network.totalHashRate == 0:
                break
        if network.totalHashRate == 0:
            #print(str(k) + ' ' + str(m))
            kBreakdown.append(k)
            mBreakdown.append(m)
            break
        m += 1000
        
plt.title('No mining pool is active for m and k', y=1.08)
plt.xlabel('k')
plt.ylabel('m')
#plt.yscale('log')
plt.plot(kBreakdown, mBreakdown)
plt.savefig('plots/No mining pool is active for m and k', bbox_inches='tight')
plt.clf()   

