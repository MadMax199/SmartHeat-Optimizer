import polars as pl
import polars.selectors as cs


#Strategie zur Behandlung von Missing Values (Übersicht)
#1. Strategie: Auffüllen mit False (Boolean) Wird verwendet, wenn das Fehlen eines Eintrags logisch als "nicht vorhanden" interpretiert werden kann.
#installation_haspvsystem, building_renovated_...,heatpump_installation_internetconnection

def fill_false(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    """
    Die ursprüngliche, einfache Version: 
    Casted direkt zu Boolean und füllt Nullwerte mit False.
    """
    return df.with_columns(
        pl.col(cols).cast(pl.Boolean).fill_null(False)
    )


#2. Strategie: Auffüllen mit 0 (Null)
#building_floorareaheated_basement / _topfloor / _secondfloor: - Stockwer existiert nicht
#building_floorareaheated_additionalareasplannedsize keine geplante erweiterung vorahnden
#kwh_returned_total - überschuss war einfach null

def fill_null(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).fill_null(0))


#3. Strategie: Auffüllen mit dem Median (Statistik)
#Wird für wichtige physikalische Gebäudemerkmale genutzt, um Verzerrungen durch Ausreißer zu minimieren.
#Hierzu zählen building_constructionyear und building_residents

def fill_median(df: pl.DataFrame, cols: list[str], group_by_col: str = None) -> pl.DataFrame:
    for c in cols:
        if group_by_col:
            df = df.with_columns(
                pl.col(c).fill_null(pl.col(c).median().over(group_by_col))
            )
        df = df.with_columns(
            pl.col(c).fill_null(pl.col(c).median())
        )
    return df



#4. Strategie: Interpolation & Carry-Over (Zeitlich/Logisch)
#Wird verwendet, um Kontinuität in Zeitreihen oder Experten-Einstellungen zu wahren.


def apply_interpolation(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    for c in cols:
        df = df.sort(["household_id", "timestamp_local"]).with_columns(
            pl.col(c)
            .interpolate()
            .forward_fill()
            .backward_fill()
            .over("household_id")
        )
        global_median = df[c].median()
        df = df.with_columns(
            pl.col(c).fill_null(global_median)
        )
    return df

#5. Stratgie: Wenn 'aftervisit' null ist, nimm 'beforevisit

def apply_carry_over(df: pl.DataFrame, target_col: str, source_col: str) -> pl.DataFrame:

    return df.with_columns(
        pl.coalesce([pl.col(target_col), pl.col(source_col)]).alias(target_col)
    )

#6. Funktion um aus string datimetime zu machen

def apply_string_to_datetime(df, cols, tz="Europe/Zurich"): # <--- tz muss hier stehen!
    return df.with_columns(
        pl.col(cols)
        .cast(pl.Datetime)
        .dt.replace_time_zone(None)
        .dt.replace_time_zone(tz)
    )


#7. Funktion um aus string date zu machen

def apply_string_to_date(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).cast(pl.Date))

#8. Funktion um aus string float zu machen

def apply_string_to_float(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).cast(pl.Float64))

#8. Funktion um aus string boolean zu machen

def apply_string_to_boolean(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).cast(pl.Boolean))

#9. Funktion um aus string integer zu machen


def apply_string_to_integer(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    # Int64 deckt alle normalen Ganzzahlen ab
    return df.with_columns(pl.col(cols).cast(pl.Int64))