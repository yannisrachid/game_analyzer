import pandas as pd
import os
import matplotlib as mpl
from matplotlib import pyplot as plt
from mplsoccer.pitch import VerticalPitch
import os
from fuzzywuzzy import process
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

class PositionalMap:
    """
    Display the positional map of both teams with all the necessary details (game, score, visualisations, logos...).
    """
    def __init__(self, events_df, mins):
        self.events_df = events_df
        self.mins = mins
        self.ax = None

    def plot_positional_map(self):
        """
        Plot the positional map for the both teams.

        Returns:
        - matplotlib.Fig: The positional map.
        """
        mins = self.mins
        events_df = self.events_df
        PositionalMap.league = events_df.loc[0, "league"]
        PositionalMap.score = events_df.loc[0, "score"].replace(":", "-")
        PositionalMap.date = events_df.loc[0, "date"].split("T")[0]
        PositionalMap.home_club = events_df[events_df["h_a"] == "h"]["team_name"].values[0].replace("-", " ")
        PositionalMap.away_club = events_df[events_df["h_a"] == "a"]["team_name"].values[0].replace("-", " ")

        plt.style.use('fivethirtyeight')
        cmap = mpl.colors.LinearSegmentedColormap.from_list("", ['#b5dcff',
                                                                '#97cbfa',
                                                                '#70b9fa',
                                                                '#2f97f5',
                                                                '#0586fa'
                                                                ])

        fig, ax = plt.subplots(1,2,figsize=(6,6), dpi=400)
        self.ax = ax
        teamId_home = events_df[events_df['h_a'] == 'h']['team_id'].unique()[0]
        teamId_away = events_df[events_df['h_a'] == 'a']['team_id'].unique()[0]

        for i, teamid in enumerate([teamId_home, teamId_away]):
            df = events_df[events_df["team_id"] == teamid]
            mask_minutes = (df['minute'] > mins[0]) & (df['minute'] < mins[1])
            df = df[mask_minutes]

            pitch = VerticalPitch(pitch_type='opta', 
                                    line_color='#7c7c7c',
                                    goal_type='box',
                                    linewidth=0.5,
                                    pad_bottom=10)
                
            #plot vertical pitches
            pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
            
            bin_statistic = pitch.bin_statistic_positional(df.x, df.y, statistic='count', positional='full', normalize=True)
            
            pitch.heatmap_positional(bin_statistic, ax=ax[i], cmap=cmap, edgecolors='#7c7c7c')
            # pitch.scatter(df.x, df.y, c='white', s=1, ax=ax[i])
            labels = pitch.label_heatmap(bin_statistic, color='#f4edf0', fontsize=14,
                                        ax=ax[i], ha='center', va='center',
                                        str_format='{:.0%}')
            
            self.add_legend(fig, i)
            
        return fig
            
    def add_legend(self, fig, i):
        """
        Add the legend for each ax (each passing network team) in the fig.

        Parameters:
        - fig (matplotlib.Fig): the matplotlib figure
        - i (int): the index for each ax of the figure.
        """
        ax = self.ax[i]

        # Adding annotations
        ax.annotate(xy=(102, 58), xytext=(102, 43), zorder=2, text='', ha='center',
                    arrowprops=dict(arrowstyle='->, head_length=0.3, head_width=0.1',
                                    color='#7c7c7c', lw=0.5))
        ax.annotate(xy=(104, 45), text='Play direction', ha='center', color='#7c7c7c', rotation=90, size=4)
        ax.annotate(xy=(50, -5), text=f'Passes from minutes {self.mins[0]} to {self.mins[1]}', ha='center', color='#7c7c7c', size=6)

        font = 'serif'
        fig.text(x=0.5, y=.92, s=f"Positional map for {PositionalMap.home_club} {PositionalMap.score} {PositionalMap.away_club}", weight='bold', va="bottom", ha="center", fontsize=10, font=font)
        fig.text(x=0.26, y=.875, s=PositionalMap.home_club, weight='bold', va="bottom", ha="center", fontsize=8, font=font)
        fig.text(x=0.745, y=.875, s=PositionalMap.away_club, weight='bold', va="bottom", ha="center", fontsize=8, font=font)
        fig.text(x=0.5, y=0.90, s=f"{PositionalMap.league} | Season 2023-2024 | {PositionalMap.date}", va="bottom", ha="center", fontsize=6, font=font)

        fig.text(x=0.87, y=0.15, s="Yannis R", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.2, y=0.15, s="linkedin.com/in/yannis-rachid-230/", va="bottom", ha="center", weight='bold', fontsize=6, font=font, color='black')

        home_logo_path = self.get_path_logo(PositionalMap.league, PositionalMap.home_club)
        home_img = Image.open(home_logo_path)

        away_logo_path = self.get_path_logo(PositionalMap.league, PositionalMap.away_club)
        away_img = Image.open(away_logo_path)

        pc = 0.35
        home_img_redim = home_img.resize((int(home_img.width * pc), int(home_img.height * pc)))
        away_img_redim = away_img.resize((int(away_img.width * pc), int(away_img.height * pc)))

        fig.figimage(home_img_redim, xo=80, yo=880, zorder=2)
        fig.figimage(away_img_redim, xo=1040, yo=880, zorder=2)
        
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)

    def get_path_logo(self, league, club):
        """
        Get the path logo for a selected team.

        Parameters:
        - league (string): The league club.
        - club (string): The selected club.

        Returns:
        - string: The path of the png logo.
        """
        dict_logo = {'EPL':'GB1',
                    'Serie A':'IT1',
                    'La Liga':'ES1',
                    'Bundesliga':'L1',
                    'Ligue 1':'FR1',
                    'Eredivisie': 'NL1',
                    'Liga Nos': 'PO1',
                    'Jupiler Pro League': 'BE1'}
        
        club = club.replace('-', ' ')

        path_to_league_logo = f"logos/{dict_logo[league]}"
        choices = os.listdir(path_to_league_logo)
        logo_name_matched = process.extractOne(club, choices, score_cutoff=80)
        
        if logo_name_matched != None:
            logo_name_matched = logo_name_matched[0]
            path_return = os.path.join(path_to_league_logo, logo_name_matched)
            return path_return
        else:
            return "img/logo_tr.png"
                