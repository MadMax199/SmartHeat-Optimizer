# 📚 HEAPO – Datensatz-Dokumentation (Zenodo 15056919)

Diese Dokumentation beschreibt den **HEAPO-Datensatz** (*An Open Dataset for Heat Pump Optimization*). Er bildet die wissenschaftliche Grundlage für dieses Projekt und wurde von Brudermüller et al. (2025) veröffentlicht.

## 📋 Kurz-Steckbrief

| Merkmal | Details |
| :--- | :--- |
| **Titel** | HEAPO – An Open Dataset for Heat Pump Optimization |
| **DOI** | [10.5281/zenodo.15056919](https://doi.org/10.5281/zenodo.15056919) |
| **Autoren** | Brudermüller, T., et al. |
| **Region** | Schweiz (Kanton Zürich) |
| **Zeitraum** | 2018 – 2024 |
| **Stichprobe** | 1.408 Haushalte mit Wärmepumpen |
| **Lizenz** | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

## 🔍 Datensatz-Architektur

Der Datensatz ist relational aufgebaut. Die Verknüpfung der einzelnen CSV-Dateien erfolgt primär über die `household_id`.



### 1. Energie-Zeitreihen (Smart Meter)
* **Auflösung:** 15-Minuten-Intervalle.
* **Inhalt:** Messung der Wirkleistung (kWh) und Blindleistung (kvarh).
* **Differenzierung:** Separate Messung für die Wärmepumpe (`HeatPump`) und den restlichen Haushalt (`Other`).

### 2. Vor-Ort-Audit-Protokolle
* **Inhalt:** Experten-Checks von über 400 Anlagen.
* **Details:** Technische Parameter (COP, Leistung), Gebäudezustand (Dämmung, Fläche) und Steuerungs-Einstellungen (Heizkurve, Heizgrenze).

### 3. Meteorologische Daten
* **Quelle:** Daten von 8 regionalen Wetterstationen.
* **Metriken:** Außentemperatur (Min/Max/Schnitt), Luftfeuchtigkeit, Sonnenscheindauer und Heizgradtage (SIA).



## 🛠 Technische Spezifikationen

* **Format:** Semikolon-separierte CSV-Dateien.
* **Encoding:** UTF-8.
* **Datentypen:** IDs als Strings, Messwerte als Floats, Zeitstempel in UTC (müssen für die Analyse oft in Lokalzeit konvertiert werden).

## 💡 Zielsetzung des Datensatzes

Der HEAPO-Datensatz wurde entwickelt, um folgende Forschungsfragen zu beantworten:
1. **Effizienz-Monitoring:** Wie verhalten sich reale Wärmepumpen im Vergleich zu Laborwerten?
2. **Fehlersuche:** Erkennung ineffizienter Betriebszustände (z.B. Takten, Heizstab-Einsatz).
3. **Optimierung:** Quantifizierung von Energieeinsparungen durch manuelle Anpassung der Reglereinstellungen.

---
