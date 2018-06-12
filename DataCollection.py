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
    url = f'http://api.champion.gg/v2/champions/{champid}/matchups/?elo={tier}&api_key={champion_api_key}'
  
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
            file = open(fileaddr,'r')
            jsonData = json.load(file)
            if 'status' in jsonData.keys():
                return False
            else:
                return True
        except:
            return False
    else: 
        return False 

if __name__ == '__main__':
    # goal is to update champion list only when needed
    if not file_acceptable():
        rewrite_init_data()
    init_data = load_init_data()
    patch = init_data['patch']
    name2id = {}
    id2name = {}
    for value in init_data['data'].values():
        name2id[value['name']] = value['id']
        id2name[value['id']] = value['name']
    data = {}
    tiers = ['BRONZE','SILVER','GOLD','PLATINUM']
    for elo in tiers:
        data[elo] = {}
        for key in id2name.keys():
            data[elo][key] = pull_matchup_data(key, tier=elo)
            time.sleep(.2) #for rate limiting
        file = open(f'{elo}/patch{patch}.json', 'w')
        file.write(json.dumps(data[elo]))
        file.close()
        print(f'{elo} collected. Saving')
        
        roles = {}
        for champ_id, stats in data[elo].items():
            for matchups in stats:
                if matchups['_id']['role']] not in roles.keys() 
                    roles[matchups['_id']['role']] = []
                roles[matchups['_id']['role']].append(matchups)
        for role in roles.keys():
            role_file = open(f'{elo}/{role}patch{patch}', 'w')
            role_file.write(json.dumps(roles[role]))
            role_file.close()
        print(f'{elo} saved')
              
        
