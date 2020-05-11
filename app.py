import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import altair as alt
import csv as csv
import numpy as np
import pandas as pd

# create APP
app = dash.Dash(__name__,
                assets_folder='assets',
                external_stylesheets=[dbc.themes.LUX,
                                      'jumbotron.css'])
server = app.server

# Set title
app.title = "Player Game-Load Monitoring"

# read in summarized data
summary_home_1 = pd.read_csv("data/Summary_Stats/home_game_1.csv")
summary_home_2 = pd.read_csv("data/Summary_Stats/home_game_2.csv")
summary_away_1 = pd.read_csv("data/Summary_Stats/away_game_1.csv")
summary_away_2 = pd.read_csv("data/Summary_Stats/away_game_2.csv")

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
        y = alt.Y('trimp_score:Q', title = "TRIMP score (AU)")
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
            session on individual athletes. The duration or volume of a training session on it's own does not \
            fully capture the difficulty of the session, as it fails to account for session intensity. \
            In it's most basic form, the TRIMP score of a session is the Rate of Perceived Exertion (RPE) \
            of the session multiplied by the duration, and it is measured in Arbitrary Units (AU).  \
            As a proxy for RPE, I have used arbitrary speed cut-offs to determine RPE zones."),
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
        html.P("The number of seconds in each of the RPE bins is then multiplied by the RPE level (1-10) to get a TRIMP Score."),
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
            in Game 1 for the Home team, player 2 covers about 0.5 the distance of player 1 \
            but has a TRIMP score about 0.75 as large as player 1's, indicating player 2 must have had some high intensity efforts. \
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