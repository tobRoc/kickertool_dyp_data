import tkinter as tk
from tkinter import ttk
from eloRangliste import get_elo_data

# Daten importieren
elo_ratings, games_played, player_data = get_elo_data()
            
def IndexOfPlayer(list, searchString):
    i=0
    for i in range (len(list)):
        if list[i].__str__().casefold()==searchString.casefold():
            break
    return i

# GUI erstellen
class EloRanglisteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Elo Rangliste")
        self.geometry("1200x600")

        self.player_label = tk.Label(self, text="Spieler:")
        self.player_label.pack(pady=10)

        self.player_combobox = ttk.Combobox(self, values=sorted(player_data.keys()))
        self.player_combobox.pack(pady=10)
        self.player_combobox.bind("<<ComboboxSelected>>", self.update_table)

        self.tree = ttk.Treeview(self, show="headings")
        self.tree["columns"] = ("Datum", "Spieler", "Elo Punkte", "Team 1 Spieler 1", "Elo Punkte 1", "Team 1 Spieler 2", "Elo Punkte 2", "Team 2 Spieler 1", "Elo Punkte 1", "Team 2 Spieler 2", "Elo Punkte 2", "Ergebnis")
        self.tree.heading("Datum", text="Datum")
        self.tree.heading("Spieler", text="Spieler")
        self.tree.heading("Elo Punkte", text="Elo Punkte")
        self.tree.heading("Team 1 Spieler 1", text="Team 1 Spieler 1")
        self.tree.heading("Elo Punkte 1", text="Elo Punkte 1")
        self.tree.heading("Team 1 Spieler 2", text="Team 1 Spieler 2")
        self.tree.heading("Elo Punkte 2", text="Elo Punkte 2")
        self.tree.heading("Team 2 Spieler 1", text="Team 2 Spieler 1")
        self.tree.heading("Elo Punkte 1", text="Elo Punkte 1")
        self.tree.heading("Team 2 Spieler 2", text="Team 2 Spieler 2")
        self.tree.heading("Elo Punkte 2", text="Elo Punkte 2")
        self.tree.heading("Ergebnis", text="Ergebnis")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

    def update_table(self, event=None):
        player = self.player_combobox.get()
        self.tree.delete(*self.tree.get_children())
        for match in player_data[player]:
            date, player1_team1, player1_team1_elo, player2_team1, player2_team1_elo, player1_team2, player1_team2_elo, player2_team2, player2_team2_elo, result1, result2 = match
            result = f"{result1}-{result2}"
            index = IndexOfPlayer(match, player)
            self.tree.insert("", "end", values=(date, player, match[index+1], player1_team1, player1_team1_elo, player2_team1, player2_team1_elo, player1_team2, player1_team2_elo, player2_team2, player2_team2_elo, result))

    def sort_column(self, col, reverse):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def filter_combobox(self, event):
        value = event.widget.get().lower()
        filtered_values = [player for player in player_data.keys() if value in player.lower()]
        self.player_combobox['values'] = filtered_values
        self.player_combobox.event_generate('<Down>')
if __name__ == "__main__":
    app = EloRanglisteApp()
    app.mainloop()