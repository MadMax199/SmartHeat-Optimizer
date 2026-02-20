

import sys
import os
import polars as pl
from pathlib import Path

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir))

from data_combine import join_data 
from data_loader import smartmeter_load, household_load, house_info_load, weather_load
from data_cleaner import fill_false, fill_null,fill_median, apply_interpolation, detect_outliers

paths = {
    "households": str(root_dir / "02_data" / "raw" / "households"),
    "info":       str(root_dir / "02_data" / "raw" / "households_info"),
    "weather":    str(root_dir / "02_data" / "raw" / "weather"),
    "protocols":  str(root_dir / "02_data" / "raw" / "protocols")
}

df_smartmeter = smartmeter_load(data_path=paths["households"])
df_household = household_load(data_path=paths["info"])
df_weather = weather_load(data_path=paths["weather"])
df_info = house_info_load(data_path=paths["protocols"])


data_combined = join_data(
    df1=df_smartmeter, 
    join_ids=['household_id'], 
    join_how='left',
    df2=df_household, 
    join_ids2=None, 
    join_how2=None,
    df3=df_weather, 
    join_ids3=['weather_id', 'date'], 
    join_how3='left',
    df4=df_info, 
    join_ids4=['household_id'], 
    join_how4='left',
)


data_combined = (
    data_combined
    .with_columns(pl.col("building_type").fill_null("unknown"))
    .sort(["household_id", "timestamp_local"])
    .pipe(fill_false, [
        "installation_haspvsystem", 
        "heatpump_installation_internetconnection",
        "building_renovated_windows",
        "building_renovated_roof", 
        "building_renovated_walls",
        "building_renovated_floor"
    ])
    .pipe(fill_null, [
        "kwh_returned_total",
        "building_floorareaheated_basement",
        "building_floorareaheated_topfloor",
        "building_floorareaheated_secondfloor",
        "building_floorareaheated_additionalareasplannedsize"
    ])
    .pipe(fill_median, ["building_constructionyear", "building_residents"], group_by_col="building_type")    
    .pipe(apply_interpolation, ["temperature_avg_daily", "kwh_received_total"])
)


output_path = root_dir / "02_data" / "temp" / "combined_data.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)
data_combined.write_csv(str(output_path), separator=";")
