import requests
import json
import os
import time

riot_api_key = "Your key"
champion_api_key = "Your key"
patch_data_location = 'patchdata.json'

def pull_matchup_data(champid, tier='PLATINUM,DIAMOND,MASTER,CHALLENGER'):
    '''
    Pulls all matchups a given champion has in all roles
    '''
    url = f'http://api.champion.gg/v2/champions/{champid}/matchups?elo={tier}&api_key={champion_api_key}'
  
    connection = requests.get(url)
    json_data = connection.json()
    connection.close()
    return json_data

def data_patch():
    '''
    Returns the patch on which the data was collected
    '''
    url = f'http://api.champion.gg/v2/champions?api_key={champion_api_key}'
    connection = requests.get(url)
    
    jsonData = connection.json()
    connection.close()
    return jsonData[0]['patch']

def rewrite_init_data(region='na1'):
    '''
    rewrites initialization data based on data collected from the riot api
    
    ***needs to be tweaked as to request data from a specific patch
    '''
    url = f'https://{region}.api.riotgames.com/lol/static-data/v3/champions?api_key={riot_api_key}'

    connection = requests.get(url)
    jsonData = connection.json()
    connection.close()
    jsonData['patch'] = data_patch()
    
    file = open(patch_data_location,'w')
    file.write(json.dumps(jsonData))
    file.close()
    print('Need to write "rewrite_init_data()"')
    
def load_init_data():
    '''
    reads file patchdata.json to supply neccesary variables for analysis
    '''
    init_file = open(patch_data_location, 'r+')
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
        name2id[value['name']] = value['id']
    return name2id

def gen_id2name():
    init_data = load_init_data()
    id2name = {}
    for value in init_data['data'].values():
        id2name[value['id']] = value['name']
    return id2name

def gen_patch():
    ''' 
    Returns the patch of the initialization data
    '''
    init_data = load_init_data()
    return init_data['patch']

def download_matchups(elo = ''):
    ''' 
    Downloads all matchups in a specific elo bracket from api.champion.gg
    '''
    print('Downloading')
    data = {}
    id2name = gen_id2name()
    patch = gen_patch()
    for key in id2name.keys():
        data[key] = pull_matchup_data(key, tier = elo)
        time.sleep(.2) #Bad rate limiting practice 
    if elo == '' or elo == 'HIGH':
        elo = 'HIGH'
    with open(f'{elo}/patch{patch}.json','w') as file:
        file.write(json.dumps(data))
    print(f'All data on {elo} elo Collected')

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
    file = open(f'{folder}/patch{patch}.json','r')
    jsonfile = json.load(file)
    file.close()
    roles = {}
    for value in jsonfile.values():
        for matchup in value:
            if matchup['_id']['role'] not in roles.keys():
                roles[matchup['_id']['role']] = []
            roles[matchup['_id']['role']].append(matchup)
    for role in roles.keys():
        print(role)
        with open(f'{folder}/{role}patch{patch}.json','w') as file:
            file.write(json.dumps(roles[role]))
    
    
if __name__ == '__main__':
    # goal is to update champion list only when needed
    if not file_acceptable():
        rewrite_init_data()

    tiers = ['BRONZE','SILVER','GOLD','PLATINUM','']
    for elo in tiers:
        download_matchups(elo = elo)
        sort_data(elo = elo)
              
        
