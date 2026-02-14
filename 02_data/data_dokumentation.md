
# Datenwörterbuch: Smart-Meter Zeitreihen (households)

Dieses Dokument beschreibt die Struktur und den Inhalt der Smart-Meter-Rohdaten aus dem Ordner `data/raw/households/`. Die Daten liegen im CSV-Format vor und verwenden ein Semikolon (`;`) als Trennzeichen.

## 📊 Spaltenübersicht

| Spalte | Datentyp | Beschreibung | Einheit |
| :--- | :--- | :--- | :--- |
| **Household_ID** | `String` | Eindeutige Identifikationsnummer des Haushalts. Primärschlüssel für den Join mit Metadaten. | ID |
| **Group** | `String` | Gruppenzuordnung innerhalb der Feldstudie (z.B. Test- oder Kontrollgruppe). | Kategorie |
| **AffectsTimePoint** | `String` | Interner Indikator für spezifische Mess- oder Interventionszeitpunkte. | - |
| **Timestamp** | `Datetime` | Zeitstempel der Messung (ISO-Format). Standardmäßig in UTC. | Zeit |
| **kWh_received_Total** | `Float64` | Gesamter elektrischer Wirkleistungsbezug des Haushalts vom Stromnetz. | kWh |
| **kWh_received_HeatPump** | `Float64` | **Kernmetrik:** Elektrischer Energieverbrauch der Wärmepumpe. | kWh |
| **kWh_received_Other** | `Float64` | Restverbrauch des Haushalts (Licht, Geräte, etc.) ohne Wärmepumpe. | kWh |
| **kWh_returned_Total** | `Float64` | Einspeisung ins Netz (relevant bei vorhandener PV-Anlage). | kWh |
| **kvarh_received_capacitive_Total** | `Float64` | Kapazitive Blindleistung (Gesamtbezug). | kvarh |
| **kvarh_received_capacitive_HeatPump**| `Float64` | Kapazitive Blindleistung (Wärmepumpe). | kvarh |
| **kvarh_received_capacitive_Other** | `Float64` | Kapazitive Blindleistung (Restlicher Haushalt). | kvarh |
| **kvarh_received_inductive_Total** | `Float64` | Induktive Blindleistung (Gesamtbezug). | kvarh |
| **kvarh_received_inductive_HeatPump** | `Float64` | Induktive Blindleistung (Wärmepumpe). | kvarh |
| **kvarh_received_inductive_Other** | `Float64` | Induktive Blindleistung (Restlicher Haushalt). | kvarh |

## 💡 Analyse-Hinweise

1. **Wirkleistung vs. Blindleistung:** Für die Berechnung der Jahresarbeitszahl (JAZ) oder des COP-Werts solltest du ausschließlich die `kWh`-Werte verwenden.
2. **Daten-Aggregation:** Da die Daten oft in 15-Minuten-Intervallen vorliegen, empfiehlt sich eine Aggregation auf Stunden- oder Tagesbasis für Vergleiche mit Wetterdaten.
3. **Berechnungskontrolle:** Es gilt in der Regel: 
   `kWh_received_Total` = `kWh_received_HeatPump` + `kWh_received_Other`.


# Datenwörterbuch: Haushalts-Metadaten (households_info)

Dieses Dokument beschreibt die Stammdaten der Haushalte aus dem Ordner `data/raw/households_info/`. Diese Tabelle fungiert als zentrales Bindeglied zwischen den Verbrauchsdaten, den Wetterstationen und den Audit-Protokollen.

## 📊 Spaltenübersicht

| Spalte | Datentyp | Beschreibung | Einheit / Format |
| :--- | :--- | :--- | :--- |
| **Household_ID** | `String` | Eindeutige Identifikationsnummer des Haushalts. Primärschlüssel für alle Joins. | ID |
| **Group** | `String` | Zugehörigkeit zur Studiengruppe (z. B. "Optimized", "Control"). | Kategorie |
| **Weather_ID** | `String` | Fremdschlüssel zur Verknüpfung mit den Wetterdaten (`weather_load`). | ID |
| **Installation_HasPVSystem** | `Boolean` | Gibt an, ob im Haushalt eine Photovoltaik-Anlage installiert ist. | True/False |
| **Protocols_Available** | `Boolean` | Zeigt an, ob Vor-Ort-Besuchsprotokolle für diesen Haushalt existieren. | True/False |
| **Protocols_HasMultipleVisits** | `Boolean` | True, wenn der Haushalt mehrfach vom Techniker besucht wurde. | True/False |
| **Protocols_ReportIDs** | `String` | Liste der IDs der zugehörigen Audit-Berichte (kommagetrennt). | Liste (ID) |
| **MetaData_Available** | `Boolean` | Statusanzeige, ob detaillierte Gebäude-Metadaten vorliegen. | True/False |
| **SmartMeterData_Available_15min** | `Boolean` | Hochaufgelöste Lastgänge im 15-Minuten-Takt vorhanden. |
| **SmartMeterData_Available_Daily** | `Boolean` | Aggregierte Tagesverbrauchswerte vorhanden. |
| **SmartMeterData_Available_Monthly** | `Boolean` | Aggregierte Monatsverbrauchswerte vorhanden. |

---

## 💡 Analyse-Hinweise

1. **Join-Logik:** Die `Weather_ID` sollte genutzt werden, um die Wetterdaten an die Verbrauchsdaten zu hängen. Nutze in Polars einen `left_join`, um keine Haushalte zu verlieren, für die eventuell keine Wetterstation gemappt ist.
2. **Filterung:** Bevor du mit Zeitreihen-Analysen startest, solltest du nach `SmartMeterData_Available_15min == True` filtern, falls du Lastkurven berechnen willst.
3. **PV-Einfluss:** Bei Haushalten mit `Installation_HasPVSystem == True` ist bei der Analyse von `kwh_received_total` Vorsicht geboten, da ein Teil des Eigenverbrauchs nicht über den Netzbezugszähler läuft (sofern nicht separat gemessen).
---

# Datenwörterbuch: Markt- & Preisdaten (API)

Dieses Dokument beschreibt die über die API bezogenen Zeitreihen. Diese Daten dienen als externe Referenz, um beispielsweise die Wirtschaftlichkeit der Wärmepumpen im Kontext von Marktpreisen zu bewerten.

## 📊 Spaltenübersicht

| Spalte | Datentyp | Beschreibung | Einheit |
| :--- | :--- | :--- | :--- |
| **date** | `Date` | Das Datum der Preisnotierung. | JJJJ-MM-TT |
| **swissix_base** | `Float64` | Der **Swiss Electricity Index (Swissix)** Base-Preis. Repräsentiert den Durchschnittspreis für Grundlaststrom in der Schweiz am Spotmarkt. | EUR/MWh oder CHF/MWh |

## 💡 Analyse-Hinweise

1. **Preis-Korrelation:** Du kannst diese Daten nutzen, um zu prüfen, ob die Wärmepumpen in deinem Datensatz antizyklisch zum Marktpreis laufen (z. B. Lastverschiebung in günstige Stunden).
2. **Währungs-Check:** Prüfe, ob die API die Werte in Euro oder Schweizer Franken liefert, um sie korrekt mit den (meist in CHF berechneten) Netzkosten der Haushalte zu vergleichen.
3. **Aggregation:** Da die anderen Daten (`households`) oft in 15-Minuten-Schritten vorliegen, musst du den `swissix_base` Wert (oft ein Tageswert) für die Analyse auf die kleineren Zeitstempel "broadcasten" (vervielfältigen).

# Datenwörterbuch: Vor-Ort-Protokolle (protocols)

Dieses Dokument beschreibt die technischen Parameter und Experten-Einschätzungen, die während der Feldstudie bei Hausbesuchen erhoben wurden.

## 📂 Metadaten & Gebäudestruktur
| Spalte | Beschreibung |
| :--- | :--- |
| **Report_ID** | Eindeutige Kennung des Audit-Berichts. |
| **Household_ID** | Verknüpfungsschlüssel zum Haushalt. |
| **Visit_Year / Visit_Date** | Jahr und exaktes Datum des Technikerbesuchs. |
| **Building_Type** | Gebäudetyp (z.B. Einfamilienhaus, Mehrfamilienhaus). |
| **Building_HousingUnits** | Anzahl der Wohneinheiten im Gebäude. |
| **Building_ConstructionYear** | Baujahr des Gebäudes (exakt oder als Intervall). |
| **Building_Renovated_...** | Sanierungsstatus (Windows, Roof, Walls, Floor) als Boolean. |
| **Building_FloorAreaHeated_...**| Beheizte Flächenanteile nach Stockwerken (Total, Basement, GroundFloor, etc.). |
| **Building_Residents** | Anzahl der im Haushalt lebenden Personen. |
| **Building_PVSystem_...** | Vorhandensein und Größe (kWp) der Photovoltaik-Anlage. |
| **Building_ElectricVehicle_...**| Vorhandensein eines Elektroautos. |

## ⚙️ Wärmepumpen-Konfiguration
| Spalte | Beschreibung |
| :--- | :--- |
| **HeatPump_Installation_Type** | Quelle/Medium (z.B. Luft/Wasser, Sole/Wasser). |
| **Manufacturer / Model** | Hersteller und Modellbezeichnung. |
| **HeatingCapacity** | Thermische Nennleistung in kW. |
| **Refrigerant_...** | Kältemitteltyp und Füllmenge. |
| **Normpoint_...** | Leistungsdaten (COP, ElectricPower, HeatingPower) am Normpunkt. |
| **InternetConnection** | Verfügbarkeit eines Internetzugangs für die WP. |

## 🚿 Warmwasser (DHW - Domestic Hot Water)
| Spalte | Beschreibung |
| :--- | :--- |
| **DHW_Production_By...** | Erzeugungstyp (Wärmepumpe, Solar, Elektro-Einsatz). |
| **DHW_TemperatureSetting_...**| Soll-Temperatur des Warmwassers (Before/After Visit). |
| **DHW_Circulation_...** | Details zur Zirkulationspumpe (Timer, Dauerlauf, TraceHeating). |

## 📈 Optimierungsparameter (Heizkurve)
| Spalte | Beschreibung |
| :--- | :--- |
| **HeatingCurveSetting_...** | Vorlauftemperaturen bei +20°C, 0°C und -8°C Außentemperatur. |
| **HeatingLimitSetting_...** | Außentemperatur, ab der die Heizung abschaltet (Heizgrenze). |
| **NightSetbackSetting_...** | Status der Nachtabsenkung (Before/After Visit). |

## 🛠 Technischer Zustand & Empfehlungen
| Spalte | Beschreibung |
| :--- | :--- |
| **HeatPump_BasicFunctionsOkay**| Wurden grundlegende Mängel festgestellt? |
| **AirSource_... / GroundSource_...**| Spezifische Checks für Luft- oder Erdsonden-WPs. |
| **Recommendation_...** | Empfehlungen (Rohre isolieren, Ventile installieren, etc.). |

# Datenwörterbuch: Wetterdaten (weather)

Dieses Dokument beschreibt die meteorologischen Zeitreihen, die zur Kontextualisierung des Energieverbrauchs der Wärmepumpen genutzt werden. Die Daten liegen als tägliche Aggregationswerte vor.

## 📊 Spaltenübersicht

| Spalte | Datentyp | Beschreibung | Einheit |
| :--- | :--- | :--- | :--- |
| **Weather_ID** | `String` | Eindeutige Kennung der Wetterstation. Verknüpfungsschlüssel zu den Haushalts-Metadaten. | ID |
| **Timestamp** | `Datetime` | Datum des Messtages (Aggregation auf 24h). | Zeit |
| **Temperature_max_daily** | `Float64` | Maximale gemessene Außentemperatur des Tages. | °C |
| **Temperature_min_daily** | `Float64` | Minimale gemessene Außentemperatur des Tages. | °C |
| **Temperature_avg_daily** | `Float64` | **Kernmetrik:** Durchschnittliche Außentemperatur (24h-Mittel). | °C |
| **HeatingDegree_SIA_daily**| `Float64` | Heizgradtage nach Schweizer Norm (SIA 381/3). Basis: 12°C Heizgrenze / 20°C Raumziel. | K·d |
| **HeatingDegree_US_daily** | `Float64` | Heizgradtage nach US-Standard (Basis: 65°F). | K·d |
| **CoolingDegree_US_daily** | `Float64` | Kühlgradtage (relevant für Reversible WPs im Sommerbetrieb). | K·d |
| **Humidity_avg_daily** | `Float64` | Durchschnittliche relative Luftfeuchtigkeit. | % |
| **Precipitation_total_daily**| `Float64` | Gesamte Niederschlagsmenge des Tages (Regen/Schnee). | mm |
| **Sunshine_duration_daily** | `Float64` | Tatsächliche Sonnenscheindauer pro Tag. | Minuten |

---

## 💡 Analyse-Hinweise für die Wärmepumpen-Forschung

### 1. Heizgradtage (HDD) & Heizlast
Die Metrik `HeatingDegree_SIA_daily` erlaubt es, den Energieverbrauch witterungsbereinigt zu vergleichen. Ein hoher Wert korreliert direkt mit einer hohen thermischen Last des Gebäudes.

### 2. Korrelation: Temperatur vs. COP
Bei Luft/Wasser-Wärmepumpen sinkt die Effizienz (COP) mit abnehmender `Temperature_avg_daily`. Du kannst diese Daten nutzen, um zu prüfen, ab welcher Außentemperatur die Wärmepumpen in deinem Datensatz ineffizient werden oder den Elektro-Heizstab zuschalten.

### 3. Luftfeuchtigkeit & Abtauzyklen
Hohe Werte bei `Humidity_avg_daily` kombiniert mit Temperaturen knapp über dem Gefrierpunkt (0°C bis 5°C) führen oft zu einer schnelleren Vereisung des Verdampfers. Dies erzwingt Abtauzyklen, die im Smart-Meter-Lastgang als kurze, intensive Verbrauchsspitzen sichtbar werden können.

### 4. Solarer Einfluss
Die `Sunshine_duration_daily` erklärt oft Abweichungen in der Heizkurve: An sonnigen Tagen reduziert sich die Heizlast durch passive solare Gewinne (Fensterflächen), was trotz niedriger Außentemperaturen zu einem geringeren Verbrauch führen kann.