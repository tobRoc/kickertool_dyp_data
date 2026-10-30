#!/usr/bin/env python3
import json

with open('eloAwards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

year = "2026"
disc = "monster_dyp"

if year in data["awards"] and disc in data["awards"][year]:
    poty = data["awards"][year][disc]["player_of_the_year"]
    print(f"✅ Awards 2026/monster_dyp geladen")
    print(f"   Top 1: {poty['top_3'][0]['player']} ({poty['top_3'][0]['value']})")
    print(f"   Top 3 count: {len(poty['top_3'])}, Rest count: {len(poty['rest'])}")
else:
    print(f"❌ Awards nicht gefunden")
