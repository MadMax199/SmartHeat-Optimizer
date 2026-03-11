
import polars as pl
import numpy as np
import os
import glob
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor 
from sklearn.metrics import mean_absolute_error, r2_score
import time
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
import time
import shap
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

def check_missing_values(df: pl.DataFrame):
    """
    Gibt eine Übersicht der fehlenden Werte (nulls) pro Spalte zurück.
    """
    missing_report = df.select([
        pl.all().null_count().name.suffix("_nulls"),
        (pl.all().null_count() / df.height * 100).name.suffix("_percent")
    ])
    
    # Für eine bessere Lesbarkeit im Notebook transponieren wir das Ergebnis
    return missing_report

def train_test_split(df: pl.DataFrame, feature_cols, target_col):

     """
    Führt den Train Testsplit für die Tagesdaten aus
    """
     df_ml = df.sort("date")

     split_idx = int(len(df_ml) * 0.8)

     X = df_ml.select(feature_cols).to_pandas()
     y = df_ml.select(target_col).to_pandas().values.ravel()

     X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
     y_train, y_test = y[:split_idx], y[split_idx:]

     return X_train, X_test, y_train, y_test

def correlated_features_drop(X_train: pl.DataFrame,X_test: pl.DataFrame,feautre_cols):
     
    """
    Checkt ob die X Varibalen im Traingsdatensatz miteinader korreliert sind
    """

    corr_matrix = X_train.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    to_drop = [column for column in upper.columns if any(upper[column] > 0.90)]

    final_features = [f for f in feautre_cols if f not in to_drop]

    print(f"Entfernte redundante Features: {to_drop}")
    print(f"Verbleibende Features ({len(final_features)}): {final_features}")

    return X_train[final_features], X_test[final_features], final_features

def feature_importance_analyse(model, X_test, output_dir= "../05_plots",filename="test.png"):
    """
    Berechnet SHAP-Werte für ein Sample der Testdaten und speichert den Bar-Plot 
    im Verzeichnis '05_plots'.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Ordner wurde neu erstellt: {output_dir}")

    # 2. Den Pfad sicher zusammenbauen (verhindert Probleme mit Slashes)
    full_path = os.path.join(output_dir, filename)

    # 3. SHAP Analyse (dein bestehender Code)
    explainer = shap.TreeExplainer(model)
    X_sample = X_test.sample(min(500, len(X_test)), random_state=42)
    shap_values = explainer.shap_values(X_sample)
    
    if isinstance(shap_values, list): 
        shap_values = shap_values[0]

    # --- PLOT 1: Global Importance (Bar) ---
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
    plt.title("Globale Feature Importance (Bar)")
    path_bar = os.path.join(output_dir, f"{filename}_bar.png")
    plt.savefig(path_bar, dpi=300, bbox_inches='tight')
    plt.close()

    # --- PLOT 2: Feature Einflüsse (Beeswarm) ---
    plt.figure(figsize=(12, 8))
    # Ohne plot_type="bar" erstellt SHAP automatisch den Beeswarm-Plot
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.title("Feature Einfluss Analyse (Beeswarm)")
    path_bee = os.path.join(output_dir, f"{filename}_beeswarm.png")
    plt.savefig(path_bee, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Beide Plots wurden in {output_dir} gespeichert.")


def compare_models(X_train, X_test, y_train, y_test):
    # Stichprobengröße festlegen
    sample_size = min(len(X_train), 5000)
    print(f"--- Benchmark gestartet (Sample-Größe: {sample_size}) ---")
    
    # Zufällige Indizes ziehen
    indices = np.random.choice(len(X_train), sample_size, replace=False)
    
    # Sicherer Zugriff auf X (Pandas)
    X_train_sub = X_train.iloc[indices]
    
    # Sicherer Zugriff auf y (Numpy oder Pandas)
    if hasattr(y_train, "iloc"):
        y_train_sub = y_train.iloc[indices]
    else:
        y_train_sub = y_train[indices]

    models = {
        "Ridge (Linear)": Ridge(),
        "XGBoost (Fast)": XGBRegressor(
            n_estimators=100, 
            tree_method="hist", 
            n_jobs=-1,
            random_state=42
        ),
        "RandomForest (Limited)": RandomForestRegressor(
            n_estimators=50, 
            max_depth=12,
            n_jobs=-1, 
            random_state=42
        )
    }
    
    results = []
    for name, model in models.items():
        print(f"  -> Teste {name}...", end=" ", flush=True)
        t0 = time.time()
        
        try:
            model.fit(X_train_sub, y_train_sub)
            t1 = time.time()
            
            preds = model.predict(X_test)
            results.append({
                "Model": name,
                "MAE_kWh": round(mean_absolute_error(y_test, preds), 3),
                "R2_Score": round(r2_score(y_test, preds), 3),
                "Duration_sec": round(t1 - t0, 2)
            })
            print(f"Fertig ({results[-1]['Duration_sec']}s)")
        except Exception as e:
            print(f"FEHLER bei {name}: {e}")
            
    return pd.DataFrame(results).sort_values("MAE_kWh")



def tune_random_forest(X_train, y_train):
    print("--- Starte Hyperparameter-Tuning (RandomizedSearch) ---")
    
    param_dist = {
        'n_estimators': [50, 100, 200],
        'max_depth': [10, 15, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None]
    }
    
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    # cv=3 reicht bei Zeitreihen oft aus, um eine Tendenz zu sehen
    random_search = RandomizedSearchCV(
        estimator=rf, 
        param_distributions=param_dist, 
        n_iter=15, 
        cv=3, 
        scoring='neg_mean_absolute_error',
        verbose=1,
        random_state=42,
        n_jobs=-1
    )
    
    random_search.fit(X_train, y_train)
    
    print(f"Beste Parameter: {random_search.best_params_}")
    return random_search.best_estimator_


def plot_final_prediction(y_test, y_pred, n_days=30):
    plt.figure(figsize=(14, 6))
    # Wir plotten einen Ausschnitt von 30 Tagen (Tagesbasis)
    plt.plot(range(n_days), y_test[:n_days], label='Realität (Smart Meter)', color='#1f77b4', linewidth=2, marker='o')
    plt.plot(range(n_days), y_pred[:n_days], label='KI-Vorhersage', color='#ff7f0e', linestyle='--', linewidth=2, marker='x')
    
    plt.title(f"Modell-Präzision über {n_days} Tage", fontsize=16)
    plt.xlabel("Tage im Testzeitraum", fontsize=12)
    plt.ylabel("Verbrauch (kWh)", fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_business_drivers(model, X_sample):
    plt.figure(figsize=(10, 8))
    # SHAP Summary Plot als Bar-Chart (Magnitude)
    shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
    
    plt.title("Business-Treiber: Welche Faktoren beeinflussen den Heizverbrauch?", fontsize=14)
    plt.xlabel("Durchschnittlicher Einfluss auf die Vorhersage (kWh)", fontsize=12)
    plt.tight_layout()
    plt.show()
