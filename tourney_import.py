import sys
import time
from datetime import datetime
import pysmashgg
import csv
import json
import urllib.request as urllib2
from graphqlclient import GraphQLClient
import codecs

def get_top_8(event_id, authToken):
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
    "perPage": 8
  })
  # print(f'{result}\n\n')
  result = str(result).replace('"data":{"event":{"standings":{"nodes":[{', '')
  result = result.replace('{"placement":','')
  result = result.replace(',"entrant":{"name":"','. ')
  result = result.replace('"}}',''); result = result.replace(',',' ; ')
  result = result.split(']}}}')[0]
  return result

## Make sure to run `pip install graphqlclient`

authToken = None #BE SURE TO ENTER YOUR AUTHTOKEN FROM START.GG
apiVersion = 'alpha'


tourn_database  = open('database_tournaments.csv', 'w+')
tourn_writer    = csv.writer(tourn_database); tourn_writer.writerow(['Tournament Name', 'Date', 'Number of Entrants', 'Tournament URL', 'Top-8'])
player_database = open('database_players.csv', 'w+')
player_writer   = csv.writer(player_database); player_writer.writerow(['Tag', 'Known Alts', 'Tournament: Placing'])

smash = pysmashgg.SmashGG(authToken, True)

client = GraphQLClient('https://api.start.gg/gql/alpha')
client.inject_token('Bearer ' + authToken)
tournaments = json.load(open('tournaments.json'))
knownalts   = json.load(open('knownAlts.json'))
broke_tourneys = []
players = {}
for tourney in tournaments:
###Tournaments Loop
  i = 0
  sets = ["dummmy"]
  while (sets != []):
    i += 1
    try:
      if 'slug' in tourney.keys():
        #if slug is defined, use slug
        sets = smash.tournament_show_sets(tourney['slug'], 'melee-singles', i)
        # print(f"Slug defined: {sets}\n\n")
      else:
        #if url is only defined, use url to get slug
        slug1 = tourney['url'].split("tournament/")[1].split("/")[0]
        tourney["slug"] = slug1
        sets  = smash.tournament_show_sets(slug1, 'melee-singles', i)
    except (TypeError, IndexError) as e:
      broke_tourneys.append(tourney)
      print("Broken, Index Error or Type Error")
      with open('errors.txt', 'a+') as errors:
        errors.write(tourney)
        errors.write('\n')
        break
    if i == 1:
      tourn_w_brack = smash.tournament_show_with_brackets(tourney['slug'], 'melee-singles')
      date = str(datetime.utcfromtimestamp(int(tourn_w_brack["startTimestamp"]))).split(' ')[0]
      top8 = get_top_8(tourn_w_brack["eventId"], authToken)
      #print tournament stats the first time the tournament is looped over
      tourn_writer.writerow([tourn_w_brack["name"], date, tourn_w_brack["entrants"], tourney['url'], top8])
    if (i % 7 == 0):
      print("Sleeping")
      time.sleep(10) # Might be able to remove, but idk, just not to time out API
    for set in sets:
      entrant1 = set['entrant1Players'][0]['playerTag'].split(' | ')[-1].strip().lower()
      entrant2 = set['entrant2Players'][0]['playerTag'].split(' | ')[-1].strip().lower()
      
      if (set['completed'] and set['entrant1Score'] >= 0 and set['entrant2Score'] >= 0):
        if (entrant1 == None or entrant2 == None):
          continue
        if entrant1 not in players:
          if "Tag" in players:
            # if entrant1 CHECK IF ENTRANT1'S TAG IS IN THE KNOWN ALT LIST BEFORE ADDING IT TO THE PLAYERS LIST
            players["Tag"].append(entrant1)
          else:
            players["Tag"] = [entrant1]
        if entrant2 not in players:
          players["Tag"].append(entrant2)
        
        
      

      
    # print(sets)
#print(len(sets))
#print('\n')
#for ii, item in enumerate(sets):
#  print("Page = 1")
#  print(f"{ii+1} item in list is {item}\n")
#print('\n')
#print(len(sets))

#sets = smash.tournament_show_sets('meat-40', 'melee-singles', 2)
#for ii, item in enumerate(sets):
#  print("Page = 2")
#  print(f"{ii+1} item in list is {item}\n")
#print('\n')
#print(len(sets))





# results = smash.tournament_show_lightweight_results('meat-40', 'melee-singles', 1)
# print(results)

# print('\n\n\n')
# tournament_with_bracket = smash.tournament_show_with_brackets('meat-40', 'melee-singles')
# print(tournament_with_bracket)
# print(cr)
# seedMapping = []
# for index, row in enumerate(cr):
    # if index == 0: # skip the header row
        # continue
    # seedId = row[0] # check your columns!
    # seedNum = row[1] # check your columns!
    # seedMapping.append({
        # "seedId": seedId,
        # "seedNum": seedNum,
    # })
# client = GraphQLClient('https://api.start.gg/gql/alpha')
# client.inject_token('Bearer ' + authToken)
# result = client.execute('''
# query EventSets($eventId: slug!, $page: Int!, $perpage: Int!) {
#   event(id: $eventId) {
#     tournament {
#       name
#       id
#     }
#     name
#     id
#     sets(
#       page: $page
#       perpage: $perpage
#       sortType: STANDARD
#     ) {
#       pageInfo {
#         total
        
#       }
#       nodes {
#         id
#         displayScore
#         round
        
#         slots {
#           id
#           entrant {
#             id
#             name
            
#           }
#         }
#       }
#     }
#   }
# }''',
# {
#   "eventId":753036,
#   "page": 1,
#   "perPage": 5
# })
    
    #'''
# mutation UpdatePhaseSeeding ($phaseId: ID!, $seedMapping: [UpdatePhaseSeedInfo]!) {
#   updatePhaseSeeding (phaseId: $phaseId, seedMapping: $seedMapping) {
#     id
#   }
# }
# ''',
# {
#     "phaseId": phaseId,
#     "seedMapping": seedMapping,
# # })
# resData = json.loads(result)
# print(resData)
# if 'errors' in resData:
#     print('Error:')
#     print(resData['errors'])
# else:
#     print('Successfully Got Sets!')