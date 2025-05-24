
import pandas as pd
import json

# Load model profile
with open("RacingModel_May22.json", "r") as f:
    model_profile = json.load(f)

# Load race data
df_race = pd.read_csv("ALLStats_SAMPLE.csv")
df_comments = pd.read_excel("horse_comments.xlsx")
df_history = pd.read_csv("HorseHistory.csv")

# Normalize function
def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

# Normalize scores
df_race["speed_score"] = normalize(df_race[["avgSpeed", "finalSpeed1Back", "speedLastRace", "backSpeed"]].mean(axis=1))
df_race["class_score"] = 1 - normalize(df_race["averageClassRank"])
df_race["trainer_score"] = normalize(df_race["trainerWinPercent"])
df_race["jockey_score"] = normalize(df_race["jockeyWinPercent"])
df_race["pace_score"] = normalize(df_race[["averagePaceE1", "averagePaceE2", "averagePaceLp"]].mean(axis=1))

# Base composite score
weights = {
    "speed_score": 0.30,
    "class_score": 0.25,
    "trainer_score": 0.10,
    "jockey_score": 0.10,
    "pace_score": 0.25
}
df_race["composite_score"] = (
    df_race["speed_score"] * weights["speed_score"] +
    df_race["class_score"] * weights["class_score"] +
    df_race["trainer_score"] * weights["trainer_score"] +
    df_race["jockey_score"] * weights["jockey_score"] +
    df_race["pace_score"] * weights["pace_score"]
)

# Merge comments
df_combined = df_race.merge(df_comments, how="left", left_on="horseName", right_on="Name")

# Merge history
df_history["raceDate"] = pd.to_datetime(df_history["raceDateString"], errors="coerce")
df_recent = df_history.sort_values(by="raceDate", ascending=False).groupby("horseName").head(3)
form_summary = df_recent.groupby("horseName").agg(
    recent_finishes=("finish", lambda x: ", ".join(x.dropna().astype(str))),
    avg_finish=("finish", "mean"),
    recent_comments=("comment", lambda x: " | ".join(x.dropna().astype(str)))
).reset_index()
df_final = df_combined.merge(form_summary, how="left", on="horseName")

# Apply model logic from profile
for flag, details in model_profile["flags"].items():
    if isinstance(details, list):
        df_final[flag] = df_final["PositiveComments"].apply(
            lambda x: sum(kw in str(x).lower() for kw in details) >= 3
        )
    elif "trip_keywords" in details:
        df_final[flag] = df_final.apply(
            lambda row: (
                row["pace_score"] >= float(details["requires"].split(">= ")[1])
                if "pace_score" in details["requires"] else True
            ) and any(kw in str(row["recent_comments"]).lower() for kw in details["trip_keywords"]),
            axis=1
        )

# Apply boost for bestSpeedLateAtDistanceSurface
top_speed = df_final["bestSpeedLateAtDistanceSurface"].max()
df_final["boost_best_speed_late"] = (df_final["bestSpeedLateAtDistanceSurface"] == top_speed).astype(float) * 0.015

# Apply final scoring
df_final["composite_score"] += (
    df_final["flag_comment_multiple_win_signals"].astype(float) * 0.03 +
    df_final["flag_front_runner_comment_boost"].astype(float) * 0.02 +
    df_final["flag_hidden_closer"].astype(float) * 0.01 +
    df_final["flag_comment_best_speed_distance"].astype(float) * 0.015 +
    df_final["flag_tactical_pace_setter"].astype(float) * 0.015 +
    df_final["boost_best_speed_late"]
)

df_final["rank"] = df_final["composite_score"].rank(method="first", ascending=False)
df_final.sort_values("rank").to_csv("RacePredictionOutput.csv", index=False)
print("Prediction output saved to RacePredictionOutput.csv")
