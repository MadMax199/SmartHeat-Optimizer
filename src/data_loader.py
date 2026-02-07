
import polars as pl
import os
import glob

def smartmeter_load(data_path: str = None):

    "Lädt alle csv Dateien in ein Dataframe"

    search_pattern = os.path.join(data_path, "[0-9]*.csv")
    
    try:

        df = pl.read_csv(
            search_pattern,
            separator=";",
            infer_schema_length=0,
            ignore_errors=True
        )

        if df.is_empty():
            print(f"Keine Daten unter {search_pattern} gefunden.")
            return pl.DataFrame()

        df = df.with_columns([
            pl.col("Timestamp")
                .str.to_datetime(strict=False, time_zone="UTC")
                .alias("timestamp"),
            
            pl.col("Household_ID").alias("household_id"),
            pl.col("Group").alias("group_assignment"),
            pl.col("AffectsTimePoint").alias("affects_timepoint"),
            
            pl.col("kWh_received_Total").cast(pl.Float64, strict=False).alias("kwh_received_total"),
            pl.col("kWh_received_HeatPump").cast(pl.Float64, strict=False).alias("kwh_received_heatpump"),
            pl.col("kWh_received_Other").cast(pl.Float64, strict=False).alias("kwh_received_other"),
            pl.col("kWh_returned_Total").cast(pl.Float64, strict=False).alias("kwh_returned_total")
        ])

        df = df.with_columns([
            pl.col("timestamp").dt.convert_time_zone("Europe/Zurich").alias("timestamp_local")
        ]).with_columns([
            pl.col("timestamp_local").dt.date().alias("date")
        ])

        return df.select([
            "timestamp",
            "timestamp_local",
            "date",
            "household_id",
            "group_assignment",
            "affects_timepoint",
            "kwh_received_total",
            "kwh_received_heatpump",
            "kwh_received_other",
            "kwh_returned_total"
        ])

    except Exception as e:
        print(f"Fehler: {e}")
        return pl.DataFrame()
    
def weather_load(data_path: str = None):
    if data_path is None:
        return pl.DataFrame()

    search_pattern = os.path.join(data_path, "[0-9]*.csv")

    try:
        # 1. Lazy Scan vorbereiten
        df_lazy = (
            pl.scan_csv(
                search_pattern,
                separator=";",
                infer_schema_length=0,
                ignore_errors=True,
                rechunk=True
            )
            .with_columns([
                # Zeitstempel & ID
                pl.col("Weather_ID").alias("weather_id"),
                pl.col("Timestamp")
                    .str.to_datetime(strict=False, time_zone="UTC")
                    .dt.convert_time_zone("Europe/Zurich")
                    .alias("timestamp_local"),
                
                # Alle numerischen Spalten laut deinem ursprünglichen Wunsch
                pl.col("Temperature_max_daily").cast(pl.Float64, strict=False).alias("temperature_max_daily"),
                pl.col("Temperature_min_daily").cast(pl.Float64, strict=False).alias("temperature_min_daily"),
                pl.col("Temperature_avg_daily").cast(pl.Float64, strict=False).alias("temperature_avg_daily"),
                pl.col("HeatingDegree_SIA_daily").cast(pl.Float64, strict=False).alias("heatingdegree_sia_daily"),
                pl.col("HeatingDegree_US_daily").cast(pl.Float64, strict=False).alias("heatingdegree_us_daily"),
                pl.col("CoolingDegree_US_daily").cast(pl.Float64, strict=False).alias("coolingdegree_us_daily"),
                pl.col("Humidity_avg_daily").cast(pl.Float64, strict=False).alias("humidity_avg_daily"),
                pl.col("Precipitation_total_daily").cast(pl.Float64, strict=False).alias("precipitation_total_daily"),
                pl.col("Sunshine_duration_daily").cast(pl.Float64, strict=False).alias("sunshine_duration_daily"),
            ])
            .with_columns([
                # Reines Datum für den Join extrahieren
                pl.col("timestamp_local").dt.date().alias("date")
            ])
        )

        # 2. Ausführung (Eager)
        df = df_lazy.collect()

        if df.is_empty():
            print(f"⚠️ Keine Daten unter {search_pattern} gefunden.")
            return pl.DataFrame()

        # 3. Spalten sortieren für eine saubere Übersicht
        return df.select([
            "date",
            "weather_id",
            "temperature_avg_daily",
            "temperature_max_daily",
            "temperature_min_daily",
            "heatingdegree_sia_daily",
            "heatingdegree_us_daily",
            "coolingdegree_us_daily",
            "humidity_avg_daily",
            "precipitation_total_daily",
            "sunshine_duration_daily",
            "timestamp_local"
        ]).sort(["weather_id", "date"])

    except Exception as e:
        print(f"❌ Fehler beim Laden der Wetterdaten: {e}")
        return pl.DataFrame()
    


def household_load(data_path: str = None):


   search_pattern = os.path.join(data_path, "*.csv")
   
   df = pl.read_csv(
            search_pattern,
            separator=";", 
            infer_schema_length=1000,
            ignore_errors=True
        )
   return df.rename({col: col.lower() for col in df.columns})



def household_metainfo_load(data_path: str = None):
    search_pattern = os.path.join(data_path, "*.csv")
    
    df = pl.read_csv(
        search_pattern,
        separator=";",
        infer_schema_length=1000,
        ignore_errors=True,
        # Tipp: Probiere try_parse_dates=True, das erkennt viele Formate automatisch
        try_parse_dates=True 
    )

    # Spaltennamen direkt am Anfang klein machen, damit die Auswahl einfacher ist
    df = df.rename({col: col.lower() for col in df.columns})

    return df.with_columns([
        pl.col("visit_date").str.to_date(format="%d.%m.%Y", strict=False),
        pl.col("visit_year").cast(pl.String).str.to_date(format="%Y", strict=False)
    ])