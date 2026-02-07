
import polars as pl
import os
import glob

import polars as pl

def check_missing_values(df: pl.DataFrame):
    """
    Gibt eine Übersicht der fehlenden Werte (nulls) pro Spalte zurück.
    """
    missing_report = df.select([
        pl.all().null_count().name.suffix("_nulls"),
        (pl.all().null_count() / df.height * 100).name.suffix("_percent")
    ])
    
    # Für eine bessere Lesbarkeit im Notebook transponieren wir das Ergebnis
    return missing_report