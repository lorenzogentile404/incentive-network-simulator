library(ineq)

hashRates <- c(1, 2, 3)

Gini(hashRates)
Herfindahl(hashRates)
# Gini and Herfindahl give almost the same result
# > Gini(hashRates)
# [1] 0.2222222
# > Herfindahl(hashRates)
# [1] 0.3888889

hashRates <- c(0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 1, 2, 3) # "centralized" network

Gini(hashRates)
Herfindahl(hashRates) 
# Herfindahl is not suitable to measure decentralization because 
# it does not take into consideration miners with low percentages
# of the total hashRate of the network
# > Gini(hashRates)
# [1] 0.8039746
# > Herfindahl(hashRates) 
# [1] 0.3877251

# Test for miners' policies (if dencetralizationIndex < 0.6 then network is centralized)
computeDecentralizationIndexOnOff <- function(hashRates){
  print(paste('global:',1-Gini(hashRates)))
  print(paste('others:',1-Gini(hashRates[-1])))
}

# Globally centralized, others decentralized -> on
computeDecentralizationIndexOnOff(c(10, 1, 1, 1))

# Globally centralized, others centralized -> off
computeDecentralizationIndexOnOff(c(1, 1, 10, 1))

# Globally decentralized, others centralized -> on
computeDecentralizationIndexOnOff(c(10, 2, 10, 1))


