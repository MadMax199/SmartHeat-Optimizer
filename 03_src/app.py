import sys
import os
import polars as pl
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.model_selection import TimeSeriesSplit, cross_validate

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
    target_col, feature_cols, feature_cols_cleaned
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
    feature_importance_analyse, compare_models,
    tune_lightgbm, plot_final_prediction,
    plot_business_drivers, validate_model_assumptions
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
        {"df": df_protocols, "left_on": ["household_id", "date"], "right_on": ["household_id_info"], "how": "left"}, --discuss
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

# ---  Direkter Check in der Pipline --- 

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


# ---  Zwischenspeichern Raw-Combined --- Notwendig um Pipline Entwicklung zu beschleunigen
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
sample_idx = np.random.choice(len(X_train_cleaned), 20_000, replace=False)
X_sample = X_train_cleaned.iloc[sample_idx]
y_sample = y_train[sample_idx]

rf = RandomForestRegressor(
    n_estimators=50,   
    max_depth=10,     
    random_state=42,
    n_jobs=-1
)
rf.fit(X_sample, y_sample)

#---Random Forst als Basis verwenden 
feature_importance_analyse(
    model=rf,
    X_test=X_test_cleaned,
    output_dir=os.path.join(root_dir, "05_plots"),
    filename="shap_plot.png"
)

#--Datensatz nach der Analyse reduzieren
X_train_red, X_test_red, y_train_red, y_test_red = train_test_split(
    df_ml, 
    feature_cols=feature_cols_cleaned, 
    target_col=target_col,
)
#--- Korrelations-Check auf dem reduzierten Set
X_train_final, X_test_final, final_features = correlated_features_drop(
    X_train_red, 
    X_test_red,
    feautre_cols=feature_cols_cleaned
)
#---Modellvergleich um das beste Modell zu finden
comparison = compare_models(X_train_final, X_test_final, y_train_red, y_test_red)
print(comparison)
print("\n--- LightGBM Tuning (Standard) ---")
lgbm_model_std, study_std = tune_lightgbm(
    X_train=X_train_final,
    y_train=y_train,
    X_test=X_test_final,
    y_test=y_test,
    final_features=final_features,
    output_dir=os.path.join(root_dir, "05_plots"),
    n_trials=50,
    log_transform=False
)

print("\n--- LightGBM Tuning (Log-Transformation) ---")
lgbm_model_log, study_log = tune_lightgbm(
    X_train=X_train_final,
    y_train=y_train,
    X_test=X_test_final,
    y_test=y_test,
    final_features=final_features,
    output_dir=os.path.join(root_dir, "05_plots"),
    n_trials=50,
    log_transform=True
)

# --- Bestes Modell auswählen ---
y_pred_std = lgbm_model_std.predict(X_test_final)
y_pred_log = np.expm1(lgbm_model_log.predict(X_test_final))

mae_std = mean_absolute_error(y_test, y_pred_std)
mae_log = mean_absolute_error(y_test, y_pred_log)

print(f"\n📊 Vergleich Standard vs. Log-Transformation:")
print(f"   Standard – MAE: {mae_std:.3f} kWh | R²: {r2_score(y_test, y_pred_std):.3f}")
print(f"   Log      – MAE: {mae_log:.3f} kWh | R²: {r2_score(y_test, y_pred_log):.3f}")

if mae_log < mae_std:
    print("\n✅ Log-Transformation ist besser – verwende log-transformiertes Modell")
    lgbm_model = lgbm_model_log
    y_pred     = y_pred_log
else:
    print("\n✅ Standard ist besser – verwende Standard-Modell")
    lgbm_model = lgbm_model_std
    y_pred     = y_pred_std

# ============================================================
# 12. MODELLANNAHMEN VALIDIEREN
# ============================================================
print("\n--- Modellannahmen Validierung ---")
validate_model_assumptions(
    model=lgbm_model,
    X_test=X_test_final,
    y_test=y_test,
    output_dir=os.path.join(root_dir, "05_plots"),
    log_transform=(mae_log < mae_std) 
)

# ============================================================
# 13. KREUZVALIDIERUNG
# ============================================================
print("\n--- Kreuzvalidierung ---")
tscv = TimeSeriesSplit(n_splits=3)
scores = cross_validate(
    lgbm_model, X_train_final, y_train,
    cv=tscv,
    scoring={"MAE": "neg_mean_absolute_error", "R2": "r2"},
    return_train_score=False
)

for i, (mae, r2) in enumerate(zip(-scores["test_MAE"], scores["test_R2"])):
    print(f"Fold {i+1}: MAE={mae:.3f} kWh | R²={r2:.3f}")

print(f"\nCV MAE:  {-scores['test_MAE'].mean():.3f} ± {scores['test_MAE'].std():.3f} kWh")
print(f"CV R²:   {scores['test_R2'].mean():.3f} ± {scores['test_R2'].std():.3f}")

# ============================================================
# 14. PREDICTION & VISUALISIERUNG
# ============================================================
plot_final_prediction(
    y_test=y_test,
    y_pred=y_pred,
    output_dir=os.path.join(root_dir, "05_plots")
)

plot_business_drivers(
    model=lgbm_model,
    X_sample=X_test_final.sample(2000, random_state=42),
    output_dir=os.path.join(root_dir, "05_plots")
)
