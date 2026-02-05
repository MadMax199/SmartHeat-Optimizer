
import polars as pl
import os
import glob

def smartmeter_load(data_path: str = None):

    "Lädt alle csv Dateien in ein Dataframe"

    search_pattern = os.path.join(data_path, "[0-9]*.csv")
    
    try:
        # 1. Daten laden (Schema-Inferenz auf 0, um alles als String zu lesen)
        df = pl.read_csv(
            search_pattern,
            separator=";",
            infer_schema_length=0,
            ignore_errors=True
        )

        if df.is_empty():
            print(f"⚠️ Keine Daten unter {search_pattern} gefunden.")
            return pl.DataFrame()

        # 2. Transformationen & Umbenennung gemäß deines ClickHouse-Schemas
        df = df.with_columns([
            # Zeitstempel mit Zeitzonen-Fix (wie im Screenshot DateTime)
            pl.col("Timestamp")
                .str.to_datetime(strict=False, time_zone="UTC")
                .alias("timestamp"),
            
            # IDs und Gruppen (Strings laut deinem Screenshot)
            pl.col("Household_ID").alias("household_id"),
            pl.col("Group").alias("group_assignment"),
            pl.col("AffectsTimePoint").alias("affects_timepoint"),
            
            # Numerische Werte (Float64)
            pl.col("kWh_received_Total").cast(pl.Float64, strict=False).alias("kwh_received_total"),
            pl.col("kWh_received_HeatPump").cast(pl.Float64, strict=False).alias("kwh_received_heatpump"),
            pl.col("kWh_received_Other").cast(pl.Float64, strict=False).alias("kwh_received_other"),
            pl.col("kWh_returned_Total").cast(pl.Float64, strict=False).alias("kwh_returned_total")
        ])

        # 3. Lokale Zeit und Datum für Schweizer Kontext hinzufügen
        df = df.with_columns([
            pl.col("timestamp").dt.convert_time_zone("Europe/Zurich").alias("timestamp_local")
        ]).with_columns([
            pl.col("timestamp_local").dt.date().alias("date")
        ])

        # 4. Auswahl der Spalten in der Reihenfolge deines Schemas
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
        print(f"❌ Fehler: {e}")
        return pl.DataFrame()
    