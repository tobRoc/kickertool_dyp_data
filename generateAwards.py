#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from statistics import stdev, mean
import sys

print("="*60, file=sys.stderr)
print("🚀 Awards Generator startet...", file=sys.stderr)
print("="*60, file=sys.stderr)

try:
    print("📂 [1/4] Lade Daten...", file=sys.stderr)
    with open('eloRangliste.json', 'r', encoding='utf-8') as f:
        elo_data = json.load(f)
    
    with open('eloRanglisteDetailed.json', 'r', encoding='utf-8') as f:
        detailed_data = json.load(f)
    
    elo_ratings = elo_data['elo_ratings']
    games_played = elo_data['games_played']
    player_data = detailed_data['player_data']
    
    print(f"✅ {len(player_data)} Spieler geladen", file=sys.stderr)
    
    # ====== Extrahiere Jahre und Disziplinen ======
    print("📅 [2/4] Extrahiere Jahre und Disziplinen...", file=sys.stderr)
    
    all_years = set()
    for player in player_data:
        for match in player_data[player]:
            if len(match) >= 1:
                date_str = match[0]
                try:
                    year = int(date_str.split('-')[0])
                    all_years.add(year)
                except:
                    pass
    
    all_years = sorted(list(all_years), reverse=True)
    
    all_disciplines = set()
    for player in elo_ratings:
        for discipline in elo_ratings[player]:
            if games_played[player][discipline] > 0:
                all_disciplines.add(discipline)
    
    all_disciplines = sorted(list(all_disciplines))
    print(f"✅ Jahre: {all_years}, Disziplinen: {len(all_disciplines)}", file=sys.stderr)
    
    # ====== Funktionen für Award-Berechnung ======
    
    def get_players_and_stats_for_year_discipline(year, discipline):
        """Gibt Spieler-Stats für ein bestimmtes Jahr und Disziplin zurück"""
        player_stats = defaultdict(lambda: {
            'elo': 1000,
            'games': 0,
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
                
                # match = [date, p1, elo1, p2, elo2, p3, elo3, p4, elo4, result1, result2]
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
        
        return {p: stats for p, stats in player_stats.items() if stats['games'] > 0}
    
    def create_award_entry(player, value):
        return {'player': player, 'value': value}
    
    def get_top_3_and_more(data_dict, format_fn=None, limit=3):
        """Gibt Top 3 + Rest der Rankings zurück"""
        sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        
        top_3 = []
        rest = []
        
        for idx, (name, value) in enumerate(sorted_items):
            entry = create_award_entry(name, format_fn(value) if format_fn else str(value))
            if idx < limit:
                top_3.append(entry)
            else:
                rest.append(entry)
        
        return top_3, rest
    
    def calculate_awards_for_year_discipline(year, discipline):
        """Berechnet alle Awards für ein Jahr und eine Disziplin"""
        awards = {}
        players = get_players_and_stats_for_year_discipline(year, discipline)
        
        if not players:
            return awards
        
        # === 1. Player of the Year ===
        poty_dict = {p: stats['elo'] for p, stats in players.items()}
        top_3, rest = get_top_3_and_more(poty_dict, format_fn=lambda v: f"{v:.2f}")
        awards['player_of_the_year'] = {
            'icon': '🏆',
            'title': 'Player of the Year',
            'description': 'Höchste Elo Bewertung',
            'top_3': top_3,
            'rest': rest
        }
        
        # === 2. Most Improved Player ===
        improved_dict = {p: stats['elo'] - 1000 for p, stats in players.items()}
        top_3, rest = get_top_3_and_more(improved_dict, format_fn=lambda v: f"+{v:.1f}")
        awards['most_improved'] = {
            'icon': '📈',
            'title': 'Most Improved Player',
            'description': 'Größter Elo-Zuwachs',
            'top_3': top_3,
            'rest': rest
        }
        
        # === 3. Ironman Award ===
        ironman_dict = {p: stats['games'] for p, stats in players.items()}
        top_3, rest = get_top_3_and_more(ironman_dict, format_fn=lambda v: str(int(v)))
        awards['ironman'] = {
            'icon': '🎲',
            'title': 'Ironman Award',
            'description': 'Die meisten gespielten Matches',
            'top_3': top_3,
            'rest': rest
        }
        
        # === 4. Best Teammate ===
        teammate_dict = {p: len(stats['teammates']) for p, stats in players.items()}
        top_3, rest = get_top_3_and_more(teammate_dict, format_fn=lambda v: str(int(v)))
        awards['best_teammate'] = {
            'icon': '🤝',
            'title': 'Best Teammate',
            'description': 'Gewinnt mit den meisten unterschiedlichen Partnern',
            'top_3': top_3,
            'rest': rest
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
            top_3, rest = get_top_3_and_more(comebacks, format_fn=lambda v: f"+{v:.1f}")
            awards['comeback_king'] = {
                'icon': '💪',
                'title': 'Comeback King',
                'description': 'Höchste Elo-Rückgewinnung nach Tiefpunkt',
                'top_3': top_3,
                'rest': rest
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
            top_3, rest = get_top_3_and_more(volatility, format_fn=lambda v: f"±{v:.1f}")
            awards['rollercoaster'] = {
                'icon': '🎢',
                'title': 'Rollercoaster Award',
                'description': 'Größte Elo-Schwankungen',
                'top_3': top_3,
                'rest': rest
            }
        
        # === 7. Giant Killer ===
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
                if p1 == player and p2 in top_10_players and result1 > result2:
                    giant_kills[player] += 1
                elif p2 == player and p1 in top_10_players and result1 < result2:
                    giant_kills[player] += 1
        
        if giant_kills:
            top_3, rest = get_top_3_and_more(dict(giant_kills), format_fn=lambda v: str(int(v)))
            awards['giant_killer'] = {
                'icon': '💣',
                'title': 'Giant Killer',
                'description': 'Die meisten Top-10-Spieler geschlagen',
                'top_3': top_3,
                'rest': rest
            }
        
        # === 8. Lucky Bastard Award ===
        win_rates = {}
        for player, stats in players.items():
            if stats['games'] >= 5:
                win_rate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
                win_rates[player] = win_rate
        
        if win_rates:
            top_3, rest = get_top_3_and_more(win_rates, format_fn=lambda v: f"{v*100:.1f}%")
            awards['lucky_bastard'] = {
                'icon': '🍀',
                'title': 'Lucky Bastard Award',
                'description': 'Auffällig hohe Gewinnquote',
                'top_3': top_3,
                'rest': rest
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
            top_3, rest = get_top_3_and_more(improvement_trends, format_fn=lambda v: f"+{v:.1f}")
            awards['slow_starter'] = {
                'icon': '😴',
                'title': 'Slow Starter Award',
                'description': 'Schwach begonnen, stark beendet',
                'top_3': top_3,
                'rest': rest
            }
        
        return awards
    
    # ====== Berechne Awards für alle Jahre und Disziplinen ======
    print("🏆 [3/4] Berechne Awards...", file=sys.stderr)
    
    awards_by_year_discipline = defaultdict(lambda: defaultdict(dict))
    
    for year in all_years:
        for discipline in all_disciplines:
            awards_by_year_discipline[str(year)][discipline] = calculate_awards_for_year_discipline(year, discipline)
    
    # ====== Speichere Awards ======
    print("💾 [4/4] Speichere eloAwards.json...", file=sys.stderr)
    
    output = {
        "awards": dict(awards_by_year_discipline),
        "years": [str(y) for y in all_years],
        "latest_year": str(all_years[0]) if all_years else None
    }
    
    with open('eloAwards.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Fertig! Awards für {len(all_years)} Jahre generiert", file=sys.stderr)

except Exception as e:
    print(f"❌ FEHLER: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
