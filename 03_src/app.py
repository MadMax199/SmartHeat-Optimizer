

import sys
import os
import polars as pl
from pathlib import Path

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir))

from data_combine import join_data 
from data_loader import smartmeter_load, household_load, house_info_load, weather_load

paths = {
    "households": str(root_dir / "data" / "raw" / "households"),
    "info":       str(root_dir / "data" / "raw" / "households_info"),
    "weather":    str(root_dir / "data" / "raw" / "weather"),
    "protocols":  str(root_dir / "data" / "raw" / "protocols")
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

output_path = root_dir / "data" / "processed" / "combined_data.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)
data_combined.write_csv(str(output_path), separator=";")
