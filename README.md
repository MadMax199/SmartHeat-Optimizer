# SmartHeat-Optimizer  
**HEAPO: HeatPump-Insights 🌡️⚡**

Der SmartHeat-Optimizer ist eine Pipeline zur **Analyse realer Wärmepumpen-Feldstudiendaten**.  
Das Projekt integriert Smart-Meter-Zeitreihen, Gebäudemetadaten, Anlageninformationen und Wetterdaten, um Leistungskennzahlen wie Effizienz und Betriebsmuster systematisch auszuwerten.

Ziel ist es, reproduzierbare Datenprozesse bereitzustellen – von Rohdaten bis zu analysefertigen Features.

---

## 🎯 Projektziele

- Vereinheitlichung heterogener Datenquellen  
- Robuste & nachvollziehbare Join-Strategien  
- Schnelle Verarbeitung großer Zeitreihen  
- Bereitstellung einer Basis für statistische Analysen & ML  
- Transparente Exploration über Notebooks

---

## 📂 Projektstruktur

```text
SmartHeat-Optimizer/
├── 01_business_understanding/        # Kontext, Notizen, Projektverständnis
├── data/
│   ├── raw/                          # Originaldaten (CSV, unverändert)
│   └── processed/                    # Bereinigte & gemergte Daten
├── notebooks/
│   ├── explorative_analyse_univariat.ipynb
│   └── explorative_analyse_bivariat.ipynb
├── src/
│   ├── __init__.py
│   ├── app.py                        # Einstiegspunkt der Pipeline
│   ├── data_loader.py                # Laden & Typisieren der Rohdaten
│   ├── data_combine.py               # Merge- und Integrationslogik
│   ├── data_scrap.py                 # Aufbereitung zusätzlicher Infos
│   ├── features.py                   # Feature Engineering
│   └── utils.py                      # Hilfsfunktionen
├── .env
├── .gitignore
├── requirements.txt
└── README.md
