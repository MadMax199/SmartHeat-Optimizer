
# 📑 HEAPO Projektdokumentation: Datenwörterbücher

Diese Dokumentation dient als zentrale Referenz für den **HEAPO-Datensatz** (An Open Dataset for Heat Pump Optimization). Sie beschreibt die Struktur und Analysepotenziale der integrierten Datenquellen (Smart-Meter, Audits, Wetter).

---

## 1. Smart-Meter Zeitreihen (`households`)

**Quelle:** 15-Minuten-Lastprofile (Wirkleistung) und tägliche Summenwerte (Wirk- und Blindleistung) in UTC.

| Spalte | Datentyp | Beschreibung | Einheit |
| :--- | :--- | :--- | :--- |
| **Household_ID** | `String` | Primärschlüssel zur Verknüpfung mit Metadaten. | ID |
| **Group** | `String` | `Treatment` (Audit durchgeführt) oder `Control` (nur Messdaten). | Kategorie |
| **AffectsTimePoint** | `String` | Zeitbezug zum Audit: `before`, `during`, `after` oder `unknown`. | - |
| **Timestamp** | `Datetime` | UTC-Zeitstempel der Messung. | Zeit |
| **kWh_received_Total** | `Float64` | Gesamter Wirkleistungsbezug vom Netz (OBIS 1.8.0). | kWh |
| **kWh_received_HeatPump**| `Float64` | **Kernmetrik:** Elektrischer Verbrauch der Wärmepumpe. | kWh |
| **kWh_received_Other** | `Float64` | Restverbrauch des Haushalts ohne Wärmepumpe. | kWh |
| **kWh_returned_Total** | `Float64` | Netz-Einspeisung (nur bei PV-Anlagen, tägliche Auflösung). | kWh |
| **kvarh_received_...** | `Float64` | Blindleistung (kapazitiv/induktiv) für Netzanalysen. | kvarh |

### 💡 Analyse-Hinweise
* **Verlustfreie Summierung:** In der Regel gilt `Total = HeatPump + Other`. Fehlende Intervall-Daten werden durch kumulative Zählerstände bei der nächsten Ablesung korrigiert.
* **Eigenverbrauch:** `kWh_returned_Total` erfasst **nicht** den direkt selbst verbrauchten PV-Strom, sondern nur den Überschuss, der ins Netz zurückgespeist wird.

---

## 2. Haushalts-Metadaten (`households_info`)

Zentrales Mapping-File zur Verknüpfung der Teildatensätze.

| Spalte | Datentyp | Beschreibung |
| :--- | :--- | :--- |
| **Household_ID** | `String` | Eindeutige Identifikation des Haushalts. |
| **Weather_ID** | `String` | Mapping zur nächstgelegenen Wetterstation (per Haversine-Distanz). |
| **Installation_HasPVSystem** | `Boolean` | Vorhandensein einer Photovoltaik-Anlage. |
| **Protocols_Available** | `Boolean` | Kennzeichnet Haushalte der **Treatment-Gruppe**. |
| **Protocols_ReportIDs** | `String` | Verweis auf die zugehörigen Audit-Berichte (kommagetrennt). |
| **SmartMeterData_Available_...**| `Boolean` | Verfügbarkeit in 15-min, täglicher oder monatlicher Auflösung. |

---

## 3. Vor-Ort-Protokolle (`protocols`)

Technische "Ground-Truth"-Daten aus 410 Experten-Audits von Fachberatern.

### 🏠 Gebäude & Bewohner
* **Building_Type / ConstructionYear:** Struktur und Alter des Gebäudes.
* **Building_Renovated_...:** Sanierungsstatus (Fenster, Dach, Fassade, Boden).
* **Building_FloorAreaHeated_Total:** Beheizte Fläche (m²) – Basis für die Heizlastberechnung.
* **Building_Residents:** Anzahl der Bewohner (Einfluss auf den Warmwasserbedarf).

### ⚙️ Wärmepumpen-Technik & Optimierung
* **HeatPump_Installation_Type:** z.B. Luft/Wasser (ASHP) oder Sole/Wasser (GSHP).
* **HeatingCapacity / Normpoint_COP:** Thermische Nennleistung und Effizienz laut Datenblatt.
* **HeatingCurveSetting_...:** Vorlauftemperaturen bei +20°C, 0°C und -8°C (jeweils **Before** und **After** Visit).
* **DHW_TemperatureSetting_...:** Warmwasser-Soll-Temperatur (Potenzial für Effizienzsteigerung).



---

## 4. Wetterdaten (`weather`)

Meteorologische Zeitreihen zur Witterungsbereinigung des Verbrauchs.

| Spalte | Datentyp | Beschreibung | Einheit |
| :--- | :--- | :--- | :--- |
| **Temperature_avg_daily** | `Float64` | Tagesmitteltemperatur (MeteoSchweiz). | °C |
| **HeatingDegree_SIA_daily**| `Float64` | Heizgradtage nach Schweizer Norm (SIA 381/3). | K·d |
| **Humidity_avg_daily** | `Float64` | Durchschnittliche relative Luftfeuchtigkeit. | % |
| **Sunshine_duration_daily** | `Float64` | Tatsächliche Sonnenscheindauer pro Tag. | Minuten |

### 💡 Analyse-Hinweise
* **Heizgradtage (SIA):** Berechnung basierend auf der 12°C Heizgrenze und 20°C Raumzieltemperatur.
  $$HDD_{SIA} = \begin{cases} 20^\circ C - T_{avg} & \text{wenn } T_{avg} \leq 12^\circ C \\ 0 & \text{sonst} \end{cases}$$
* **Abtauzyklen:** Bei Luft/Wasser-Wärmepumpen führen hohe Luftfeuchtigkeit und Temperaturen um 0°C zu Vereisung. Dies zeigt sich im 15-Minuten-Profil oft als kurze, intensive Verbrauchsspitze.



---

## 5. Markt- & Preisdaten (API)

| Spalte | Datentyp | Beschreibung |
| :--- | :--- | :--- |
| **date** | `Date` | Datum der Preisnotierung. |
| **swissix_base** | `Float64` | Swiss Electricity Index (Spotmarktpreis für Grundlast). |

### 💡 Analyse-Hinweise
* **Wirtschaftlichkeit:** Ermöglicht die Simulation von variablen Tarifen und die Analyse des Sparpotenzials durch Lastverschiebung (Demand Side Management).