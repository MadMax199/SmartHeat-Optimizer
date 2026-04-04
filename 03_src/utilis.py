
import polars as pl
import numpy as np
import os
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor 
from sklearn.metrics import mean_absolute_error, r2_score
import time
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import time
import shap
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from lightgbm import LGBMRegressor
import lightgbm as lgb
import optuna
import joblib
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_validate



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


def compare_models(X_train, X_test, y_train, y_test, label: str = ""):
    sample_size = min(len(X_train), 5000)
    print(f"--- Benchmark gestartet (Sample-Größe: {sample_size}) ---")
    indices = np.random.choice(len(X_train), sample_size, replace=False)
    X_train_sub = X_train.iloc[indices]
    y_train_sub = y_train.iloc[indices] if hasattr(y_train, "iloc") else y_train[indices]

    median_vals = X_train_sub.median()
    X_train_sub = X_train_sub.fillna(median_vals)
    X_test_clean = X_test.fillna(median_vals)

    models = {
        "Ridge (Linear)": Ridge(),
        "XGBoost (Fast)": XGBRegressor(
            n_estimators=100, tree_method="hist", n_jobs=-1, random_state=42
        ),
        "LightGBM": LGBMRegressor(                  # NEU
            n_estimators=100, n_jobs=-1, random_state=42, verbose=-1
        ),
        "RandomForest (Limited)": RandomForestRegressor(
            n_estimators=50, max_depth=12, n_jobs=-1, random_state=42
        )
    }

    results = []
    for name, model in models.items():
        print(f"  -> Teste {name}...", end=" ", flush=True)
        t0 = time.time()
        try:
            model.fit(X_train_sub, y_train_sub)
            t1 = time.time()
            preds = model.predict(X_test_clean)
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

def validate_model_assumptions(model, X_test, y_test, output_dir, log_transform=False):
    
    """
    Validiert die Modellannahmen eines trainierten Regressionsmodells.
    Erstellt drei Plots: Residuen vs. Vorhersage, Residuen-Verteilung, Actual vs. Predicted.
    """
    y_pred_raw = model.predict(X_test)
    y_pred     = np.expm1(y_pred_raw) if log_transform else y_pred_raw
    residuals  = y_test - y_pred

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # --- Plot 1: Residuen vs. Vorhersage ---
    axes[0].scatter(y_pred, residuals, alpha=0.3, color="steelblue", s=10)
    axes[0].axhline(0, color="red", linestyle="--")
    axes[0].set_title("Residuen vs. Vorhersage")
    axes[0].set_xlabel("Vorhergesagter Verbrauch (kWh)")
    axes[0].set_ylabel("Residuum (kWh)")

    # --- Plot 2: Residuen-Verteilung ---
    axes[1].hist(residuals, bins=50, color="steelblue", edgecolor="white")
    axes[1].axvline(0, color="red", linestyle="--")
    axes[1].set_title("Verteilung der Residuen")
    axes[1].set_xlabel("Residuum (kWh)")
    axes[1].set_ylabel("Häufigkeit")

    # --- Plot 3: Actual vs. Predicted ---
    axes[2].scatter(y_test, y_pred, alpha=0.3, color="steelblue", s=10)
    axes[2].plot([y_test.min(), y_test.max()],
                 [y_test.min(), y_test.max()],
                 color="red", linestyle="--")
    axes[2].set_title("Actual vs. Predicted")
    axes[2].set_xlabel("Tatsächlicher Verbrauch (kWh)")
    axes[2].set_ylabel("Vorhergesagter Verbrauch (kWh)")

    plt.suptitle("Modellannahmen-Validierung", fontsize=14)
    plt.tight_layout()

    path = os.path.join(output_dir, "model_validation.png")
    plt.savefig(path)
    plt.close()

    print(f"   Mean Residuum:      {residuals.mean():.3f} kWh  (sollte ~0 sein)")
    print(f"   Std Residuum:       {residuals.std():.3f} kWh")
    print(f"   Max Unterschätzung: {residuals.max():.3f} kWh")
    print(f"   Max Überschätzung:  {residuals.min():.3f} kWh")
    print(f"📊 Validierungsplot gespeichert: {path}")

    return residuals

def evaluate_with_cv(model, X_train, y_train, n_splits=5):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = cross_validate(
        model, X_train, y_train,
        cv=tscv,
        scoring={"MAE": "neg_mean_absolute_error", "R2": "r2"},
        return_train_score=True
    )
    print(f"CV MAE:  {-scores['test_MAE'].mean():.3f} ± {scores['test_MAE'].std():.3f} kWh")
    print(f"CV R²:   {scores['test_R2'].mean():.3f} ± {scores['test_R2'].std():.3f}")
    return scores

def tune_lightgbm(
    X_train, y_train, X_test, y_test,
    final_features,
    output_dir,
    n_trials=50,
    n_splits=5,
    log_transform=False        # ← neu
):
    tscv = TimeSeriesSplit(n_splits=n_splits)

    # --- LOG-TRANSFORMATION ---
    y_train_fit = np.log1p(y_train) if log_transform else y_train

    # --- OPTUNA OBJECTIVE ---
    def objective(trial):
        params = {
            "objective": "regression",
            "metric": "mae",
            "verbosity": -1,
            "boosting_type": "gbdt",
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 20, 150),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 100),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 1.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 1.0, log=True),
        }

        mae_scores = []
        for train_idx, val_idx in tscv.split(X_train):
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr = y_train_fit[train_idx]
            y_val_orig = y_train[val_idx]  # original für MAE-Berechnung

            model = lgb.LGBMRegressor(**params)
            model.fit(
                X_tr, y_tr,
                eval_set=[(X_val, np.log1p(y_val_orig) if log_transform else y_val_orig)],
                callbacks=[lgb.early_stopping(50, verbose=False),
                           lgb.log_evaluation(period=-1)]
            )
            preds = model.predict(X_val)
            # Immer auf originaler Skala evaluieren
            preds_orig = np.expm1(preds) if log_transform else preds
            mae_scores.append(mean_absolute_error(y_val_orig, preds_orig))

        return np.mean(mae_scores)

    # --- TUNING ---
    print("🔍 Starte Optuna Tuning...")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"✅ Bestes MAE (CV): {study.best_value:.3f} kWh")
    print(f"✅ Beste Parameter: {study.best_params}")

    # --- FINALES MODELL ---
    best_params = {
        "objective": "regression",
        "metric": "mae",
        "verbosity": -1,
        **study.best_params
    }

    final_model = lgb.LGBMRegressor(**best_params)

    # Lernkurven-Daten sammeln
    evals_result = {}
    X_tr_final  = X_train.iloc[:int(len(X_train)*0.8)]
    X_val_final = X_train.iloc[int(len(X_train)*0.8):]
    y_tr_final  = y_train_fit[:int(len(y_train_fit)*0.8)]
    y_val_final = y_train_fit[int(len(y_train_fit)*0.8):]

    final_model.fit(
        X_tr_final, y_tr_final,
        eval_set=[(X_tr_final, y_tr_final), (X_val_final, y_val_final)],
        eval_names=["train", "val"],
        callbacks=[
            lgb.record_evaluation(evals_result),
            lgb.early_stopping(50, verbose=False),
            lgb.log_evaluation(period=-1)
        ]
    )

    # --- LERNKURVEN PLOT ---
    suffix = "log" if log_transform else "std"
    ylabel = "MAE (log kWh)" if log_transform else "MAE (kWh)"

    plt.figure(figsize=(10, 5))
    plt.plot(evals_result["train"]["l1"], label="Train MAE", color="steelblue")
    plt.plot(evals_result["val"]["l1"], label="Val MAE", color="tomato")
    plt.axvline(x=final_model.best_iteration_, color="gray", linestyle="--", label="Best Iteration")
    plt.xlabel("Iteration")
    plt.ylabel(ylabel)
    plt.title(f"LightGBM Lernkurven ({suffix})")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"lgbm_learning_curve_{suffix}.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"📊 Lernkurven gespeichert: {plot_path}")

    # --- TEST EVALUATION (immer auf originaler Skala) ---
    y_pred_raw = final_model.predict(X_test)
    y_pred     = np.expm1(y_pred_raw) if log_transform else y_pred_raw

    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)
    print(f"\n📈 Test-Ergebnisse:")
    print(f"   MAE:  {mae:.3f} kWh")
    print(f"   R²:   {r2:.3f}")

    # --- MODELL SPEICHERN ---
    model_path = os.path.join(output_dir, f"lgbm_final_model_{suffix}.pkl")
    joblib.dump(final_model, model_path)
    print(f"💾 Modell gespeichert: {model_path}")

    return final_model, study


def plot_final_prediction(y_test, y_pred, output_dir, n_days=30, filename="final_prediction.png"):
    plt.figure(figsize=(14, 6))
    plt.plot(range(n_days), y_test[:n_days], label='Realität (Smart Meter)', color='#1f77b4', linewidth=2, marker='o')
    plt.plot(range(n_days), y_pred[:n_days], label='KI-Vorhersage (LightGBM)', color='#ff7f0e', linestyle='--', linewidth=2, marker='x')
    
    mae = mean_absolute_error(y_test[:n_days], y_pred[:n_days])
    r2  = r2_score(y_test[:n_days], y_pred[:n_days])
    
    plt.title(f"Modell-Präzision über {n_days} Tage | MAE: {mae:.2f} kWh | R²: {r2:.3f}", fontsize=14)
    plt.xlabel("Tage im Testzeitraum", fontsize=12)
    plt.ylabel("Verbrauch (kWh)", fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    path = os.path.join(output_dir, filename)
    plt.savefig(path)
    plt.close()
    print(f"📊 Prediction Plot gespeichert: {path}")


def plot_business_drivers(model, X_sample, output_dir, filename="business_drivers.png"):
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
    
    plt.title("Business-Treiber: Welche Faktoren beeinflussen den Verbrauch?", fontsize=14)
    plt.xlabel("Durchschnittlicher Einfluss auf die Vorhersage (kWh)", fontsize=12)
    plt.tight_layout()
    
    path = os.path.join(output_dir, filename)
    plt.savefig(path)
    plt.close()
    print(f"📊 Business Drivers Plot gespeichert: {path}")
