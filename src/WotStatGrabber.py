# Copyright 2013 Richard Valencia
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import json
import urllib.request
import argparse
from operator import itemgetter

REQ_SOURCE_TOKEN = 'WG-WoT_Assistant-1.3.2'
REQ_APP_IDS = {'NA' : '16924c431c705523aae25b6f638c54dd',
               'RU' : '171745d21f7f98fd8878771da1000a31',
               'EU' : 'd0a293dc77667c9328783d489c8cef73',
               'ASIA' : '39b4939f5f2460b3285bfa708e4b252c',
               'KR' : 'ffea0f1c3c5f770db09357d94fe6abfb'}
REQ_BASE_URLS = {'NA' : 'http://api.worldoftanks.com',
                 'RU' : 'http://api.worldoftanks.ru',
                 'EU' : 'http://api.worldoftanks.eu',
                 'ASIA' : 'http://api.worldoftanks.asia',
                 'KR' : 'http://api.worldoftanks.kr'}
REQ_PLAYER_INFO = '/2.0/account/info/?{params}'
REQ_PLAYER_SEARCH = '/2.0/account/list/?{params}'
REQ_PLAYER_TANKS = '/2.0/account/tanks/?{params}'
REQ_PLAYER_STATS_SLICE = '/2.0/stats/accountbytime/?{params}'
REQ_CLAN_INFO = '/2.0/clan/info//?{params}'
REQ_CLAN_SEARCH = '/2.0/clan/info//?{params}'
REQ_TANKS_LIST = '/2.0/encyclopedia/tanks/?{params}'
REQ_TANK_INFO = '/2.0/encyclopedia/tankinfo/?{params}'

USER_ID_REQ_OFFSET = '0'
USER_ID_REQ_LIMIT = '1'
USER_ID_REQ_URL = 'http://api.worldoftanks.com/uc/accounts/api/1.1/?{params}'
USER_STATS_REQ_URL = ('http://api.worldoftanks.com/uc/accounts/'
                      '{id}/api/1.9/?{params}')
_wn = False
_top_low_tiers1 = 3
_top_low_tiers2 = 5
_req_server = 'NA'
_tank_ids = []
_tank_tiers = {}


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class PlayerNotFoundError(Error):
    """Exception raised when a player cannot be found

    Attributes:
        player -- username that was looked up
        message -- explanation of the error

    """

    def __init__(self, player, message):
        """Initialization of exception

        Keyword arguments:
            player -- username that was looked up
            message -- explanation of the error
        """

        self.player = player
        self.message = message


class RequestError(Error):
    """Exception raised when a request fails
    
    Attributes:
        message -- explanation of the error
    """
    
    def __init__(self, message):
        """Initialization of exception

        Keyword arguments:
            message -- explanation of the error
        """

        self.message = message
        

def request_user_id(user_name):
    """Get the user ID from WG API given user name

    Keyword arguments:
        userName -- user to look up

    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({
        'application_id' : REQ_APP_IDS[_req_server], 
        'search' : user_name
        })
    urlstring = ''.join([REQ_BASE_URLS[_req_server], 
                         REQ_PLAYER_SEARCH.format(params=parameters)
                         ])
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()

    # Parse the JSON and get the user ID after
    # making sure we've found the correct user.
    userInfo = json.loads(response.read().decode(encoding))
    items = userInfo['data']
    # Usernames are not case-sensitive for API requests
    if not items:
        raise PlayerNotFoundError(user_name, 'Player was not found')
    
    for user in items:
        if user['nickname'].lower() == user_name.lower():
            user_id = user['id']
    
    if not user_id:
        raise PlayerNotFoundError(user_name, 'Player was not found')

    return user_id


def request_user_stats(user_id):
    """Get the user statistics from WG API given user ID

    Keyword arguments:
        user_id -- user to look up

    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({
        'application_id' : REQ_APP_IDS[_req_server],
        'account_id' : user_id
        })
    urlstring = ''.join([REQ_BASE_URLS[_req_server], 
                         REQ_PLAYER_INFO.format(params=parameters)
                         ])
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()

    # Parse and return the JSON after checking for errors
    user_info = json.loads(response.read().decode(encoding))
    if user_info['status'] == 'error':
        raise PlayerNotFoundError(user_id, user_info['error']['message'])
    else:
        stats = user_info['data'][str(user_id)]
    return stats


def request_user_tanks(user_id):
    """Gets the statistics for tanks played by a user
    
    Keyword arguments:
        user_id -- user to look up tank stats for
        
    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({
        'application_id' : REQ_APP_IDS[_req_server],
        'account_id' : user_id
        })
    urlstring = ''.join([REQ_BASE_URLS[_req_server],
                         REQ_PLAYER_TANKS.format(params=parameters)
                         ])
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()
    
    # Parse and return the JSON after checking for errors
    tanks_list = json.loads(response.read().decode(encoding))
    if tanks_list['status'] == 'error':
        raise RequestError('Player tank stats could not be retrieved.')
    else:
        tanks = tanks_list['data'][str(user_id)]
    return tanks


def request_tank_list():
    """Gets the tank list from WG API
    
    """
    
    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({
        'application_id' : REQ_APP_IDS[_req_server]
        })
    urlstring = ''.join([REQ_BASE_URLS[_req_server],
                         REQ_TANKS_LIST.format(params=parameters)
                         ])
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()
    
    # Parse and return the JSON after checking for errors
    tanks_list = json.loads(response.read().decode(encoding))
    if tanks_list['status'] == 'error':
        raise RequestError('Tanks list could not be retrieved.')
    else:
        tanks = tanks_list['data']
    return tanks


def populate_tank_info():
    """Requests the tanks list then compiles a 
    list of sorted ids and a dict of tiers.
    
    """
    
    tanks_list = request_tank_list()
    for key in sorted(tanks_list):
        _tank_ids.append(key)
        _tank_tiers[key] = tanks_list[key]['level']
    

def prepare_tank_list_row(tanks_list):
    """Build a dictionary with the relevant tank information
    
    Keyword arguments:
        tanks_list -- tank information loaded from json
    
    """

    tanks_row = {}
    for key in sorted(tanks_list):
        tanks_row[key] = tanks_list[key]['name']
    
    return tanks_row
    

def prepare_output_row(user_stats, user_id):
    """Build a dictionary with the relevant stats

    Keyword arguments:
        user_stats -- user stat information loaded from json
        user_id -- user ID number

    """

    ratings = user_stats['statistics']['all']
    stats_row = {}

    # Add user identifying information
    stats_row['name'] = user_stats['nickname']
    stats_row['id'] = user_id

    # Add the basic stat information
    battles = ratings['battles']
    stats_row['battles'] = battles
    stats_row['tot_xp'] = ratings['xp']
    stats_row['avg_xp'] = ratings['battle_avg_xp']
    
    # Add calculated stat information
    spots = ratings['spotted']
    stats_row['tot_spots'] = spots
    stats_row['avg_spots'] = spots / battles
    
    kills = ratings['frags']
    stats_row['tot_kills'] = kills
    stats_row['avg_kills'] = kills / battles
    
    damage = ratings['damage_dealt']
    stats_row['tot_dmg'] = damage
    stats_row['avg_dmg'] = damage / battles

    wins = ratings['wins']
    stats_row['wins'] = wins
    stats_row['win_pct'] = (wins / battles) * 100
    
    stats_row['losses'] = ratings['losses']
    stats_row['draws'] = ratings['draws']
    
    cap_points = ratings['capture_points']
    stats_row['tot_cap_points'] = cap_points
    stats_row['avg_cap_points'] = cap_points / battles 
    
    def_points = ratings['dropped_capture_points']
    stats_row['tot_def_points'] = def_points
    stats_row['avg_def_points'] = def_points / battles
    
    tanks = request_user_tanks(user_id)

    avg_tier_info = calc_tier_info(tanks, battles)
    stats_row['avg_tier'] = avg_tier_info['avg_tier']
    stats_row['vehicle_battles'] = avg_tier_info['vehicle_battles']
    
    if _wn:        
        tlb1 = ''.join(['battles_top_', str(_top_low_tiers1), '_low_tiers'])
        slt1 = ''.join(['sum_tier_top_', str(_top_low_tiers1), '_low_tiers'])
        wlt1 = ''.join(['weighted_sum_tier_top_', 
                        str(_top_low_tiers1), '_low_tiers'])
        tlb2 = ''.join(['battles_top_', str(_top_low_tiers2), '_low_tiers']) 
        slt2 = ''.join(['sum_tier_top_', str(_top_low_tiers2), '_low_tiers'])
        wlt2 = ''.join(['weighted_sum_tier_top_', 
                        str(_top_low_tiers2), '_low_tiers'])
        
        stats_row[tlb1] = avg_tier_info['top_low_battles1']
        stats_row[slt1] = avg_tier_info['sum_low_tiers1']
        stats_row[wlt1] = avg_tier_info['weighted_sum_low_tier1']
        stats_row[tlb2] = avg_tier_info['top_low_battles2']
        stats_row[slt2] = avg_tier_info['sum_low_tiers2']
        stats_row[wlt2] = avg_tier_info['weighted_sum_low_tier2']
        
        stats_row['t1_battles'] = avg_tier_info['t1_battles']
        stats_row['t2_battles'] = avg_tier_info['t2_battles']
        stats_row['t3_battles'] = avg_tier_info['t3_battles']
        stats_row['t4_battles'] = avg_tier_info['t4_battles']
        stats_row['t5_battles'] = avg_tier_info['t5_battles']
        stats_row['t6_battles'] = avg_tier_info['t6_battles']
        stats_row['t7_battles'] = avg_tier_info['t7_battles']
        stats_row['t8_battles'] = avg_tier_info['t8_battles']
        stats_row['t9_battles'] = avg_tier_info['t9_battles']
        stats_row['t10_battles'] = avg_tier_info['t10_battles']
        
        tank_battles = avg_tier_info['tank_battles']
        for key in sorted(tank_battles):
            stats_row[key] = tank_battles[key]
            _tank_ids.append(key)

    return stats_row


def calc_tier_info(tanks, battles):
    """Calculates the average tier and other tier-based
    information given a set of user statistics

    Keyword arguments:
        tanks -- user tank stat information loaded from json
        battles -- total battles for this user

    """
    
    tier_info = {}
    tier_info['vehicle_battles'] = 0
    tier_info['avg_tier'] = 0
    low_tiers = []
    
    if _wn:
        tank_battles = {}
        tier_info['t1_battles'] = 0
        tier_info['t2_battles'] = 0
        tier_info['t3_battles'] = 0
        tier_info['t4_battles'] = 0
        tier_info['t5_battles'] = 0
        tier_info['t6_battles'] = 0
        tier_info['t7_battles'] = 0
        tier_info['t8_battles'] = 0
        tier_info['t9_battles'] = 0
        tier_info['t10_battles'] = 0
    

    # Spin through all vehicles and gather low tier stats
    for tank in tanks:
        tank_stats = tank['statistics']['all']
        tank_id = tank['tank_id']
        tier = _tank_tiers[str(tank_id)]
        vehicle_battles = tank_stats['battles']
        tier_info['vehicle_battles'] += vehicle_battles
        tier_info['avg_tier'] += (tier / battles) * vehicle_battles
        
        if _wn:
            tank_battles[str(tank_id)] = vehicle_battles
            tier_info[''.join(['t', str(tier), '_battles'])] += vehicle_battles
            
            if tier <= 3:
                low_tiers.append([vehicle_battles, tier])
    
    if _wn:  
        tier_info['tank_battles'] = tank_battles
              
        # Calculate for the first set of top low tiers
        low_tier_info1 = calc_low_tiers(low_tiers, _top_low_tiers1)
        tier_info['top_low_battles1'] = low_tier_info1['top_low_battles']
        tier_info['sum_low_tiers1'] = low_tier_info1['sum_low_tier']
        tier_info['weighted_sum_low_tier1'] = low_tier_info1['weighted_low_tier']
        
        # Calculate for the second set of top low tiers
        low_tier_info = calc_low_tiers(low_tiers, _top_low_tiers2)
        tier_info['top_low_battles2'] = low_tier_info['top_low_battles']
        tier_info['sum_low_tiers2'] = low_tier_info['sum_low_tier']
        tier_info['weighted_sum_low_tier2'] = low_tier_info['weighted_low_tier']
    
    return tier_info


def calc_low_tiers(low_tiers, top_x):
    """Calculates battles, tier sum, and weighted tier in top_x low_tiers 
    given a list of low_tier tank stats
    
    Keyword arguments:
        low_tiers -- low tier tank statistics
        top_x -- number of top low tier tanks to calculate for
        
    """
    
    low_tier_info = {}
    low_battles = 0
    tier_sum = 0
    weighted_tier = 0
    for vehicle in sorted(low_tiers, key=itemgetter(0), reverse=True)[:top_x]:
        low_battles += int(vehicle[0])
        tier_sum += int(vehicle[1])
        weighted_tier += (int(vehicle[1]) * int(vehicle[0]))
    weighted_tier = weighted_tier * _top_low_tiers1 / low_battles
    
    low_tier_info['top_low_battles'] = low_battles
    low_tier_info['sum_low_tier'] = tier_sum
    low_tier_info['weighted_low_tier'] = weighted_tier
    
    return low_tier_info
    
    
def create_user_stats_csv(input_file, output_file):
    """Gets the statistics for names in inputFile and writes
    the results in csv format to outputFile
    
    Keyword arguments:
        input_file -- File with a complete username on each line
        output_file -- CSV file that will be created with results
        
    """
    fieldnames = [
        'name', 'id', 'battles',
        'tot_xp', 'avg_xp', 'tot_spots', 
        'avg_spots', 'tot_kills', 'avg_kills',
        'tot_dmg', 'avg_dmg', 'wins', 'losses', 'draws',
        'win_pct', 'tot_cap_points', 'avg_cap_points',
        'tot_def_points', 'avg_def_points', 'avg_tier', 
        'vehicle_battles'
        ]
    
    if _wn:
        fieldnames.extend([
            ''.join(['battles_top_', str(_top_low_tiers1), '_low_tiers']), 
            ''.join(['sum_tier_top_', str(_top_low_tiers1), '_low_tiers']),
            ''.join(['weighted_sum_tier_top_', 
                     str(_top_low_tiers1), '_low_tiers'
                     ]),
            ''.join(['battles_top_', str(_top_low_tiers2), '_low_tiers']), 
            ''.join(['sum_tier_top_', str(_top_low_tiers2), '_low_tiers']),
            ''.join(['weighted_sum_tier_top_', 
                     str(_top_low_tiers2), '_low_tiers'
                     ]),
            't1_battles', 't2_battles', 't3_battles', 't4_battles', 
            't5_battles', 't6_battles', 't7_battles', 't8_battles', 
            't9_battles', 't10_battles'
            ])
        
        populate_tank_info()
        fieldnames.extend(_tank_ids)
    
    with open(input_file, encoding='utf-8') as names_file:
        with open(output_file, 'w', newline='') as csv_file:
            output = csv.DictWriter(csv_file, fieldnames, dialect='excel', 
                                    extrasaction='ignore'
                                    )
            output.writeheader()
            
            while True:
                name = names_file.readline()
                if len(name) == 0:
                    break
                    
                # Get stats for this user and prepare them for output
                user_id = request_user_id(name.strip())
                stats = request_user_stats(user_id)
                row = prepare_output_row(stats, user_id)
                
                # Output stats to CSV
                output.writerow(row)


def create_tank_list_csv(output_file):
    """Gets the list of tanks names/ids and writes
    the results in csv format to outputFile
    
    Keyword arguments:
        output_file -- CSV file that will be created with results
        
    """    
    
    tanks_list = request_tank_list()
    tanks_row = prepare_tank_list_row(tanks_list)
    
    fieldnames = []
    for key in sorted(tanks_row):
        fieldnames.append(key)
    
    with open(output_file, 'w', newline='') as csv_file:
        output = csv.DictWriter(csv_file, fieldnames, dialect='excel', 
                                extrasaction='ignore'
                                )
        output.writeheader()
        output.writerow(tanks_row)
            

if __name__ == '__main__':
    # Parse the arguments
    parser = argparse.ArgumentParser(description = '''Retrieve and output WoT 
                                                    User Statistics.'''
                                    )
    parser.add_argument('input_file', metavar='input_file', type=str, 
                        help='''Complete path to a file containing the names to 
                                retrieve stats for (one name per line).'''
                        )
    parser.add_argument('output_file', metavar='output_file', type=str,
                        help='''Complete path for the output file containing 
                                stats (will be overwritten if it exists).'''
                        )
    parser.add_argument('--wn', action='store_true',
                        help='''(Optional) WNx development mode. This will 
                                output additional information useful in 
                                development of the WNx statistic.'''
                        )
    parser.add_argument('--top_lt1', metavar='N', type=int,
                        help='''(Optional) Number of top played low tier tanks 
                                used to calculate games played in low tiers 
                                for the first output field. This only 
                                functions when used with the --wn flag.'''
                        )
    parser.add_argument('--top_lt2', metavar='N', type=int,
                        help='''(Optional) Number of top played low tier tanks 
                                used to calculate games played in low tiers 
                                for the second output field. This only 
                                functions when used with the --wn flag.'''
                        )
    parser.add_argument('--server', metavar='S', type=str,
                        help ='''(Optional) Server to request statistics from. 
                                Valid options are NA, RU, EU, ASIA, KR. 
                                Defaults to NA.'''
                        )
    parser.add_argument('--tank_list', action='store_true',
                        help= '''(Optional) Outputs a list of tank ID -> tank 
                                name mappings. Input file will be ignored 
                                when this flag is specified.'''
                        )
    args = parser.parse_args()
    
    if (args.server):
        if (args.server in REQ_BASE_URLS):
            _req_server = args.server
        else:
            print(''.join([args.server, 
                           ' is not a valid server.',
                           ' Defaulting to NA server.'
                           ]))
    
    if args.wn:
        _wn = True
        
        if args.top_lt1:
            _top_low_tiers1 = args.top_lt1
        if args.top_lt2:
            _top_low_tiers2 = args.top_lt2
    
    if args.tank_list:
        #Get the tank list
        create_tank_list_csv(args.output_file)
    else:
        # Get the stats
        create_user_stats_csv(args.input_file, args.output_file)
    
    