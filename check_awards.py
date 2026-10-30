import json

with open('eloAwards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

awards = data['awards']['2026']['monster_dyp']
print(f'Awards 2026/monster_dyp: {len(awards)} Kategorien')
if 'player_of_the_year' in awards:
    poty = awards['player_of_the_year']
    print(f'Player of the Year Top 3: {len(poty.get("top_3", []))} Spieler')
    if poty.get('top_3'):
        print(f'  #1: {poty["top_3"][0]["player"]} ({poty["top_3"][0]["value"]} Elo)')
else:
    print("Player of the Year: NOT FOUND")
