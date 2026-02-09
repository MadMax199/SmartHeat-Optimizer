
import os
import pandas as pd
import polars as pl
from pathlib import Path
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

# =============================
# KONFIGURATION & API SETUP
# =============================
# Lädt die Variablen aus der .env Datei
load_dotenv()

API_KEY = os.getenv("ENTSOE_API_KEY")
if not API_KEY:
    raise ValueError("❌ API_KEY nicht gefunden! Hast du die .env Datei erstellt?")

client = EntsoePandasClient(api_key=API_KEY)

# Parameter
COUNTRY_CODE = "CH"
START_TIME = pd.Timestamp("2018-01-01", tz="Europe/Brussels")
END_TIME = pd.Timestamp("2024-03-21", tz="Europe/Brussels")

# =============================
# DATEN DOWNLOAD (BATCH-MODUS)
# =============================
all_prices = []
current_start = START_TIME

print(f"🚀 Starte Download der Day-Ahead Preise für {COUNTRY_CODE}")

while current_start < END_TIME:
    # ENTSO-E Abfragen funktionieren oft besser in kleineren Häppchen (z.B. 1 Jahr)
    current_end = min(current_start + pd.DateOffset(years=1), END_TIME)
    
    print(f"  → Lade Zeitraum: {current_start.date()} bis {current_end.date()}")
    
    try:
        s = client.query_day_ahead_prices(
            COUNTRY_CODE,
            start=current_start,
            end=current_end,
        )

        if isinstance(s, pd.Series) and not s.empty:
            all_prices.append(s)
        else:
            print("    ⚠️ Keine Daten für diesen Zeitraum erhalten.")

    except Exception as e:
        print(f"    ❌ Fehler beim Download: {e}")

    current_start = current_end

# =============================
# DATENVERARBEITUNG (POLARS)
# =============================
if not all_prices:
    raise ValueError("❌ Es wurden überhaupt keine Daten geladen. Skript abgebrochen.")

# 1. Pandas Series zusammenführen & Duplikate entfernen (an den Jahresgrenzen)
combined_prices = pd.concat(all_prices).sort_index()
combined_prices = combined_prices[~combined_prices.index.duplicated(keep='first')]

# 2. Von Pandas zu Polars konvertieren
df_pd = combined_prices.reset_index()
df_pd.columns = ["timestamp", "price_eur_mwh"]
df = pl.from_pandas(df_pd)

# 3. Baseload berechnen (Tagesmittelwert)
# Wir extrahieren das Datum und gruppieren danach
df_daily = (
    df.with_columns(pl.col("timestamp").dt.date().alias("date"))
    .group_by("date")
    .agg(pl.col("price_eur_mwh").mean().alias("swissix_base"))
    .sort("date")
)

# =============================
# SPEICHERN
# =============================
output_path = Path("data/raw/prices/swissix_prices_ch.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

df_daily.write_csv(output_path)

print("-" * 30)
print(f"✅ Download abgeschlossen!")
print(f"📊 Datensätze gesamt: {len(df_daily)}")
print(f"💾 Datei gespeichert unter: {output_path}")
print(df_daily.head())