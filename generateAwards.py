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
    print("📂 [1/6] Lade eloRangliste.json...", file=sys.stderr)
    with open('eloRangliste.json', 'r', encoding='utf-8') as f:
        elo_data = json.load(f)
    
    print("📂 [2/6] Lade eloRanglisteDetailed.json...", file=sys.stderr)
    with open('eloRanglisteDetailed.json', 'r', encoding='utf-8') as f:
        detailed_data = json.load(f)
    
    elo_ratings = elo_data['elo_ratings']
    games_played = elo_data['games_played']
    player_data = detailed_data['player_data']
    
    print(f"✅ Daten geladen: {len(player_data)} Spieler", file=sys.stderr)
    
    # ====== Extrahiere Jahre ======
    print("📅 [3/6] Extrahiere Jahre...", file=sys.stderr)
    
    def get_available_years():
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
        return sorted(list(years), reverse=True)
    
    all_years = get_available_years()
    print(f"✅ Jahre gefunden: {all_years}", file=sys.stderr)
    
    if not all_years:
        print("❌ FEHLER: Keine Jahre gefunden!", file=sys.stderr)
        sys.exit(1)
    
    # ====== Sammle Disziplinen ======
    print("📊 [4/6] Sammle Disziplinen...", file=sys.stderr)
    
    all_disciplines = set()
    for player in elo_ratings:
        for discipline in elo_ratings[player]:
            if games_played[player][discipline] > 0:
                all_disciplines.add(discipline)
    
    all_disciplines = sorted(list(all_disciplines))
    print(f"✅ Disziplinen: {all_disciplines}", file=sys.stderr)
    
    # ====== Generiere Awards ======
    print("🏆 [5/6] Generiere Awards...", file=sys.stderr)
    
    output = {
        "awards": {},
        "years": [str(y) for y in all_years],
        "latest_year": str(all_years[0]) if all_years else None
    }
    
    for year in all_years:
        output["awards"][str(year)] = {}
        for discipline in all_disciplines:
            output["awards"][str(year)][discipline] = {
                "player_of_the_year": {
                    "icon": "🏆",
                    "title": "Player of the Year",
                    "description": "Höchste Elo Bewertung",
                    "top_3": [],
                    "rest": []
                }
            }
    
    print(f"✅ Awards generiert", file=sys.stderr)
    
    # ====== Speichere Awards ======
    print("💾 [6/6] Speichere eloAwards.json...", file=sys.stderr)
    
    with open('eloAwards.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("✅ Fertig!", file=sys.stderr)

except Exception as e:
    print(f"❌ FEHLER: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
