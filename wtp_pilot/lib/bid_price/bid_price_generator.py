import random
import pandas as pd
import math

class BidCalculator:
    def __init__(self, price_range):
        self.price_range = price_range

    def V(self, x, t, delta_t, D_lambda, memo):
        price_min, price_max = self.price_range
        if x == 0 or t == 0:
            return 0
        
        if (x, t) in memo:
            return memo[(x, t)]
    
        max_value = float('-inf')
        for p in range(price_min, price_max): # lower bound of price: 100 and upper bound is 200
            probability_purchase = min(1, D_lambda * delta_t * self.WTP(p))
            term1 = probability_purchase * (p + self.V(x - 1, t - delta_t, delta_t, D_lambda, memo))
            term2 = (1 - probability_purchase) * self.V(x, t - delta_t, delta_t, D_lambda, memo)
            
            value = term1 + term2
            
            if value > max_value:
                max_value = value
    
        memo[(x, t)] = max_value
        return max_value
    
    def find_Vs(self, x, t, delta_t, memo):
        D_lambda = self.arrival_rate(t)
        self.V(x, t, delta_t, D_lambda, memo)
        return memo, D_lambda
    
    def b_star(self, x, t, delta_t, D_lambda, memo):
        if (x, t - delta_t) in memo and (x-1, t - delta_t) in memo:
            return memo[(x, t - delta_t)] - memo[(x - 1, t - delta_t)]
        else:
            return self.V(x, t-delta_t, delta_t, D_lambda, memo) - self.V(x-1, t-delta_t, delta_t, D_lambda, memo)
    
    def arrival_rate(self, t):
        ''' This is the arrival rate that should be the outcome of the forecast model.
            In general it is number of bookings per TCP
        '''
        return 0.34
    
    def WTP(self, p):
        '''Let's imagine for now WTP=1'''
        return 1
    
    def calculate_bid_prices(self, C, T):
        delta_t = 1 # IMPORTANT: For the sake of simulation we set the dt such that the probability of 2 arrivals are negligible
    
        values, D_lambda = self.find_Vs(C, T, delta_t, memo={})
        res = {}
        for s in range(1, C+1):
            for t in range(1, T+1):
                optimal_bids = self.b_star(s, t, delta_t, D_lambda, values)
                res[(s, t)] = optimal_bids
        return res


if __name__ == '__main__':
    bid_calculator = BidCalculator(price_range=(100, 400))
    res = bid_calculator.calculate_bid_prices(C = 30, T = 30)
    print(res)
