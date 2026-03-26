# 📚 Feature Engineering

Diese Dokumentation beschreibt die Vorgehensweise beim Feature Engineering 

## 📋 Feature Erstellung

In der Pipeline werden mehrere Features für die Vorhersage des Energieverbrauchs generiert. Die Beschreibung der einzelnen Features folgt der Reihenfolge im features.py-File.

Wochentage
Auf Basis des Datums werden numerische Werte generiert, die die Wochentage abbilden, wobei Sonntag den Wert 7 und Montag den Wert 1 erhält.
Wochenende
Darauf aufbauend wird ein Wochenend-Indikator erzeugt, der für Samstag und Sonntag den Wert 1 und für Werktage den Wert 0 annimmt.
Heizperiode
Die Heizperiode in Mitteleuropa dauert typischerweise von Oktober bis März. Entsprechend wird ein Dummy-Feature erstellt, das in diesen Monaten den Wert 1 und in den übrigen Monaten den Wert 0 annimmt. 
Renovationsindex
Der Renovationsindex summiert mehrere Dummy-Variablen, die angeben, ob Renovierungen an bestimmten Gebäudeteilen wie Fenstern, Dach oder Wänden durchgeführt wurden.
Heizbedarf
Der Heizbedarf wird aus der beheizten Fläche und der Anzahl der Bewohner eines Gebäudes berechnet.
Preisfeatures
Auf Basis der Day-Ahead-Strompreise werden Lag-Features sowie gleitende Durchschnittswerte für 30 und 90 Tage berechnet. Zusätzlich werden Abweichungen des aktuellen Tagespreises von diesen Durchschnittswerten bestimmt.
Solarpotenzial
Das Solarpotenzial wird durch die Multiplikation der PV-Anlagengröße mit der täglichen Sonnenscheindauer approximiert.
Thermische Dynamik
Um die thermische Trägheit von Gebäuden sowie kurzfristige Temperaturveränderungen abzubilden, werden zwei zusätzliche Temperaturfeatures berechnet: temp_inertia_ema_3d als exponentiell gewichteter gleitender Durchschnitt der Temperatur über drei Tage sowie temp_delta_1d als tägliche Veränderung der Durchschnittstemperatur zum Vortag. Zur besseren Abbildung saisonaler Effekte werden zyklische Transformationen (Sinus und Cosinus) für Monatswerte berechnet.
Gebäudetypen
Für die Gebäudetypen werden Dummy-Variablen mittels One-Hot-Encoding erstellt, wobei die Kategorie „Unbekannt" als Referenzkategorie dient und nicht explizit kodiert wird.

Zusätzlich zu den erzeugten Features werden folgende Variablen direkt aus dem Datensatz verwendet: kwh_received_heatpump, kwh_returned_total, temperature_avg_daily sowie swissix_base.

## 🛠 Feature Selektion, Importance und Validierung

1. Korrelationen der Features 

 **temp_inertia_ema_3d** weist eine hohe Korrelation mit anderen Variablen auf und kann somit als redundant betrachtet werden kann. Auf Grundlage dieser Analyse wurde das Feature aus dem Datensatz entfernt.

Die Identifikation stark korrelierter Features erfolgt mithilfe der  **def correlated_features_drop**, die eine Korrelationsmatrix des Trainingsdatensatzes berechnet und Variablen entfernt, deren Korrelation einen Schwellenwert von **0.90** überschreitet.

2. Importance und Validierung der Features

![alt text](image.png)

Um den Einfluss der Features zu analyiseren wird ein Random Forst mOdell als Basis verwendet, sodass die benötigen plots erzeugt werdne könnne. 
So sieht man anhand des Importnace Plots recht deutlich, die wichgsten Features: 1. temperature_avg_daily, 2. kwh_returned_total, 3. temp_delta_1d

Alle weiteren Features haben nur einen geringen Einfluss auf den Stromvebrauch.

![alt text](image-1.png)

Der Beeswarm-Plot ergänzt die globale Wichtigkeit um die Richtung und Stärke der Effekte. Beim Feature temperature_avg_daily zeigt sich ein deutliches Muster: Niedrige Temperaturen (blaue Punkte) führen zu stark positiven SHAP-Werten – die Kälte erhöht den Verbrauch erwartungsgemäß massiv.

Für den heating_amount wird ersichtlich, dass der Gesamtverbrauch bei hohen Werten (rote Punkte) tendenziell steigt. Da die meisten Punkte jedoch auf der vertikalen Null-Linie liegen, hat das Feature für den Großteil der Daten keinen Einfluss auf die Vorhersage. Dies ist auf die identifizierten der Missing-Werte zurückzuführen, wodurch das Feature in seiner aktuellen Form für das Modell kaum Informationsgehalt bietet.

Features die einen kleinen aber erwartebaren Effekt haben sind folgede:
kwh_received_heatpump – kleiner aber plausibler Effekt, behalten
price_lag_30d & price_relative_to_month – Preissignale mit minimalem Effekt, können bleiben wenn inhaltlich relevant
month_sin & month_cos – zyklische Monatskodierung, sinnvoll aber schwacher Effekt
is_heating_season – stark mit Temperatur korreliert, möglicherweise redundant

Auf Basis der Importance Analyse werden folgende Feature entfernt: 
heating_amount: Featee nicht sinnvoll intepretierbat
Dummys für Haustypen: SHAP = 0 -> Kein Beitrag
solar_thermal_potential: Keine Varianz im Beeswarm, grau = kein Effekt
is_weekend: Minimaler Effekt, kaum relevant
renovation_score: Fast kein Einfluss
is_heating_seaso: Redundant zu temperature_avg_daily

