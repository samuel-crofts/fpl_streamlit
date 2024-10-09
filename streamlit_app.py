import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Player IDs and names
players = {
    7326724: "Sam",
    7292048: "Pierre",
    7321581: "Jackson",
    7361093: "Jerome",
    7313074: "Dan"
}

@st.cache_data
def fetch_player_data(player_id):
    url = f"https://fantasy.premierleague.com/api/entry/{player_id}/history/"
    response = requests.get(url)
    return response.json()['current']

@st.cache_data
def fetch_game_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    return response.json()['events']

def extract_gameweek_data(player_data):
    return [(entry['event'], entry['total_points'], entry['points'], entry['rank'], entry['event_transfers']) for entry in player_data]

def create_dataframes():
    all_player_data = {}
    all_player_weekly_points = {}
    all_player_ranks = {}
    all_player_transfers = {}
    
    for player_id, player_name in players.items():
        player_data = fetch_player_data(player_id)
        extracted_data = extract_gameweek_data(player_data)
        all_player_data[player_name] = [(event, total_points) for event, total_points, _, _, _ in extracted_data]
        all_player_weekly_points[player_name] = [(event, points) for event, _, points, _, _ in extracted_data]
        all_player_ranks[player_name] = [(event, rank) for event, _, _, rank, _ in extracted_data]
        all_player_transfers[player_name] = [(event, transfers) for event, _, _, _, transfers in extracted_data]

    df = pd.DataFrame({player: dict(data) for player, data in all_player_data.items()})
    weekly_df = pd.DataFrame({player: dict(data) for player, data in all_player_weekly_points.items()})
    ranks_df = pd.DataFrame({player: dict(data) for player, data in all_player_ranks.items()})
    transfers_df = pd.DataFrame({player: dict(data) for player, data in all_player_transfers.items()})
    
    game_data = fetch_game_data()
    game_df = pd.DataFrame(game_data)
    game_df = game_df[['id', 'average_entry_score', 'ranked_count']]
    game_df = game_df.rename(columns={'id': 'Gameweek', 'average_entry_score': 'Average'})
    game_df.set_index('Gameweek', inplace=True)
    
    return df.sort_index(), weekly_df.sort_index(), ranks_df.sort_index(), transfers_df.sort_index(), game_df

def get_longest_streak(df):
    streaks = df.apply(lambda x: (x.groupby((x != x.shift()).cumsum()).cumcount() + 1) * (x.astype(int) * 2 - 1))
    max_streaks = streaks.max()
    min_streaks = streaks.min()
    return max_streaks.idxmax(), max_streaks.max(), min_streaks.idxmin(), abs(min_streaks.min())

st.title('We Hate City')

# You can add an image here. For example:
# image = Image.open('path_to_your_image.jpg')
# st.image(image, caption='We Hate City', use_column_width=True)

df, weekly_df, ranks_df, transfers_df, game_df = create_dataframes()

# Limit game_df to the current gameweek
current_gameweek = weekly_df.index.max()
game_df = game_df.loc[:current_gameweek]

st.subheader('Cumulative FPL Score Relative to Average')
fig, ax = plt.subplots(figsize=(12, 6))

for player in players.values():
    relative_scores = (df[player] - game_df['Average'].cumsum()).fillna(0)
    ax.plot(df.index, relative_scores, label=player)

ax.axhline(y=0, color='k', linestyle='--', label='Game Average')
ax.set_xlabel('Gameweek')
ax.set_ylabel('Points Relative to Average')
ax.legend()
ax.grid(True)

st.pyplot(fig)

st.subheader('🥃 The Whisky Race')
latest_gameweek = df.index.max()
rankings = df.loc[latest_gameweek].sort_values(ascending=False)
rankings_df = rankings.to_frame(name='Total Points')
rankings_df['Rank'] = rankings_df['Total Points'].rank(ascending=False, method='min').astype(int)
rankings_df['Player'] = rankings_df.index
rankings_df['Player'] = rankings_df.apply(lambda row: f"🥃 {row['Player']}" if row['Rank'] == 1 else row['Player'], axis=1)
rankings_df = rankings_df.set_index('Rank')
st.dataframe(rankings_df[['Player', 'Total Points']])

st.header('🏆 Big Winners')

# Highest all-time Gameweek score
highest_score = weekly_df.max().max()
highest_score_player = weekly_df.max().idxmax()
highest_score_gameweek = weekly_df[highest_score_player].idxmax()
st.write(f"The highest all-time Gameweek score is **{highest_score} points**, achieved by **{highest_score_player}** in Gameweek {highest_score_gameweek}.")

# Calculate percentile ranks
percentile_ranks_df = ranks_df.div(game_df['ranked_count'], axis=0) * 100

# Best all-time Gameweek rank (percentage)
best_rank = percentile_ranks_df.min().min()
best_rank_player = percentile_ranks_df.min().idxmin()
best_rank_gameweek = percentile_ranks_df[best_rank_player].idxmin()
st.write(f"The best gameweek rank was the top **{best_rank:.2f}%** of players, achieved by **{best_rank_player}** in Gameweek {best_rank_gameweek}.")

# Longest streak of beating the average
beats_average_df = weekly_df.subtract(game_df['Average'], axis=0) > 0
longest_streak_player, longest_streak, _, _ = get_longest_streak(beats_average_df)
st.write(f"The longest consecutive streak of beating the average is **{longest_streak} gameweeks**, achieved by **{longest_streak_player}**.")

st.header('💩 Big Losers')

# Lowest all-time Gameweek score
lowest_score = weekly_df.min().min()
lowest_score_player = weekly_df.min().idxmin()
lowest_score_gameweek = weekly_df[lowest_score_player].idxmin()
st.write(f"The lowest all-time Gameweek score is **{lowest_score} points**, achieved by **{lowest_score_player}** in Gameweek {lowest_score_gameweek}.")

# Worst all-time Gameweek rank (percentage)
worst_rank = percentile_ranks_df.max().max()
worst_rank_player = percentile_ranks_df.max().idxmax()
worst_rank_gameweek = percentile_ranks_df[worst_rank_player].idxmax()
st.write(f"The worst gameweek rank was the lowest **{worst_rank:.2f}%** of players, achieved by **{worst_rank_player}** in Gameweek {worst_rank_gameweek}.")

# Longest streak of not beating the average
_, _, longest_losing_streak_player, longest_losing_streak = get_longest_streak(beats_average_df)
st.write(f"The longest consecutive streak of not beating the average is **{longest_losing_streak} gameweeks**, achieved by **{longest_losing_streak_player}**.")

# Total transfers per player
st.subheader('Total Transfers per Player')
total_transfers = transfers_df.sum().sort_values(ascending=False)
st.dataframe(total_transfers.to_frame(name='Total Transfers'))

# Number of times each player has beaten the average
st.subheader('Number of Times Each Player Beats the Average')
beats_average = (weekly_df.subtract(game_df['Average'], axis=0) > 0).sum().sort_values(ascending=False)
st.dataframe(beats_average.to_frame(name='Times Above Average'))

# Display weekly scores table with game average
st.subheader('Weekly Scores Table (with Game Average)')
combined_weekly_df = weekly_df.join(game_df['Average'])
st.dataframe(combined_weekly_df)
