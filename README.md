
# SmartHeat-Optimizer  
**HEAPO – HeatPump Insights 🌡️⚡**

Der SmartHeat-Optimizer ist eine strukturierte Datenpipeline zur **Analyse realer Wärmepumpen-Feldstudiendaten**.  
Das Projekt integriert Smart-Meter-Messungen, Gebäudeeigenschaften, Anlageninformationen und externe Datenquellen, um Effizienz, Betriebsverhalten und Optimierungspotenziale datengetrieben zu untersuchen.

Der Aufbau orientiert sich am **CRISP-DM-Prozess** und trennt klar zwischen Business-Verständnis, Datenaufbereitung, Engineering und Analyse.

---

## 🎯 Projektziele

- Zusammenführung heterogener Energie- und Gebäudedaten  
- Reproduzierbare Datenpipelines statt manueller Notebook-Logik  
- Skalierbare Verarbeitung großer Zeitreihen  
- Bereitstellung analysefertiger Features  
- Transparente explorative Auswertung

---

## 🧭 Projektstruktur

```text
SmartHeat-Optimizer/
├── 01_business_understanding/
│   ├── project_charter.md
│   └── success_criteria.md
│
├── 02_data/
│   ├── raw/                # Unveränderte Originaldaten
│   ├── processed/          # Pipeline-Output
│   └── temp/               # Zwischenergebnisse
│
├── 03_src/
│   ├── __init__.py
│   ├── app.py              # Startpunkt der Datenpipeline
│   ├── data_loader.py      # Einlesen & Typisierung
│   ├── data_combine.py     # Join- & Integrationslogik
│   ├── data_scrap.py       # Ergänzende Datenquellen / Scraping
│   ├── features.py         # Feature Engineering
│   └── utils.py            # Hilfsfunktionen
│
├── 04_notebooks/
│   ├── explorative_analyse_univariat.ipynb
│   └── explorative_analyse_bivariat.ipynb
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
