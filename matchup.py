from scipy.stats import beta
from scipy.integrate import quad
from scipy.optimize import brentq
import json
import matplotlib.pyplot as plt
import math
import numpy as np


def gen_distribution(games_played, wins):
    '''
    returns the appropriate probability distribution for the probability of
    winning that matchup
    '''
    return beta(wins + 1, games_played - wins + 1)

def compare_distributions(dist1, dist2):
    '''
    compares 2 independent distributions

    Returns the probability that the value selected from dist1 is less
    than the value selected from dist2

    returns tuple of form (value, error)
    '''
    return quad(lambda x: dist1.cdf(x)*dist2.pdf(x), 0, 1)

def min_survival_function(distList):
    ''' 
    returns the survival function of the probability that a champions worst 
    matchup is p
    '''
    sfl = [thing.sf for thing in distList]
    return functionProduct(sfl)

def expected_min(distList):
    '''
    Calculates the expected minimum winrate for a given set of matchups
    '''
    productFunction = min_survival_function(distList)
    integrationResult = quad(productFunction, 0, 1)
    return integrationResult

def expected_min_square(distList):

        
    sf = min_survival_function(distList)
    productFunction = lambda x: sf(x) * x
    integrationResult = quad(productFunction, 0,1)
    return (integrationResult[0]*2, integrationResult[1]*2)

def variance_of_min(distList):
    e = expected_min(distList)[0]
    e2 = expected_min_square(distList)[0]
    return e2 - e**2
    
def std_of_min(distList):
    return math.sqrt(variance_of_min(distList))

def functionProduct(functionList):
    ''' 
    if given a list of functions f(x), g(x), h(x) ,...., q(x)
    returns f(x)*g(x)*h(x)*...*q(x)
    '''
    def prod(x):
        temp = 1
        for function in functionList:
            temp *= function(x)
        return temp
    return prod

def probability_worst_matchup_5050(distList):
    '''
    input Survival function or cdf function and get the probability that 
    a champions best matchup is better than 5050
    '''
    sf = min_survival_function(distList)
    fun = lambda x: sf(x) - .5
    return brentq(fun,0,1)
    

def load_file(elo, role, patch):
    filename = f'{elo}/{role}patch{patch}.json'
    js = ''
    with open(filename, 'r') as file:
        file = open(filename,'r')
        js = json.load(file)
    return js

def matchupToDist(matchup):
    games = matchup['count']
    wins = matchup['champ1']['wins']
    return gen_distribution(games, wins)

def performance(elo, role, patch, func):
    '''
    pass in a performance metric for a given champions matchup record
    
    the function must be over a list of distributions each representing a matchup
    '''
    data = load_file(elo, role, patch)
    print('Data Loaded')
    distArray = {champId:func(gen_distribution_array(matchups)) for champId, matchups in data.items()}
    return distArray
    
def plot_sf(champ, elo, role, patch):
    data = load_file(elo, role, patch)[champ]
    champ_dists = gen_distribution_array(data)
    function = min_survival_function(champ_dists)
    
    x = np.arange(0,1,.01)
    y = function(x)
    plt.plot(x,y)
    plt.show()
    
def plot_zipf(elo, role, patch, func = probability_worst_matchup_5050):
    perfArray = performance(elo, role, patch, func)
    perfArray = [value for value in perfArray.values()]
    perfArray = np.log10(np.array(sorted(perfArray, reverse=True)))
    x = np.arange(1,len(perfArray) + 1)
    plt.title(f'Zipf plot for {role} on {patch} at {elo} elo')
    plt.xlabel('Rank')
    plt.ylabel('log10(performance)')
    plt.scatter(x, perfArray)
    plt.show()
    
def gen_distribution_array(champData):
    distribution_array = [matchupToDist(matchup) for matchup in champData]
    return distribution_array
    
    
    
    



