from scipy.stats import beta
from scipy.integrate import quad
from scipy.optimize import brentq
import json
import numpy as np
import DataCollection as dc
import multiprocessing
import time
import pickle

class champion:
    def __init__(self,ID, patch, elo, load_all_stats = False, data = None):
        '''
        Pass champion ID, the patch in question, and the elo all as strings
        '''
        self.elo = elo if elo != '' else 'HIGH'
        self.patch = patch
        self.id = ID
        self.roles = ['MIDDLE', 'TOP', 'JUNGLE', 'DUO_SUPPORT', 'DUO_CARRY']
        # Allows loading from data one load
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
        filenames = {}
        self.roleData = {}
        for role in self.roles:
            filenames[role] = f'{self.elo}/{role}patch{self.patch}.json'
        for role,filename in filenames.items():
            with open(filename) as file:
                self.roleData[role] = json.load(file)[self.id]
        print(f'{self.id} loaded')

    def gen_distribution(self, games_played, wins):
        '''
        returns the appropriate probability distribution for the probability of
        winning that matchup
        '''
        return beta(wins + 1, games_played - wins + 1)

    def gen_matchups(self):
        self.matchups = {}
        self.distList = {}
        for role in self.roles:
            self.matchups[role] = {match['champ2_id']:self.gen_distribution(match['count'],match['champ1']['wins']) for match in self.roleData[role]}
            self.distList[role] = list(self.matchups[role].values())

    def gen_playPercentages(self):
        plays = {}
        #collecting the Number of games
        for role in self.roles:
            count = sum([thing['count'] for thing in self.roleData[role]])
            plays[role] = count
        tot = sum(plays.values())
        for role in plays.keys():
            plays[role] /= tot
        self.playPercentages = plays

    def gen_survival_functions(self):
        ''' generates a naive survival function assuming all champion
        win probabilities are independent
        '''
        survival_functions = {}
        for role in self.roles:
            funcarr = [matchup.sf for matchup in self.distList[role]]
            survival_functions[role] = functionProduct(funcarr)
        self.survival_functions = survival_functions

    def expected_mins(self):
        '''
        Calculates the expected minimum winrate for a given set of matchups
        '''
        self.expected_min_winrates = {}
        for role in self.roles:
            integrationResult = quad(lambda x: self.survival_functions[role](x), 0, 1)
            self.expected_min_winrates[role] = integrationResult[0] #[0] hides the error term

    def expected_variances(self):
        self.vars_of_mins = {}
        for role in self.roles:
            integrationResult = quad(lambda x: 2 * x * self.survival_functions[role](x), 0, 1)[0] #[0] hides the error term
            self.vars_of_mins[role] = integrationResult - self.expected_min_winrates[role]**2

    def expected_stds(self):
        self.stds = {}
        for role in self.roles:
            self.stds[role] = np.sqrt(self.vars_of_mins[role])

    def gen_pwm5050(self):
        self.gen_probabilities_worst_matchup_5050()

    def gen_probabilities_worst_matchup_5050(self):
        '''
        input Survival function or cdf function and get the probability that
        a champions best matchup is better than 5050
        '''
        self.probabilities_worst_matchup_5050 = {}
        for role in self.roles:
            func = lambda x: self.survival_functions[role](x) - .5
            self.probabilities_worst_matchup_5050[role] = brentq(func, 0, 1)
            self.pwm5050 = self.probabilities_worst_matchup_5050

class meta():
    def __init__(self, elo, patch, load_all_stats = False, parallell = True):
        self.IdList = [str(thing) for thing in dc.gen_id2name().keys()]
        self.Champions = {}
        self.elo = elo if elo != '' else 'HIGH'
        self.patch = patch
        self.roles = ['MIDDLE', 'TOP', 'JUNGLE', 'DUO_SUPPORT', 'DUO_CARRY']
        if parallell:
            self.populate_champions_parallell(load_all_stats)
        else:
            self.populate_champions(load_all_stats)

    def populate_champions(self, load_all_stats = False, progress_increment = 10):
        data = self.gen_data()
        counter = 0.
        progress = progress_increment
        st = time.monotonic()
        for champId in self.IdList:
            cdat = {role:data[champId] for role, data in data.items()}
            self.Champions[champId] = champion(champId, self.patch, self.elo, load_all_stats, data=cdat)
            if counter / len(self.IdList) > progress / 100:
                print(f'{progress}% complete')
                progress += progress_increment
            counter += 1
        print("Champions Loaded")
        print(time.monotonic() - st)

    def populate_champions_parallell(self, load_all_stats = False):
        data = self.gen_data()
        def gen_args():
            dat = []
            for champ in self.IdList:
                dat.append((champ, self.patch, self.elo, load_all_stats, {role:data[champ] for role, data in data.items()} ))
            return dat
        with multiprocessing.Pool(multiprocessing.cpu_count() >> 1) as p:
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
            filename = f'{self.elo}/{role}patch{self.patch}.json'
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
        x = meta(tier,'8.12',load_all_stats=True,parallell=True)
        with open(f'{elo}/{patch}meta.pkl', 'wb') as file:
            pickle.dump(x, file)
