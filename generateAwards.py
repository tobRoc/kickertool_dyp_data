import json
from collections import defaultdict, Counter
from statistics import stdev, mean
import math

# Lade die Elo-Daten
with open('eloRangliste.json', 'r', encoding='utf-8') as f:
    elo_data = json.load(f)

with open('eloRanglisteDetailed.json', 'r', encoding='utf-8') as f:
    detailed_data = json.load(f)

elo_ratings = elo_data['elo_ratings']
games_played = elo_data['games_played']
player_data = detailed_data['player_data']

# Struktur für Awards pro Disziplin
awards_by_discipline = defaultdict(dict)

# ====== Award-Berechnung pro Disziplin ======

def get_discipline_players(discipline):
    """Gibt alle Spieler einer Disziplin zurück"""
    return {
        player: elo_ratings[player][discipline]
        for player in elo_ratings
        if discipline in elo_ratings[player] and games_played[player][discipline] > 0
    }

def calculate_awards_for_discipline(discipline):
    """Berechnet alle Awards für eine Disziplin"""
    awards = {}
    players_in_discipline = get_discipline_players(discipline)
    
    if not players_in_discipline:
        return awards
    
    # === 1. Player of the Year ===
    # Höchste aktuelle Elo
    poty = max(players_in_discipline.items(), key=lambda x: x[1])
    awards['player_of_the_year'] = {
        'icon': '🏆',
        'title': 'Player of the Year',
        'description': 'Höchste Elo Bewertung',
        'player': poty[0],
        'value': f"{poty[1]:.2f}",
        'details': f"{games_played[poty[0]][discipline]} Spiele"
    }
    
    # === 2. Most Improved Player ===
    # Größter Elo-Zuwachs (Aktuell - Initial 1000)
    most_improved = max(
        players_in_discipline.items(),
        key=lambda x: x[1] - 1000
    )
    improvement = most_improved[1] - 1000
    awards['most_improved'] = {
        'icon': '📈',
        'title': 'Most Improved Player',
        'description': 'Größter Elo-Zuwachs',
        'player': most_improved[0],
        'value': f"+{improvement:.1f}",
        'details': f"von 1000 auf {most_improved[1]:.0f}"
    }
    
    # === 3. Ironman Award ===
    # Meiste Spiele
    ironman = max(
        ((p, games_played[p][discipline]) for p in players_in_discipline),
        key=lambda x: x[1]
    )
    awards['ironman'] = {
        'icon': '🎲',
        'title': 'Ironman Award',
        'description': 'Die meisten gespielten Matches',
        'player': ironman[0],
        'value': str(ironman[1]),
        'details': f"{ironman[1]} Spiele in {discipline}"
    }
    
    # === 4. Best Teammate ===
    # Gewinnt mit den meisten verschiedenen Partnern (nur Doppel)
    teammates = defaultdict(lambda: set())
    for player in player_data:
        if player not in players_in_discipline:
            continue
        for match in player_data[player]:
            # match = (date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2)
            if len(match) >= 11:
                date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2 = match
                # Doppel: Spieler 1 & 2 gegen 3 & 4
                if p1 == player and result1 > result2:  # Gewonnen
                    teammates[player].add(p2)
                elif p2 == player and result1 > result2:  # Gewonnen
                    teammates[player].add(p1)
                elif p3 == player and result2 > result1:  # Gewonnen
                    teammates[player].add(p4)
                elif p4 == player and result2 > result1:  # Gewonnen
                    teammates[player].add(p3)
    
    if teammates:
        best_teammate = max(teammates.items(), key=lambda x: len(x[1]))
        awards['best_teammate'] = {
            'icon': '🤝',
            'title': 'Best Teammate',
            'description': 'Gewinnt mit den meisten unterschiedlichen Partnern',
            'player': best_teammate[0],
            'value': str(len(best_teammate[1])),
            'details': f"Erfolgreiche Partnerschaften: {len(best_teammate[1])}"
        }
    
    # === 5. Comeback King ===
    # Größte Elo-Rückgewinnung nach Tiefpunkt
    comebacks = {}
    for player in players_in_discipline:
        if player not in player_data:
            continue
        matches = player_data[player]
        if len(matches) < 2:
            continue
        
        # Finde Tiefpunkt und höchsten Punkt danach
        min_elo = float('inf')
        max_elo_after_min = -float('inf')
        
        for match in matches:
            if len(match) >= 3:
                elo_at_match = match[2]  # elo nach match
                min_elo = min(min_elo, elo_at_match)
        
        # Finde höchsten Elo nach dem Tiefpunkt
        for match in matches:
            if len(match) >= 3:
                elo_at_match = match[2]
                if elo_at_match >= min_elo and elo_at_match > max_elo_after_min:
                    max_elo_after_min = elo_at_match
        
        if max_elo_after_min > min_elo:
            comeback = max_elo_after_min - min_elo
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
    # Höchste Elo-Volatilität (Standardabweichung)
    volatility = {}
    for player in players_in_discipline:
        if player not in player_data:
            continue
        matches = player_data[player]
        if len(matches) < 2:
            continue
        
        elos = [match[2] for match in matches if len(match) >= 3]
        if len(elos) >= 2:
            try:
                volatility[player] = stdev(elos)
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
    # Meiste Top-10-Spieler besiegt
    top_10_players = set(
        sorted(players_in_discipline.items(), key=lambda x: x[1], reverse=True)[:10]
    )
    top_10_players = {p for p, _ in top_10_players}
    
    giant_kills = defaultdict(int)
    for player in player_data:
        if player not in players_in_discipline:
            continue
        for match in player_data[player]:
            if len(match) >= 11:
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
    # Auffällig hohe Win-Rate
    win_rates = {}
    for player in player_data:
        if player not in players_in_discipline:
            continue
        matches = player_data[player]
        if not matches:
            continue
        
        wins = 0
        total = 0
        
        for match in matches:
            if len(match) >= 11:
                date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2 = match
                if p1 == player:
                    if result1 > result2:
                        wins += 1
                    elif result1 == result2:
                        wins += 0.5
                    total += 1
                elif p2 == player:
                    if result1 > result2:
                        wins += 1
                    elif result1 == result2:
                        wins += 0.5
                    total += 1
        
        if total >= 5:  # Mindestens 5 Spiele
            win_rates[player] = wins / total if total > 0 else 0
    
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
    # Startet schwach, endet stark (Elo-Verbesserung im Verlauf)
    improvement_trends = {}
    for player in player_data:
        if player not in players_in_discipline:
            continue
        matches = player_data[player]
        if len(matches) < 4:
            continue
        
        elos = [match[2] for match in matches if len(match) >= 3]
        if len(elos) >= 4:
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
            'details': f"Elo-Trend über Saison"
        }
    
    return awards

# ====== Berechne Awards für alle Disziplinen ======

all_disciplines = set()
for player in elo_ratings:
    for discipline in elo_ratings[player]:
        if games_played[player][discipline] > 0:
            all_disciplines.add(discipline)

for discipline in sorted(all_disciplines):
    awards_by_discipline[discipline] = calculate_awards_for_discipline(discipline)

# ====== Speichere Awards ======

output = {
    "awards": dict(awards_by_discipline)
}

with open('eloAwards.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=4)

print(f"✅ Awards generiert für {len(all_disciplines)} Disziplinen")
print(f"   Disziplinen: {', '.join(sorted(all_disciplines))}")
print(f"   Datei: eloAwards.json")
