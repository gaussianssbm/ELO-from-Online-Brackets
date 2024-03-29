import os
import re
import sys
import time
import json
import pysmashgg
import pandas as pd
from datetime import datetime
from graphqlclient import GraphQLClient

import gaussheet_funcs

def main():
    # authFile = open('auth_token.txt')
    # authToken = authFile.read()
    # authFile.close()
    for ii, line in enumerate(open('auth_token.txt')):
        if re.search('startgg', line):
            authToken_startgg = re.search('.*?\s+([\S]+)', str(line)).group(1)
        if re.search('challonge', line):
            authToken_challonge = re.search('.*?\s+([\S]+)', str(line)).group(1)

    #initalize pysmashgg (if you're reading this, go thank ETossed) and API client
    apiVersion = 'alpha'
    smash = pysmashgg.SmashGG(authToken_startgg, True)
    client = GraphQLClient('https://api.start.gg/gql/alpha')
    client.inject_token('Bearer ' + authToken_startgg)

    tournaments_input = json.load(open('tournaments.json')) #reads list of tournaments from .json file. Only URL is required, but name of tournament may be good for organizing the json file.
    knownalts   = json.load(open('knownAlts.json'))
    custom_tournament_weights = gaussheet_funcs.read_custom_tournament_weights()
    api_calls = 0
    broke_tourneys = []
    analyzed_tourneys = []
    players     = {}
    tournaments = []
    tourn_placement_list = []; tourn_date_list = []; tourn_name_list = []; tourn_size_list = []; tourn_url_list = []; tourn_event_list = []
    if os.path.exists('database_tournaments.csv'):
        known_database = pd.read_csv('database_tournaments.csv',sep=',', header = None, nrows = 3 )
    players_h2hsets_df  = pd.DataFrame()
    players_h2hgames_df = pd.DataFrame()
    #sort list in sequential order:
    new_tournament = False
    for tourney in tournaments_input:
        if 'slug' in tourney.keys():
            if 'url' not in tourney.keys():
                tourney['url'] = f"start.gg/tournament/{tourney['slug']}/details"
        elif 'url' in tourney.keys():
            # if 'slug' not in tourney.keys():
            slug1 = tourney['url'].split("tournament/")[1].split("/")[0]
            tourney["slug"] = slug1
        all_events = smash.tournament_show_events(tourney['slug'])
        api_calls += 1
        kept_events = []
        for event in all_events:
            if "Melee Singles" in event['name']:
                kept_events.append(event)
        tourney['events'] = kept_events
        tourn_w_brack = smash.tournament_show_with_brackets(tourney['slug'], kept_events[0])
        # tourney['tourn_w_bracket']
        # print(tourn_w_bracket)
        tourney['timestamp'] = tourn_w_brack['startTimestamp']
        # tourney['timestamp'] = int(tourn_w_brack["startTimestamp"])
    # print(tournaments_input)
    # return 0
    tournaments_input = sorted(tournaments_input, key=lambda d: d['timestamp']) 
    # print(tournaments_input)
    for zz, tourney in enumerate(tournaments_input):

    ###Tournaments Loop
        for event in tourney['events']:
            i = 0
            sets = ["dummmy"]
            while (sets != []):
                i += 1
                try:
                    sets  = smash.tournament_show_sets(tourney['slug'], event['slug'], i)
                    api_calls += 1
                except (TypeError, IndexError) as e:
                    broke_tourneys.append(tourney)
                    print("Broken, Index Error or Type Error")
                    with open('errors.txt', 'a+') as errors:
                        errors.write(tourney)
                        errors.write('\n')
                        break

                if i == 1:
                    #print tournament stats the first time the tournament is looped over
                    tourn_w_brack = smash.tournament_show_with_brackets(tourney['slug'], event['name'])
                    api_calls += 1
                    date = str(datetime.utcfromtimestamp(int(tourn_w_brack["startTimestamp"]))).split(' ')[0]
                    if new_tournament == False:
                        print(known_database.loc[0,zz])
                        print(known_database.loc[1,zz])
                        if tourn_w_brack['name'] == known_database.loc[0,zz] and event['name'] == known_database.loc[1, zz] and date == known_database.loc[2,zz]:
                            print(f"Skipping Tournament {tourn_w_brack['name']}, {event['name']}: already analyzed.")
                            break
                        else:
                            new_tournament = True
                    print(f"Analyzing Tournament {tourn_w_brack['name']}, {event['name']}...")
                    
                    placements = gaussheet_funcs.get_ordered_results(event["id"], authToken, alt_tag_dict_list=knownalts)
                    api_calls += 1
                    tourn_placement_list.append([placements]); tourn_date_list.append(date); tourn_url_list.append(tourney['url']); tourn_name_list.append(tourn_w_brack["name"]); tourn_size_list.append(f"Number of Entrants: {tourn_w_brack['entrants']}"); tourn_event_list.append(event['name'])
                    tournaments.append(gaussheet_funcs.Tournament(tourn_w_brack['name'], event['name'], date, tourney['url'], placements, tourney['weight'], custom_tournament_weights))
                # if (i % 6 == 0):
                sleeptime = 2.5
                time.sleep(sleeptime) # Might be able to remove, but idk, just not to time out API


            for set in sets:
                entrant1_cap = set['entrant1Players'][0]['playerTag'].split(' | ')[-1].strip()
                entrant1 = entrant1_cap.lower()
                entrant2_cap = set['entrant2Players'][0]['playerTag'].split(' | ')[-1].strip()
                entrant2 = entrant2_cap.lower()


                if (set['completed'] and set['entrant1Score'] >= 0 and set['entrant2Score'] >= 0):
                    if (entrant1 == None or entrant2 == None):
                        continue
                    #Checks if player is not an alt tag, and then if player has been seen before. Inializes player object and panda head2head sheet row/col if first time seeing them.
                    #If seen this player before, just a few checks to see if this player has used an alt before or not and adds player values appropriately.
                    if entrant1 not in [alt_t["Alt"].lower() for alt_t in knownalts]:# entrant1 not in alt_tags:
                        
                        if not entrant1 in players.keys():
                            players[entrant1] = gaussheet_funcs.Player(tag_init_lower= entrant1, tag_init_cap= entrant1_cap, ID_init= set['entrant1Players'][0]['playerId'])
                            players_h2hgames_df[entrant1] = "0-0"; players_h2hgames_df.loc[entrant1] = "0-0"
                            players_h2hsets_df[entrant1]  = "0-0"; players_h2hsets_df.loc[entrant1]  = "0-0"
                            players_h2hgames_df.at[entrant1, entrant1] = "X";players_h2hsets_df.at[entrant1, entrant1] = "X"

                        else:    
                            if players[entrant1].tag_cap != entrant1_cap:
                                players[entrant1].tag_cap = entrant1_cap 
                            if set['entrant1Players'][0]['playerId'] not in players[entrant1].startggID:
                                players[entrant1].startggID.append(set['entrant1Players'][0]['playerId'])

                    elif entrant1 in [alt_t["Alt"].lower() for alt_t in knownalts]:
                        alt_indx = [alt_t["Alt"].lower() for alt_t in knownalts].index(entrant1)
                        entrant1 = knownalts[alt_indx]["Tag"].lower()

                        if not entrant1 in players.keys():# [p.tag for p in players]:#if not any(p.tag == entrant1 for p in players):  
                            players[entrant1] = gaussheet_funcs.Player(tag_init_lower= entrant1, tag_init_cap= entrant1, ID_init= set['entrant1Players'][0]['playerId'])
                            players[entrant1].alts.append(entrant1_cap.lower())
                            players_h2hgames_df[entrant1] = "0-0"; players_h2hgames_df.loc[entrant1] = "0-0"
                            players_h2hsets_df[entrant1]  = "0-0"; players_h2hsets_df.loc[entrant1]  = "0-0"
                            players_h2hgames_df.at[entrant1, entrant1] = "X";players_h2hsets_df.at[entrant1, entrant1] = "X"

                        else:
                            if not set['entrant1Players'][0]['playerId'] in players[entrant1].startggID:
                                players[entrant1].startggID.append(set['entrant1Players'][0]['playerId'])

                            if not entrant1_cap.lower() in players[entrant1].alts:
                                players[entrant1].alts.append(entrant1_cap.lower())

                    else:
                        print(f"DID NOT KNOW HOW TO PROCESS PLAYER {entrant1} FOR TOURNAMENT {tourn_w_brack['name']}")

                    if entrant2 not in [alt_t["Alt"].lower() for alt_t in knownalts]:# entrant2 not in alt_tags:
            
                        if not entrant2 in players.keys():#[p.tag for p in players]:#if not any(player.tag == entrant2 for player in players): #First time seeing entrant1. Initalize row in pandas dataframes.
                            players[entrant2] = gaussheet_funcs.Player(tag_init_lower= entrant2, tag_init_cap= entrant2_cap, ID_init= set['entrant2Players'][0]['playerId'])
                            players_h2hgames_df[entrant2] = "0-0"; players_h2hgames_df.loc[entrant2] = "0-0"
                            players_h2hsets_df[entrant2]  = "0-0"; players_h2hsets_df.loc[entrant2]  = "0-0"
                            players_h2hgames_df.at[entrant2, entrant2] = "X"; players_h2hsets_df.at[entrant2, entrant2] = "X"
            
                        else:
                            if players[entrant2].tag_cap != entrant2_cap:
                                players[entrant2].tag_cap = entrant2

                            if set['entrant2Players'][0]['playerId'] not in players[entrant2].startggID:
                                players[entrant2].startggID.append(set['entrant2Players'][0]['playerId'])

                    elif entrant2 in [alt_t["Alt"].lower() for alt_t in knownalts]:# any([entrant2 == alt_t["Alt"] for alt_t in knownalts]):#tag is a known alt, check if actual player is in the database already:
                        alt_indx = [alt_t["Alt"].lower() for alt_t in knownalts].index(entrant2)
                        entrant2 = knownalts[alt_indx]["Tag"].lower()
            
                        if not entrant2 in players.keys():# [p.tag for p in players]:# any(p.tag == entrant1 for p in players):
                            players[entrant2] = gaussheet_funcs.Player(tag_init_lower= entrant2, tag_init_cap= entrant2, ID_init= set['entrant2Players'][0]['playerId'])
                            players[entrant2].alts.append(entrant2_cap.lower())
                            players_h2hgames_df[entrant2] = "0-0"; players_h2hgames_df.loc[entrant2] = "0-0"
                            players_h2hsets_df[entrant2]  = "0-0"; players_h2hsets_df.loc[entrant2]  = "0-0"
                            players_h2hgames_df.at[entrant2, entrant2] = "X"; players_h2hsets_df.at[entrant2, entrant2] = "X"
            
                        else:
                            if not set['entrant2Players'][0]['playerId'] in players[entrant2].startggID:
                                players[entrant2].startggID.append(set['entrant2Players'][0]['playerId'])

                            if not entrant2_cap.lower() in players[entrant2].alts:
                                players[entrant2].alts.append(entrant2_cap.lower())

                    else:
                        print(f"DID NOT KNOW HOW TO PROCESS PLAYER {entrant2} FOR TOURNAMENT {tourn_w_brack['name']}")
                    # print(set)
                    # sys.exit()
                    players[entrant1].update_gamecount(int(set['entrant1Score']), int(set['entrant2Score']))
                    players[entrant2].update_gamecount(int(set['entrant2Score']), int(set['entrant1Score']))
                    players[entrant1].add_tournament(tourney)
                    players[entrant2].add_tournament(tourney)


                    players_h2hgames_df.at[entrant1, entrant2] = f"{int(str(players_h2hgames_df.loc[entrant1, entrant2]).split('-')[0]) + int(set['entrant1Score'])}-{int(str(players_h2hgames_df.loc[entrant1, entrant2]).split('-')[1]) + int(set['entrant2Score'])}"; 
                    players_h2hgames_df.at[entrant2, entrant1] = f"{int(str(players_h2hgames_df.loc[entrant2, entrant1]).split('-')[0]) + int(set['entrant2Score'])}-{int(str(players_h2hgames_df.loc[entrant2, entrant1]).split('-')[1]) + int(set['entrant1Score'])}"

                    if set['entrant1Score'] > set['entrant2Score']:
                        players_h2hsets_df.at[entrant1, entrant2] = f"{int(str(players_h2hsets_df.loc[entrant1, entrant2]).split('-')[0]) + 1}-{int(str(players_h2hsets_df.loc[entrant1, entrant2]).split('-')[1])}"; 
                        players_h2hsets_df.at[entrant2, entrant1] = f"{int(str(players_h2hsets_df.loc[entrant2, entrant1]).split('-')[0])}-{int(str(players_h2hsets_df.loc[entrant2, entrant1]).split('-')[1]) + 1}"
                        players[entrant1].update_setcount('win')
                        players[entrant2].update_setcount('loss')
                        winner = players[entrant1]

                    elif set['entrant1Score'] < set['entrant2Score']:
                        players_h2hsets_df.at[entrant1, entrant2] = f"{int(str(players_h2hsets_df.loc[entrant1, entrant2]).split('-')[0])}-{int(str(players_h2hsets_df.loc[entrant1, entrant2]).split('-')[1]) + 1}"; 
                        players_h2hsets_df.at[entrant2, entrant1] = f"{int(str(players_h2hsets_df.loc[entrant2, entrant1]).split('-')[0]) + 1}-{int(str(players_h2hsets_df.loc[entrant2, entrant1]).split('-')[1])}"
                        players[entrant1].update_setcount('loss')
                        players[entrant2].update_setcount('win')
                        winner = players[entrant2]

                    gaussheet_funcs.ELO_exchange(players[entrant1], players[entrant2], tournaments[-1].get_weight_k(), winner, update_immediately=True)

    
    players_h2hgames_df.replace('0-0', '',inplace = True); 
    players_h2hgames_df.sort_index(inplace = True); players_h2hgames_df.sort_index(axis = 1, inplace = True)
    players_h2hgames_df.to_csv('database_head2heads_games.csv')
    players_h2hsets_df.replace('0-0', '', inplace = True); players_h2hsets_df.sort_index(inplace = True); 
    players_h2hsets_df.sort_index(axis = 1, inplace = True)
    players_h2hsets_df.to_csv('database_head2heads_sets.csv')

    tourn_pd = pd.DataFrame([tourn_name_list, tourn_event_list, tourn_date_list, tourn_url_list, tourn_size_list])
    tourn_placement_list = pd.DataFrame.from_dict({kk: [item.split(';')[ii] for item in tourn_placement_list[kk] for ii in range(item.count(';'))] for kk in range(len(tourn_name_list))},orient='index').transpose()
    tourn_pd = pd.concat([tourn_pd, tourn_placement_list], ignore_index=True)
    tourn_pd.to_csv('database_tournaments.csv',header=False, index=False)
    elo_file = open("player_elo.csv", "w", encoding = 'utf8')
    for tag, player in players.items():
    # print(f"Set win percentage for {player.tag} is {player.set_percent}")
    # print(f"Game win percentage for {player.tag} is {player.game_percent}")
        elo_file.write(f"{player.tag},{player.get_ELO()}\n")
    elo_file.close()
    print("Finished analyzing.")

if __name__ == "__main__":
    main()