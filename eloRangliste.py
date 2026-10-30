import json
import os
import csv
from collections import defaultdict
from datetime import datetime
from dateutil import parser

# Pfad zum Verzeichnis mit den heruntergeladenen Turnierdateien
tournaments_dir = './tournaments/'
output_csv_path = './elo_rangliste.csv'

# Initiale Elo-Bewertung
INITIAL_ELO = 1000
K_FACTOR = 32

# Funktion zur Berechnung der neuen Elo-Bewertung
def calculate_elo(player_elo, opponent_elo, result):
    expected_score = 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))
    return player_elo + K_FACTOR * (result - expected_score)

# Laden der Turnierdateien
tournament_files = [f for f in os.listdir(tournaments_dir) if f.endswith('.json')]

# Turnierdateien nach Datum sortieren
def get_tournament_date(file_name):
    file_path = os.path.join(tournaments_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        tournament_data = json.load(file)
    return parser.parse(tournament_data['createdAt'])

tournament_files.sort(key=get_tournament_date)

# Elo-Bewertungen für jeden Spieler in jeder Disziplin
elo_ratings = defaultdict(lambda: defaultdict(lambda: INITIAL_ELO))
games_played = defaultdict(lambda: defaultdict(int))
player_data = defaultdict(list)

# Funktion zur Initialisierung der Elo-Bewertung für Spieler
def initialize_elo(player, discipline):
    if discipline not in elo_ratings[player]:
        elo_ratings[player][discipline] = INITIAL_ELO

# Funktion zur Verarbeitung von Matches
def process_matches(matches, discipline, date):
    for match in matches:
        if 'team1' not in match or 'result' not in match:
            continue
        if match['team1'] is None or match['team2'] is None:
            continue
        
        team1 = [(player['_id'], player['name']) for player in match['team1']['players']]
        team2 = [(player['_id'], player['name']) for player in match['team2']['players']]
        result = match['result']
        
        if len(team1) == 2 and len(team2) == 2 and len(result) == 2:
            # Doppel
            (player1_team1, name1_team1), (player2_team1, name2_team1) = team1
            (player1_team2, name1_team2), (player2_team2, name2_team2) = team2
            result1, result2 = result
            
            # Initialisieren
            initialize_elo(name1_team1, discipline)
            initialize_elo(name2_team1, discipline)
            initialize_elo(name1_team2, discipline)
            initialize_elo(name2_team2, discipline)
            
            # Spiele zählen
            games_played[name1_team1][discipline] += 1
            games_played[name2_team1][discipline] += 1
            games_played[name1_team2][discipline] += 1
            games_played[name2_team2][discipline] += 1
            
            # Bestimme Gewinner
            if result1 > result2:
                team1_result, team2_result = 1, 0
            elif result1 < result2:
                team1_result, team2_result = 0, 1
            else:
                team1_result, team2_result = 0.5, 0.5
            
            # Speichere ELO VOR dem Match
            elo1_before = elo_ratings[name1_team1][discipline]
            elo2_before = elo_ratings[name2_team1][discipline]
            elo3_before = elo_ratings[name1_team2][discipline]
            elo4_before = elo_ratings[name2_team2][discipline]
            
            # Berechne durchschnittliche Elo
            team1_elo = (elo1_before + elo2_before) / 2
            team2_elo = (elo3_before + elo4_before) / 2
            
            # Berechne neue Elo
            new_team1_elo = calculate_elo(team1_elo, team2_elo, team1_result)
            new_team2_elo = calculate_elo(team2_elo, team1_elo, team2_result)
            
            # Berechne Delta
            elo_delta_team1 = (new_team1_elo - team1_elo) / 2
            elo_delta_team2 = (new_team2_elo - team2_elo) / 2
              # Update Elo
            elo_ratings[name1_team1][discipline] = elo1_before + elo_delta_team1
            elo_ratings[name2_team1][discipline] = elo2_before + elo_delta_team1
            elo_ratings[name1_team2][discipline] = elo3_before + elo_delta_team2
            elo_ratings[name2_team2][discipline] = elo4_before + elo_delta_team2
            
            # Speichere Match-Details mit allen Infos (notwendig für Awards)
            # Format: (date, p1, elo1_before, p2, elo2_before, p3, elo3_before, p4, elo4_before, result1, result2)
            match_tuple = (date, name1_team1, elo1_before, name2_team1, elo2_before, name1_team2, elo3_before, name2_team2, elo4_before, result1, result2)
            player_data[name1_team1].append(match_tuple)
            player_data[name2_team1].append(match_tuple)
            player_data[name1_team2].append(match_tuple)
            player_data[name2_team2].append(match_tuple)
                
        elif len(team1) == 1 and len(team2) == 1 and len(result) == 2:
            # Einzel
            (player1, name1), (player2, name2) = team1[0], team2[0]
            result1, result2 = result
            
            # Initialisieren
            initialize_elo(name1, discipline)
            initialize_elo(name2, discipline)
            
            # Spiele zählen
            games_played[name1][discipline] += 1
            games_played[name2][discipline] += 1
            
            # Bestimme Gewinner
            if result1 > result2:
                player1_result, player2_result = 1, 0
            elif result1 < result2:
                player1_result, player2_result = 0, 1
            else:
                player1_result, player2_result = 0.5, 0.5
            
            # Speichere ELO VOR
            player1_elo_before = elo_ratings[name1][discipline]
            player2_elo_before = elo_ratings[name2][discipline]
            
            # Berechne neue Elo
            new_player1_elo = calculate_elo(player1_elo_before, player2_elo_before, player1_result)
            new_player2_elo = calculate_elo(player2_elo_before, player1_elo_before, player2_result)
            
            # Update
            elo_ratings[name1][discipline] = new_player1_elo
            elo_ratings[name2][discipline] = new_player2_elo
            
            # Speichere nur VOR/NACH Elo
            player_data[name1].append((date, player1_elo_before, new_player1_elo))
            player_data[name2].append((date, player2_elo_before, new_player2_elo))

# Durchlaufen der Turnierdateien
for file_name in tournament_files:
    file_path = os.path.join(tournaments_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        tournament_data = json.load(file)
    
    discipline = tournament_data.get('mode', 'unknown')
    date = parser.parse(tournament_data['createdAt']).strftime('%Y-%m-%d')
    
    # Verarbeiten der Qualifikationsspiele
    if 'qualifying' in tournament_data and len(tournament_data['qualifying']) > 0 and 'rounds' in tournament_data['qualifying'][0]:
        for round_data in tournament_data['qualifying'][0]['rounds']:
            if 'matches' in round_data:
                process_matches(round_data['matches'], discipline, date)
    
    # Verarbeiten der KO-Runden
    if 'eliminations' in tournament_data:
        for elimination in tournament_data['eliminations']:
            if 'levels' in elimination:
                for level in elimination['levels']:
                    if 'matches' in level:
                        process_matches(level['matches'], discipline, date)
            if 'leftLevels' in elimination:
                for level in reversed(elimination['leftLevels']):
                    if 'matches' in level:
                        process_matches(level['matches'], discipline, date)

# Exportieren der Daten
def get_elo_data():
    return elo_ratings, games_played, player_data

# Ausgabe der Elo-Rangliste als CSV
with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Disziplin', 'Platz', 'Spieler', 'Elo'])
    
    for discipline in set(d for ratings in elo_ratings.values() for d in ratings):
        sorted_players = sorted(
            [(player, ratings[discipline]) for player, ratings in elo_ratings.items() if games_played[player][discipline] > 0],
            key=lambda x: x[1],
            reverse=True
        )
        for rank, (player, elo) in enumerate(sorted_players, start=1):
            csvwriter.writerow([discipline, rank, player, f"{elo:.2f}"])

# Speichern der Daten in JSON
data = {
    "elo_ratings": elo_ratings,
    "games_played": games_played,
}

with open('eloRangliste.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

# Speichern der detaillierten Spieler-Daten
detailed_data = {
    "player_data": player_data
}

with open('eloRanglisteDetailed.json', 'w', encoding='utf-8') as f:
    json.dump(detailed_data, f, ensure_ascii=False, indent=4)

print("Fertig!")
