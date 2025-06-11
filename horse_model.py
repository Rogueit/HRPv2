
import pandas as pd

def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

def compute_early_pace(row):
    if row['avgSpeed'] > 0:
        return row['avgSpeed']
    elif row['averageCompetitiveLevel'] > 0:
        return row['averageCompetitiveLevel'] * 0.6
    else:
        return 0

def form_bonus(row):
    if 'Ran 2nd' in str(row['PositiveComments']) or 'Finished close' in str(row['PositiveComments']):
        return 0.05
    return 0

def workout_bonus(row):
    if 'Sharp' in str(row['PositiveComments']) and 'workout' in str(row['PositiveComments']):
        return 0.05
    return 0

def pace_setup_bonus(row, top_pace, second_pace):
    if abs(row['earlyPaceProxy'] - top_pace) <= 5 and row['avgSpeed'] < 0.1:
        return 0.03
    return 0

def stalker_bias_bonus(row, field_size):
    if 0.4 < row['score_early_pace'] < 0.7 and field_size <= 6 and row['NegativeComments'] is None:
        return 0.02
    return 0

def dominant_pace_favorite_bonus(row, top_pace, second_pace):
    if row['earlyPaceProxy'] == top_pace and (top_pace - second_pace > 8) and 'favorite' in str(row['PositiveComments']).lower():
        return 0.04
    return 0

def layoff_penalty(row):
    if row['daysSinceLastRace'] > 180:
        return -0.07
    elif row['daysSinceLastRace'] > 90:
        return -0.05
    elif row['daysSinceLastRace'] > 60:
        return -0.03
    return 0

def speed_style_combo_bonus(row):
    if 'Highest last race speed rating' in str(row['PositiveComments']) and 'Early speed running style' in str(row['PositiveComments']):
        return 0.04
    return 0

def last_out_speed_good_trainer_bonus(row, trainer_threshold=0.75):
    if 'Highest last race speed rating' in str(row['PositiveComments']) and row['score_trainer'] >= trainer_threshold:
        return 0.035
    return 0

claiming_weights = {
    'speed': 0.25,
    'comp_level': 0.2,
    'trainer': 0.15,
    'jockey': 0.10,
    'early_pace': 0.2,
    'positive': 0.05,
    'negative': -0.05
}
