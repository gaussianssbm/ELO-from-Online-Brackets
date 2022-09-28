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
head2head_sets  = open('database_head2heads.csv', 'w+')
head2head_games = open('database_head2heads_games.csv', 'w+')
head2head_sets_writer  = csv.writer(head2head_sets)
head2head_games_writer = csv.writer(head2head_games)

smash = pysmashgg.SmashGG(authToken, True)

client = GraphQLClient('https://api.start.gg/gql/alpha')
client.inject_token('Bearer ' + authToken)
tournaments = json.load(open('tournaments.json')) #reads list of tournaments from .json file. Only URL is required, but name of tournament may be good for organizing the json file.
knownalts   = json.load(open('knownAlts.json'))
broke_tourneys = []
analyzed_tourneys = []
players = {}
for tourney in tournaments:
  if tourney in analyzed_tourneys:
    continue
  else:
    analyzed_tourneys.append(tourney)
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