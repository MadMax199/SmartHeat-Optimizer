# SmartHeat-Optimizer  
**HEAPO: HeatPump-Insights 🌡️⚡**

Dieses Projekt unterstützt die **Analyse und Optimierung von Wärmepumpensystemen** auf Basis realer Feldstudiendaten. Es vereint Smart-Meter-Zeitreihen, Gebäude-Metainformationen und Wetterdaten, um die Effizienz von Heizsystemen (z. B. COP) zu bewerten und systematische Optimierungspotenziale sichtbar zu machen.

Ziel ist es, aus heterogenen Rohdaten einen konsistenten, auswertbaren Datensatz zu erzeugen und darauf aufbauend reproduzierbare Analysen zu ermöglichen.

---

## 📂 Projektstruktur

```text
SmartHeat-Optimizer/
├── data/
│   ├── raw/                  # Unverarbeitete Originaldaten (CSV)
│   │   ├── households/       # Smart-Meter Zeitreihen
│   │   ├── households_info/  # Stammdaten der Haushalte
│   │   ├── weather/          # Historische Wetterdaten
│   │   └── protocols/        # Vor-Ort-Besuchsprotokolle
│   └── processed/            # Kombinierte & bereinigte Datensätze
├── src/
│   ├── app.py                # Hauptanwendung / Pipeline-Einstieg
│   ├── data_loader.py        # Einlesen & Typisierung der CSV-Dateien
│   ├── data_combine.py       # Join- & Merge-Logik
│   └── analysis.ipynb        # Exploration & Visualisierung
└── README.md
