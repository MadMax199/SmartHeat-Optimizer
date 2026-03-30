
import polars as pl
import numpy as np

def add_weekdays(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.col('date').dt.weekday().alias("weekday"))

def add_weekend(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.when(pl.col("weekday").is_in([6, 7])).then(1).otherwise(0).alias("is_weekend")
    )


def add_heatpump(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.when(pl.col("group") == "treatment") 
        .then(1)
        .otherwise(0)
        .cast(pl.Int8)
        .alias("is_heatpump")
    )


def add_pv(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("installation_haspvsystem").cast(pl.Int8).alias("is_pv")
    )

def heating_season(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("date").dt.month().is_in([10, 11, 12, 1, 2, 3])
        .cast(pl.Int8)
        .alias("is_heating_season")
    )

def renovation_index(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        (
            pl.col('building_renovated_windows').cast(pl.Int8).fill_null(0) +
            pl.col('building_renovated_roof').cast(pl.Int8).fill_null(0) +
            pl.col('building_renovated_walls').cast(pl.Int8).fill_null(0) +
            pl.col('building_renovated_floor').cast(pl.Int8).fill_null(0)
        ).alias('renovation_score')
    )

def heating_amount(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        (pl.col('building_floorareaheated_total') * pl.col('building_residents')).alias('heating_amount')
    )



def add_price_features(df: pl.DataFrame) -> pl.DataFrame:
   
    
    df = df.sort(["household_id", "date"]).with_columns([
        pl.col("swissix_base").shift(30).over("household_id").alias("price_lag_30d"),
        pl.col("swissix_base").shift(90).over("household_id").alias("price_lag_90d"),
        pl.col("swissix_base").rolling_mean(window_size=30).over("household_id").alias("price_rolling_mean_30d"),
        pl.col("swissix_base").rolling_mean(window_size=90).over("household_id").alias("price_rolling_mean_90d"),
        (pl.col("swissix_base") / (
            pl.col("swissix_base").rolling_mean(window_size=30).over("household_id") + 1e-6
        )).alias("price_relative_to_month")
    ])

    for col in ["price_lag_30d", "price_lag_90d", "price_rolling_mean_30d",
                "price_rolling_mean_90d", "price_relative_to_month"]:
        global_median = df[col].median()
        df = df.with_columns(
            pl.col(col)
            .forward_fill()
            .backward_fill()
            .over("household_id")
        ).with_columns(
            pl.col(col).fill_null(global_median)
        )

    return df


def solar_potentials(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        (pl.col('sunshine_duration_daily') * pl.col('building_pvsystem_size')).alias('solar_thermal_potential')
    )


def add_thermal_dynamics(df: pl.DataFrame) -> pl.DataFrame:
    """Berechnet das thermische Gedächtnis und Temperatur-Trends."""
    return df.sort(["household_id", "date"]).with_columns([
        pl.col("temperature_avg_daily").ewm_mean(span=3).over("household_id").alias("temp_inertia_ema_3d"),
        pl.col("temperature_avg_daily").diff().over("household_id").fill_null(0).alias("temp_delta_1d")
    ])

def add_cyclic_features(df: pl.DataFrame) -> pl.DataFrame:
    """Zyklische Transformation für Monate und Wochentage."""
    return df.with_columns([
        (pl.col("date").dt.month().map_elements(lambda m: np.sin(2 * np.pi * m / 12), return_dtype=pl.Float64)).alias("month_sin"),
        (pl.col("date").dt.month().map_elements(lambda m: np.cos(2 * np.pi * m / 12), return_dtype=pl.Float64)).alias("month_cos"),
    ])



def add_building_type_dummies(df: pl.DataFrame, reference: str = "Unbekannt") -> pl.DataFrame:
    """
    Erstellt One-Hot-Dummies fuer building_type.
    Die Referenzkategorie (default: "Unbekannt") wird weggelassen.
    Spalten werden als "building_type_<wert>" benannt.
    Die originale building_type Spalte wird entfernt.
    """
    categories = [
        v for v in df["building_type"].unique().to_list()
        if v is not None and v != reference
    ]
    dummies = [
        (pl.col("building_type") == cat)
        .cast(pl.Int8)
        .alias(f"building_type_{cat.lower().replace(' ', '_')}")
        for cat in sorted(categories)
    ]
    return df.with_columns(dummies).drop("building_type")