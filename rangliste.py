import json
import os
import csv
from collections import defaultdict
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from dateutil import parser

# Pfad zum Verzeichnis mit den heruntergeladenen Turnierdateien
tournaments_dir = './tournaments/'
output_csv_path = './platzierung_pro_disziplin.csv'
output_html_path = './platzierung_pro_disziplin.html'

# Laden der Turnierdateien
tournament_files = [f for f in os.listdir(tournaments_dir) if f.endswith('.json')]

# Turnierdateien nach Datum sortieren
def get_tournament_date(file_name):
    file_path = os.path.join(tournaments_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        tournament_data = json.load(file)
    
    return parser.parse(tournament_data['createdAt'])

tournament_files.sort(key=get_tournament_date)

# Platzierungsdaten für jeden Spieler in jeder Disziplin pro Jahr
platzierung_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
teilnahmen_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
turnier_details = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
year_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# Funktion zur Verarbeitung von Endergebnissen
def process_end_results(end_results, discipline, year):
    teilnehmerzahl = len(end_results)
    for platzierung, player in enumerate(end_results, start=1):
        name = player['name']
        platzierung_data[name][discipline][year] += teilnehmerzahl / platzierung
        teilnahmen_data[name][discipline][year] += 1
        turnier_details[name][discipline][year].append((platzierung, teilnehmerzahl))

# Funktion zur Verarbeitung von Eliminations
def process_eliminations(eliminations, discipline, year, total_players):
    for elimination in eliminations:
        if 'standings' in elimination:
            standings = elimination['standings']
            for standing in standings:
                if 'stats' in standing and 'place' in standing['stats']:
                    place = standing['stats']['place']
                    name = standing['name']
                    platzierung_data[name][discipline][year] += total_players / place
                    teilnahmen_data[name][discipline][year] += 1
                    turnier_details[name][discipline][year].append((place, total_players))
                
# Funktion zur Verarbeitung von Qualifying
def process_qualifying(qualifying, discipline, year, elimination_count):
    if 'standings' in qualifying:
        standings = qualifying['standings']
        rankEli = elimination_count + 1
        total_players = len(standings)
        for rank, standing in enumerate(standings, start=1):
            name = standing['name']
            if name not in platzierung_data or year not in platzierung_data[name][discipline]:
                platzierung_data[name][discipline][year] += total_players / rankEli
                teilnahmen_data[name][discipline][year] += 1
                turnier_details[name][discipline][year].append((rankEli, total_players))
                rankEli += 1

# Durchlaufen der Turnierdateien und Aktualisieren der Platzierungsdaten
for file_name in tournament_files:
    file_path = os.path.join(tournaments_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        tournament_data = json.load(file)
    
    discipline = tournament_data.get('mode', 'unknown')
    year = parser.parse(tournament_data['createdAt']).year
    year_data[year]=year
    
    elimination_count = 0
    # Verarbeiten der Eliminations
    if 'eliminations' in tournament_data:
        if(len(tournament_data['eliminations']) == 0):
            continue
        else:
            process_eliminations(tournament_data['eliminations'], discipline, year, len(tournament_data['qualifying'][0]['standings']))
            elimination_count = len(tournament_data['eliminations'][0]['standings'])
    
    # Verarbeiten der Qualifikationsspiele
    if 'qualifying' in tournament_data:
        process_qualifying(tournament_data['qualifying'][0], discipline, year, elimination_count)

# Zusätzliche Disziplinen für die Jahre hinzufügen
additional_disciplines = {
    2023: ['double_elimination', 'round_robin', 'monster_dyp'],
    2024: ['whist', 'round_robin', 'monster_dyp']
}

for year, disciplines in additional_disciplines.items():
    for discipline in disciplines:
        if discipline not in platzierung_data:
            platzierung_data[discipline] = defaultdict(lambda: defaultdict(float))
            teilnahmen_data[discipline] = defaultdict(lambda: defaultdict(int))
            turnier_details[discipline] = defaultdict(lambda: defaultdict(list))

# GUI erstellen
class RanglisteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rangliste")
        self.geometry("1200x600")

        current_year = datetime.now().year

        self.year_label = tk.Label(self, text="Jahr:")
        self.year_label.pack(pady=10)

        self.year_combobox = ttk.Combobox(self, values=sorted(set(y for data in platzierung_data.values() for d in data.values() for y in d)), state="readonly")
        self.year_combobox.set(current_year)
        self.year_combobox.pack(pady=10)
        self.year_combobox.bind("<<ComboboxSelected>>", self.update_disciplines)

        self.discipline_label = tk.Label(self, text="Disziplin:")
        self.discipline_label.pack(pady=10)

        self.discipline_combobox = ttk.Combobox(self, state="readonly")
        self.discipline_combobox.set("monster_dyp")
        self.discipline_combobox.pack(pady=10)
        self.discipline_combobox.bind("<<ComboboxSelected>>", self.update_table)

        self.view_option = tk.StringVar(value="Turnierdetails")
        self.view_option_menu = ttk.OptionMenu(self, self.view_option, "Turnierdetails", "Turnierdetails", "Häufigkeiten", command=self.update_table)
        self.view_option_menu.pack(pady=10)

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.update_disciplines()
        self.update_table()

    def update_disciplines(self, event=None):
        year = self.year_combobox.get()
        disciplines = sorted(set(d for player in platzierung_data for d in platzierung_data[player] if year in platzierung_data[player][d]))
        # Zusätzliche Disziplinen für das ausgewählte Jahr hinzufügen
        if int(year) in additional_disciplines:
            disciplines.extend(additional_disciplines[int(year)])
            disciplines = sorted(set(disciplines))
        self.discipline_combobox["values"] = disciplines
        if "monster_dyp" in disciplines:
            self.discipline_combobox.set("monster_dyp")
        elif disciplines:
            self.discipline_combobox.set(disciplines[0])
        self.update_table()

    def update_table(self, event=None):
        year = self.year_combobox.get()
        discipline = self.discipline_combobox.get()
        view_option = self.view_option.get()
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ("Disziplin", "Platz", "Spieler", "Punkte", "Details")
        self.tree.heading("Disziplin", text="Disziplin")
        self.tree.heading("Platz", text="Platz")
        self.tree.heading("Spieler", text="Spieler")
        self.tree.heading("Punkte", text="Punkte")
        self.tree.heading("Details", text="Details")

        if view_option == "Häufigkeiten":
            max_platz = max(p for data in turnier_details.values() for d in data.values() for y in d.values() for p, _ in y)
            self.tree["columns"] = ["Disziplin", "Platz", "Spieler", "Punkte"] + [str(i) for i in range(1, max_platz + 1)]
            for i in range(1, max_platz + 1):
                self.tree.heading(str(i), text=str(i))

        sorted_players = sorted(
            [(player, platzierung_data[player][discipline][int(year)]) for player in platzierung_data if teilnahmen_data[player][discipline][int(year)] > 0],
            key=lambda x: x[1],
            reverse=True
        )
        for rank, (player, platzierung) in enumerate(sorted_players, start=1):
            if view_option == "Turnierdetails":
                details = "; ".join([f"Platz: {p}, Teilnehmer: {t}" for p, t in turnier_details[player][discipline][int(year)]])
                self.tree.insert("", "end", values=(discipline, rank, player, f"{platzierung:.2f}", details))
            else:  # view_option == "Häufigkeiten"
                platzierungen = [p for p, _ in turnier_details[player][discipline][int(year)]]
                max_platz = max(platzierungen) if platzierungen else 0
                haeufigkeiten = [platzierungen.count(i) for i in range(1, max_platz + 1)]
                row_values = [discipline, rank, player, f"{platzierung:.2f}"] + haeufigkeiten
                self.tree.insert("", "end", values=row_values)

if __name__ == "__main__":
    try:
        app = RanglisteApp()
        app.mainloop()
    except Exception as e:
        print(f"Error: {e}")

# JSON-Datei mit den Daten erstellen
data = {
    "platzierungData": platzierung_data,
    "teilnahmenData": teilnahmen_data,
    "turnierDetails": turnier_details,
    "additionalDisciplines": additional_disciplines,
    "yearData": year_data
}

with open('rangliste.json', 'w') as json_file:
    json.dump(data, json_file)
