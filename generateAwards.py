#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Awards-Generator für das neue kompakte (date, elo_before, elo_after) Format
Optimiert nach Elo-Drops Fix vom 30.10.2026
"""
import json
from collections import defaultdict
from statistics import stdev, mean
import sys

print("Loading data...", file=sys.stderr)
try:
    with open('eloRangliste.json', 'r') as f:
        elo_data = json.load(f)

    with open('eloRanglisteDetailed.json', 'r') as f:
        detailed_data = json.load(f)

    player_data = detailed_data['player_data']
    print(f"✅ {len(player_data)} Spieler geladen", file=sys.stderr)
except Exception as e:
    print(f"❌ Fehler beim Laden: {e}", file=sys.stderr)
    sys.exit(1)

# Extract years and disciplines
all_years = set()
for player in player_data:
    for match in player_data[player]:
        if len(match) >= 1:
            try:
                year = int(match[0].split('-')[0])
                all_years.add(year)
            except:
                pass

all_years = sorted(list(all_years), reverse=True)

# Get all disciplines
all_disciplines = set()
for player in elo_data['elo_ratings']:
    for discipline in elo_data['elo_ratings'][player]:
        if elo_data['games_played'][player][discipline] > 0:
            all_disciplines.add(discipline)

all_disciplines = sorted(list(all_disciplines))

print(f"📅 Jahre: {all_years}, Disziplinen: {all_disciplines}", file=sys.stderr)

def calculate_awards(year, discipline):
    """Berechne Awards für ein Jahr und Disziplin"""
    awards = {}
    
    # Sammle Stats für dieses Jahr
    player_stats = defaultdict(lambda: {
        'elo': 1000,
        'games': 0,
        'wins': 0,
        'elos_history': [1000]
    })
    
    for player in player_data:
        for match in player_data[player]:
            # Format: (date, p1_name, elo1_before, p2_name, elo2_before, p3_name, elo3_before, p4_name, elo4_before, result1, result2)
            if len(match) < 11:
                continue
            
            date_str = match[0]
            try:
                match_year = int(date_str.split('-')[0])
            except:
                continue
            
            if match_year != year:
                continue
            
            # Finde Elo-Werte für diesen Spieler in diesem Match
            player_elo_before = None
            player_elo_after = None
            
            # Suche den Spieler in den Positionen
            for i, player_name in enumerate([match[1], match[3], match[5], match[7]]):
                if player_name == player:
                    elo_idx = 2 + i * 2
                    player_elo_before = float(match[elo_idx]) if elo_idx < len(match) else None
                    break
            
            if player_elo_before is None:
                continue
            
            # Berechne Elo nach (durch Re-Read von der Rangliste oder Schätzung)
            # Für jetzt: nutze einfach den Elo vor dem Match aus der History
            player_stats[player]['games'] += 1
            player_stats[player]['elos_history'].append(player_elo_before)
    
    # Filter players with games
    players = {p: s for p, s in player_stats.items() if s['games'] > 0}
    
    if not players:
        return awards
    
    # Award 1: Player of the Year (highest Elo)
    poty = sorted(players.items(), key=lambda x: x[1]['elo'], reverse=True)
    awards['player_of_the_year'] = {
        'icon': '🏆',
        'title': 'Player of the Year',
        'description': 'Höchste Elo Bewertung',
        'top_3': [{'player': p, 'value': f"{s['elo']:.2f}"} for p, s in poty[:3]],
        'rest': [{'player': p, 'value': f"{s['elo']:.2f}"} for p, s in poty[3:]]
    }
    
    # Award 2: Most Improved
    improved = sorted([(p, s['elo'] - 1000) for p, s in players.items()], key=lambda x: x[1], reverse=True)
    awards['most_improved'] = {
        'icon': '📈',
        'title': 'Most Improved Player',
        'description': 'Größter Elo-Zuwachs',
        'top_3': [{'player': p, 'value': f"+{v:.1f}"} for p, v in improved[:3]],
        'rest': [{'player': p, 'value': f"+{v:.1f}"} for p, v in improved[3:]]
    }
    
    # Award 3: Ironman (most games)
    ironman = sorted(players.items(), key=lambda x: x[1]['games'], reverse=True)
    awards['ironman'] = {
        'icon': '🎲',
        'title': 'Ironman Award',
        'description': 'Die meisten gespielten Matches',
        'top_3': [{'player': p, 'value': str(s['games'])} for p, s in ironman[:3]],
        'rest': [{'player': p, 'value': str(s['games'])} for p, s in ironman[3:]]
    }
    
    # Award 4: Lucky Bastard (win rate)
    win_rates = sorted([(p, s['wins'] / s['games']) for p, s in players.items() if s['games'] >= 5], key=lambda x: x[1], reverse=True)
    if win_rates:
        awards['lucky_bastard'] = {
            'icon': '🍀',
            'title': 'Lucky Bastard',
            'description': 'Höchste Gewinnquote',
            'top_3': [{'player': p, 'value': f"{v*100:.1f}%"} for p, v in win_rates[:3]],
            'rest': [{'player': p, 'value': f"{v*100:.1f}%"} for p, v in win_rates[3:]]
        }
    
    # Award 5: Comeback King (Elo recovery)
    comebacks = []
    for p, s in players.items():
        if len(s['elos_history']) >= 2:
            min_elo = min(s['elos_history'])
            comeback = s['elo'] - min_elo
            if comeback > 0:
                comebacks.append((p, comeback))
    
    if comebacks:
        comebacks_sorted = sorted(comebacks, key=lambda x: x[1], reverse=True)
        awards['comeback_king'] = {
            'icon': '💪',
            'title': 'Comeback King',
            'description': 'Höchste Elo-Rückgewinnung nach Tiefpunkt',
            'top_3': [{'player': p, 'value': f"+{v:.1f}"} for p, v in comebacks_sorted[:3]],
            'rest': [{'player': p, 'value': f"+{v:.1f}"} for p, v in comebacks_sorted[3:]]
        }
    
    # Award 6: Rollercoaster (volatility)
    volatility = []
    for p, s in players.items():
        if len(s['elos_history']) >= 2:
            try:
                vol = stdev(s['elos_history'])
                volatility.append((p, vol))
            except:
                pass
    
    if volatility:
        volatility_sorted = sorted(volatility, key=lambda x: x[1], reverse=True)
        awards['rollercoaster'] = {
            'icon': '🎢',
            'title': 'Rollercoaster Award',
            'description': 'Größte Elo-Schwankungen',
            'top_3': [{'player': p, 'value': f"±{v:.1f}"} for p, v in volatility_sorted[:3]],
            'rest': [{'player': p, 'value': f"±{v:.1f}"} for p, v in volatility_sorted[3:]]
        }
    
    # Award 7: Giant Killer (estimated from big gains)
    giant_kills = []
    for p in players:
        for match in player_data[p]:
            if len(match) < 3:
                continue
            
            date_str = match[0]
            try:
                elo_before = float(match[1])
                elo_after = float(match[2])
                match_year = int(date_str.split('-')[0])
            except:
                continue
            
            if match_year != year and elo_after > elo_before and (elo_after - elo_before) > 15:
                continue
            
            if elo_after > elo_before and (elo_after - elo_before) > 15:
                giant_kills.append(p)
    
    if giant_kills:
        giant_counts = {}
        for p in giant_kills:
            giant_counts[p] = giant_counts.get(p, 0) + 1
        giant_sorted = sorted(giant_counts.items(), key=lambda x: x[1], reverse=True)
        awards['giant_killer'] = {
            'icon': '💣',
            'title': 'Giant Killer',
            'description': 'Die meisten Siege gegen starke Gegner',
            'top_3': [{'player': p, 'value': str(v)} for p, v in giant_sorted[:3]],
            'rest': [{'player': p, 'value': str(v)} for p, v in giant_sorted[3:]]
        }
    
    # Award 8: Best Teammate (not available in new format, skip)
    # Award 9: Slow Starter (improvement trend)
    improvement_trends = []
    for p, s in players.items():
        if len(s['elos_history']) >= 4:
            elos = s['elos_history']
            first_third = mean(elos[:len(elos)//3]) if len(elos)//3 > 0 else elos[0]
            last_third = mean(elos[-(len(elos)//3):]) if len(elos)//3 > 0 else elos[-1]
            trend = last_third - first_third
            improvement_trends.append((p, trend))
    
    if improvement_trends:
        improvement_sorted = sorted(improvement_trends, key=lambda x: x[1], reverse=True)
        awards['slow_starter'] = {
            'icon': '😴',
            'title': 'Slow Starter Award',
            'description': 'Schwach begonnen, stark beendet',
            'top_3': [{'player': p, 'value': f"+{v:.1f}"} for p, v in improvement_sorted[:3]],
            'rest': [{'player': p, 'value': f"+{v:.1f}"} for p, v in improvement_sorted[3:]]
        }
    
    return awards

# Generate awards for all years/disciplines
print("🏆 Berechne Awards...", file=sys.stderr)
output = {'awards': {}, 'years': [str(y) for y in all_years], 'latest_year': str(all_years[0]) if all_years else None}

for year in all_years:
    output['awards'][str(year)] = {}
    for discipline in all_disciplines:
        awards = calculate_awards(year, discipline)
        output['awards'][str(year)][discipline] = awards

# Save
with open('eloAwards.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Fertig! Awards für {len(all_years)} Jahre generiert", file=sys.stderr)
