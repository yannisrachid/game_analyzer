import pandas as pd
import numpy as np
from scipy.stats import binned_statistic_2d
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.patches import RegularPolygon, Arrow, ArrowStyle,FancyArrowPatch, Circle,FancyArrow
from mplsoccer.pitch import Pitch, VerticalPitch
from matplotlib.colors import Normalize
from matplotlib import cm
from highlight_text import fig_text, ax_text
from clubs import Ligue_1
import warnings
warnings.filterwarnings("ignore")

class PlayerVisualization():
    def __init__(self, events_df, player, mins):
        self.events_df = events_df
        self.player = player
        self.mins = mins
        self.ax = None
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
        
    def prepare_data(self, events_df, player, mins):
        df = events_df[(events_df['minute'] >= mins[0]) & (events_df['minute'] <= mins[1])].reset_index(drop=True)
        df_player = df[df["player_name"] == player].reset_index(drop=True)
        return df_player
    
    def draw_pitch(self):
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
        return fig, ax

    def plot_dribbles(self):
        # Prepare data and pitch
        df = self.prepare_data(self.events_df, self.player, self.mins)
        fig, ax = self.draw_pitch()

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
        fig.text(x=0.6, y=1, s=f"Dribbles map for {self.player}", weight='bold', va="bottom", ha="center", fontsize=15, font=font)
        fig.text(x=0.87, y=-0.0, s="Yannis R", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
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

        plt.tight_layout()
        
        return fig
    
    def plot_passes(self):
        df = self.prepare_data(self.events_df, self.player, self.mins)
        fig, ax = self.draw_pitch()

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

            # slope = round(abs((end_y - start_y)*105/100 / (end_x - start_x)*68/100),1)

            head_length = 0.3
            head_width = 0.2

            # ax.arrow(x=start_x,
             #        y=start_y,
              #       dx=dx,
               #      dy=dy,
                #     color="green" if row["outcome"] == True else "red",
                 #    width=0.3,
                  #   alpha=pass_value+0.5,
                   #  length_includes_head=True,
                    # head_width=0.5)
            
            ax.annotate("", xy=(end_x, end_y), xytext=(start_x, start_y),
                    arrowprops=dict(arrowstyle=f'->, head_length = {head_length}, head_width={head_width}', color=arrow_color, lw=0.5))

        font = 'serif'
        fig.text(x=0.6, y=1, s=f"Passes map for {self.player}", weight='bold', va="bottom", ha="center", fontsize=15, font=font)
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
        green_arrow_patch = FancyArrowPatch((3400, 1570), (3400+100, 1570+100), arrowstyle=style, color='green')
        red_arrow_patch = FancyArrowPatch((3400, 1470), (3400+100, 1470+100), arrowstyle=style, color='red')
        orange_arrow_patch = FancyArrowPatch((3400, 1370), (3400+100, 1370+100), arrowstyle=style, color='orange')
        fig.patches.extend([green_arrow_patch, red_arrow_patch, orange_arrow_patch])
        fig.text(x=0.8, y=0.35, s=f"LEGEND", va="bottom", ha="center", weight='bold', fontsize=12, font=font, color='black')
        fig.text(x=0.8, y=0.32, s="Successful Pass", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.806, y=0.30, s="Unsuccessful Pass", va="bottom", ha="center", fontsize=12, font=font, color='black')
        fig.text(x=0.784, y=0.28, s="Key Pass", va="bottom", ha="center", fontsize=12, font=font, color='black')

        plt.tight_layout()

        return fig