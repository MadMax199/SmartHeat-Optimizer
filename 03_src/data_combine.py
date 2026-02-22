
import polars as pl
import os
import glob

# Angepasste join_data-Funktion
def join_data(base_df, joins: list):
    """
    Führt mehrere Joins sequenziell aus.
    Unterstützt gleiche Spaltennamen (on) oder unterschiedliche (left_on / right_on).
    """
    df = base_df

    for join in joins:
        df = df.join(
            join["df"],
            on=join.get("on"),                  # gleiche Spaltennamen
            left_on=join.get("left_on"),        # linke Spaltennamen, falls unterschiedlich
            right_on=join.get("right_on"),      # rechte Spaltennamen, falls unterschiedlich
            how=join.get("how", "left"),
            coalesce=True
        )

    return df