from flask import Flask, render_template, request
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
import pandas as pd

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/schedule')
def schedule():
    # Get the schedule for the 2024-25 season
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2024-25', league_id_nullable='00')
    games = gamefinder.get_data_frames()[0]

    # Get latest 10 games
    games = games[['GAME_ID', 'GAME_DATE', 'MATCHUP']].head(15)
    return render_template('schedule.html', games=games.to_dict(orient='records'))


@app.route('/boxscore/<game_id>')
def boxscore(game_id):

    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    stats = boxscore.player_stats.get_data_frame()
    stats = stats[['TEAM_ABBREVIATION', 'PLAYER_NAME', 'MIN', 'PTS', 'AST', 'REB', 'FGM', 'FGA', 'FG_PCT',
                   'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
                   'STL', 'BLK', 'TO', 'PF', 'PLUS_MINUS']]

    def format_minutes(min_val):
        try:
            if min_val is None:
                return "DNP"

            # Split on ':' and only take the part before (i.e., "24.000000")
            min_str = str(min_val).split(':')[0]
            min_float = float(min_str)

            total_seconds = int(min_float * 60)
            minutes = total_seconds // 60
            return f"{minutes}"
        except (ValueError, TypeError):
            return "00:00"

    stats['MIN'] = stats['MIN'].apply(format_minutes)

    teams = {}
    for _, row in stats.iterrows():
        team = row['TEAM_ABBREVIATION']
        if team not in teams:
            teams[team] = []
        teams[team].append(row.to_dict())  # Convert row to dict for easy use in template

    return render_template('boxscore.html', teams=teams)





if __name__ == '__main__':
    app.run(debug=True)
