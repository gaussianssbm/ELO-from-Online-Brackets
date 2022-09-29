import sys
import time
from datetime import datetime
import pysmashgg
import csv
import json
import urllib.request as urllib2
from graphqlclient import GraphQLClient
import codecs
import pandas as pd

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
  result = str(result).replace('"data":{"event":{"standings":{"nodes":[{', '')
  result = result.replace('{"placement":','')
  result = result.replace(',"entrant":{"name":"','. ')
  result = result.replace('"}}',''); result = result.replace(',',' ; ')
  result = result.split(']}}}')[0]
  return result

# authToken = open('9292bda8f96a5b1f2f425c546de5ae92').read() #BE SURE TO ENTER YOUR AUTHTOKEN FROM START.GG
authFile = open('auth_token.txt')
authToken = authFile.read()
authFile.close()
apiVersion = 'alpha'

#Make csv files that will be the output for data
tourn_database  = open('database_tournaments.csv', 'w+')
tourn_writer    = csv.writer(tourn_database); tourn_writer.writerow(['Tournament Name', 'Date', 'Number of Entrants', 'Tournament URL', 'Top-8'])
player_database = open('database_players.csv', 'w+')
player_writer   = csv.writer(player_database); player_writer.writerow(['Tag', 'Known Alts', 'Tournament: Placing'])
head2head_sets  = open('database_head2heads.csv', 'w+') #work in progress
head2head_games = open('database_head2heads_games.csv', 'w+') #work in progress
head2head_sets_writer  = csv.writer(head2head_sets)
head2head_games_writer = csv.writer(head2head_games)

#initalize pysmashgg (if you're reading this, go thank ETossed) and API client
smash = pysmashgg.SmashGG(authToken, True)
client = GraphQLClient('https://api.start.gg/gql/alpha')
client.inject_token('Bearer ' + authToken)
tournaments = json.load(open('tournaments.json')) #reads list of tournaments from .json file. Only URL is required, but name of tournament may be good for organizing the json file.
knownalts   = json.load(open('knownAlts.json'))
alt_tags = [alt_dict["Alt"].lower() for alt_dict in knownalts]
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
      # print(knownalts)
      if (set['completed'] and set['entrant1Score'] >= 0 and set['entrant2Score'] >= 0):
        # print(set)
        # print(entrant1)
        if (entrant1 == None or entrant2 == None):
          continue
        if entrant1 not in players.keys():
          if entrant1 not in alt_tags:
            players[entrant1] = [] #Thinking about what best to put here! 9/23/22
          elif entrant1 in alt_tags:#tag is a known alt, check if actual player is in the database already:
            for knowntag_dict in knownalts: #THERE'S got to be a more efficient way to do this, but my brain is tired :)
              if entrant1 == knowntag_dict["Alt"].lower():
                if knowntag_dict["Tag"] not in players:
                  # print(knowntag_dict["Tag"])
                  # print(knowntag_dict["Alt"])
                  players[knowntag_dict["Tag"].lower()] = []
          else:
            print(f"DID NOT KNOW HOW TO PROCESS PLAYER {entrant1} FOR TOURNAMENT {tourn_w_brack['name']}")

        if entrant2 not in players.keys():
          if entrant2 not in alt_tags:
            players[entrant2] = [] #Thinking about what best to put here! 9/23/22
          elif entrant2 in alt_tags:#tag is a known alt, check if actual player is in the database already:
            for knowntag_dict in knownalts: #THERE'S got to be a more efficient way to do this, but my brain is tired :)
              if entrant2 == knowntag_dict["Alt"].lower():
                if knowntag_dict["Tag"] not in players:
                  players[knowntag_dict["Tag"].lower()] = []
          else:
            print(f"DID NOT KNOW HOW TO PROCESS PLAYER {entrant2} FOR TOURNAMENT {tourn_w_brack['name']}")