import csv as csv
import numpy as np
import pandas as pd

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

# Read in summary stats for each game
summary_home_1 = make_summary_stats(home_game_1)
summary_home_2 = make_summary_stats(home_game_2)
summary_away_1 = make_summary_stats(away_game_1)
summary_away_2 = make_summary_stats(away_game_2)

# write this to file
pd.DataFrame.to_csv(summary_home_1, "data/Summary_Stats/home_game_1.csv")
pd.DataFrame.to_csv(summary_home_2, "data/Summary_Stats/home_game_2.csv")
pd.DataFrame.to_csv(summary_away_1, "data/Summary_Stats/away_game_1.csv")
pd.DataFrame.to_csv(summary_away_2, "data/Summary_Stats/away_game_2.csv")