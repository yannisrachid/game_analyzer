import pandas as pd
import os
import json
import numpy as np
from scipy.stats import binned_statistic_2d
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.patches import RegularPolygon, Arrow, ArrowStyle,FancyArrowPatch, Circle,FancyArrow
from mplsoccer.pitch import Pitch, VerticalPitch
from matplotlib.colors import Normalize
from matplotlib import cm
from highlight_text import fig_text, ax_text
from clubs import clubs_list
import warnings
warnings.filterwarnings("ignore")

class PassingNetwork():
    def __init__(self, events_df, mins):
        self.events_df = events_df
        self.mins = mins
        self.ax = None
        self.res_dict = self.create_res_dict()
        self.head_length = 0.3
        self.head_width = 0.1

    def change_range(self, value, old_range, new_range):
        new_value = ((value-old_range[0]) / (old_range[1]-old_range[0])) * (new_range[1]-new_range[0]) + new_range[0]
        if new_value >= new_range[1]:
            return new_range[1]
        elif new_value <= new_range[0]:
            return new_range[0]
        else:
            return new_value
        
    def create_res_dict(self):
        res_dict = {}

        mins = self.mins

        teamIds = self.events_df['team_id'].unique()
        PassingNetwork.league = self.events_df.loc[0, "league"]
        PassingNetwork.score = self.events_df.loc[0, "score"].replace(":", "-")
        PassingNetwork.date = self.events_df.loc[0, "date"].split("T")[0]
        PassingNetwork.home_club = self.events_df[self.events_df["h_a"] == "h"]["team_name"].values[0]
        PassingNetwork.away_club = self.events_df[self.events_df["h_a"] == "a"]["team_name"].values[0]

        for teamId in teamIds:
            
            mask = self.events_df['team_id'] == teamId
            df_ = self.events_df[mask]
            
            teamName = df_['team_name'].unique()[0]
                
            venue = 'home' if df_[df_['team_id'] == teamId]['h_a'].unique()[0] == 'h' else 'away'

            mask1 = df_['cardType'].apply(lambda x: x in ["SecondYellow", "Red"])
            first_red_card_minute = df_[mask1].minute.min()

            mask2 = self.events_df['type_name'] == 'SubstitutionOn'
            first_sub_min = self.events_df[mask2].minute.min()

            max_minute = df_.minute.max()

            minutes_with_first_eleven = min(first_sub_min, first_red_card_minute, max_minute)
            
            passes_df = df_.reset_index().drop('index', axis=1)
            passes_df['player_id'] = passes_df['player_id'].astype('Int64')
            passes_df = passes_df[passes_df['player_id'].notnull()]
            passes_df['passRecipientName'] = passes_df['player_name'].shift(-1)
            passes_df = passes_df[passes_df['passRecipientName'].notnull()]
            
            #DF with all passes
            mask1 = passes_df['type_name'].apply(lambda x: x in ['Pass'])
            passes_df_all = passes_df[mask1]
            
            #DF with all passes before num_minutes (additional filter on first 11 players)
            # mask2 = passes_df_all['minute'] < num_minutes
            mask2 = (passes_df_all['minute'] > mins[0]) & (passes_df_all['minute'] < mins[1])
            # players = passes_df_all[passes_df_all['minute'] < num_minutes]['player_name'].unique()
            players = passes_df_all[(passes_df_all['minute'] > mins[0]) & (passes_df_all['minute'] < mins[1])]['player_name'].unique()
            mask3 = passes_df_all['player_name'].apply(lambda x: x in players)
            passes_df_short = passes_df_all[mask2 & mask3]
            
            
            #DF with successed / completed passes
            mask2 = passes_df_all['player_name'] != passes_df_all['passRecipientName']
            mask3 = passes_df_all['outcome'] == True
            passes_df_suc = passes_df_all[mask2&mask3]
            

            #DF with successed passes before num_minutes (additional filter on first 11 players)
            # mask2 = passes_df_suc['minute'] < num_minutes
            mask2 = (passes_df_all['minute'] > mins[0]) & (passes_df_all['minute'] < mins[1])
            # players = passes_df_suc[passes_df_suc['minute'] < num_minutes]['player_name'].unique()
            players = passes_df_suc[(passes_df_suc['minute'] > mins[0]) & (passes_df_suc['minute'] < mins[1])]['player_name'].unique()
            mask3 = passes_df_suc['player_name'].apply(lambda x: x in players) & \
                    passes_df_suc['passRecipientName'].apply(lambda x: x in players)
            passes_df_suc_short = passes_df_suc[mask2 & mask3]
            
            # print('team: ',teamName)
            # print('passes: ', passes_df_all.shape[0])
            # print('suc passes: ', passes_df_suc.shape[0])
            # print('last minute: min(first red / substitution / end game) = ', mins[1])
            # print('last minute: min(first red / substitution / end game) = ', mins[1])
            
            # print('suc passes befor last minute: ', passes_df_short.shape[0])
            # print('\n')
            
            res_dict[teamId] = {}
            
            res_dict[teamId]['passes_df_all'] = passes_df_all
            res_dict[teamId]['passes_df_short'] = passes_df_short
            res_dict[teamId]['passes_df_suc'] = passes_df_suc
            res_dict[teamId]['passes_df_suc_short'] = passes_df_suc_short
            res_dict[teamId]['minutes'] = mins[1]
            res_dict[teamId]['minutes_with_first_eleven'] = minutes_with_first_eleven
            # res_dict[teamId]['minutes'] = num_minutes

            var = 'player_name'
            var2 = 'passRecipientName'

            passes_df_all = res_dict[teamId]['passes_df_all']
            passes_df_suc = res_dict[teamId]['passes_df_suc']
            passes_df_short = res_dict[teamId]['passes_df_short']
            passes_df_suc_short = res_dict[teamId]['passes_df_suc_short']
            
            player_position = passes_df_short.groupby(var).agg({'x': ['median'], 'y': ['median']})

            player_position.columns = ['x', 'y']
            player_position.index.name = 'player_name'
            player_position.index = player_position.index.astype(str)

            player_pass_count_all = passes_df_all.groupby(var).agg({'player_id':'count'}).rename(columns={'player_id':'num_passes_all'})
            player_pass_count_suc = passes_df_suc.groupby(var).agg({'player_id':'count'}).rename(columns={'player_id':'num_passes'})
            player_pass_count_suc_short = passes_df_suc_short.groupby(var).agg({'player_id':'count'}).rename(columns={'player_id':'num_passes2'})
            player_pass_count = player_pass_count_all.join(player_pass_count_suc).join(player_pass_count_suc_short)
            
            passes_df_all["pair_key"] = passes_df_all.apply(lambda x: "_".join([str(x[var]), str(x[var2])]), axis=1)
            passes_df_suc["pair_key"] = passes_df_suc.apply(lambda x: "_".join([str(x[var]), str(x[var2])]), axis=1)
            passes_df_suc_short["pair_key"] = passes_df_suc_short.apply(lambda x: "_".join([str(x[var]), str(x[var2])]), axis=1)

            pair_pass_count_all = passes_df_all.groupby('pair_key').agg({'player_id':'count'}).rename(columns={'player_id':'num_passes_all'})
            pair_pass_count_suc = passes_df_suc.groupby('pair_key').agg({'player_id':'count'}).rename(columns={'player_id':'num_passes'})
            pair_pass_count_suc_short = passes_df_suc_short.groupby('pair_key').agg({'player_id':'count'}).rename(columns={'player_id':'num_passes2'})
            pair_pass_count = pair_pass_count_all.join(pair_pass_count_suc).join(pair_pass_count_suc_short)
            
            player_pass_value_suc = (passes_df_suc.groupby(var)
                                        .agg({'xT_added':'sum'})
                                        .round(3)
                                        .rename(columns={'xT_added':'pass_value'}))
            player_pass_value_suc_short = (passes_df_suc_short.groupby(var)
                                        .agg({'xT_added':'sum'})
                                        .round(3)
                                        .rename(columns={'xT_added':'pass_value2'}))
            player_pass_value = player_pass_value_suc.join(player_pass_value_suc_short)

            pair_pass_value_suc = (passes_df_suc.groupby(['pair_key'])
                                    .agg({'xT_added':'sum'})
                                    .round(3)
                                    .rename(columns={'xT_added':'pass_value'}))
            pair_pass_value_suc_short = (passes_df_suc_short.groupby(['pair_key'])
                                .agg({'xT_added':'sum'})
                                .round(3)
                                .rename(columns={'xT_added':'pass_value2'}))
            pair_pass_value = pair_pass_value_suc.join(pair_pass_value_suc_short)

            
            player_position['z'] = player_position['x']
            player_position['x'] = player_position['y']
            player_position['y'] = player_position['z']
            
            res_dict[teamId]['player_position'] = player_position
            res_dict[teamId]['player_pass_count'] = player_pass_count
            res_dict[teamId]['pair_pass_count'] = pair_pass_count
            res_dict[teamId]['player_pass_value'] = player_pass_value
            res_dict[teamId]['pair_pass_value'] = pair_pass_value

        return res_dict
        
    def plot_passing_network(self):

        nodes_cmap = mpl.colors.LinearSegmentedColormap.from_list("", ['#b5dcff',
                                                               '#97cbfa',
                                                               '#70b9fa',
                                                               '#2f97f5',
                                                               '#0586fa'
                                                            ])
        node_cmap = cm.get_cmap(nodes_cmap)

        norm = Normalize(vmin=0, vmax=1)

        res_dict = self.create_res_dict()

        # print(res_dict[304]['pair_pass_value'])

        #nodes
        min_node_size = 5
        max_node_size = 35

        # max_player_count = 90
        max_player_count = max([res_dict[list(res_dict.keys())[0]]["player_pass_count"]["num_passes"].max(), res_dict[list(res_dict.keys())[1]]["player_pass_count"]["num_passes"].max()])
        PassingNetwork.max_player_count = max_player_count
        min_player_count = 1

        # max_player_value = 0.36
        max_player_value = max([res_dict[list(res_dict.keys())[0]]["player_pass_value"]["pass_value"].max(), res_dict[list(res_dict.keys())[1]]["player_pass_value"]["pass_value"].max()])
        PassingNetwork.max_player_value = max_player_value
        min_player_value = 0.01

        #font
        font_size = 8
        font_color = 'black'

        #edges arrow

        min_edge_width = 0.5
        max_edge_width = 5

        head_length = 0.3
        head_width = 0.1

        # max_pair_count = 20
        max_pair_count = max([res_dict[list(res_dict.keys())[0]]["pair_pass_count"]["num_passes"].max(), res_dict[list(res_dict.keys())[1]]["pair_pass_count"]["num_passes"].max()])
        PassingNetwork.max_pair_count = max_pair_count
        min_pair_count = 1

        min_pair_value  = 0.01
        # max_pair_value = 0.085
        max_pair_value = max([res_dict[list(res_dict.keys())[0]]["pair_pass_value"]["pass_value"].max(), res_dict[list(res_dict.keys())[1]]["pair_pass_value"]["pass_value"].max()])
        PassingNetwork.max_pair_value = max_pair_value

        min_passes = 5

        plt.style.use('fivethirtyeight')

        fig,ax = plt.subplots(1,2,figsize=(6,6), dpi=400)
        self.ax = ax

        teamId_home = self.events_df[self.events_df['h_a'] == 'h']['team_id'].unique()[0]
        teamId_away = self.events_df[self.events_df['h_a'] == 'a']['team_id'].unique()[0]

        for i, teamid in enumerate([teamId_home, teamId_away]):    

            #define dataframes
            position = res_dict[teamid]['player_position']
            player_pass_count = res_dict[teamid]['player_pass_count']
            pair_pass_count = res_dict[teamid]['pair_pass_count']
            player_pass_value = res_dict[teamid]['player_pass_value']
            pair_pass_value = res_dict[teamid]['pair_pass_value']
            minutes_ = res_dict[teamid]['minutes']
            minutes_with_first_eleven = res_dict[teamid]['minutes_with_first_eleven']

            pitch = VerticalPitch(pitch_type='opta', 
                                line_color='#7c7c7c',
                                goal_type='box',
                                linewidth=0.5,
                                pad_bottom=10)
            
            #plot vertical pitches
            pitch.draw(ax=ax[i], constrained_layout=False, tight_layout=False)
            
            # Step 1: processing for plotting edges
            pair_stats = pd.merge(pair_pass_count, pair_pass_value, left_index=True, right_index=True)
            pair_stats = pair_stats.sort_values('num_passes',ascending=False)
            pair_stats2 = pair_stats[pair_stats['num_passes'] >= min_passes]
            
            # Step 2: processing for plotting nodes
            player_stats = pd.merge(player_pass_count, player_pass_value, left_index=True, right_index=True)

            #FILTER first 11 players
            mask = self.events_df['minute'] < minutes_with_first_eleven
            players_in_first_eleven = list(set(self.events_df[mask]['player_name'].dropna()))
            
            #FILTER players during timelapse selected 
            mask = self.events_df['minute'] < minutes_
            players_ = list(set(self.events_df[mask]['player_name'].dropna()))
            
            mask_ = player_stats.index.map(lambda x: x in players_)
            player_stats = player_stats.loc[mask_]
            
            mask_ = pair_stats2.index.map(lambda x: (x.split('_')[0] in players_) &  (x.split('_')[1] in players_))
            pair_stats2 = pair_stats2[mask_]
            
            ind = position.index.map(lambda x: x in players_)
            position = position.loc[ind]
            
            
            # Step 3: plotting nodes
            for var, row in player_stats.iterrows():
                try:
                    player_x = position.loc[var]["x"]
                    player_y = position.loc[var]["y"]

                    num_passes = row["num_passes"]
                    pass_value = row["pass_value"]

                    marker_size = self.change_range(num_passes, (min_player_count, max_player_count), (min_node_size, max_node_size))

                    norm = Normalize(vmin=min_player_value, vmax=max_player_value)
            #         node_cmap = cm.get_cmap(nodes_cmap)
                    node_color = node_cmap(norm(pass_value)) 
            #         print(node_color)
            #         node_color = tuple([0.9 if n == 3 else i for n, i in enumerate(node_color)])
                    if var in players_in_first_eleven:
                        marker_type = "."
                    else:
                        marker_type = "^"

                    ax[i].plot(player_x, player_y, marker_type, color=node_color, markersize=marker_size, zorder=5)
                    ax[i].plot(player_x, player_y, marker_type, markersize=marker_size+2, zorder=4, color='white')

                    var_ = ' '.join(var.split(' ')[1:]) if len(var.split(' ')) > 1 else var

                    name_x = player_x
                    if marker_size > 30:
                        delta_y = 5
                    elif marker_size > 20:
                        delta_y = 3.5
                    elif marker_size > 10:
                        delta_y = 2.5
                    else:
                        delta_y = 1.5
                    name_y = player_y+delta_y if player_y > 48 else player_y - delta_y

                    ax[i].annotate(var_, xy=(name_x, name_y), ha="center", va="center", zorder=7,
                                fontsize=4, 
            #                     color=tuple([min(i*1.5, 1) if n != 3 else 1 for n, i in enumerate(node_color)]), 
                                color = 'black',
                                font = 'serif',
                                weight='heavy'
                                )

                    player_stats.loc[var, 'marker_size'] = marker_size
                except KeyError:
                    pass
                
            # Step 4: ploting edges  
            for pair_key, row in pair_stats2.iterrows():
                try:
                    player1, player2 = pair_key.split("_")

                    player1_x = position.loc[player1]["x"]
                    player1_y = position.loc[player1]["y"]

                    player2_x = position.loc[player2]["x"]
                    player2_y = position.loc[player2]["y"]

                    num_passes = row["num_passes"]
                    pass_value = row["pass_value"]

                    line_width = self.change_range(num_passes, (min_pair_count, max_pair_count), (min_edge_width, max_edge_width))
                    alpha = self.change_range(pass_value, (min_player_value, max_player_value), (0.4, 1))

                    norm = Normalize(vmin=min_pair_value, vmax=max_pair_value)
                    edge_cmap = cm.get_cmap(nodes_cmap)
                    edge_color = edge_cmap(norm(pass_value))

                    x = player1_x
                    y = player1_y
                    dx = player2_x-player1_x
                    dy = player2_y-player1_y
                    rel = 68/105
                    shift_x = 2
                    shift_y = shift_x*rel

                    slope = round(abs((player2_y - player1_y)*105/100 / (player2_x - player1_x)*68/100),1)

                    mutation_scale = 1
                    if (slope > 0.5):
                        if dy > 0:
                            ax[i].annotate("", xy=(x+dx+shift_x, y+dy), xytext=(x+shift_x, y),zorder=2,
                                    arrowprops=dict(arrowstyle=f'->, head_length = {head_length}, head_width={head_width}',
                                                    color=tuple([alpha if n == 3 else i for n, i in enumerate(edge_color)]),
                                                    fc = 'blue',
                                                    lw=line_width,
                                                    shrinkB=player_stats.loc[player2, 'marker_size']/5))
                            
                            
                        elif dy <= 0:
                            ax[i].annotate("", xy=(x+dx-shift_x, y+dy), xytext=(x-shift_x, y),zorder=2,
                                    arrowprops=dict(arrowstyle=f'->, head_length = {head_length}, head_width={head_width}',
                                                    color=tuple([alpha if n == 3 else i for n, i in enumerate(edge_color)]),
                                                    fc = 'blue',
                                                    lw=line_width,
                                                    shrinkB=player_stats.loc[player2, 'marker_size']/5))
                            
                    elif (slope <= 0.5) & (slope >=0):
                        if dx > 0:
            #                 print(2)

                            ax[i].annotate( "", xy=(x+dx, y+dy-shift_y), xytext=(x, y-shift_y),zorder=2,
                                    arrowprops=dict(arrowstyle=f'->, head_length = {head_length}, head_width={head_width}',
                                                    color=tuple([alpha if n == 3 else i for n, i in enumerate(edge_color)]),
                                                    fc = 'blue',
                                                    lw=line_width,
                                                    shrinkB=player_stats.loc[player2, 'marker_size']/5))

                        elif dx <= 0:

                            ax[i].annotate("", xy=(x+dx, y+dy+shift_y), xytext=(x, y+shift_y),zorder=2,
                                    arrowprops=dict(arrowstyle=f'->, head_length = {head_length}, head_width={head_width}',
                                                    color=tuple([alpha if n == 3 else i for n, i in enumerate(edge_color)]),
                                                    fc = 'blue',
                                                    lw=line_width,
                                                    shrinkB=player_stats.loc[player2, 'marker_size']/5))
                    else:
                        print(1)
                except KeyError:
                    pass
                    
            self.add_legend(fig, i)

        return fig

    def add_legend(self, fig, i):
        ax = self.ax[i]

        nodes_cmap = mpl.colors.LinearSegmentedColormap.from_list("", ['#b5dcff',
                                                               '#97cbfa',
                                                               '#70b9fa',
                                                               '#2f97f5',
                                                               '#0586fa'
                                                            ])
        
        node_cmap = cm.get_cmap(nodes_cmap)

        norm = Normalize(vmin=0, vmax=1)
        node_color1 = node_cmap(norm(0)) 
        node_color2 = node_cmap(norm(0.25)) 
        node_color3 = node_cmap(norm(0.5)) 
        node_color4 = node_cmap(norm(0.75)) 
        node_color5 = node_cmap(norm(1))

        # Plotting pass count ranges

        # ax.plot([21, 21], [ax.get_ylim()[0]+19, ax.get_ylim()[1]-19], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        # ax.plot([78.8, 78.8], [ax.get_ylim()[0]+19, ax.get_ylim()[1]-19], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        # ax.plot([36.8, 36.8], [ax.get_ylim()[0]+8.5, ax.get_ylim()[1]-8.5], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        # ax.plot([100-36.8, 100-36.8], [ax.get_ylim()[0]+8.5, ax.get_ylim()[1]-8.5], ls=':',dashes=(1, 3), color='gray', lw=0.4)

        # ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [83,83], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        # ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [67, 67], ls=':',dashes=(1, 3), color='gray', lw=0.4)

        # ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [100-83,100-83], ls=':',dashes=(1, 3), color='gray', lw=0.4)
        # ax.plot([ax.get_xlim()[0]-4, ax.get_xlim()[1]+4], [100-67, 100-67], ls=':',dashes=(1, 3), color='gray', lw=0.4)


        # Adding annotations
        ax.annotate(xy=(102, 58), xytext=(102, 43), zorder=2, text='', ha='center',
                    arrowprops=dict(arrowstyle=f'->, head_length={self.head_length}, head_width={self.head_width}',
                                    color='#7c7c7c', lw=0.5))
        ax.annotate(xy=(104, 45), text='Play direction', ha='center', color='#7c7c7c', rotation=90, size=4)
        ax.annotate(xy=(50, -5), text=f'Passes from minutes {self.mins[0]} to {self.mins[1]}', ha='center', color='#7c7c7c', size=6)

        # Adding text annotations
        font = 'serif'
        fig.text(x=0.5, y=.92, s=f"Passing network for {PassingNetwork.home_club} {PassingNetwork.score} {PassingNetwork.away_club}", weight='bold', va="bottom", ha="center", fontsize=10, font=font)
        fig.text(x=0.26, y=.875, s=PassingNetwork.home_club, weight='bold', va="bottom", ha="center", fontsize=8, font=font)
        fig.text(x=0.745, y=.875, s=PassingNetwork.away_club, weight='bold', va="bottom", ha="center", fontsize=8, font=font)
        fig.text(x=0.5, y=0.90, s=f"{PassingNetwork.league} | Season 2023-2024 | {PassingNetwork.date}", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.87, y=-0.0, s="Yannis R", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.14, y=.14, s="Pass count between", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.38, y=.14, s="Pass value between (xT)", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.61, y=.14, s="Player pass count", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.84, y=.14, s="Player pass value (xT)", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.41, y=.038, s="Low", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.6, y=.038, s="High", va="bottom", ha="center", fontsize=6, font=font)
        fig.text(x=0.1, y=-0.0, s="linkedin.com/in/yannis-rachid-230/", va="bottom", ha="center", weight='bold', fontsize=6, font=font, color='black')
        fig.text(x=0.04, y=0.02, s="Template: FOOTSCI", va="bottom", ha="center", weight='bold', fontsize=6, font=font, color='black')
        fig.text(x=0.13, y=0.07, s=f"5 to {int(PassingNetwork.max_pair_count)}", va="bottom", ha="center", fontsize=5, font=font, color='black')
        fig.text(x=0.37, y=0.07, s=f"0 to {round(PassingNetwork.max_pair_value, 2)}", va="bottom", ha="center", fontsize=5, font=font, color='black')
        fig.text(x=0.61, y=0.07, s=f"1 to {PassingNetwork.max_player_count}", va="bottom", ha="center", fontsize=5, font=font, color='black')
        fig.text(x=0.84, y=0.07, s=f"0.01 to {round(PassingNetwork.max_player_value, 2)}", va="bottom", ha="center", fontsize=5, font=font, color='black')

        head_length = 20
        head_width = 20

        x0 = 170
        y0 = 130
        dx = 30
        dy = 60
        shift_x = 40

        x1 = 425
        x2 = 750
        y2 = 150
        shift_x2 = 35
        radius = 10

        x3 = 975
        shift_x3 = 50

        color='black'

        style = ArrowStyle('->', head_length=5, head_width=3)

        arrow1 = FancyArrowPatch((x0,y0), (x0+dx, y0+dy), lw=0.5,
                                arrowstyle=style, color=color) 
        arrow2 = FancyArrowPatch((x0+shift_x,y0), (x0+dx+shift_x, y0+dy), lw=1.5,
                                arrowstyle=style, color=color)
        arrow3 = FancyArrowPatch((x0+2*shift_x,y0), (x0+dx+2*shift_x, y0+dy), lw=2.5,
                                arrowstyle=style, color=color)


        arrow4 = FancyArrowPatch((x1,y0), (x1+dx, y0+dy), lw=2.5,
                                arrowstyle=style, color=node_color1) 
        arrow5 = FancyArrowPatch((x1+shift_x,y0), (x1+dx+shift_x, y0+dy), lw=2.5,
                                arrowstyle=style, color=node_color2)
        arrow6 = FancyArrowPatch((x1+2*shift_x,y0), (x1+dx+2*shift_x, y0+dy), lw=2.5,
                                arrowstyle=style, color=node_color3)
        arrow7 = FancyArrowPatch((x1+3*shift_x,y0), (x1+dx+3*shift_x, y0+dy), lw=2.5,
                                arrowstyle=style, color=node_color4)
        arrow8 = FancyArrowPatch((x1+4*shift_x,y0), (x1+dx+4*shift_x, y0+dy), lw=2.5,
                                arrowstyle=style, color=node_color5)

        circle1 = Circle(xy=(x2, y2), radius=radius, edgecolor='black',fill=False)
        circle2 = Circle(xy=(x2+shift_x2, y2), radius=radius*1.5, edgecolor='black',fill=False)
        circle3 = Circle(xy=(x2+2.3*shift_x2, y2), radius=radius*2, edgecolor='black',fill=False)

        circle4 = Circle(xy=(x3, y2), radius=radius*2, color=node_color1)
        circle5 = Circle(xy=(x3 + shift_x3, y2), radius=radius*2, color=node_color2)
        circle6 = Circle(xy=(x3 + 2*shift_x3, y2), radius=radius*2, color=node_color3)
        circle7 = Circle(xy=(x3 + 3*shift_x3, y2), radius=radius*2, color=node_color4)
        circle8 = Circle(xy=(x3 + 4*shift_x3, y2), radius=radius*2, color=node_color5)

        fig.patches.extend([arrow1, arrow2, arrow3 ])
        fig.patches.extend([arrow4, arrow5, arrow6, arrow7, arrow8 ])
        fig.patches.extend([circle1 , circle2, circle3])
        fig.patches.extend([circle4,circle5,circle6,circle7,circle8])

        x4 = 575
        y4 = 75
        dx = 190

        arrow9 = FancyArrowPatch((x4,y4), (x4+dx, y4), lw=1,
                                arrowstyle=style, color='black')

        fig.patches.extend([arrow9])

        plt.tight_layout()
        plt.subplots_adjust(wspace=0.1, hspace=0, bottom=0.1)