

import polars as pl
import os

def smartmeter_load(data_path: str = None):
    "Lädt alle csv Dateien in ein Dataframe"
    if data_path is None: return pl.DataFrame()
    search_pattern = os.path.join(data_path, "[0-9]*.csv")
    
    try:
        df = pl.read_csv(
            search_pattern,
            separator=";",
            infer_schema_length=0, # Alles als String lesen für maximale Sicherheit
            ignore_errors=True
        )

        if df.is_empty():
            print(f"Keine Daten unter {search_pattern} gefunden.")
            return pl.DataFrame()

        # Transformationen
        df = df.with_columns([
            pl.col("Timestamp")
                .str.to_datetime(strict=False, time_zone="UTC")
                .alias("timestamp"),
            
            # ID direkt als String sicherstellen
            pl.col("Household_ID").cast(pl.String).alias("household_id"),
            
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
            "timestamp", "timestamp_local", "date", "household_id",
            "group_assignment", "affects_timepoint", "kwh_received_total",
            "kwh_received_heatpump", "kwh_received_other", "kwh_returned_total"
        ])

    except Exception as e:
        print(f"Fehler Smartmeter: {e}")
        return pl.DataFrame()
    
def weather_load(data_path: str = None):
    if data_path is None: return pl.DataFrame()
    search_pattern = os.path.join(data_path, "[0-9]*.csv")

    try:
        df_lazy = (
            pl.scan_csv(
                search_pattern,
                separator=";",
                infer_schema_length=0,
                ignore_errors=True,
                rechunk=True
            )
            .with_columns([
                # ID direkt als String sicherstellen
                pl.col("Weather_ID").cast(pl.String).alias("weather_id"),
                
                pl.col("Timestamp")
                    .str.to_datetime(strict=False, time_zone="UTC")
                    .dt.convert_time_zone("Europe/Zurich")
                    .alias("timestamp_local"),
                
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
                pl.col("timestamp_local").dt.date().alias("date")
            ])
        )

        df = df_lazy.collect()
        if df.is_empty(): return pl.DataFrame()

        return df.select([
            "date", "weather_id", "temperature_avg_daily", "temperature_max_daily",
            "temperature_min_daily", "heatingdegree_sia_daily", "heatingdegree_us_daily",
            "coolingdegree_us_daily", "humidity_avg_daily", "precipitation_total_daily",
            "sunshine_duration_daily", "timestamp_local"
        ]).sort(["weather_id", "date"])

    except Exception as e:
        print(f"❌ Fehler Wetterdaten: {e}")
        return pl.DataFrame()
    
def household_load(data_path: str = None):
    if data_path is None: return pl.DataFrame()
    search_pattern = os.path.join(data_path, "*.csv")
    
    df = pl.read_csv(
            search_pattern,
            separator=";", 
            infer_schema_length=1000,
            ignore_errors=True
        )
    
    # Spalten klein machen
    df = df.rename({col: col.lower() for col in df.columns})
    
    # ID & Wetter_ID zu String casten für Join-Kompatibilität
    return df.with_columns([
        pl.col("household_id").cast(pl.String),
        pl.col("weather_id").cast(pl.String)
    ])

def house_info_load(data_path: str = None):
    if data_path is None: return pl.DataFrame()
    search_pattern = os.path.join(data_path, "*.csv")
    
    df = pl.read_csv(
        search_pattern,
        separator=";",
        infer_schema_length=1000,
        ignore_errors=True,
        try_parse_dates=True 
    )

    df = df.rename({col: col.lower() for col in df.columns})

    return df.with_columns([
        # ID zu String casten
        pl.col("household_id").cast(pl.String),
        pl.col("visit_date").str.to_date(format="%d.%m.%Y", strict=False),
        pl.col("visit_year").cast(pl.String).str.to_date(format="%Y", strict=False)
    ])


def processed_data_load(file_path: str):
    """
    Lädt den bereits kombinierten und bereinigten Datensatz aus dem processed-Ordner.
    """
    try:
        # Wir nutzen infer_schema_length=10000, damit Polars die 
        # Datentypen (Float, Int, String) nach dem Join wieder korrekt erkennt.
        df = pl.read_csv(
            file_path,
            separator=";",
            infer_schema_length=10000,
            ignore_errors=True
        )
        
        print(f"✅ Processed Data geladen: {df.shape[0]} Zeilen, {df.shape[1]} Spalten.")
        return df

    except Exception as e:
        print(f"❌ Fehler beim Laden der Processed Data: {e}")
        return pl.DataFrame()