import pandas as pd
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.patches import ArrowStyle,FancyArrowPatch
from mplsoccer.pitch import VerticalPitch
import seaborn as sns
import os
from fuzzywuzzy import process
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

class PlayerVisualization():
    """
    Display all the player visualisations with all the necessary details (game, score, visualisations, logos...).
    """
    def __init__(self, events_df, player, mins, club):
        self.events_df = events_df
        self.player = player
        self.mins = mins
        self.club = club.replace("-", " ")
        self.ax = None
        self.head_length = 0.3
        self.head_width = 0.1

    def change_range(self, value, old_range, new_range):
        """
        Changes the value relative to all the values in the Series.

        Parameters:
        - value (int): Current value to change
        - old_range (tuple): Current range of values (min_value, max_value) for the Series.
        - new_range (tuple): New range of values (min_node_size, max_node_size).

        Returns:
        - int: New value in the new range.
        """
        new_value = ((value-old_range[0]) / (old_range[1]-old_range[0])) * (new_range[1]-new_range[0]) + new_range[0]
        if new_value >= new_range[1]:
            return new_range[1]
        elif new_value <= new_range[0]:
            return new_range[0]
        else:
            return new_value
        
    def preprocessing(self, events_df, player, mins):
        """
        Performs all data pre-processing based on information entered by the user.

        Parameters:
        - events_df (pd.DataFrame): All the events of the game.
        - player (string): The player selected by the user.
        - mins (tuple): The game timelapse selected by the user.

        Returns:
        - pd.DataFrame: Preprocesses the events DataFrame with the user choices and instantiates necessary bodies info.
        """
        df = events_df[(events_df['minute'] >= mins[0]) & (events_df['minute'] <= mins[1])].reset_index(drop=True)
        df_player = df[df["player_name"] == player].reset_index(drop=True)
        PlayerVisualization.league = events_df.loc[0, "league"]
        PlayerVisualization.score = events_df.loc[0, "score"].replace(":", "-")
        PlayerVisualization.date = events_df.loc[0, "date"].split("T")[0]
        return df_player
    
    def draw_pitch(self):
        """
        Draw a Vertical Pitch with the Opta type.

        Returns:
        - matplotlib.Fig: The matplotlib figure.
        - matplotlib.ax: The matplotlib ax.
        - pitch: The vertical pitch.
        """
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=[18,12], dpi=400)
        self.ax = ax
        pitch = VerticalPitch(pitch_type='opta', 
                                line_color='#7c7c7c',
                                goal_type='box',
                                linewidth=0.5,
                                pad_bottom=10)
            
        pitch.draw(ax=self.ax, constrained_layout=False, tight_layout=False)
        ax.plot([21, 21], [ax.get_ylim()[0]+19, ax.get_ylim()[1]-19], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        ax.plot([78.8, 78.8], [ax.get_ylim()[0]+19, ax.get_ylim()[1]-19], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        ax.plot([36.8, 36.8], [ax.get_ylim()[0]+8.5, ax.get_ylim()[1]-8.5], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        ax.plot([100-36.8, 100-36.8], [ax.get_ylim()[0]+8.5, ax.get_ylim()[1]-8.5], ls=':',dashes=(1, 3), color='gray', lw=0.4)

        ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [83,83], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [67, 67], ls=':',dashes=(1, 3), color='gray', lw=0.4)

        ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [100-83,100-83], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [100-67, 100-67], ls=':',dashes=(1, 3), color='gray', lw=0.4)

        ax.annotate(xy=(102, 58), xytext=(102, 43), zorder=2, text='', ha='center',
                    arrowprops=dict(arrowstyle=f'->, head_length={self.head_length}, head_width={self.head_width}',
                                    color='#7c7c7c', lw=0.5))
        ax.annotate(xy=(104, 45), text='Play direction', ha='center', color='#7c7c7c', rotation=90, size=10)
        ax.annotate(xy=(50, -5), text=f'Events from minutes {self.mins[0]} to {self.mins[1]}', ha='center', color='#7c7c7c', size=10)
        return fig, ax, pitch

    def plot_dribbles(self):
        """
        Plot the player dribble map.

        Returns:
        - matplotlib.Fig: The matplotlib figure with all the dribbles.
        """
        # Prepare data and pitch
        df = self.preprocessing(self.events_df, self.player, self.mins)
        fig, ax, pitch = self.draw_pitch()

        # Get dribbles
        df_dribbles = df[df["type_name"] == "TakeOn"]
        df_dribbles_lt = df_dribbles[df_dribbles["x"] > 67]

        total = len(df_dribbles)
        dribbles_lt = len(df_dribbles_lt)

        try:
            success = df_dribbles["outcome"].value_counts()[True]
        except KeyError:
            success = 0

        try:
            success_lt = df_dribbles_lt["outcome"].value_counts()[True]
        except KeyError:
            success_lt = 0
        except ZeroDivisionError:
            success_lt = 0

        if total != 0:
            pct = int((success/total) * 100)
        else:
            pct = 0
        
        if dribbles_lt != 0:
            pct_lt = int((success_lt/dribbles_lt) * 100)
        else:
            pct_lt = 0

        marker_size = 12
        marker_type = "^"

        # Plot
        for index, row in df_dribbles.iterrows():
            loc_z = row["x"]
            loc_x = row["y"]
            loc_y = loc_z
            marker_color = "green" if row["outcome"] == True else "red"
            ax.plot(loc_x, loc_y, marker_type, color=marker_color, markersize=marker_size, zorder=5)

        # Legend details
        # Créer des marqueurs personnalisés pour la légende
        green_triangle = plt.Line2D([0], [0], marker='^', color='g', markersize=10, label='Successful dribble', linestyle='None')
        red_triangle = plt.Line2D([0], [0], marker='^', color='r', markersize=10, label='Unsuccessful dribble', linestyle='None')

        
        font = 'serif'
        fig.text(x=0.6, y=1, s=f"{self.player} | Dribble map | {self.club}", weight='bold', va="bottom", ha="center", fontsize=18, font=font)
        fig.text(x=0.6, y=0.982, s=f"{PlayerVisualization.league} | Season 2023-2024 | {PlayerVisualization.date}", va="bottom", ha="center", fontsize=12, font=font)
        fig.text(x=0.37, y=-0.0, s="linkedin.com/in/yannis-rachid-230/", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')

        fig.text(x=0.8, y=0.8, s="GLOBAL", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.77, s=f"{total} dribbles attempted", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.75, s=f"{success} successful dribbles", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.73, s=f"{pct}% of successful dribbles", va="bottom", ha="center", fontsize=12, font=font, color='black')

        fig.text(x=0.8, y=0.65, s="DRIBBLES IN LAST THIRD", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.62, s=f"{dribbles_lt} dribbles attempted in last third", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.60, s=f"{success_lt} successful dribbles in last third", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.58, s=f"{pct_lt}% of successful dribbles in last third", va="bottom", ha="center", fontsize=12, font=font, color='black')

        fig.text(x=0.8, y=0.5, s=f"LEGEND", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        ax.legend(handles=[green_triangle, red_triangle], loc='upper center', bbox_to_anchor=(1.22, 0.49))

        # fig_logo = plt.figure()
        logo_path = self.get_path_logo(self.league, self.club)
        img = plt.imread(logo_path)
        fig.figimage(img, xo=1830, yo=2100, zorder=2)

        plt.tight_layout()
        
        return fig
    
    def plot_passes_game(self):
        """
        Plot the player pass map.

        Returns:
        - matplotlib.Fig: The matplotlib figure with all the passes.
        """
        df = self.preprocessing(self.events_df, self.player, self.mins)
        fig, ax, pitch = self.draw_pitch()

        df_passes = df[df["type_name"] == "Pass"]
        df_forward = df_passes[df_passes["x"] < df_passes["end_x"]]
        df_last_third = df_passes[df_passes["end_x"] > 67]

        total = len(df_passes)
        forward_passes = len(df_forward)
        last_third_passes = len(df_last_third)

        try:
            success = df_passes["outcome"].value_counts()[True]
        except KeyError:
            success = 0
        try:
            success_forward = df_forward["outcome"].value_counts()[True]
        except KeyError:
            success_forward = 0
        try:
            success_lt = df_last_third["outcome"].value_counts()[True]
        except KeyError:
            success_lt = 0

        if total != 0:
            pct = int((success/total) * 100)
        else:
            pct = 0

        if forward_passes != 0:
            pct_forward = int((success_forward/forward_passes) * 100)
        else:
            pct_forward = 0

        if last_third_passes != 0:
            pct_lt = int((success_lt/last_third_passes) * 100)
        else:
            pct_lt = 0

        for index, row in df_passes.iterrows():
            start_z = row["x"]
            start_x = row["y"]
            start_y = start_z

            end_z = row["end_x"]
            end_x = row["end_y"]
            end_y = end_z

            pass_value = row["xT_added"]

            key_pass = False
            for qualifier in row["qualifiers"]:
                if qualifier["type"]["displayName"] == "KeyPass":
                    key_pass = True

            if key_pass == True:
                arrow_color = "orange"
            elif row["outcome"] == True:
                arrow_color = "green"
            else:
                arrow_color = "red"

            line_width = 0.5
            alpha = 1

            dx = end_x-start_x
            dy = end_y-start_y
            rel = 68/105
            shift_x = 2
            shift_y = shift_x*rel

            # pitch.lines(row["x"], row["y"], row["end_x"], row["end_y"], color=arrow_color, ax=ax, lw=3, transparent=True)
            pitch.lines(row["x"], row["y"], row["end_x"], row["end_y"], color=arrow_color, ax=ax, lw=4, comet=True, transparent=True)
            # pitch.scatter(row["end_x"], row["end_y"], s=50, c="white", edgecolors=arrow_color, ax=ax, lw=2, zorder=2)
            pitch.scatter(row["end_x"], row["end_y"], s=20, c=arrow_color, edgecolors=arrow_color, ax=ax, lw=2, zorder=2)

        font = 'serif'
        fig.text(x=0.6, y=1, s=f"{self.player} | Pass map | {self.club}", weight='bold', va="bottom", ha="center", fontsize=20, font=font)
        fig.text(x=0.6, y=0.982, s=f"{PlayerVisualization.league} | Season 2023-2024 | {PlayerVisualization.date}", va="bottom", ha="center", fontsize=12, font=font)
        fig.text(x=0.87, y=-0.0, s="Yannis R", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.37, y=-0.0, s="linkedin.com/in/yannis-rachid-230/", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')

        fig.text(x=0.8, y=0.8, s=f"GLOBAL PASSES", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.77, s=f"{total} passes attempted", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.75, s=f"{success} successful passes", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.73, s=f"{pct}% of successful passes", va="bottom", ha="center", fontsize=12, font=font, color='black')

        fig.text(x=0.8, y=0.65, s=f"FORWARD PASSES", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.62, s=f"{forward_passes} forward passes attempted", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.60, s=f"{success_forward} successful forward passes", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.58, s=f"{pct_forward}% of successful forward passes", va="bottom", ha="center", fontsize=12, font=font, color='black')

        fig.text(x=0.8, y=0.50, s=f"LAST THIRD PASSES", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.47, s=f"{last_third_passes} passes in last third attempted", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.45, s=f"{success_lt} successful passes in last third", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.43, s=f"{pct_lt}% of successful passes in last third", va="bottom", ha="center", fontsize=12, font=font, color='black')

        style = ArrowStyle('->', head_length=5, head_width=3)
        green_arrow_patch = FancyArrowPatch((1670, 780), (1670+50, 780+50), arrowstyle=style, color='green')
        red_arrow_patch = FancyArrowPatch((1670, 730), (1670+50, 730+50), arrowstyle=style, color='red')
        orange_arrow_patch = FancyArrowPatch((1670, 680), (1670+50, 680+50), arrowstyle=style, color='orange')
        fig.patches.extend([green_arrow_patch, red_arrow_patch, orange_arrow_patch])
        fig.text(x=0.8, y=0.35, s=f"LEGEND", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.32, s="Successful Pass", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.806, y=0.30, s="Unsuccessful Pass", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.784, y=0.28, s="Key Pass", va="bottom", ha="center", fontsize=12, font=font, color='black')

        logo_path = self.get_path_logo(self.league, self.club)  # Chemin d'accès à l'image du logo
        img = plt.imread(logo_path)
        fig.figimage(img, xo=1830, yo=2100, zorder=2)
        plt.tight_layout()

        return fig
    

    def plot_heatmap_game(self):
        """
        Plot the player heat map.

        Returns:
        - matplotlib.Fig: The matplotlib figure with all the events.
        """
        df = self.preprocessing(self.events_df, self.player, self.mins)
        fig, ax, pitch = self.draw_pitch()

        events_location_list = [[row["y"], row["x"]] for index, row in df.iterrows() if not pd.isnull(row["y"]) and not pd.isnull(row["x"])]
        events_location = np.array(events_location_list)

        x = events_location[:,0]
        y = events_location[:,1]

        # plot the heatmap
        cmap = plt.get_cmap("hot").reversed()
        ax = sns.kdeplot(x=x, y=y, shade=True, cmap=cmap, bw=0.1, n_levels=200)

        font = 'serif'
        fig.text(x=0.5, y=1, s=f"{self.player} | Heat map | {self.club}", weight='bold', va="bottom", ha="center", fontsize=12, font=font)
        fig.text(x=0.5, y=0.982, s=f"{PlayerVisualization.league} | Season 2023-2024 | {PlayerVisualization.date}", va="bottom", ha="center", fontsize=10, font=font)
        fig.text(x=0.7, y=-0.0, s="Yannis R", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.37, y=-0.0, s="linkedin.com/in/yannis-rachid-230/", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')

        logo_path = self.get_path_logo(self.league, self.club)
        img = Image.open(logo_path)
        pc = 0.75
        img_redim = img.resize((int(img.width * pc), int(img.height * pc)))
        fig.figimage(img_redim, xo=1300, yo=2330, zorder=2)

        plt.tight_layout()

        return fig
    
    def get_shot_data(self, dictionnary_list):
        """
        Get the player shot data details.

        Parameters:
        - dictionnary_list (list): The player data shot infos.

        Returns:
        - dict: The dict with all necessary informations.
        """
        if type(dictionnary_list) == "str":
            dictionnary_list = eval(dictionnary_list)
        # Variables init
        type_shot = None
        goal_mouth_z = None
        goal_mouth_y = None

        # Iterate each dict in the list
        for item in dictionnary_list:
            # Get the type event
            if 'type' in item.keys() and 'displayName' in item['type'].keys():
                event_type = item['type']['displayName']
                if event_type in ['RightFoot', 'LeftFoot', 'Head']:
                    type_shot = event_type
            
            # Get the GoalMouthZ value
            if 'type' in item.keys() and 'displayName' in item['type'].keys():
                if item['type']['displayName'] == 'GoalMouthZ' and 'value' in item:
                    goal_mouth_z = float(item['value'])
            
            # Get the GoalMouthY value
            if 'type' in item.keys() and 'displayName' in item['type'].keys():
                if item['type']['displayName'] == 'GoalMouthY' and 'value' in item:
                    goal_mouth_y = float(item['value'])
        
        return {"type": type_shot, "goal_mouth_z": goal_mouth_z, "goal_mouth_y": goal_mouth_y}
    
    def plot_shotmap_player(self):
        """
        Plot the player shot map.

        Returns:
        - matplotlib.Fig: The matplotlib figure with all the shots.
        """
        df = self.preprocessing(self.events_df, self.player, self.mins)
        df["shot_data"] = df["qualifiers"].apply(self.get_shot_data)
        plt.style.use('fivethirtyeight')
        used_labels = []

        pitch = VerticalPitch(pitch_type='opta', 
                                line_color='#7c7c7c',
                                goal_type='box',
                                linewidth=0.5,
                                pad_bottom=-10,
                                half=True)

        fig, axs = pitch.grid(figheight=8, endnote_height=0,  # no endnote
                            title_height=0.1, title_space=0.02,
                            # Turn off the endnote/title axis. I usually do this after
                            # I am happy with the chart layout and text placement
                            axis=False,
                            grid_height=0.83)

        #pitch.draw(ax=ax, constrained_layout=False, tight_layout=False)

        df_shots = df[df["shot"] == True].reset_index()

        for index, row in df_shots.iterrows():
            marker_color = "black" if row["goal"] == True else "#ADADAD"
            type_shot = row["shot_data"]["type"]
            if row["goal"] == True:
                label = f"Goal: {type_shot}"
                edge_color = "green" if row["shot_data"]["type"] == "RightFoot" else ("red" if row["shot_data"]["type"] == "LeftFoot" else "blue")
            else:
                label = "Attempted"
                edge_color = None

            if label not in used_labels:
                pitch.scatter(row["x"], row["y"], s=200, c=marker_color, edgecolors=edge_color, label=label, ax=axs["pitch"], linewidths=1)
                used_labels.append(label)
            else:
                pitch.scatter(row["x"], row["y"], s=200, c=marker_color, edgecolors=edge_color, ax=axs["pitch"], linewidths=1)
            #if label == "Goal":
            #    shot_data = row["shot_data"]
            #    pitch.lines(row["x"], row["y"], row["shot_data"]["goal_mouth_z"], row["shot_data"]["goal_mouth_y"], comet=True, label=row["shot_data"]["type"], color='#cb5a4c', ax=axs['pitch'])

        legend = axs['pitch'].legend(loc='center left', labelspacing=0.5)

        font = "serif"
        axs['title'].text(0.5, 0.5, s=f"{self.player} | Shot map | {self.club}", weight='bold', va="bottom", ha="center", fontsize=18, font=font)
        axs['title'].text(0.5, 0.1, s=f"{PlayerVisualization.league} | Season 2023-2024 | {PlayerVisualization.date}", va="bottom", ha="center", fontsize=12, font=font)

        # fig_logo = plt.figure()
        logo_path = self.get_path_logo(self.league, self.club)
        img = plt.imread(logo_path)
        fig.figimage(img, xo=1700, yo=1300, zorder=2)

        return fig
    
    def plot_game_player_defensive(self):
        """
        Plot the player defensive map.

        Returns:
        - matplotlib.Fig: The matplotlib figure with all the defensives map.
        """
        df = self.preprocessing(self.events_df, self.player, self.mins)
        fig, ax, pitch = self.draw_pitch()

        df_def = df[df["type_name"].isin(["Tackle", "Interception", "BlockedPass", "Clearance", "Aerial"])]
        df_def = df_def[df_def["outcome"] == True].reset_index()

        color_dict = {
            "Tackle": "yellow",
            "Interception": "orange", 
            "BlockedPass": "red", 
            "Clearance": "green", 
            "Aerial": "blue"
        }

        used_labels = []

        for index, row in df_def.iterrows():
            marker_color = color_dict[row["type_name"]]

            label = row["type_name"]

            if label not in used_labels:
                pitch.scatter(row["x"], row["y"], s=200, c=marker_color, label=label, linewidths=1, ax=ax)
                used_labels.append(label)
            else:
                pitch.scatter(row["x"], row["y"], s=200, c=marker_color, linewidths=1, ax=ax)

        legend = ax.legend(loc='best', labelspacing=0.5)

        font = 'serif'
        fig.text(x=0.5, y=0.905, s=f"{self.player} | Defensive map | {self.club}", weight='bold', va="bottom", ha="center", fontsize=12, font=font)
        fig.text(x=0.5, y=0.890, s=f"{PlayerVisualization.league} | Season 2023-2024 | {PlayerVisualization.date}", va="bottom", ha="center", fontsize=10, font=font)
        fig.text(x=0.7, y=-0.0, s="Yannis R", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.37, y=-0.0, s="linkedin.com/in/yannis-rachid-230/", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')

        # fig_logo = plt.figure()
        logo_path = self.get_path_logo(self.league, self.club)
        img = Image.open(logo_path)
        pc = 0.75
        img_redim = img.resize((int(img.width * pc), int(img.height * pc)))
        #img = plt.imread(logo_path)
        fig.figimage(img_redim, xo=1300, yo=2100, zorder=2)

        return fig
    
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