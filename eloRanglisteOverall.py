import tkinter as tk
from tkinter import ttk
from eloRangliste import get_elo_data

# Daten importieren
elo_ratings, games_played, player_data = get_elo_data()

# GUI erstellen
class EloRanglisteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Elo Rangliste")
        self.geometry("1200x600")

        self.discipline_label = tk.Label(self, text="Disziplin:")
        self.discipline_label.pack(pady=10)

        self.discipline_combobox = ttk.Combobox(self, values=sorted(set(d for data in elo_ratings.values() for d in data)), state="readonly")
        self.discipline_combobox.pack(pady=10)
        self.discipline_combobox.bind("<<ComboboxSelected>>", self.update_table)

        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        self.tree["columns"] = ("Rang", "Spieler", "Elo Punkte", "Spiele")
        self.tree.heading("Rang", text="Rang", command=lambda: self.sort_column("Rang", False))
        self.tree.heading("Spieler", text="Spieler", command=lambda: self.sort_column("Spieler", False))
        self.tree.heading("Elo Punkte", text="Elo Punkte", command=lambda: self.sort_column("Elo Punkte", False))
        self.tree.heading("Spiele", text="Spiele", command=lambda: self.sort_column("Spiele", False))
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

    def update_table(self, event=None):
        discipline = self.discipline_combobox.get()
        self.tree.delete(*self.tree.get_children())
        sorted_players = sorted(elo_ratings.items(), key=lambda x: x[1][discipline], reverse=True)
        for rank, (player, ratings) in enumerate(sorted_players, start=1):
            elo = ratings[discipline]
            games = games_played[player][discipline]
            self.tree.insert("", "end", values=(rank, player, f"{elo:.2f}", games))

    def sort_column(self, col, reverse):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

if __name__ == "__main__":
    app = EloRanglisteApp()
    app.mainloop()