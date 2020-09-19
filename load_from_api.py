import roleml
import cassiopeia as cass
from config import *
import os
import json
import sys
import time
import datetime
from sql_tools import *

# CONFIG CONSTANTS
MIN_TIME = 7200
ALLOWED_VERSIONS = ['10.18', '10.19', '10.20', '10.21', '10.22', '10.23']


cass.apply_settings({'global': {'version_from_match': 'patch', 'default_region': None}, 'plugins': {}, 'pipeline': {'Cache': {}, 'DDragon': {}, 'RiotAPI': {'api_key': 'RIOT_API_KEY'}}, 'logging': {'print_calls': False, 'print_riot_api_key': False, 'default': 'WARNING', 'core': 'WARNING'}})
cass.set_riot_api_key(API_KEY)
def load_champions():
    res = {}
    for i in cass.get_champions():
        res[i.id] = i
    return res

cass.set_default_region("NA")
champs = load_champions()

if len(sys.argv) < 2:
    cass.set_default_region("NA")
    region = 'NA'
else:
    cass.set_default_region(sys.argv[1])
    region = sys.argv[1]


def write_match(match, timeline):
    role_index = { 'top' : 0, 'jgl' : 1, 'mid' : 2, 'bot' : 3, 'sup' : 4}
    try:
        roles = roleml.predict(match, timeline, True)
    except:
        print("game too short: %s" % match['id'], file=sys.stderr)
        return True
    match['creation'] = match['creation'].timestamp
    match['duration'] = match['duration'].seconds
    for i in match['participants']:
        i['side'] = i['side'].value
    for i in match['teams']:
        i['side'] = i['side'].value
        for j in i['participants']:
            j['side'] = j['side'].value
    m = match
    match_id = m['id']
    game_id = m['id']
    blue_ban_ids = m['teams'][0]['bans']
    red_ban_ids = m['teams'][1]['bans']
    blue_bans = [champs.get(_x, '') for _x in blue_ban_ids]
    red_bans = [champs.get(_x, '') for _x in red_ban_ids]
    blue_bans = [_x if _x == '' else _x.name for _x in blue_bans]
    red_bans = [_x if _x == '' else _x.name for _x in red_bans]
    match_id = m['id']
    version = m['version']
    version = ".".join(version.split('.')[:2])
    result = 1 if m['teams'][0]['isWinner'] else 0
    creation = m['creation']
    duration = m['duration']
    region = m['region']
    load_game(match_id, version, result, creation, duration, region)
    load_bans(match_id, region, 1, blue_bans[0], blue_bans[1], blue_bans[2], blue_bans[3], blue_bans[4])
    load_bans(match_id, region, 0, red_bans[0], red_bans[1], red_bans[2], red_bans[3], red_bans[4])

    blue_champs = [0, 0, 0, 0, 0]
    red_champs = [0, 0, 0, 0, 0]

    blue_team = [0, 0, 0, 0, 0]
    red_team = [0, 0, 0, 0, 0]
    
    for p, pid in zip(m['participants'], range(1, len(m['participants']) + 1)):
        name = p['summonerName']
        champ_id = p['championId']
        k = p['stats']['kills']
        d = p['stats']['deaths']
        a = p['stats']['assists']
        cc = p['stats']['timeCCingOthers']
        gold_spent = p['stats']['goldSpent']
        damage = p['stats']['totalDamageDealtToChampions']
        heal = p['stats']['totalHeal']
        tank = p['stats']['totalDamageTaken']
        cs10 = round(p['timeline']['creepsPerMinDeltas'].get('0-10', 0), 1)
        cs20 = round(p['timeline']['creepsPerMinDeltas'].get('0-10', 0) + p['timeline']['creepsPerMinDeltas'].get('10-20', 0), 1)
        g10 = round(p['timeline']['goldPerMinDeltas'].get('0-10', 0), 1)
        g20 = round(p['timeline']['goldPerMinDeltas'].get('0-10', 0) + p['timeline']['goldPerMinDeltas'].get('10-20', 0), 1)
        xp10 = round(p['timeline']['xpPerMinDeltas'].get('0-10', 0), 1)
        xp20 = round(p['timeline']['xpPerMinDeltas'].get('0-10', 0) + p['timeline']['xpPerMinDeltas'].get('10-20', 0), 1)
        role = roles[pid][:3].replace('jun', 'jgl')
        champ = champs[champ_id].name
        if champ[0] not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            print("Bad champ name")
            return False
        is_blue = 1 if p['side'] == 100 else 0
        side_res = result if is_blue else 1 - result
        load_lane_info(match_id, region, role, is_blue, name, champ, side_res)
        load_stats(match_id, region, role, is_blue, champ, side_res, k, d, a, cc, gold_spent, damage, heal, tank, cs10, cs20, g10, g20, xp10, xp20)
        if p['side'] == 100:
            blue_champs[role_index[role]] = champ
            blue_team[role_index[role]] = name
        else:
            red_champs[role_index[role]] = champ
            red_team[role_index[role]] = name
    return True

def check_timeline(mid):
    filename = 'data/timeline_%s.json' % mid
    return os.path.exists(filename)

def check_match(mid):
    filename = 'data/timeline_%s.json' % mid
    return os.path.exists(filename)

def write_timeline(timeline):
    try:
        mid = timeline['id']
        filename = 'data/timeline_%s.json' % mid
        outfile = open(filename, 'w')
        json.dump(timeline, outfile)
        outfile.close()
    except:
        return False
    return True

def update_matches(player, region, min_time = 7200, max_matches = 100):
    try:
        match_history = cass.MatchHistory(summoner=cass.get_summoner(name=player), queues={cass.Queue.ranked_solo_fives})[:max_matches]
        return match_history
    except: 
        return []

x = 0
players_list = [cass.get_challenger_league(queue=cass.Queue.ranked_solo_fives), cass.get_master_league(queue=cass.Queue.ranked_solo_fives)]
for players in players_list:
    cps = [p.summoner.name for p in players]
    n = -1
    matches = get_matches(region)
    while n < len(cps)-1:
        n+= 1
        p = cps[n]
        print("summoner:", p)
        now_time = int(datetime.datetime.now().timestamp())
        if now_time - get_last_game(p) < MIN_TIME: 
            print("too soon:", now_time - get_last_game(p), p)
            continue
        match_history = update_matches(p, region)
        try:
            for m in match_history:
                x+=1
                mid = m.id
                try:
                    if ".".join(m.version.split('.')[:2]) not in ALLOWED_VERSIONS:
                        print("too old")
                        x -= 1
                        break
                except cass.datastores.riotapi.common.APIError:
                    print("got API Error, pausing")
                    time.sleep(30)
                    if ".".join(m.version.split('.')[:2]) not in ALLOWED_VERSIONS:
                        print("too old")
                        x -= 1
                        break
                if mid in matches:
                    break
                try:
                    match = m.load()
                    match.timeline.load()
                except cass.datastores.riotapi.common.APIError:
                    print("got API Error, pausing")
                    time.sleep(30)
                    match = m.load()
                    match.timeline.load()
                match_dict = match.to_dict()
                for _y in match_dict['participants']:
                    if _y['summonerName'] not in cps:
                        cps.append(_y['summonerName'])
                        print("ADDING %s" % _y['summonerName'])
                print(x, match.id, datetime.datetime.fromtimestamp(match_dict['creation'].timestamp).strftime("%Y_%m_%d %H:%M:%S"))
                assert write_match(match_dict, match.timeline.to_dict())
        except IndexError:
            print('match history empty: ', p)
            continue
