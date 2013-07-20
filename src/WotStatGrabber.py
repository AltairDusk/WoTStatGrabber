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

REQ_SOURCE_TOKEN = 'WG-WoT_Assistant-1.3.2'
USER_ID_REQ_OFFSET = '0'
USER_ID_REQ_LIMIT = '1'
USER_ID_REQ_URL = 'http://api.worldoftanks.com/uc/accounts/api/1.1/?{params}'
USER_STATS_REQ_URL = ('http://api.worldoftanks.com/uc/accounts/'
                      '{id}/api/1.9/?{params}')


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


def request_user_id(user_name):
    """Get the user ID from WG API given user name

    Keyword arguments:
    userName -- user to look up

    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({
        'source_token': REQ_SOURCE_TOKEN,
        'search': user_name,
        'offset': USER_ID_REQ_OFFSET,
        'limit': USER_ID_REQ_LIMIT
        })
    urlstring = USER_ID_REQ_URL.format(params=parameters)
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()

    # Parse the JSON and get the user ID after
    # making sure we've found the correct user.
    userInfo = json.loads(response.read().decode(encoding))
    items = userInfo['data']['items']
    if len(items) > 1:
        raise PlayerNotFoundError(user_name, 'Multiple players found')
    # Usernames are not case-sensitive for API requests
    elif not items or items[0]['name'].lower() != user_name.lower():
        raise PlayerNotFoundError(user_name, 'Player was not found')
    else:
        user_id = items[0]['id']

    return user_id


def request_user_stats(user_id):
    """Get the user statistics from WG API given user ID

    Keyword arguments:
    user_id -- user to look up

    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({'source_token': REQ_SOURCE_TOKEN})
    urlstring = USER_STATS_REQ_URL.format(id=str(user_id), params=parameters)
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()

    # Parse and return the JSON after checking for errors
    user_info = json.loads(response.read().decode(encoding))
    if user_info['status'] != 'ok':
        raise PlayerNotFoundError(user_id, user_info['status_code'])
    else:
        stats = user_info['data']
    return stats


def prepare_output_row(user_stats, user_id):
    """Build a dictionary with the relevant stats

    Keyword arguments:
        user_stats -- user stat information loaded from json
        user_id -- user ID number

    """

    ratings = user_stats['ratings']
    stats_row = {}

    # Add user identifying information
    stats_row['name'] = user_stats['name']
    stats_row['id'] = user_id

    # Add the basic stat information
    battles = ratings['battles']['value']
    stats_row['battles'] = battles
    stats_row['tot_xp'] = ratings['xp']['value']
    stats_row['avg_xp'] = ratings['battle_avg_xp']['value']

    # Add calculated stat information
    spots = ratings['spotted']['value']
    stats_row['tot_spots'] = spots
    stats_row['avg_spots'] = spots / battles
    
    kills = ratings['frags']['value']
    stats_row['tot_kills'] = kills
    stats_row['avg_kills'] = kills / battles
    
    damage = ratings['damage_dealt']['value']
    stats_row['tot_dmg'] = damage
    stats_row['avg_dmg'] = damage / battles

    wins = ratings['battle_wins']['value']
    stats_row['wins'] = wins
    stats_row['win_pct'] = (wins / battles) * 100

    avg_tier_info = calc_tier_info(user_stats, battles)
    stats_row['avg_tier'] = avg_tier_info['avg_tier']
    stats_row['vehicle_battles'] = avg_tier_info['vehicle_battles']
    stats_row['battles_top3_low_tiers'] = avg_tier_info['top3_low_battles']

    return stats_row


def calc_tier_info(user_stats, battles):
    """Calculates the average tier and other tier-based
    information given a set of user statistics

    Keyword arguments:
        user_stats -- user stat information loaded from json
        battles -- total battles for this user

    """
    
    tier_info = {}
    tier_info['vehicle_battles'] = 0
    tier_info['avg_tier'] = 0
    low_tiers = []

    # Spin through all vehicles and calculate battle/tier info
    for vehicle in user_stats['vehicles']:
        tier = vehicle['level']
        vehicle_battles = vehicle['battle_count']
        tier_info['vehicle_battles'] += vehicle_battles
        tier_info['avg_tier'] += (tier / battles) * vehicle_battles
        
        if tier <= 3:
            low_tiers.append(vehicle_battles)
            
    tier_sum = 0
    for tier in sorted(low_tiers, reverse=True)[:5]:
        tier_sum += tier
    tier_info['top3_low_battles'] = tier_sum / 3
    
    return tier_info
    
    
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
        'tot_dmg', 'avg_dmg', 'wins',
        'win_pct', 'avg_tier', 'vehicle_battles',
        'battles_top3_low_tiers'
        ]
    
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
                

if __name__ == '__main__':
    # Parse the arguments
    parser = argparse.ArgumentParser(description = 'Retrieve and output WoT User Statistics.')
    parser.add_argument('input_file', metavar='input_file', type=str, 
                        help='Complete path to a file containing the names to retrieve stats for (one name per line).'
                        )
    parser.add_argument('output_file', metavar='output_file', type=str,
                        help='Complete path for the output file containing stats (will be overwritten if it exists).'
                        )
    args = parser.parse_args()
    
    # Get the stats
    create_user_stats_csv(args.input_file, args.output_file)
    
    