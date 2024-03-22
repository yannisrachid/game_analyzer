import streamlit as st
import pandas as pd
import numpy as np
from passing_network import PassingNetwork
from player_visualization import PlayerVisualization
from clubs import clubs_list, clubs_ids

st.markdown("<h3 style='text-align: center; color: black;'>For any contact or support:</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    st.write(' ')
with col2:
    st.image("img/logo_tr.png")
with col3:
    st.write(' ')

# col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col4:
    st.markdown("[![My LinkedIn profile](https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Bug.svg.original.svg)](https://www.linkedin.com/in/yannis-rachid-230/)")
# with col2:
#    st.markdown('<a href="https://www.buymeacoffee.com/yannisr" target="_blank"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=votrepseudo&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"></a>', unsafe_allow_html=True)

st.sidebar.markdown("<h1 style='text-align: center; color: white;'>{}</h1>".format("Game analyzer by Yannis R"), unsafe_allow_html=True)
st.sidebar.text("Data last updated on 2024-03-22")

st.sidebar.markdown("<h2 style='text-align: center; color: white;'>Team performance</h2>", unsafe_allow_html=True)

league = st.sidebar.selectbox('Select a league', ["Bundesliga", "Eredivisie", "EPL", "Jupiler Pro League", "La Liga", "Liga Nos", "Ligue 1", "Serie A"])

@st.cache_data
def load_dataframe(league):
    return pd.read_csv("csv_data/{league}_events.csv".format(league=league.replace(" ", "_")))

df = load_dataframe(league)
df = df.sort_values(by="date")
game = st.sidebar.selectbox("Select a game", df["game"].unique())

events_df = df[df["game"] == game].reset_index()

def check_card_type(qualifiers):
    display_names = []
    for i in range (0, len(qualifiers)):
        display_names.append(qualifiers[i]["type"]["displayName"])
    if "Red" in display_names:
        return "Red"
    elif "SecondYellow" in display_names:
        return "SecondYellow"
    elif "Yellow" in display_names:
        return "Yellow"
    else:
        return None
    

def calculate_expected_threat(row):
    if row['type_name'] == 'Pass':
        # Calcul de la distance entre le début de la passe et le but adverse
        distance_to_goal = np.sqrt((100 - row['start_x'])**2 + (50 - row['start_y'])**2)
        # Calcul de l'Expected Threat
        # Plus la distance au but est faible, plus l'Expected Threat est élevé
        expected_threat = np.exp(-0.1 * distance_to_goal)
    else:
        expected_threat = 0
    return expected_threat

def find_clubs(ws_name, clubs_list):
    return list(filter(lambda club: club in ws_name, clubs_list))

events_df["league"] = league.replace("_", " ")
ids = [events_df.loc[0, "team_id"], events_df.loc[1, "team_id"]]
clubs = find_clubs(events_df.loc[0, "game"], clubs_list)

# Déterminer l'ordre des clubs dans la chaîne de caractères
club_order = [events_df.loc[0, "game"].index(club) for club in clubs]

# Réorganiser la liste clubs en fonction de cet ordre
clubs_sorted = [club for _, club in sorted(zip(club_order, clubs))]

team_ids = {value: key for key, value in clubs_ids.items()}

events_df["team_name"] = events_df["team_id"].apply(lambda x: team_ids[x])
events_df["h_a"] = events_df["team_name"].apply(lambda x: 'h' if x == clubs_sorted[0] else 'a')
# events_df["h_a"] = events_df["team_id"].apply(lambda x: 'h' if x == home_id else 'a')
events_df["qualifiers"] = events_df["qualifiers"].apply(lambda x: eval(x))
events_df['cardType'] = events_df.apply(lambda row: check_card_type(row['qualifiers']) if row['type_name'] == 'Card' else None, axis=1)
events_df['xT_added'] = events_df.apply(calculate_expected_threat, axis=1)
events_df = events_df.rename(columns={'start_x': 'x', 'start_y': 'y'})

max_minute = events_df["minute"].max()
minutes = st.sidebar.slider('Select the game timelapse', 0, max_minute, (0, max_minute))

st.markdown("<h2 style='text-align: center; color: black;'>Team performance</h2>", unsafe_allow_html=True)

passing_network = PassingNetwork(events_df, mins=minutes)
st.pyplot(passing_network.plot_passing_network())


st.sidebar.markdown("<h2 style='text-align: center; color: white;'>Player performance</h2>", unsafe_allow_html=True)

club = st.sidebar.selectbox("Select a club", clubs_sorted)
events_df = events_df[events_df["team_name"] == club].reset_index(drop=True)

player = st.sidebar.selectbox("Select a player", sorted([x for x in events_df["player_name"].unique() if isinstance(x, str)]))
player_viz = PlayerVisualization(events_df, player, minutes, club)

st.markdown("<h2 style='text-align: center; color: black;'>Player performance</h2>", unsafe_allow_html=True)

st.pyplot(player_viz.plot_passes_game())
st.pyplot(player_viz.plot_heatmap_game())
st.pyplot(player_viz.plot_dribbles())
st.pyplot(player_viz.plot_shotmap_player())
st.pyplot(player_viz.plot_game_player_defensive())