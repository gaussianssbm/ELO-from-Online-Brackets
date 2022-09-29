# UNDER DEVELOPMENT! Please contact gaussianssbm@gmail.com with any questions until further notice!
Will update and maintain an ELO score base of players based on results imported from supplied start.gg tournament URL's.

## Intro:
tourney_import.py is a python file that can be run to process information from a list of tournaments in 'tournaments.json'. Known player alt tags / smurf tags can be accounted for in 'knownAlts.json'. Python is required to run the 'tourney_import.py' file, as well as the python packages: pysmashgg, csv, json, urllib, graphqlclient, and pandas.

## tourney_import.py Output:
The output of running this script is 4 .csv files: a general tournament database from the input tournamnets "database_players.csv" **(Under Construction)**, a general database of players "database_players.csv" **(Under Construction)**, and two head-to-head result tables for set counts "database_head2heads_sets.csv" (Under Construction) and game counts "database_head2heads_games.csv" **(Under Construction)**.

## Tournament input deck format (tournaments.json)
- The format for inputs to 'tournaments.json' is below. Each tournament must be in curly {} brackets, and the file begins with and ends with square [] brackets. A comma is required after every set of curly {} brackets EXCEPT the last one. 
- The code only requires the URL to the details page of each tournament; for example: https://www.start.gg/tournament/meat-40/details **HOWEVER** it is **STRONGLY** recommended including the name for your own readability and the weight of the tournament ('local-lite', 'local', 'local-weekend', 'regional', 'major') for ranking algorithm purposes **(UNDER CONSTRUCTION)**.   
- A comma is required acter every key: value pair except for the final one in the curly {} brackets. This is read as a list of python dictionaries in the code. Instead of URL, tournament slug may be provided (refer to start.gg api documentation).  
**EXAMPLE:**  
[  
&emsp; {  
&emsp; &emsp; "name": "MEAT 40",  
&emsp; &emsp; "slug": "meat-40",  
&emsp; &emsp; "url": "https://www.start.gg/tournament/meat-40/details",  
&emsp; &emsp; "weight": "local"  
&emsp; },  
&emsp; {  
&emsp; &emsp; "name": "MEAT 39",  
&emsp; &emsp; "slug": "meat-39",  
&emsp; &emsp; "url": "https://www.start.gg/tournament/meat-39/details",  
&emsp; &emsp; "weight": "local"  
&emsp; },  
&emsp; {  
&emsp; &emsp; "name": "MEAT 38",  
&emsp; &emsp; "url": "https://www.start.gg/tournament/meat-38/details",  
&emsp; &emsp; "weight": "local"  
&emsp; }  
]  

## Known alt tags input deck format (knownAlts.json)
- The format for the inputs to 'knownAlts.json' is below. Each alt/tag set must be in curly {} brackets, and the file begins with and ends with square [] brackets. A comma is required after every set of curly {} brackets EXCEPT the last one.  
- Each entry needs a "Tag" defined and an "Alt" defined, as exampled below. A comma is required acter every key: value pair except for the final one in the curly {} brackets. This is read as a list of python dictionaries in the code.  
**Example:**  
[  
&emsp; {  
&emsp; &emsp; "Tag": "Prince Abu",  
&emsp; &emsp; "Alt": "Dennis Reynolds"  
&emsp; },  
&emsp; {  
&emsp; &emsp; "Tag":"Kuyashi",  
&emsp; &emsp; "Alt":"Gaymook"  
&emsp; }  
] 

