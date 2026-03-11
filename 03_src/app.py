import sys
import os
import polars as pl
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns
import shap

# --- PFAD SETUP ---
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir))

# --- IMPORTE ---
from config import (
    Schema, fill_false_list, fill_null_list, 
    fill_median_list, fill_inter_list,
    fill_string_float, fill_string_boolean, 
    fill_string_integer, fill_unbekannt_list,
    target_col, feature_cols
)
from data_combine import join_data
from data_loader import smartmeter_load, household_load, house_info_load, weather_load, load_price_data
from data_cleaner import  (
   fill_false, fill_null, fill_median, apply_interpolation, 
   apply_string_to_datetime, apply_string_to_date,
   apply_string_to_float, apply_string_to_boolean, apply_string_to_integer,
   apply_unbekannt, compare_imputation, check_amount_nulls
)
from data_validation import (
    double_numbers, detect_outliers, 
    check_data_quality
)
from features import (
add_weekdays,add_weekend, 
heating_season, renovation_index,
heating_amount, add_price_features, 
solar_potentials, add_thermal_dynamics, add_cyclic_features, add_building_type_dummies
)
from utilis import (
    train_test_split, correlated_features_drop,
    feature_importance_analyse, compare_models,tune_random_forest,
    plot_final_prediction
)

# --- PFADE ---
paths = {
    "households": str(root_dir / "02_data" / "raw" / "households"),
    "info":       str(root_dir / "02_data" / "raw" / "households_info"),
    "weather":    str(root_dir / "02_data" / "raw" / "weather"),
    "protocols":  str(root_dir / "02_data" / "raw" / "protocols"),
    "prices":  str(root_dir / "02_data" / "raw" / "prices")
}

# --- DATEN LADEN & JOINEN ---
df_smartmeter = smartmeter_load(data_path=paths["households"])
df_protocols = house_info_load(data_path=paths["protocols"])
df_household_info = household_load(data_path=paths["info"])
df_prices = load_price_data(data_path=paths["prices"])
df_weather = weather_load(data_path=paths["weather"])

print(f"Anzahl Unique Haushalte Verbrauchsdaten: {df_smartmeter.select(pl.col('household_id').n_unique()).item()}")
print(f"Anzahl Unique Haushalte Protokolldaten: {df_protocols.select(pl.col('household_id').n_unique()).item()}")
print(f"Anzahl Unique Haushalte Metadaten: {df_household_info.select(pl.col('household_id').n_unique()).item()}")


data_combined = join_data(
    df_smartmeter,
    joins=[
        {"df": df_household_info, "on": ["household_id"], "how": "left"},
        {"df": df_weather, "on": ["weather_id", "date"], "how": "left"},
        {"df": df_protocols, "left_on": ["household_id"], "right_on": ["household_id_info"], "how": "left"},
        {"df": df_prices, "on": ["date"], "how": "left"},
    ]
)

print(f"Anzahl Unique Combined-Info: {data_combined.select(pl.col('household_id').n_unique()).item()}")
print(f"Anzahl Beobachtungen Combined-Info: {data_combined.select(pl.col('household_id').count()).item()}")

# --- INITIALES CLEANING (Imputation) ---
data_combined_filled = (
    data_combined
    .pipe(apply_unbekannt, fill_unbekannt_list)
    .pipe(fill_false,fill_false_list)
    .pipe(fill_null,fill_null_list)
    .pipe(fill_median, fill_median_list, group_by_col="building_type")
    .sort(["household_id", "date"])
    .pipe(apply_interpolation, fill_inter_list)
)

# Direkter CHeck in der Pipline on die Inputaiton erfolgreich war
compare_imputation(
    df_before=data_combined,
    df_after=data_combined_filled,
    col_lists={
        "building_type":    ["building_type"],
        "fill_false_list":  fill_false_list,
        "fill_null_list":   fill_null_list,
        "fill_median_list": fill_median_list,
        "fill_unbekannt":   fill_unbekannt_list,
        "fill_inter_list":  fill_inter_list,
    }
)


# Zwischenspeichern Raw-Combined
output_path_temp = root_dir / "02_data" / "temp" / "combined_data.csv"
output_path_temp.parent.mkdir(parents=True, exist_ok=True)
data_combined_filled.write_csv(str(output_path_temp), separator=";")

# --- VALIDATION (Teil 1) ---
print("Starte erste Validierung...")
double_numbers(data_combined_filled)
detect_outliers(data_combined_filled)
check_data_quality(data_combined_filled, Schema)

# --- DATEN-TYP KONVERTIERUNG (Refining) ---
data_combined_cleaned = (
    data_combined_filled
    .pipe(apply_string_to_datetime, ["timestamp_local_right"], tz="Europe/Zurich")
    .pipe(apply_string_to_float,fill_string_float)
    .pipe(apply_string_to_boolean,fill_string_boolean)
    .pipe(apply_string_to_integer, fill_string_integer)
    .pipe(apply_string_to_date, ["visit_date"])
)

# --- Erneute Validierung und Daten wegschreiben ---
print("Starte finale Validierung...")
check_data_quality(data_combined_cleaned, Schema)
output_path_parquet = root_dir / "02_data" / "processed" / "combined_data_cleaned.parquet"
output_path_parquet.parent.mkdir(parents=True, exist_ok=True)
data_combined_cleaned.write_parquet(str(output_path_parquet))
print(f"✅ Datei erfolgreich als Parquet gespeichert: {output_path_parquet.name}")

#---Feature für Machine Learning Modell auswählen
df_ml = (
    data_combined_cleaned
    .pipe(add_weekdays)
    .pipe(add_weekend)
    .pipe(heating_season)
    .pipe(renovation_index)
    .pipe(heating_amount)
    .pipe(add_price_features)
    .pipe(solar_potentials)
    .pipe(add_thermal_dynamics)
    .pipe(add_cyclic_features)
    .pipe(add_building_type_dummies)
    .select(["date",target_col] + feature_cols)
)
check_amount_nulls(df_ml)


#---Train-Testsplit ausführen
X_train, X_test, y_train, y_test = train_test_split(df_ml,feature_cols=feature_cols,target_col=target_col)

#---Check ob Features untereinander korreliert sind 
X_train_cleaned, X_test_cleaned, final_features = correlated_features_drop(X_train, X_test,feautre_cols=feature_cols)

#---Random Forst als Basis verwenden 
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train_cleaned, y_train)

#---Feature Importance und Validierung 
feature_importance_analyse(model=rf, X_test= X_test_cleaned,output_dir= os.path.join(root_dir, "05_plots"),filename="shape_plot.png")

#---Modellvergleich um das beste Modell zu finden
comparison = compare_models(X_train_cleaned, X_test_cleaned, y_train, y_test)
print(comparison)

#---Modell Tuning auf Basis des Output des Modellchecks

best_rf = tune_random_forest(X_train_cleaned, y_train)
tscv = TimeSeriesSplit(n_splits=5)
scores = cross_val_score(best_rf, X_train_cleaned, y_train, cv=tscv, scoring='r2')
print(f"CV R² Scores: {scores}")
print(f"Mean CV R²: {scores.mean():.4f}")

# ---Finale Validierung mit dem getunten Modell
y_pred_final = best_rf.predict(X_test_cleaned)
final_r2 = r2_score(y_test, y_pred_final)
final_mae = mean_absolute_error(y_test, y_pred_final)

plot_final_prediction(y_test, y_pred_final)