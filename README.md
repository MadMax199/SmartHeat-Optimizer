# SmartHeat-Optimizer
HEAPO: HeatPump-Insights 🌡️⚡

Dieses Projekt dient der Analyse und Optimierung von Wärmepumpensystemen basierend auf realen Feldstudiendaten. Es kombiniert Smart-Meter-Daten, Gebäude-Metainformationen und Wetterdaten, um die Effizienz von Heizungssystemen (COP) zu bewerten und Optimierungspotenziale aufzuzeigen.

📂 Projektstruktur
Plaintext

SmartHeat-Optimizer/
├── data/
│   ├── raw/                # Unverarbeitete Originaldaten (CSV)
│   │   ├── households/     # Smart-Meter Zeitreihen
│   │   ├── households_info/# Stammdaten der Haushalte
│   │   ├── weather/        # Historische Wetterdaten
│   │   └── protocols/      # Vor-Ort-Besuchsprotokolle
│   └── processed/          # Kombinierter & bereinigter Datensatz
├── src/
│   ├── app.py              # Hauptanwendung / Einstiegspunkt
│   ├── data_loader.py      # Funktionen zum Einlesen der CSV-Dateien
│   ├── data_combine.py     # Logik für Joins und Datensatz-Merge
│   └── analysis.ipynb      # Jupyter Notebook für Exploration & Plots
└── README.md
📊 Datensatz-Referenz
Dieses Projekt nutzt den "Heat pumps field study dataset", der im Rahmen einer umfassenden Feldstudie in der Schweiz erhoben wurde. Der Datensatz ist öffentlich zugänglich und bietet eine einzigartige Grundlage für die energetische Forschung.

Original-Quelle: Heat pumps field study dataset (Zenodo)

Herausgeber: Fachhochschule Nordwestschweiz (FHNW) / EnergieSchweiz

Inhalt: Hochaufgelöste Lastgänge von über 100 Wärmepumpen, detaillierte Anlagenkonfigurationen und anonymisierte Gebäudedaten.

🚀 Installation & Nutzung
Umgebung einrichten:

Bash

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install polars matplotlib seaborn
Daten verarbeiten: Führe die app.py aus, um die Rohdaten aus den verschiedenen Quellen zu laden, die Datentypen zu vereinheitlichen und einen kombinierten Datensatz zu erstellen:

Bash

python src/app.py
Analyse: Nutze das Jupyter Notebook in src/, um die Verteilungen der Gebäudemerkmale und die Effizienz der Wärmepumpen zu visualisieren.

🛠 Hauptfunktionen
Robuster Daten-Loader: Automatisches Casting von IDs (String) und Zeitstempeln (DateTime), um konsistente Joins zu gewährleisten.

Polars-Powered: Nutzung der Polars-Library für extrem schnelle Datenverarbeitung auch bei großen Zeitreihen (> 900.000 Zeilen).

Automatisierte Visualisierung: Skripte zur Generierung von Histogrammen und Balkendiagrammen für über 40 Gebäudemetriken.