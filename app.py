import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import altair as alt
import csv as csv
import numpy as np
import pandas as pd


alt.data_transformers.disable_max_rows()

# create APP
app = dash.Dash(__name__,
                assets_folder='assets',
                external_stylesheets=[dbc.themes.LUX,
                                      'jumbotron.css'])

# Set title
app.title = "Player Game-Load Monitoring"

# read in tracking file and it's pecularities
def read_tracking_data(game_num, team):
    csvfile =  open(f'data/Sample_Game_{game_num}/Sample_Game_{game_num}_RawTrackingData_{team}_Team.csv', 
    'r') 
    # create csv file reader
    reader = csv.reader(csvfile)
    # first row, 4th column is team name
    teamname = next(reader)[3].lower()
    # then need list of player names from second row of the raw data
    players = [x for x in next(reader) if x != '']
    columns = next(reader)
    # create x and y location column for each player
    for index in range(len(columns)):
        if columns[index][0:6] == "Player":
            columns[index] = columns[index]+"_x"
        if len(columns[index]) == 0:
            columns[index] = columns[index-1][:-1]+"y"
    # create columns for ball location
    columns[-2] = "Ball_x"
    columns[-1] = "Ball_y"

    # after extracting info can read in the dataframe
    df = pd.read_csv(f'data/Sample_Game_{game_num}/Sample_Game_{game_num}_RawTrackingData_{team}_Team.csv',
                skiprows = 3, names = columns)
    return df

# read in all four dataframes - hardcoded for now
home_game_1 = read_tracking_data("1", "Home")
home_game_2 = read_tracking_data("2", "Home")
away_game_1 = read_tracking_data("1", "Away")
away_game_2 = read_tracking_data("2", "Away")


def make_summary_stats(game):
    """
    Creates summary statistics for a tracking dataframe
    """
    df = game
    # Convert positions from metrica units to meters 
    x_columns = [col for col in df.columns if col[-1]=='x']
    y_columns = [col for col in df.columns if col[-1]=='y']
    
    # based on pitch dimension
    df[x_columns] = ( df[x_columns]-0.5) * 105
    df[y_columns] = -1 * ( df[y_columns]-0.5 ) * 68

    # extract list of players
    player_nums = np.unique([c[:-2] for c in df.columns if c[:6] == "Player"])
    # delta time info for measuring velocity
    time_diff = df['Time [s]'].diff()

    # now get velocities:
    for player in player_nums:
        # smooth it with window = 5
        v_x = (df[player+'_x'].diff()/time_diff).rolling(window = 5).mean()
        v_y = (df[player+'_x'].diff()/time_diff).rolling(window = 5).mean()
        # append to df
        df[player+'_VX'] = v_x
        df[player+'_VY'] = v_y
        # drop outliers based on top max speed- 12.4m/s
        df[player+'Velocity'] = np.where(np.sqrt(v_x**2 + v_y**2) > 12.4, 
                                        np.nan, np.sqrt(v_x**2 + v_y**2))
    # Create Summary df for players
    summary_stats = pd.DataFrame(index=player_nums)
    # Calculate total distance covered for each player
    distance = []
    minutes_played = []
    trimp_score = []
    for player in player_nums:
        velocity_col = player + 'Velocity'
        # 25 for 25HZ to average out over 1s, 1000 to convert to KM
        player_distance = df[velocity_col].sum()/25/1000 
        distance.append(player_distance)
        # determine MP, use X-loc arbitrarily
        player_time = df[player+'_x'].count()/25/60 
        minutes_played.append(player_time)
        # determine trimp score
        # determine speed buckets correlating to RPE scores
        # lets define 1,2,3,4,5,6,7,8,9,10 as our deciles for RPE, naturally intuitive
        for i in range(1,10):
            df[player+f'RPE{i}'] = df[velocity_col].apply(lambda s: True if i-1 <= s <= i else False)
        df[player+'RPE10'] = df[velocity_col].apply(lambda s: True if s > 9 else False)
        # now sum up the amount of time in each bucket
        player_trimp = 0
        for effort in range(1,11):
            player_trimp += df[f'{player}RPE{effort}'].sum()/25 * effort
        trimp_score.append(player_trimp)
        df.drop(columns = [col for col in df.columns if 'RPE' in col])
    
    # summary df including the three stats
    summary_stats['distance_ran'] = distance
    summary_stats['playing_time'] = minutes_played
    summary_stats['trimp_score'] = trimp_score

    return summary_stats

# Read in summary stats for each game- ONLY ONCE
summary_home_1 = make_summary_stats(home_game_1)
summary_home_2 = make_summary_stats(home_game_2)
summary_away_1 = make_summary_stats(away_game_1)
summary_away_2 = make_summary_stats(away_game_2)

def make_minutes_plot(summary_df):
    chart = alt.Chart(summary_df.reset_index()).mark_bar().encode(
        x = alt.X('index:O', title = "player"),
        y = alt.Y('playing_time:Q', title = "minutes played")
    ).properties(title = "Playing time by player")
    return chart

def make_distance_plot(summary_df):
    chart = alt.Chart(summary_df.reset_index()).mark_bar(color = 'green').encode(
        x = alt.X('index:O', title = "player"),
        y = alt.Y('distance_ran:Q', title = "distance ran (km)")
        ).properties(title = "Distance ran by player")
    return chart

def make_trimp_plot(summary_df):
    chart = alt.Chart(summary_df.reset_index()).mark_bar(color = 'red').encode(
        x = alt.X('index:O', title = "player"),
        y = alt.Y('trimp_score:Q', title = "TRIMP score")
        ).properties(title = "TRIMP score by player")
    return chart

def make_plot(game, team, plot):
    if game == "1" and team == "Home":
        summary_df = summary_home_1
    if game == "2" and team == "Home":
        summary_df = summary_home_2
    if game == "1" and team == "Away":
        summary_df = summary_away_1
    if game == "2" and team == "Away":
        summary_df = summary_away_2
    if plot == "minutes":
        return make_minutes_plot(summary_df)
    if plot == "distance":
        return make_distance_plot(summary_df)
    if plot == "trimp":
        return make_trimp_plot(summary_df)

# Set JUMBOTRON element
JUMBOTRON = dbc.Jumbotron(
    [
        dbc.Col(
            [
                html.H1("Game Load Tracker", className="display-3"),
                html.P(
                    "Monitor player's physical loads using tracking data." ,
                    className="lead"),
            ],
            style={"text-align": 'center'})],
    fluid=True,
)

# Declate CONTENT element for dash
CONTENT = dbc.Container(
    [
        html.P(
            "This app allows coaches, training staff or other decision makers to explore the physical load of a match on individual players."
        ),
        dbc.Row(dbc.Col(html.H4('Motivation and Background'))),
        html.P(
            "The advent of tracking data in soccer has allowed for exciting developments in the analysis of tactics. \
            However this is not the only exciting use of this data, as it can also be used on the sports-science \
            side to more accurately monitor the physical toll of matches on players. This information can then be used \
            in both game-day and in training decisions."
            ),
        html.P("The TRIMP (TRaining IMpulse) [reference #3]  score framework has been used to assign a player load \
            score to each player, for each game. \
            The TRIMP model has been used in endurance sports to quantify the load of a given training \
            session on individual athletes. In it's most basic form, the TRIMP score of a session will be the RPE \
            of the session multiplied by the duration, and it is measured in Arbitrary Units (AU).  \
            As a proxy for RPE, I have used arbitrary speed cut-offs."),
        dbc.Row(dbc.Col(html.Ul(id='my-list', 
            children=["RPE 1: speed less than 1 m/s",
            html.Br(),
            "RPE 2: speed between 1-2 m/s ",
            html.Br(),
            "RPE 3: speed less than 2-3 m/s",
            html.Br(),
            "RPE 4: speed between 3-4 m/s",
            html.Br(),
            "RPE 5: speed less than 4-5 m/s",
            html.Br(),
            "RPE 6: speed less than 5-6 m/s",
            html.Br(),
            "RPE 7: speed between 6-7 m/s",
            html.Br(),
            "RPE 8: speed between 7-8 m/s",
            html.Br(),
            "RPE 9: speed between 8-9 m/s",
            html.Br(),
            "RPE 10: speed > 9 m/s"]))),
        html.P("The number of seconds in each of these RPE bins is then multiplied by the RPE level to get a total TRIMP Score."),
        dbc.Row(dbc.Col(html.H4('Data'))),
        html.P("Currently there are only two games in the demo. The games used in the analysis come from the Sample data on the Metrica Sports \
            Github page [reference #1]. The games and players are anonymized in the data."),

        html.Br(),
        dbc.Row(dbc.Col(html.H3('Game Load Summaries Per Player'))),
        dbc.Row(dbc.Col(html.Hr(hidden=False,
                        style={'height':1,
                                'background-color': '#50107a',
                                'margin-top': 0}))
                           ),
        dbc.Row(dbc.Col(html.H5('Choose a Game'))),
        dbc.Row(
                dcc.Dropdown(
                    id = 'game-dropdown',
                    options=[
                        {'label': 'Game 1', 'value': '1'},
                        {'label': 'Game 2', 'value': '2'}
                            ],
                    value='1', style=dict(width='50%')),
                ),
        dbc.Row(dbc.Col(html.Br())),
        dbc.Row(dbc.Col(html.H5('Choose a Team'))),
        dbc.Row(
                dcc.Dropdown(
                    id = 'team-dropdown',
                    options=[
                        {'label': 'Home', 'value': 'Home'},
                        {'label': 'Away', 'value': 'Away'}
                            ],
                    value='Home', style=dict(width='50%')),
                            ),                      
        dbc.Row([
                html.Iframe(
                        sandbox='allow-scripts',
                        id='minutes-plot',
                        height=450,
                        width=350,
                        style={'border-width': '0'},
                            ),
                html.Iframe(
                        sandbox='allow-scripts',
                        id='distance-plot',
                        height=450,
                        width=350,
                        style={'border-width': '0'},
                            ),
                html.Iframe(
                        sandbox='allow-scripts',
                        id='trimp-plot',
                        height=450,
                        width=350,
                        style={'border-width': '0'},
                            ),
                ]),
        dbc.Row(dbc.Col(html.H4('Discussion'))),
        html.P("In this demo the TRIMP score tracks quite closely with the distance ran. \
            However there are a few exceptions where it provides additional and useful information. For example, \
            in Game 1 for the Home team player 11 covers about 0.5 the distance of player 10 \
            but has a TRIMP score about 0.75 as large as player 10's, indicating player 11 must have had some high intensity efforts. \
            The TRIMP framework here could also be improved by tailoring the RPE cut-off speeds to each individual, as well as \
            potentially using other metrics such as acceleration."),
        html.Br(),
        html.Br(),
    ])

FOOTER = dbc.Container(
    [
    dbc.Row(dbc.Col(html.H3('References'))),
    dbc.Row(dbc.Col(dcc.Link('1. Metrica Sports Sample Data', href='https://github.com/metrica-sports/sample-data'))),
    dbc.Row(dbc.Col(dcc.Link('2. Friends of Tracking - Laurie Shaw', href='https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking'))),
    dbc.Row(dbc.Col(dcc.Link('3. A new approach to monitor exercise training.', 
    href='https://www.ncbi.nlm.nih.gov/pubmed/11708692'))),
    dbc.Row(dbc.Col(html.Br())),
    ]
)
            #]),
    #])
        
app.layout = html.Div([JUMBOTRON, 
                       CONTENT,
                       FOOTER])

# Callbacks
@app.callback(
        dash.dependencies.Output('minutes-plot', 'srcDoc'),
       [dash.dependencies.Input('game-dropdown', 'value'),
       dash.dependencies.Input('team-dropdown', 'value')])

def update_minutes_plot(game_value, team_value):
    return make_plot(game_value, team_value, "minutes").to_html()

@app.callback(
        dash.dependencies.Output('distance-plot', 'srcDoc'),
       [dash.dependencies.Input('game-dropdown', 'value'),
       dash.dependencies.Input('team-dropdown', 'value')])

def update_distance_plot(game_value, team_value):
    return make_plot(game_value, team_value, "distance").to_html()

@app.callback(
        dash.dependencies.Output('trimp-plot', 'srcDoc'),
       [dash.dependencies.Input('game-dropdown', 'value'),
       dash.dependencies.Input('team-dropdown', 'value')])

def update_trimp_plot(game_value, team_value):
    return make_plot(game_value, team_value, "trimp").to_html()
    
if __name__ == '__main__':
    app.run_server(debug=True)