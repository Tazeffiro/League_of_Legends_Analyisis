from scipy.stats import beta
from scipy.integrate import quad
import json
from pandas.io.json import json_normalize
import matplotlib.pyplot as plt
from DataCollection import gen_id2name 

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

def expected_min(distList):
    '''
    Calculates the expected minimum winrate for a given set of matchups
    '''
    survivalFunctionList = []
    for distribution in distList:
        survivalFunctionList.append(distribution.sf)
        
    productFunction = functionProduct(survivalFunctionList)
    integrationResult = quad(productFunction, 0, 1)
    return integrationResult

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

def query(champid, data):
    '''
    returns matchup data where champ1 is the searchable champion, and 2 
    corresponds to a given matchup
    '''
    ischamp1 = data['champ1_id'] == champid
    ischamp2 = data['champ2_id'] == champid
    def search(param):
        series1 = data[ischamp1]
        series2 = data[ischamp2]
        return series1[f'champ1.{param}'].append(series2[f'champ2.{param}'])
    return search

if __name__ == "__main__":
    elo = 'PLATINUM'
    role = 'MIDDLE'
    
    #Loads the file and flattens it to work nicely with numpy
    file = open(f'{elo}/{role}patch8.11.json','r')
    data = json.load(file)
    file.close()
    pddata = json_normalize(data)
    
    #generating the expected winrate from the record of games
    pddata['champ1.expected_winrate'] = (pddata['champ1.wins'] + 1 )/ (pddata['count'] + 2)
    pddata['champ2.expected_winrate'] = (pddata['champ2.wins'] + 1 )/ (pddata['count'] + 2)
    
    pddata['champ1.opponent'] = pddata['champ2_id']
    pddata['champ2.opponent'] = pddata['champ1_id']
    
    pddata['champ1.count'] = pddata['count']
    pddata['champ2.count'] = pddata['count']
    ids = pddata['champ1_id'].append(pddata['champ2_id'])
    ids = ids.unique()
    worstWinrates = {}
    for champion in ids:
        dat = query(champion, pddata)
        opponents = dat('opponent')
        wins = dat('wins')
        count = dat('count')
        distList = []
        for i in range(count.size):
            distrib = gen_distribution(count.iloc[i], wins.iloc[i])
            distList.append(distrib)
        worstWinrates[champion] = expected_min(distList)[0]

        
