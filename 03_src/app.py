import sys
import os
import polars as pl
from pathlib import Path

# --- PFAD SETUP ---
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir))

# --- IMPORTE ---
from config import Schema
from data_combine import join_data
from data_loader import smartmeter_load, household_load, house_info_load, weather_load
from data_cleaner import (
    fill_false, fill_null, fill_median, apply_interpolation,
    apply_string_to_datetime, apply_string_to_date, apply_string_to_float,
    apply_string_to_boolean, apply_string_to_integer
)
from data_validation import double_numbers, detect_outliers, check_data_quality

paths = {
    "households": str(root_dir / "02_data" / "raw" / "households"),
    "info":       str(root_dir / "02_data" / "raw" / "households_info"),
    "weather":    str(root_dir / "02_data" / "raw" / "weather"),
    "protocols":  str(root_dir / "02_data" / "raw" / "protocols")
}

# --- DATEN LADEN & JOINEN ---
df_smartmeter = smartmeter_load(data_path=paths["households"])
df_household = household_load(data_path=paths["info"])
df_weather = weather_load(data_path=paths["weather"])
df_info = house_info_load(data_path=paths["protocols"])

data_combined = join_data(
    df1=df_smartmeter, join_ids=['household_id'], join_how='left',
    df2=df_household,  join_ids2=None,            join_how2=None,
    df3=df_weather,    join_ids3=['weather_id', 'date'], join_how3='left',
    df4=df_info,       join_ids4=['household_id'], join_how4='left',
)

# --- INITIALES CLEANING (Imputation) ---
data_combined = (
    data_combined
    .with_columns(pl.col("building_type").fill_null("unknown"))
    .sort(["household_id", "timestamp_local"])
    .pipe(fill_false, [
        "building_pvsystem_available",
        "installation_haspvsystem",
        "heatpump_installation_internetconnection",
        "building_renovated_windows",
        "building_renovated_roof",
        "building_renovated_walls",
        "building_renovated_floor",
        "building_electricvehicle_available",
        "smartmeterdata_available_15min", 
        "smartmeterdata_available_daily",
        'heatdistribution_system_radiators', 
        'heatdistribution_system_floorheating', 'heatdistribution_system_thermostaticvalve', 
        'heatdistribution_system_buffertankavailable', 'dhw_production_byheatpump', 
        'dhw_production_byelectricwaterheater', 'dhw_production_bysolar', 
        'dhw_production_byheatpumpboiler', 'dhw_circulation_notinuse', 
        'dhw_circulation_bytraceheating', 'dhw_circulation_bycirculationpump', 
        'dhw_circulation_switchedbytimer', 'dhw_sterilization_available', 
        'dhw_sterilization_active', 'heatpump_clean', 'heatpump_basicfunctionsokay', 
        'heatpump_technicallyokay', 'heatpump_installation_correctlyplanned', 
        'heatpump_airsource_airductsdistanceokay', 'heatpump_airsource_airductsfree', 
        'heatpump_airsource_airductscleaningrequired', 'heatpump_airsource_airductsdrainokay', 
        'heatpump_airsource_evaporatorclean', 'heatpump_groundsource_brinecircuit_antifreezeexists', 
        'heatpump_groundsource_currentpressure_okay', 'heatpump_groundsource_currenttemperature_okay', 
        'heatpump_heatingcurvesetting_toohigh_beforevisit', 'heatpump_heatingcurvesetting_changed', 
        'heatpump_heatinglimitsetting_toohigh_beforevisit', 'heatpump_heatinglimitsetting_changed', 
        'heatpump_nightsetbacksetting_activated_beforevisit', 'heatpump_nightsetbacksetting_activated_aftervisit', 
        'dhw_temperaturesetting_changed', 'dhw_storage_lastdescaling_toolongago', 
        'heatdistribution_circulation_pumpstageposition_changed', 'heatdistribution_recommendation_insulatepipes', 
        'heatdistribution_recommendation_installthermostaticvalve', 'heatdistribution_recommendation_installrpmvalve',
        'building_floorareaheated_additionalareasplanned'
          
    ])
    .pipe(fill_null, [
        "kwh_returned_total",
        "building_floorareaheated_basement",
        "building_floorareaheated_topfloor",
        "building_floorareaheated_secondfloor",

    ])
    .pipe(fill_median, ["building_constructionyear", "building_residents"], group_by_col="building_type")
    .pipe(apply_interpolation, ["temperature_avg_daily", "kwh_received_total"])
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
    .pipe(apply_string_to_float, [
        "heatpump_installation_normpoint_heatingpower",
        "heatpump_groundsource_brinecircuit_length",
        "heatpump_groundsource_brinecircuit_depth",
        "heatpump_groundsource_brinecircuit_numberofholes",
        "heatpump_groundsource_brinecircuit_coolingcapacity",
        "dhw_temperaturesetting_beforevisit",
        "dhw_temperaturesetting_aftervisit"
    ])
    .pipe(apply_string_to_boolean, [
        "building_electricvehicle_available",
        "dhw_sterilization_available",
        "dhw_sterilization_active",
        "heatpump_airsource_airductsdistanceokay",
        "heatpump_airsource_airductsfree",
        "heatpump_airsource_airductscleaningrequired",
        "heatpump_airsource_airductsdrainokay",
        "heatpump_airsource_evaporatorclean",
        "heatpump_heatinglimitsetting_toohigh_beforevisit",
        "heatpump_heatinglimitsetting_changed",
        "heatdistribution_circulation_pumpstageposition_changed"
    ])
    .pipe(apply_string_to_integer, [
        "visit_year",
        "dhw_storage_lastdescaling_year",
        "heatpump_installation_year",
        "building_constructionyear",
        "dhw_temperaturesetting_aftervisit",
        "heatdistribution_circulation_pumpstageposition_beforevisit",
        "heatdistribution_circulation_pumpstageposition_aftervisit",
        "heatpump_heatinglimitsetting_beforevisit",
        "heatpump_heatinglimitsetting_aftervisit"
    ])
    .pipe(apply_string_to_date, [
        "heatdistribution_expansiontank_pressure_actual",
        "heatdistribution_expansiontank_pressure_target"
    ])
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