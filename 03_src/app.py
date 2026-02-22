import sys
import os
import polars as pl
from pathlib import Path

# --- PFAD SETUP ---
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir))

# --- IMPORTE ---
from config import Schema, fill_false_list, fill_null_list, fill_median_list, fill_inter_list, fill_string_float, fill_string_boolean, fill_string_integer, fill_unbekannt_list
from data_combine import join_data
from data_loader import smartmeter_load, household_load, house_info_load, weather_load, load_price_data
from data_cleaner import (
    fill_false, fill_null, fill_median, apply_interpolation,
    apply_string_to_datetime, apply_string_to_date, apply_string_to_float,
    apply_string_to_boolean, apply_string_to_integer,
    apply_unbekannt

)
from data_validation import double_numbers, detect_outliers, check_data_quality

paths = {
    "households": str(root_dir / "02_data" / "raw" / "households"),
    "info":       str(root_dir / "02_data" / "raw" / "households_info"),
    "weather":    str(root_dir / "02_data" / "raw" / "weather"),
    "protocols":  str(root_dir / "02_data" / "raw" / "protocols"),
    "prices":  str(root_dir / "02_data" / "raw" / "prices")
}

# --- DATEN LADEN & JOINEN ---
df_smartmeter = smartmeter_load(data_path=paths["households"])
df_household = household_load(data_path=paths["info"])
df_weather = weather_load(data_path=paths["weather"])
df_info = house_info_load(data_path=paths["protocols"])
df_prices = load_price_data(data_path=paths["prices"])

data_combined = join_data(
    df_smartmeter,
    joins=[
        {"df": df_household, "on": ["household_id"], "how": "left"},
        {"df": df_weather, "on": ["weather_id", "date"], "how": "left"},
        {"df": df_info, "left_on": ["household_id"], "right_on": ["household_id_info"], "how": "left"},
        {"df": df_prices, "on": ["date"], "how": "left"},
    ]
)

# --- INITIALES CLEANING (Imputation) ---
data_combined = (
    data_combined
    .with_columns(pl.col("building_type").fill_null("unknown"))
    .sort(["household_id", "timestamp_local"])
    .pipe(fill_false,fill_false_list)
    .pipe(fill_null,fill_null_list)
    .pipe(fill_median, fill_median_list, group_by_col="building_type")
    .pipe(apply_unbekannt, fill_unbekannt_list)
    .pipe(apply_interpolation, fill_inter_list)
)

# Zwischenspeichern Raw-Combined
output_path_temp = root_dir / "02_data" / "temp" / "combined_data.csv"
output_path_temp.parent.mkdir(parents=True, exist_ok=True)
data_combined.write_csv(str(output_path_temp), separator=";")

# --- VALIDATION (Teil 1) ---
print("Starte erste Validierung...")
double_numbers(data_combined)
detect_outliers(data_combined)
check_data_quality(data_combined, Schema)

# --- DATEN-TYP KONVERTIERUNG (Refining) ---
data_combined_cleaned = (
    data_combined
    .pipe(apply_string_to_datetime, ["timestamp_local_right"], tz="Europe/Zurich")
    .pipe(apply_string_to_float,fill_string_float)
    .pipe(apply_string_to_boolean,fill_string_boolean)
    .pipe(apply_string_to_integer, fill_string_integer)
    .pipe(apply_string_to_date, ["visit_date"])
)

# --- VALIDATION (Teil 2) ---
print("Starte finale Validierung...")
check_data_quality(data_combined_cleaned, Schema)

# --- OUTPUT SPEICHERN ---
output_path_parquet = root_dir / "02_data" / "processed" / "combined_data_cleaned.parquet"
output_path_parquet.parent.mkdir(parents=True, exist_ok=True)

# Speichern als Parquet
data_combined_cleaned.write_parquet(str(output_path_parquet))

print(f"✅ Datei erfolgreich als Parquet gespeichert: {output_path_parquet.name}")