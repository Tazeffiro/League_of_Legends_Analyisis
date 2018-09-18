# -*- coding: utf-8 -*-
"""
Created on Sun Jun 10 15:30:29 2018

@author: Trevor
"""

from scipy.stats import beta
from scipy.integrate import quad
from scipy.optimize import brentq
import json
import numpy as np
import DataCollection as dc
import multiprocessing
import time
import pickle
import os

fileloc = 'YourFileLoc'

class champion:
    def __init__(self,ID, patch, elo, load_all_stats = False, data = None):
        '''
        Pass champion ID, the patch in question, and the elo all as strings

        currently after stats are generated the survival functions are deleted
        as such they must be regenerated -> deleted on each unpickling
        '''
        self.elo = elo if elo != '' else 'HIGH'
        self.patch = patch
        self.id = ID
        self.roles = ['MIDDLE', 'TOP', 'JUNGLE', 'DUO_SUPPORT', 'DUO_CARRY']

        if data == None:
            self.load_data() # Creates roleData dictionary (self.roleData)
        else:
            self.roleData = data # takes data from initialization

        self.gen_matchups()
        self.gen_playPercentages()
        self.gen_survival_functions() # Generates self.survivial_functions
        if load_all_stats:
            self.load_stats()
        del self.survival_functions

    def load_stats(self):
        self.expected_mins()
        self.expected_variances()
        self.expected_stds()
        self.gen_pwm5050()

    def load_data(self):
        '''
        Loads data from files stored on disk
        '''
        filenames = {}
        self.roleData = {}
        for role in self.roles:
            filenames[role] = fileloc + f'{self.elo}/{role}patch{self.patch}.json'
        for role,filename in filenames.items():
            with open(filename) as file:
                print(self.id,role)
                jsonData = json.load(file)
                if role in jsonData.keys():
                    self.roleData[role] = json.load(file)[self.id]
                else:
                    self.roleData[role] = []
        print(f'{self.id} loaded')

    def __applyStat(self, func, baseline=0):
        '''
        A utility function to make the creation of functions less tedious
        uses func that accepts a string ('TOP', 'DUO_CARRY', etc) and the
        desired output

        baseline applies when roleData[role] == []

        only run after data has been loaded
        '''
        stats = {}
        for role, data in self.roleData.items():
            if data:
                stats[role] = func(role)
            else:
                stats[role] = baseline
        return stats

    def gen_distribution(self, games_played, wins):
        '''
        returns the appropriate probability distribution for the probability of
        winning that matchup
        '''
        return beta(wins + 1, games_played - wins + 1)

    def gen_matchups(self):
        '''
        Converts each record into a corresponding beta distribution in an effort
        to quantify how well quantified we have the probability of winning
        '''
        def mu(role):
            return {match['champ2_id']:self.gen_distribution(match['count'],match['champ1']['wins']) for match in self.roleData[role]}
        self.matchups = self.__applyStat(mu, baseline = {})

        def dl(role):
            return list(self.matchups[role].values())
        self.distList = self.__applyStat(dl, baseline = [])

    def gen_playPercentages(self):
        '''
        A measure of how often a champion plays a specific role
        '''
        def pp(role):
            return sum([thing['count'] for thing in self.roleData[role]])
        plays = self.__applyStat(pp)
        totplays = sum(plays.values())
        if totplays == 0:
            plays = {role:.2 for role in self.roles}
        else:
            for key in plays.keys():
                plays[key] = plays[key] / totplays
        self.playPercentages = plays

    def gen_survival_functions(self):
        ''' generates a naive survival function assuming all champion
        win probabilities are independent

        i.e. an estimate that the lowest winrate is greater than some value

        some f(x) must be selected for the baseline, higher values incentivise
        further data collection
        '''
        def sf(role):
            funcarr = [matchup.sf for matchup in self.distList[role]]
            return functionProduct(funcarr)
        self.survival_functions =  self.__applyStat(sf, baseline = lambda x: 1)

    def expected_mins(self):
        '''
        Calculates the expected minimum winrate for a given set of matchups
        '''
        def em(role):
            return quad(lambda x: self.survival_functions[role](x), 0, 1)[0]
        self.expected_min_winrates = self.__applyStat(em, baseline =  0)

    def expected_variances(self):
        '''
        Calculates the variance of each survival function ()
        '''
        def ev(role):
            ir =  quad(lambda x: 2 * x * self.survival_functions[role](x), 0, 1)[0]
            ir -= self.expected_min_winrates[role]**2
            return ir
        self.vars_of_mins = self.__applyStat(ev, baseline = 1)

    def expected_stds(self):
        self.stds = self.__applyStat(lambda role: np.sqrt(self.vars_of_mins[role]), 1)

    def gen_pwm5050(self):
        self.gen_probabilities_worst_matchup_5050()

    def gen_probabilities_worst_matchup_5050(self):
        '''
        input Survival function or cdf function and get the probability that
        a champions best matchup is better than 5050
        '''
        def ff(role):
            func = lambda x: self.survival_functions[role](x) - .5
            return brentq(func, 0,1)
        self.probabilities_worst_matchup_5050 = self.__applyStat(ff, 0)

class meta:
    def __init__(self, elo, patch, load_all_stats = False):
        self.IdList = [str(thing) for thing in dc.gen_id2name().keys()]
        self.Champions = {}
        self.elo = elo if elo != '' else 'HIGH'
        self.patch = patch
        self.roles = ['MIDDLE', 'TOP', 'JUNGLE', 'DUO_SUPPORT', 'DUO_CARRY']
        self.populate_champions(load_all_stats)

    def populate_champions(self, load_all_stats = False):
        data = self.gen_data()
        def gen_args():
            dat = []
            for champ in self.IdList:
                dictval = {}
                for role in data.keys():
                    if champ in data[role]:
                        dictval[role] = data[role][champ]
                    else:
                        dictval[role] = []
                dat.append((champ, self.patch, self.elo, load_all_stats, dictval))
            return dat
        with multiprocessing.Pool(max(multiprocessing.cpu_count(), 1) >> 1) as p:
            results = p.starmap(create_champ, gen_args())
            for result in results:
                self.Champions[result[0]] = result[1]

    def gen_data(self):
        '''
        Compiles a dictionary of champion matchup data sorted by role and then
        by champion
        '''
        dat = {}
        for role in self.roles:
            filename = fileloc + f'{self.elo}/{role}patch{self.patch}.json'
            with open(filename, 'r') as file:
                dat[role] = json.load(file)
        return dat

    def eval_metric(self, role, func):
        '''
        Evaluated a metric for the champions played in a specific role in the
        given meta
        '''
        metrics = {key:func(champ,role) for key, champ in self.Champions.items()}
        return metrics

    def pull_metrics(self, role, category):
        metrics = {key:getattr(champ,category,None) for key, champ in self.Champions.items()}
        try:
            met = {}
            for key,metric in metrics.items():
                met[key] = metric[role]
            return met
        except:
            return metrics

def compare_distributions(dist1, dist2):
    '''
    compares 2 independent distributions

    Returns the probability that the value selected from dist1 is less
    than the value selected from dist2

    returns tuple of form (value, error)
    '''
    return quad(lambda x: dist1.cdf(x)*dist2.pdf(x), 0, 1)

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

def create_champ(champId, patch, elo, load_all, dats):
    return champId, champion(champId, patch, elo, load_all_stats=load_all, data = dats)

if __name__ == "__main__":
    if not dc.file_acceptable():
        dc.rewrite_init_data()
    tiers = ['BRONZE','SILVER','GOLD','PLATINUM','']
    patch = dc.gen_patch()
    for tier in tiers:
        dc.download_matchups_async(elo=tier)
        dc.sort_data(elo = tier)
        elo = tier if tier != '' else 'HIGH'
        x = meta(tier,patch,load_all_stats=True)
        with open( fileloc + f'/{elo}/{patch}meta.pkl', 'wb') as file:
            pickle.dump(x, file)
