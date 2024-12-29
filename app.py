from datetime import datetime

from flask import Flask, render_template, request
import pandas as pd
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

data_file = 'static/players.csv'


def load_data():
    """Load player data from a CSV file."""
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"{data_file} not found. Please download the dataset from Kaggle.")
    return pd.read_csv(data_file)


# initial data load
data = load_data()

# rename 'name' column
data = data.rename(columns={'name': 'player_name'})

# add age column
data['date_of_birth'] = pd.to_datetime(data['date_of_birth'])
data['age'] = data['date_of_birth'].apply(lambda x: (datetime.now() - x).days // 365)

# current_search_data is needed to store latest search results for filtering
current_search_data = None

# variables for containing information for filters
positions = data['position'].unique().tolist()
countries = sorted(data['country_of_citizenship'].unique().astype(str).tolist())


@app.route('/')
def index():
    """Homepage showing top players by market value."""
    top_players = data.sort_values(by='market_value_in_eur', ascending=False).head(20)
    return render_template(
        'index.html',
        results=top_players,
        positions=positions,
        countries=countries
    )


@app.route('/search', methods=['POST'])
# def search():
#     """Search for players based on name or attributes."""
#     global current_search_data
#
#     query = request.form.get('search-query', '').lower()
#     results = data[data['player_name'].str.lower().str.contains(query)].sort_values('market_value_in_eur',
#                                                                                     ascending=False) if query else data.sort_values(
#         'market_value_in_eur', ascending=False)
#     current_search_data = results
#     return render_template(
#         'search.html',
#         results=results,
#         positions=positions,
#         countries=countries,
#
#         search_query=query,
#     )
def search():
    """Search for players based on name or attributes."""
    global current_search_data

    query = request.form.get('search-query', '').lower()

    # Create regex pattern for case-insensitive search
    pattern = re.escape(query) if query else '.*'  # Escapes special characters in the query
    results = data[data['player_name'].str.contains(pattern, case=False, regex=True)].sort_values('market_value_in_eur',
                                                                                                  ascending=False)

    current_search_data = results
    return render_template(
        'search.html',
        results=results,
        positions=positions,
        countries=countries,
        search_query=query,
    )



@app.route('/filter', methods=['POST'])
def filter():
    global current_search_data

    if current_search_data is None:
        current_search_data = data.copy()

    search_query = request.form.get('search-query', '').lower()
    position_filter = request.form.get('position-filter', '').lower()
    country_filter = request.form.get('country-filter', '').lower()

    conditions = [
        current_search_data['player_name'].str.lower().str.contains(search_query),
        current_search_data['position'].str.lower().str.contains(position_filter),
        current_search_data['country_of_citizenship'].str.lower().str.contains(country_filter)
        # current_search_data['country_of_citizenship'].str.lower().str.contains('')
    ]

    print(conditions[0])
    print(conditions[1])
    print(conditions[2])

    results = current_search_data[conditions[0] & conditions[1] & conditions[2]].sort_values('market_value_in_eur',
                                                                                             ascending=False)
    return render_template(
        'search.html',
        results=results,
        positions=positions,
        countries=countries,
        search_query=search_query,
        position_filter=position_filter,
        country_filter=country_filter
    )


@app.route('/player/<player_id>')
def player_detail(player_id):
    """Display detailed stats for a specific player."""
    player = data[data['player_id'] == int(player_id)].squeeze()
    if player.empty:
        return "Player not found.", 404
    return render_template('player_detail.html', player=player)


@app.route('/plot', methods=['GET', 'POST'])
def plot_players():
    age_filter = int(request.form.get('age-query', '0'))
    if age_filter == 0:
        top_players = data.sort_values('market_value_in_eur', ascending=False).head(30)[
            ['player_name', 'market_value_in_eur', 'highest_market_value_in_eur']]
    elif age_filter == 1:
        top_players = data.sort_values('market_value_in_eur', ascending=False)[
            ['player_name', 'market_value_in_eur', 'highest_market_value_in_eur', 'age']]
        top_players = top_players[top_players['age'] < 20].head(30)
    elif age_filter == 2:
        top_players = data.sort_values('market_value_in_eur', ascending=False)[
            ['player_name', 'market_value_in_eur', 'highest_market_value_in_eur', 'age']]
        top_players = top_players[(top_players['age'] >= 20) & (top_players['age'] < 25)].head(30)
    elif age_filter == 3:
        top_players = data.sort_values('market_value_in_eur', ascending=False)[
            ['player_name', 'market_value_in_eur', 'highest_market_value_in_eur', 'age']]
        top_players = top_players[(top_players['age'] >= 25) & (top_players['age'] < 30)].head(30)
    elif age_filter == 4:
        top_players = data.sort_values('market_value_in_eur', ascending=False)[
            ['player_name', 'market_value_in_eur', 'highest_market_value_in_eur', 'age']]
        top_players = top_players[(top_players['age'] >= 30) & (top_players['age'] < 35)].head(30)

    # Plot the data
    plt.figure(figsize=(15, 8))
    x = range(len(top_players))
    width = 0.35

    # Bar plots for current and highest market values
    plt.bar(x, top_players['market_value_in_eur'], width, label='Current val', color='skyblue')
    plt.bar([i + width for i in x], top_players['highest_market_value_in_eur'], width, label='Max val', color='orange')

    # Labels, title, and customization
    plt.xlabel('Players', fontsize=14)
    plt.ylabel('Value (100 million eur)', fontsize=14)
    plt.title('Current vs max values comparison for top-30 players', fontsize=16)
    plt.xticks([i + width / 2 for i in x], top_players['player_name'], rotation=45, ha='right', fontsize=10)
    plt.legend(fontsize=12)
    plt.tight_layout()

    # Save plot to a BytesIO object for direct usage
    plot_path = 'static/plot.png'
    plt.savefig(plot_path, format='png')
    plt.close()

    # Return the plot as a response
    return render_template('plot.html', image_path=plot_path)
