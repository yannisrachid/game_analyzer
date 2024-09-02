import streamlit as st
import pandas as pd
import numpy as np
from passing_network import PassingNetwork
from player_visualization import PlayerVisualization
from positional_map import PositionalMap
from clubs import clubs_list, clubs_ids
from st_files_connection import FilesConnection
from utils import find_clubs, check_card_type, calculate_expected_threat

st.set_page_config(page_title='Game Analyzer')

## Display analysis logo in the sidebar
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    st.write(' ')
with col2:
    st.image("img/logo_tr.png")
with col3:
    st.write(' ')

## Display Linkedin profile
st.markdown("<h3 style='text-align: center; color: black;'>For any contact or support:</h3>", unsafe_allow_html=True)
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col4:
    st.markdown("[![My LinkedIn profile](https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Bug.svg.original.svg)](https://www.linkedin.com/in/yannis-rachid-230/)")

## Sidebar text details
st.sidebar.markdown("<h1 style='text-align: center; color: white;'>{}</h1>".format("Game analyzer by Yannis R"), unsafe_allow_html=True)
st.sidebar.text("Last updated: 2024-09-02")

## User league selection
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>Team performance</h2>", unsafe_allow_html=True)
league = st.sidebar.selectbox('Select a league', ["Bundesliga", "Eredivisie", "EPL", "Jupiler Pro League", "La Liga", "Liga Nos", "Ligue 1", "Serie A"])

# Unused: load csv from folder
@st.cache_data
def load_dataframe(league):
    return pd.read_csv("csv_data/{league}_events.csv".format(league=league.replace(" ", "_")))

# Load league data in AWS S3 bucket, cached for 10 mins.
@st.cache_data
def load_dataframe_s3(league):
    conn = st.connection('s3', type=FilesConnection)
    df = conn.read("footballanalytics/{league}_events.csv".format(league=league.replace(" ", "_")), input_format="csv", ttl=600)
    return df

## Load data in df and select the events from the game chose by the user
df = load_dataframe_s3(league)
df = df.sort_values(by="date")
game = st.sidebar.selectbox("Select a game", df["game"].unique())
events_df = df[df["game"] == game].reset_index()

## Data Preprocessing
events_df["league"] = league.replace("_", " ")
ids = [events_df.loc[0, "team_id"], events_df.loc[1, "team_id"]]
clubs = find_clubs(events_df.loc[0, "game"], clubs_list)
# Determine the order of the clubs in the string
club_order = [events_df.loc[0, "game"].index(club) for club in clubs]
# Reorganise the clubs list according to this order
clubs_sorted = [club for _, club in sorted(zip(club_order, clubs))]
team_ids = {value: key for key, value in clubs_ids.items()}
events_df["team_name"] = events_df["team_id"].apply(lambda x: team_ids[x])
events_df["h_a"] = events_df["team_name"].apply(lambda x: 'h' if x == clubs_sorted[0] else 'a')
events_df["qualifiers"] = events_df["qualifiers"].apply(lambda x: eval(x))
events_df['cardType'] = events_df.apply(lambda row: check_card_type(row['qualifiers']) if row['type_name'] == 'Card' else None, axis=1)
events_df['xT_added'] = events_df.apply(calculate_expected_threat, axis=1)
events_df = events_df.rename(columns={'start_x': 'x', 'start_y': 'y'})

# Display the length of the match
max_minute = events_df["minute"].max()
minutes = st.sidebar.slider('Select the game timelapse', 0, max_minute, (0, max_minute))

## Display the team performance visualisations
st.markdown("<h2 style='text-align: center; color: black;'>Team performance</h2>", unsafe_allow_html=True)

passing_network = PassingNetwork(events_df, mins=minutes)
st.pyplot(passing_network.plot_passing_network())

positional_map = PositionalMap(events_df=events_df , mins= minutes)
st.pyplot(positional_map.plot_positional_map())

## Display the player filters
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>Player performance</h2>", unsafe_allow_html=True)
club = st.sidebar.selectbox("Select a club", clubs_sorted)
# Select only the player events
events_df = events_df[events_df["team_name"] == club].reset_index(drop=True)
player = st.sidebar.selectbox("Select a player", sorted([x for x in events_df["player_name"].unique() if isinstance(x, str)]))

## Display the player performance visualisations
player_viz = PlayerVisualization(events_df, player, minutes, club)
st.markdown("<h2 style='text-align: center; color: black;'>Player performance</h2>", unsafe_allow_html=True)
st.pyplot(player_viz.plot_passes_game())
st.pyplot(player_viz.plot_heatmap_game())
st.pyplot(player_viz.plot_dribbles())
st.pyplot(player_viz.plot_shotmap_player())
st.pyplot(player_viz.plot_game_player_defensive())
