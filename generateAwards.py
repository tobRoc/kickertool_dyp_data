import json
from collections import defaultdict, Counter
from statistics import stdev, mean
import math
from datetime import datetime

# Lade die Elo-Daten
with open('eloRangliste.json', 'r', encoding='utf-8') as f:
    elo_data = json.load(f)

with open('eloRanglisteDetailed.json', 'r', encoding='utf-8') as f:
    detailed_data = json.load(f)

elo_ratings = elo_data['elo_ratings']
games_played = elo_data['games_played']
player_data = detailed_data['player_data']

# Struktur für Awards pro Jahr und Disziplin
awards_by_year_discipline = defaultdict(lambda: defaultdict(dict))

# ====== Extrahiere Jahre aus den Match-Daten ======

def get_available_years():
    """Gibt alle Jahre mit Match-Daten zurück"""
    years = set()
    for player in player_data:
        for match in player_data[player]:
            if len(match) >= 1:
                date_str = match[0]
                try:
                    year = int(date_str.split('-')[0])
                    years.add(year)
                except:
                    pass
    return sorted(list(years), reverse=True)  # Neueste zuerst

def get_players_and_stats_for_year_discipline(year, discipline):
    """Gibt Spieler-Stats für ein bestimmtes Jahr und Disziplin zurück"""
    player_stats = defaultdict(lambda: {
        'elo': 1000,
        'games': 0,
        'matches': [],
        'wins': 0,
        'losses': 0,
        'teammates': set(),
        'elos_history': [1000]
    })
    
    # Durchlaufe alle Spieler und ihre Matches
    for player in player_data:
        for match in player_data[player]:
            if len(match) < 11:
                continue
            
            date_str = match[0]
            try:
                match_year = int(date_str.split('-')[0])
            except:
                continue
            
            if match_year != year:
                continue
            
            # match = (date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2)
            date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2 = match
            
            # Speichere die Elo nach dem Match
            if p1 == player:
                player_stats[player]['elo'] = elo1
                player_stats[player]['elos_history'].append(elo1)
                player_stats[player]['games'] += 1
                if result1 > result2:
                    player_stats[player]['wins'] += 1
                    player_stats[player]['teammates'].add(p2)
                else:
                    player_stats[player]['losses'] += 1
                    
            elif p2 == player:
                player_stats[player]['elo'] = elo2
                player_stats[player]['elos_history'].append(elo2)
                player_stats[player]['games'] += 1
                if result1 > result2:
                    player_stats[player]['wins'] += 1
                    player_stats[player]['teammates'].add(p1)
                else:
                    player_stats[player]['losses'] += 1
                    
            elif p3 == player:
                player_stats[player]['elo'] = elo3
                player_stats[player]['elos_history'].append(elo3)
                player_stats[player]['games'] += 1
                if result2 > result1:
                    player_stats[player]['wins'] += 1
                    player_stats[player]['teammates'].add(p4)
                else:
                    player_stats[player]['losses'] += 1
                    
            elif p4 == player:
                player_stats[player]['elo'] = elo4
                player_stats[player]['elos_history'].append(elo4)
                player_stats[player]['games'] += 1
                if result2 > result1:
                    player_stats[player]['wins'] += 1
                    player_stats[player]['teammates'].add(p3)
                else:
                    player_stats[player]['losses'] += 1
    
    # Filtere nur Spieler mit Spielen in dieser Disziplin
    players_with_games = {
        p: stats for p, stats in player_stats.items()
        if stats['games'] > 0
    }
    
    return players_with_games

# ====== Award-Berechnung pro Jahr + Disziplin ======

def calculate_awards_for_year_discipline(year, discipline):
    """Berechnet alle Awards für ein Jahr und eine Disziplin"""
    awards = {}
    
    players = get_players_and_stats_for_year_discipline(year, discipline)
    
    if not players:
        return awards
    
    # === 1. Player of the Year ===
    poty = max(players.items(), key=lambda x: x[1]['elo'])
    awards['player_of_the_year'] = {
        'icon': '🏆',
        'title': 'Player of the Year',
        'description': 'Höchste Elo Bewertung',
        'player': poty[0],
        'value': f"{poty[1]['elo']:.2f}",
        'details': f"{poty[1]['games']} Spiele"
    }
    
    # === 2. Most Improved Player ===
    most_improved = max(
        ((p, stats) for p, stats in players.items()),
        key=lambda x: x[1]['elo'] - 1000 if len(x[1]['elos_history']) > 0 else 0
    )
    improvement = most_improved[1]['elo'] - 1000
    awards['most_improved'] = {
        'icon': '📈',
        'title': 'Most Improved Player',
        'description': 'Größter Elo-Zuwachs',
        'player': most_improved[0],
        'value': f"+{improvement:.1f}",
        'details': f"von 1000 auf {most_improved[1]['elo']:.0f}"
    }
    
    # === 3. Ironman Award ===
    ironman = max(
        players.items(),
        key=lambda x: x[1]['games']
    )
    awards['ironman'] = {
        'icon': '🎲',
        'title': 'Ironman Award',
        'description': 'Die meisten gespielten Matches',
        'player': ironman[0],
        'value': str(ironman[1]['games']),
        'details': f"{ironman[1]['games']} Spiele in {year}"
    }
    
    # === 4. Best Teammate ===
    teammates_dict = {p: len(stats['teammates']) for p, stats in players.items()}
    if teammates_dict:
        best_teammate = max(teammates_dict.items(), key=lambda x: x[1])
        awards['best_teammate'] = {
            'icon': '🤝',
            'title': 'Best Teammate',
            'description': 'Gewinnt mit den meisten unterschiedlichen Partnern',
            'player': best_teammate[0],
            'value': str(best_teammate[1]),
            'details': f"Erfolgreiche Partnerschaften: {best_teammate[1]}"
        }
    
    # === 5. Comeback King ===
    comebacks = {}
    for player, stats in players.items():
        if len(stats['elos_history']) >= 2:
            min_elo = min(stats['elos_history'])
            max_elo_after_min = max([e for e in stats['elos_history'] if e >= min_elo])
            comeback = max_elo_after_min - min_elo
            if comeback > 0:
                comebacks[player] = comeback
    
    if comebacks:
        comeback_king = max(comebacks.items(), key=lambda x: x[1])
        awards['comeback_king'] = {
            'icon': '💪',
            'title': 'Comeback King',
            'description': 'Höchste Elo-Rückgewinnung nach Tiefpunkt',
            'player': comeback_king[0],
            'value': f"+{comeback_king[1]:.1f}",
            'details': f"Elo-Rückgewinnung: {comeback_king[1]:.1f}"
        }
    
    # === 6. Rollercoaster Award ===
    volatility = {}
    for player, stats in players.items():
        if len(stats['elos_history']) >= 2:
            try:
                volatility[player] = stdev(stats['elos_history'])
            except:
                pass
    
    if volatility:
        rollercoaster = max(volatility.items(), key=lambda x: x[1])
        awards['rollercoaster'] = {
            'icon': '🎢',
            'title': 'Rollercoaster Award',
            'description': 'Größte Elo-Schwankungen',
            'player': rollercoaster[0],
            'value': f"±{rollercoaster[1]:.1f}",
            'details': f"Elo-Volatilität: {rollercoaster[1]:.1f}"
        }
      # === 7. Giant Killer ===
    # Top 10 dieser Saison
    top_10_list = sorted(players.items(), key=lambda x: x[1]['elo'], reverse=True)[:10]
    top_10_players = {p for p, _ in top_10_list}
    
    giant_kills = defaultdict(int)
    for player in player_data:
        if player not in players:
            continue
        for match in player_data[player]:
            if len(match) < 11:
                continue
            
            date_str = match[0]
            try:
                match_year = int(date_str.split('-')[0])
            except:
                continue
            
            if match_year != year:
                continue
            
            date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2 = match
            
            # Einzel
            if p1 == player and p2 in top_10_players and result1 > result2:
                giant_kills[player] += 1
            elif p2 == player and p1 in top_10_players and result1 < result2:
                giant_kills[player] += 1
    
    if giant_kills:
        giant_killer = max(giant_kills.items(), key=lambda x: x[1])
        awards['giant_killer'] = {
            'icon': '💣',
            'title': 'Giant Killer',
            'description': 'Die meisten Top-10-Spieler geschlagen',
            'player': giant_killer[0],
            'value': str(giant_killer[1]),
            'details': f"{giant_killer[1]} Top-10-Spieler besiegt"
        }
    
    # === 8. Lucky Bastard Award ===
    win_rates = {}
    for player, stats in players.items():
        if stats['games'] >= 5:  # Mindestens 5 Spiele
            win_rate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            win_rates[player] = win_rate
    
    if win_rates:
        lucky = max(win_rates.items(), key=lambda x: x[1])
        awards['lucky_bastard'] = {
            'icon': '🍀',
            'title': 'Lucky Bastard Award',
            'description': 'Auffällig hohe Gewinnquote',
            'player': lucky[0],
            'value': f"{lucky[1]*100:.1f}%",
            'details': f"Gewinnquote über alle Spiele"
        }
    
    # === 9. Slow Starter Award ===
    improvement_trends = {}
    for player, stats in players.items():
        if len(stats['elos_history']) >= 4:
            elos = stats['elos_history']
            first_third = mean(elos[:len(elos)//3]) if len(elos)//3 > 0 else elos[0]
            last_third = mean(elos[-(len(elos)//3):]) if len(elos)//3 > 0 else elos[-1]
            trend = last_third - first_third
            improvement_trends[player] = trend
    
    if improvement_trends:
        slow_starter = max(improvement_trends.items(), key=lambda x: x[1])
        awards['slow_starter'] = {
            'icon': '😴',
            'title': 'Slow Starter Award',
            'description': 'Schwach begonnen, stark beendet',
            'player': slow_starter[0],
            'value': f"+{slow_starter[1]:.1f}",
            'details': f"Elo-Trend über Jahr"
        }
    
    return awards

# ====== Berechne Awards für alle Jahre und Disziplinen ======

all_years = get_available_years()
all_disciplines = set()

for player in elo_ratings:
    for discipline in elo_ratings[player]:
        if games_played[player][discipline] > 0:
            all_disciplines.add(discipline)

print(f"✅ Verfügbare Jahre: {all_years}")
print(f"✅ Verfügbare Disziplinen: {sorted(all_disciplines)}")

for year in all_years:
    for discipline in sorted(all_disciplines):
        awards_by_year_discipline[str(year)][discipline] = calculate_awards_for_year_discipline(year, discipline)

# ====== Speichere Awards ======

output = {
    "awards": dict(awards_by_year_discipline),
    "years": [str(y) for y in all_years],
    "latest_year": str(all_years[0]) if all_years else None
}

with open('eloAwards.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=4)

print(f"✅ Awards generiert für {len(all_years)} Jahre")
print(f"   Datei: eloAwards.json")

# ====== Award-Berechnung pro Disziplin (Gesamt aller Jahre) ======

def get_discipline_players(discipline):
    """Gibt alle Spieler einer Disziplin zurück"""
    return {
        player: elo_ratings[player][discipline]
        for player in elo_ratings
        if discipline in elo_ratings[player] and games_played[player][discipline] > 0
    }
