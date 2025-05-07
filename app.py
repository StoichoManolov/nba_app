from flask import Flask, render_template, request
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2, commonplayerinfo, playercareerstats


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/schedule')
def schedule():
    # Get the schedule for the 2024-25 season
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2024-25', league_id_nullable='00')
    games = gamefinder.get_data_frames()[0]

    # Get the latest 30 games
    games = games[['GAME_ID', 'GAME_DATE', 'MATCHUP']].head(60)

    final_games = []

    # Iterate over the rows of the DataFrame
    for _, game in games.iterrows():
        # Only add games that do not contain '@' in the matchup
        if '@' not in game['MATCHUP']:
            final_games.append(game)

    # Limit to first 30 games
    final_games = final_games[:30]

    search_query = request.args.get('search', '').lower()

    if search_query:
        final_games = [game for game in final_games if search_query in game['MATCHUP'].lower() or search_query in game['GAME_DATE'].lower()]

    # Split into two columns
    column1_games = final_games[:15]
    column2_games = final_games[15:]

    return render_template('schedule.html', column1_games=column1_games, column2_games=column2_games, search_query=search_query)







@app.route('/boxscore/<game_id>')
def boxscore(game_id):

    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    stats = boxscore.player_stats.get_data_frame()
    stats = stats[['PLAYER_ID', 'TEAM_ABBREVIATION', 'PLAYER_NAME', 'MIN', 'PTS', 'AST', 'REB', 'FGM', 'FGA', 'FG_PCT',
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


@app.route('/player/<int:player_id>')
def player_page(player_id):
    # Basic player info
    info_data = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_normalized_dict()
    info = info_data['CommonPlayerInfo'][0]

    # Career + season averages
    career_data = playercareerstats.PlayerCareerStats(player_id=player_id).get_normalized_dict()
    all_stats = career_data['SeasonTotalsRegularSeason']

    # Get most recent season and career row
    season_avg = all_stats[-1] if all_stats else None
    career_avg = all_stats[-1].copy() if all_stats else None

    # Calculate per-game career stats manually (some older seasons may miss headline data)
    if all_stats:
        total_pts = sum([s['PTS'] for s in all_stats])
        total_ast = sum([s['AST'] for s in all_stats])
        total_reb = sum([s['REB'] for s in all_stats])
        total_gp = sum([s['GP'] for s in all_stats])

        if total_gp > 0:
            career_avg = {
                'PTS': round(total_pts / total_gp, 1),
                'AST': round(total_ast / total_gp, 1),
                'REB': round(total_reb / total_gp, 1),
            }

    return render_template(
        'player_info.html',
        info=info,
        season_avg=season_avg,
        career_avg=career_avg
    )


if __name__ == '__main__':
    app.run(debug=True)
