from modelWithMultiplierAndNumberOfMachines import *

# number of machines super mining pool could decide to use (100, 1000, 10000, 100000, 1000000)
for m in (100, 1000, 10000, 100000, 1000000):
    # hash rate multiplier available to super mining pool (1, 10, 100, 1000)
    for k in (1, 10, 100, 1000):
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
        np.random.seed(1) # Set the random seed in order to make an experiment repeatable
        # superMiningPool parameters are changed in order to simulate different scenarios
        # note that a lambda is used because in order to initialize an agent its model is required
        superMiningPool = lambda model: MiningPool(0, k, m, model)
        network = Network(superMiningPool, numMiningPools, averageNumMachinePerMiningPool, maxHashRatePerMachine, energyConsumptionPerMachine, initialReward, blockTime, initialCurrencyValueWrtFiat)
        for i in range(steps):
            print('Step ' + str(i) + '...\n')
            network.step()
            # Print active mining pools
            print('Active mining pools: ', str(list(map(lambda a: a.unique_id, list(filter(lambda a: a.hashRate > 0, network.schedule.agents))))))
            if network.totalHashRate == 0:
                print('There is no more hash rate in the network.')
        
        # Plot hash rates by step and mining pool
        miningPoolsInfo = network.datacollector.get_agent_vars_dataframe()
        ind = np.arange(steps) # The x locations for the groups
        width = 0.35 # The width of the bars: can also be len(x) sequence
        bottom = () # Useful to stake bars
        p = [0] * numMiningPools # Useful to create legend
        
        plt.title('Hash rates by step and mining pool, m = ' + str(m) + ', k = ' + str(k), y=1.08)
        plt.xlabel('Step')
        plt.ylabel('Hash rates')
        plt.xticks(ind, np.asarray(list(map(lambda e: str(e), ind))))
        
        for i in range(numMiningPools):
            oneMiningPoolHashRate = miningPoolsInfo.xs(i, level="AgentID").hashRate
            if (i == 0):      
                bottom = np.array(oneMiningPoolHashRate)
                p[i] = plt.bar(ind, oneMiningPoolHashRate, width, color=str(i/numMiningPools))
            else:
                p[i] = plt.bar(ind, oneMiningPoolHashRate, width, color=str(i/numMiningPools), bottom=bottom)
                bottom += np.array(oneMiningPoolHashRate)
        
        plt.legend(np.asarray(list(map(lambda el: el[0], p))),np.asarray(list(map(lambda e: 'Mining pool ' +  str(e), ind))),bbox_to_anchor=(1.4, 0.8))
                   
        plt.savefig('plots/Hash rates by step and mining pool, m = ' + str(m) + ', k = ' + str(k),bbox_inches='tight')
        plt.clf()           
                   
        # Plot reward per mining pool at simulation\'s end
        eachMiningPoolRewardEndSimulation = miningPoolsInfo.xs(steps - 1, level="Step")["reward"]
        plt.title('Reward per mining pool at simulation\'s end, m = ' + str(m) + ', k = ' + str(k), y=1.08)
        plt.xlabel('Mining pool')
        plt.ylabel('Reward')
        plt.plot(eachMiningPoolRewardEndSimulation)
        
        plt.savefig('plots/Reward per mining pool at simulation\'s end, m = ' + str(m) + ', k = ' + str(k), bbox_inches='tight')
        plt.clf()   
        
        # Plot decentralizationIndex per step
        networkInfo = network.datacollector.get_model_vars_dataframe()
        decentralizationIndexPerStep = networkInfo.decentralizationIndex
        plt.title('decentralizationIndex per step, m = ' + str(m) + ', k = ' + str(k), y=1.08)
        plt.xlabel('Step')
        plt.ylabel('decentralizationIndex')
        plt.ylim(0,1)
        plt.plot(decentralizationIndexPerStep)
        
        plt.savefig('plots/decentralizationIndex per step, m = ' + str(m) + ', k = ' + str(k), bbox_inches='tight')
        plt.clf()   
        
        # Plot number of active mining pools per step
        numActiveMiningPoolsPerStep = list(map(lambda step: sum(miningPoolsInfo.xs(step, level="Step")["hashRate"] > 0), range(0, steps)))
        plt.title('Number active mining pools per step, m = ' + str(m) + ', k = ' + str(k), y=1.08)
        plt.xlabel('Step')
        plt.ylabel('Number of active mining pools')
        plt.ylim(0,numMiningPools)
        plt.plot(numActiveMiningPoolsPerStep)
        
        plt.savefig('plots/Number active mining pools per step, m = ' + str(m) + ', k = ' + str(k), bbox_inches='tight')
        plt.clf()   


