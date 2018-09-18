''' 
RateLimiter Class taken from https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741
'''
import requests
import json
import os
import time
import asyncio
import aiohttp

riot_api_key = "your key"
champion_api_key = "your key"
patch_data_location = 'patchdata.json'


class RateLimiter:
    RATE = 5
    MAX_TOKENS = 5

    def __init__(self, client):
        self.client = client
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.wait_for_token()
        return self.client.get(*args, **kwargs)

    async def wait_for_token(self):
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(1)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.RATE
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now


def pull_matchup_data(champid, tier=''):
    '''
    Takes Data from champion.gg api and outputs all of the matchups a champion
    has in the current patch
    '''
    url = f'http://api.champion.gg/v2/champions/{champid}/matchups?elo={tier}&limit=10000&api_key={champion_api_key}'
    connection = requests.get(url)
    json_data = connection.json()
    connection.close()
    return json_data

def data_patch():
    '''
    Returns the patch on which the data was collected
    '''
    url = f'http://api.champion.gg/v2/champions?limit=1&api_key={champion_api_key}'
    connection = requests.get(url)

    jsonData = connection.json()
    connection.close()
    return jsonData[0]['patch']

def rewrite_init_data(region='na1', patch = data_patch()):
    '''
    rewrites initialization data based on data collected from the riot api

    ***needs to be tweaked as to request data from a specific patch
    '''
    url = f'http://ddragon.leagueoflegends.com/cdn/{patch}.1/data/en_US/champion.json'
    jsonData = ''
    with requests.get(url) as conn:
        jsonData = conn.json()
    jsonData['patch'] = patch

    with open(patch_data_location,'w') as file:
        file.write(json.dumps(jsonData))

def load_init_data():
    '''
    reads file patchdata.json to supply neccesary variables for analysis
    '''
    init_file = open(patch_data_location, 'r')
    init_data = json.load(init_file)
    init_file.close()
    return init_data

def file_acceptable(fileaddr = patch_data_location):
    '''
    checks if file exists and is non-empty
    if so, attempts to open and create a parse it as json,
    if the riot api request failed, a status key will be present in the file,

    failing on any front results in returning false
    '''
    file_exists = os.path.isfile(fileaddr) and os.path.getsize(fileaddr) > 0
    if file_exists:
        try:
            init_data = load_init_data()
            if 'status' in init_data.keys():
                return False
            else:
                #checks patch on data for annie
                dat = pull_matchup_data(1)
                return dat[0]['patch'] == gen_patch()
        except:
            return False
    else:
        return False

def gen_name2id():
    init_data = load_init_data()
    name2id = {}
    for value in init_data['data'].values():
        name2id[value['id']] = value['key']
    return name2id

def gen_id2name():
    init_data = load_init_data()
    id2name = {}
    for value in init_data['data'].values():
        id2name[str(value['key'])] = value['id']
    return id2name

def gen_patch():
    '''
    Returns the patch of the initialization data
    '''
    init_data = load_init_data()
    return init_data['patch']

def download_matchups_async(elo = ''):
    champs = []
    init_data = load_init_data()
    for value in init_data['data'].values():
        champs.append(str(value['key']))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(CollectData(tier = elo, clist = champs))

def sort_data(elo = ''):
    '''
    Sorts the data on a given elo by role and outputs each into its own
    respective file
    NOTE: only run after download_matchups
    '''
    folder = elo
    if folder == '':
        folder = 'HIGH'
    patch = gen_patch()
    file = open(fileloc + f'{folder}/patch{patch}.json','r')
    jsonfile = json.load(file)
    file.close()
    roles = {}
    for champid, matchupList in jsonfile.items():
        for matchup in matchupList:
            role = matchup['_id']['role']
            if role not in roles.keys():
                roles[role] = {}
            if champid not in roles[role].keys():
                roles[role][champid] = []
            roles[role][champid].append(matchup)
    for role in roles.keys():
        for champ, matchup in roles[role].items():
            ensure_champ1(champ, matchup)
        with open(fileloc + f'{folder}/{role}patch{patch}.json','w') as file:
            file.write(json.dumps(roles[role]))

def ensure_champ1(champ, matchups):
    '''
    Used in sort_data() to ensure that champ1 is always the champion being referenced
    when looked up in the role json file
    '''
    for matchup in matchups:
        del matchup['_id']
        if str(matchup['champ2_id']) == champ:
            temp = matchup['champ1']
            matchup['champ1'] = matchup['champ2']
            matchup['champ2'] = temp
            temp = matchup['champ1_id']
            matchup['champ1_id'] = matchup['champ2_id']
            matchup['champ2_id'] = temp


async def pull_m_data(champid, Throttler, tier = ''):
    '''
    Pulls all matchups a given champion has in all roles
    '''
    #limit chosen so that all matchups will be pulled

    url = f'http://api.champion.gg/v2/champions/{champid}/matchups?elo={tier}&limit=1000&api_key={champion_api_key}'
    async with await Throttler.get(url) as resp:
        return champid, await resp.json()

async def CollectData(tier = '', clist = ['24','13','555','1','2','3','4','5','6','7','8']):
    tasks = []
    responses = []
    patch = gen_patch()
    async with aiohttp.ClientSession() as session:
        throttle = RateLimiter(session)
        for champ in clist:
            task = asyncio.ensure_future(pull_m_data(champ,throttle,tier=tier))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
    if tier == '':
        tier = 'HIGH'
    values = {}
    for result in responses:
        values[result[0]] = result[1]
    with open(fileloc + f'{tier}/patch{patch}.json','w') as file:
        file.write(json.dumps(values))

if __name__ == '__main__':
    # goal is to update champion list only when needed

    if not file_acceptable():
        rewrite_init_data()

    tiers = ['BRONZE','SILVER','GOLD','PLATINUM','']
    for elo in tiers:
        download_matchups_async(elo = elo)
        sort_data(elo = elo)
