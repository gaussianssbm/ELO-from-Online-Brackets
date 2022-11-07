class Player:
    def __init__(self, tag_init_lower, tag_init_cap, ID_init):
        self.tag          = tag_init_lower
        self.tag_cap      = tag_init_cap
        self.alts         = []
        self.tournaments  = []
        self.sets         = []
        self.startggID    = [ID_init]
        self.games_won    = 0
        self.games_lost   = 0
        self.sets_won     = 0
        self.sets_lost    = 0
        self.set_percent  = 0
        self.game_percent = 0
        self.elo          = 1500
        self.temp_elo     = 1500

    def update_gamecount(self, m_won, m_lost):
        self.games_won    = self.games_won  + m_won
        self.games_lost   = self.games_lost + m_lost
        self.game_percent = 100*(float(self.games_won)/float((self.games_won + self.games_lost)))

    def update_setcount(self, m_win_loss):
        if m_win_loss == 'win':
            self.sets_won    = self.sets_won  + 1
        elif m_win_loss == 'loss':
            self.sets_lost   = self.sets_lost + 1
        else:
            print(f"Unknown update_setcount input for player {Player.tag}")
        self.set_percent = 100*(float(self.sets_won)/float((self.sets_won + self.sets_lost)))

    def add_tournament(self, m_tournament):
        self.tournaments.append(m_tournament)

    def get_ELO(self):
        return self.elo
  
    def set_ELO(self, elo):
        self.elo = elo

    def get_tempELO(self):
        return self.temp_elo
  
    def set_tempELO(self, temp_elo):
        self.temp_elo = temp_elo





class Tournament:
    def weight_k_calc(self, weight_str, tourney_k_dict = {}):
        if weight_str == 'local_lite':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 0.25
        elif weight_str == 'local':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 0.5
        elif weight_str == 'local_weekend':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 1.0
        elif weight_str == 'monthly':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 1.0
        elif weight_str == 'regional':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 1.5
        elif weight_str == 'major':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 2.0
        elif weight_str == 'amature':
            if weight_str in tourney_k_dict.keys():
                if type(tourney_k_dict[weight_str]) == float or type(tourney_k_dict[weight_str]) == int:
                    return tourney_k_dict[weight_str]
            return 0.1
        else:
            return 0.0

    def __init__(self, name, date, url, placements, weight = 'local', tourney_k_dict = {}):
        self.name       = name
        self.date       = date
        self.url        = url
        self.placements = placements
        self.weight     = weight
        self.weight_k   = self.weight_k_calc(weight, tourney_k_dict)

    def get_weight_k(self):
        return self.weight_k



class Set:
    def __init__(self, entrant1, entrant2, entrant1Score, entrant2Score, roundName):
        self.entrant1 = entrant1
        self.entrant2 = entrant2
        self.entrant1score = entrant1Score
        self.entrant2score = entrant2Score
        self.round         = roundName

  


def ELO_exchange(Player1, Player2, tournament_weight_k, winner, update_immediately = True):
    E_1 = 1/(1 + 10**((Player2.get_ELO() - Player1.get_ELO())/400))
    E_2 = 1/(1 + 10**((Player1.get_ELO() - Player2.get_ELO())/400))
    if winner == Player1:
        Player1.set_tempELO(Player1.get_ELO() + tournament_weight_k*(1 - E_1))
        Player2.set_tempELO(Player2.get_ELO() + tournament_weight_k*(0 - E_2))
    elif winner == Player2:
        Player1.set_tempELO(Player1.get_ELO() + tournament_weight_k*(0 - E_1))
        Player2.set_tempELO(Player2.get_ELO() + tournament_weight_k*(1 - E_2))
    if update_immediately:
        Player1.set_ELO(Player1.get_tempELO())
        Player2.set_ELO(Player2.get_tempELO())
    return 1


def read_custom_tournament_weights():
    import json
    import os
    if os.path.exists('custom_tournament_weights.json'):
        if os.stat('custom_tournament_weights.json').st_size != 0:
            return json.load(open('custom_tournament_weights.json'))
        else:
            return {}
    else:
        return {}

def get_ordered_results(event_id, authToken, alt_tag_dict_list):
    import re
    from graphqlclient import GraphQLClient
    client = GraphQLClient('https://api.start.gg/gql/alpha')
    client.inject_token('Bearer ' + authToken)
    result = client.execute('''
    query EventStandings($eventId: ID!, $page: Int!, $perPage: Int!) {
        event(id: $eventId) {
        standings(query: {
            perPage: $perPage,
            page: $page
        }){
            nodes {
            placement
            entrant {
                name
            }
            }
        }
        }
    }''',
    {
        "eventId": event_id,
        "page": 1,
        "perPage": 499
    })
    result = str(result).replace('"data":{"event":{"standings":{"nodes":[{', '')
    result = result.replace('{"placement":','')
    result = result.replace(',"entrant":{"name":"','. ')
    result = result.replace('"}}',''); result = result.replace(',',' ; ')
    result = result.split(']}}}')[0]
    result = result.split(' ; ')
    for zz, placer in enumerate(result):
        placer_tmp = re.sub(r'^(\d+?)\.\s', '',placer.split(' | ')[-1].strip().lower())
        if placer_tmp in [alt_t["Alt"].lower() for alt_t in alt_tag_dict_list]:
            placer_tmp = alt_tag_dict_list[[alt_t["Alt"].lower() for alt_t in alt_tag_dict_list].index(placer_tmp)]["Tag"]
            placer = str(zz + 1) + '. ' + placer_tmp
        else:
            placer = placer.strip()
        result[zz] = placer
    result = ' ; '.join(result)
    return result