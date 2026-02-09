from entsoe import EntsoePandasClient
import pandas as pd
import polars as pl

client = EntsoeRawClient(api_key=<YOUR API KEY>)

<<<<<<< Updated upstream
start = pd.Timestamp('20181103', tz='Europe/Zurich')
end = pd.Timestamp('20240321', tz='Europe/Brussels')
country_code = 'CH'

try:
    print(f"Lade Day-Ahead Preise für {country_code}...")

    # Diese Methode gibt eine saubere Zeitreihe (Pandas Series) zurück
    # Intern nutzt sie 'query_day_ahead_prices'
    prices_series = client.query_day_ahead_prices(country_code, start=start, end=end)

    # 2. Umwandlung in Polars
    # Wir machen aus der Pandas Series ein DataFrame
    df_pd = prices_series.reset_index()
    df_pd.columns = ["timestamp", "price_eur_mwh"]
    
    # In Polars DataFrame konvertieren
    df = pl.from_pandas(df_pd)

    # 3. Baseload (Tagesdurchschnitt) berechnen
    # Das ist das Äquivalent zu dem, was du bei EPEX Spot als "Baseload" siehst
    df_daily = df.group_by(pl.col("timestamp").dt.date()).agg(
        pl.col("price_eur_mwh").mean().alias("swissix_base")
    ).sort("timestamp")

    print(df_daily)

    # 4. Speichern
    df_daily.write_csv("raw\prices\swissix_prices_ch.csv")
    print("\nDatei 'swissix_prices_ch.csv' wurde erstellt.")

except Exception as e:
    print(f"Fehler: {e}")
=======
# =============================
# API KEY
# =============================
API_KEY = "65129fd6-82f2-4f86-9dff-75f77b71689e"

client = EntsoePandasClient(api_key=API_KEY)


# =============================
# PARAMETER
# =============================
country_code = "CH"

start = pd.Timestamp("2018-01-01", tz="Europe/Brussels")
end = pd.Timestamp("2024-03-21", tz="Europe/Brussels")


# =============================
# DOWNLOAD
# =============================
print(f"Lade Day-Ahead Preise für {country_code}")

prices = client.query_day_ahead_prices(
    country_code,
    start=start,
    end=end,
)

print(type(prices))
print(prices.head())


# =============================
# PANDAS → POLARS
# =============================
df_pd = prices.reset_index()
df_pd.columns = ["timestamp", "price_eur_mwh"]

df = pl.from_pandas(df_pd)


# =============================
# BASELOAD (TAGESMITTEL)
# =============================
df_daily = (
    df.group_by(pl.col("timestamp").dt.date())
    .agg(pl.col("price_eur_mwh").mean().alias("swissix_base"))
    .sort("timestamp")
)

print(df_daily.head())


# =============================
# SPEICHERN
# =============================
output = Path("data/raw/prices/swissix_prices_ch.csv")
output.parent.mkdir(parents=True, exist_ok=True)

df_daily.write_csv(output)

print(f"\nDatei gespeichert unter: {output}")
>>>>>>> Stashed changes
