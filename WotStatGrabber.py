import csv
import json
import urllib.request

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


def request_user_id(userName):
    """Get the user ID from WG API given user name

    Keyword arguments:
    userName -- user to look up

    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({
        'source_token': REQ_SOURCE_TOKEN,
        'search': userName,
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
        raise PlayerNotFoundError(userName, 'Multiple players found')
    # Usernames are not case-sensitive for API requests
    elif len(items) == 0 or items[0]['name'].lower() != userName.lower():
        raise PlayerNotFoundError(userName, 'Player was not found')
    else:
        userID = items[0]['id']

    return userID


def request_user_stats(userID):
    """Get the user statistics from WG API given user ID

    Keyword arguments:
    userID -- user to look up

    """

    # Build the URL and make the request to WG API.
    parameters = urllib.parse.urlencode({'source_token': REQ_SOURCE_TOKEN})
    urlstring = USER_STATS_REQ_URL.format(id=str(userID), params=parameters)
    response = urllib.request.urlopen(urlstring)
    encoding = response.headers.get_content_charset()

    # Parse and return the JSON after checking for errors
    userInfo = json.loads(response.read().decode(encoding))
    if userInfo['status'] != 'ok':
        raise PlayerNotFoundError(userID, userInfo['status_code'])
    else:
        stats = userInfo['data']
    return stats


def prepare_output_row(userStats, userID):
    """Build a dictionary with the relevant stats

    Keyword arguments:
        userStats -- user stat information loaded from json
        userID -- user ID number

    """

    ratings = userStats['ratings']
    statsRow = {}

    # Add user identifying information
    statsRow['name'] = userStats['name']
    statsRow['id'] = userID

    # Add the basic stat information
    battles = ratings['battles']['value']
    statsRow['battles'] = battles
    statsRow['tot_xp'] = ratings['xp']['value']
    statsRow['avg_xp'] = ratings['battle_avg_xp']['value']

    # Add calculated stat information
    spots = ratings['spotted']['value']
    statsRow['tot_spots'] = spots
    statsRow['avg_spots'] = spots / battles
    
    kills = ratings['frags']['value']
    statsRow['tot_kills'] = kills
    statsRow['avg_kills'] = kills / battles
    
    damage = ratings['damage_dealt']['value']
    statsRow['tot_dmg'] = damage
    statsRow['avg_dmg'] = damage / battles

    wins = ratings['battle_wins']['value']
    statsRow['wins'] = wins
    statsRow['win_pct'] = (wins / battles) * 100

    avgTierInfo = calc_tier_info(userStats, battles)
    statsRow['avg_tier'] = avgTierInfo['avg_tier']
    statsRow['vehicle_battles'] = avgTierInfo['vehicle_battles']
    statsRow['battles_top3_low_tiers'] = avgTierInfo['top3_low_battles']

    return statsRow


def calc_tier_info(userStats, battles):
    """Calculates the average tier and other tier-based
    information given a set of user statistics

    Keyword arguments:
        userStats -- user stat information loaded from json
        battles -- total battles for this user

    """
    tierInfo = {}
    tierInfo['vehicle_battles'] = 0
    tierInfo['avg_tier'] = 0
    lowTiers = []

    # Spin through all vehicles and calculate battle/tier info
    for vehicle in userStats['vehicles']:
        tier = vehicle['level']
        vehicleBattles = vehicle['battle_count']
        tierInfo['vehicle_battles'] += vehicleBattles
        tierInfo['avg_tier'] += (tier / battles) * vehicleBattles
        
        if tier <= 3:
            lowTiers.append(vehicleBattles)
            
    tierSum = 0
    for tier in sorted(lowTiers, reverse=True)[:3]:
        tierSum += tier
    tierInfo['top3_low_battles'] = tierSum / 3
    
    return tierInfo
    
    
def create_user_stats_csv(inputFile, outputFile):
    """Gets the statistics for names in inputFile and writes
    the results in csv format to outputFile
    
    Keyword arguments:
        inputFile -- File with a complete username on each line
        outputFile -- CSV file that will be created with results
        
    """
    
    fieldnames = [
        'name', 'id', 'battles',
        'tot_xp', 'avg_xp', 'tot_spots', 
        'avg_spots', 'tot_kills', 'avg_kills',
        'tot_dmg', 'avg_dmg', 'wins',
        'win_pct', 'avg_tier', 'vehicle_battles',
        'battles_top3_low_tiers'
        ]
    
    with open(inputFile, encoding='utf-8') as namesFile:
        with open(outputFile, 'w', newline='') as csvFile:
            output = csv.DictWriter(csvFile, fieldnames, dialect='excel', 
                                    extrasaction='ignore'
                                    )
            output.writeheader()
            
            while True:
                name = namesFile.readline()
                if len(name) == 0:
                    break
                    
                # Get stats for this user and prepare them for output
                id = request_user_id(name.strip())
                stats = request_user_stats(id)
                row = prepare_output_row(stats, id)
                
                # Output stats to CSV
                output.writerow(row)
                
