# HEAPO – Stromverbrauchsvorhersage ⚡🌡️

**Datenbasis:** Dieses Projekt nutzt den HEAPO-Datensatz (Zenodo 15056919).  
Brudermüller, T., et al. (2025). HEAPO – An Open Dataset for Heat Pump Optimization.

Dieses Repo beinhaltet eine strukturierte Datenpipeline zur **tagesbasierten Vorhersage 
des Stromverbrauchs von Schweizer Haushalten**. Das Projekt integriert 
Smart-Meter-Messungen, Gebäudeeigenschaften, Vor-Ort-Audit-Protokolle, Wetterdaten 
und Strompreise, um auf Basis von Machine-Learning-Methoden präzise Verbrauchsprognosen 
für Energieversorger zu erstellen.

Der Aufbau orientiert sich am **CRISP-DM-Prozess** und trennt klar zwischen 
Business-Verständnis, Datenaufbereitung, Feature Engineering, Modellierung und Evaluation.

---

## 🎯 Forschungsfrage

Inwiefern lässt sich der tägliche Stromverbrauch von Schweizer Haushalten im Kontext 
der Elektrifizierung des Wärmesektors unter Einfluss von Wetterbedingungen, 
Gebäudeeigenschaften und Strompreissignalen mithilfe von Machine-Learning-Methoden 
zuverlässig vorhersagen?

---

## 💼 Business-Kontext

Energieversorger tragen ein erhebliches finanzielles Risiko, wenn sie den Strombedarf 
ihrer Kunden am Großhandelsmarkt zu ungenau prognostizieren. Haushalte mit Wärmepumpen 
verursachen stark wetterabhängige und saisonal schwankende Lasten. Ungenaue Day-Ahead-
Prognosen führen zu Über- oder Unterbeschaffung, teuren Ausgleichsenergien und 
erschwerter Netzplanung. Das Modell adressiert diese Problematik durch:

- **Reduktion von Beschaffungs- und Ausgleichskosten** durch präzisere Day-Ahead-Prognosen
- **Entlastung des Verteilnetzes** durch frühzeitige Erkennung von Lastspitzen
- **Grundlage für Flexibilitätsprodukte** wie dynamische Tarife und steuerbare Wärmepumpen

---

## 🏆 Ergebnisse

| Metrik | Wert |
|---|---|
| Modell | LightGBM (log-transformiert, Optuna-getuned) |
| MAE (Test) | 11.39 kWh |
| R² (Test) | 0.316 |
| CV MAE (Ø) | 12.79 kWh |
| CV R² (Ø) | 0.302 |

**Top-3 Features:** `temperature_avg_daily`, `kwh_returned_total`, `temp_delta_1d`

---

## 🧭 Projektziele

- Zusammenführung heterogener Energie-, Gebäude- und Wetterdaten
- Einbindung von Strompreisdaten zur Erfassung von Preisschockeffekten
- SHAP-basierte Feature-Importance-Analyse und Selektion
- Hyperparameter-Optimierung via Optuna (50 Trials, TimeSeriesSplit)
- Reproduzierbare Datenpipelines statt manueller Notebook-Logik
- Transparente Modellvalidierung und Evaluation

---

## 🗂 Projektstruktur
```text
HEAPO-ConsumptionPredict/
├── 01_business_understanding/
│   ├── project_charter.md          # CRISP-DM Prozessübersicht
│   ├── problemstellung.md          # Business-Problemstellung
│   ├── datenqualitätsbericht.md    # Datensatz-Dokumentation
│   └── success_criteria.md         # Erfolgskriterien je Phase
│
├── 02_data/
│   ├── raw/                        # Unveränderte Originaldaten
│   ├── processed/                  # Pipeline-Output (Parquet)
│   └── temp/                       # Zwischenergebnisse (CSV)
│
├── 03_src/
│   ├── __init__.py
│   ├── app.py                      # Startpunkt der Datenpipeline
│   ├── config.py                   # Zentrale Konfiguration & Feature-Listen
│   ├── data_cleaner.py             # Imputation & Typkonvertierung
│   ├── data_loader.py              # Einlesen & Typisierung
│   ├── data_combine.py             # Join- & Integrationslogik
│   ├── data_scrap.py               # Strompreisdaten (SwissIX API)
│   ├── data_validation.py          # Schema-Validierung via Pandera
│   ├── features.py                 # Feature Engineering
│   └── utilis.py                   # ML-Funktionen (Tuning, Plots, Evaluation)
│
├── 04_notebooks/
│   ├── explorative_analyse_univariat.ipynb
│   └── explorative_analyse_bivariat.ipynb
│
├── 05_plots/                       # Gespeicherte Plots & Modelle
│   ├── shap_plot_bar.png
│   ├── shap_plot_beeswarm.png
│   ├── lgbm_learning_curve_log.png
│   ├── model_validation.png
│   ├── final_prediction.png
│   ├── business_drivers.png
│   └── lgbm_final_model_log.pkl
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 Datenpipeline

Die Pipeline verarbeitet vier heterogene Datenquellen:

| Quelle | Inhalt | Verknüpfung |
|---|---|---|
| Smart Meter (`households`) | 15-min & tägliche kWh-Messwerte | `household_id` |
| Metadaten (`households_info`) | Gebäudetyp, PV, EV, Bewohner | `household_id` |
| Audit-Protokolle (`protocols`) | Technische WP-Parameter, Renovierungsstatus | `household_id` |
| Wetterdaten (`weather`) | Temperatur, Heizgradtage, Sonnenschein | `weather_id` + `date` |
| Strompreise (`prices`) | SwissIX Day-Ahead-Preis | `date` |

---

## ⚙️ Installation
```bash
# Repository klonen
git clone https://github.com/dein-repo/HEAPO-ConsumptionPredict

# Virtuelle Umgebung erstellen
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Mac/Linux

# Abhängigkeiten installieren
pip install -r requirements.txt

# Pipeline starten
python 03_src/app.py
```

---

## 📦 Wichtigste Abhängigkeiten

| Paket | Verwendung |
|---|---|
| `polars` | Schnelle Datenverarbeitung großer Zeitreihen |
| `pandera` | Schema-basierte Datenvalidierung |
| `lightgbm` | Finales Vorhersagemodell |
| `optuna` | Bayesianische Hyperparameter-Optimierung |
| `shap` | Modellinterpretierbarkeit & Feature-Importance |
| `scikit-learn` | ML-Utilities, Metriken, Kreuzvalidierung |
| `selenium` | Scraping der SwissIX-Strompreisdaten |

---

## 📖 Lizenz

Dieses Projekt wurde im Rahmen einer Seminararbeit erstellt.  
Datensatz: HEAPO (Zenodo 15056919, CC BY 4.0) – Brudermüller et al. (2025).
