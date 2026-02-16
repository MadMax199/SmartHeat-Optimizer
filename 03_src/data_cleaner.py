import polars as pl

#Strategie zur Behandlung von Missing Values (Übersicht)
#1. Strategie: Auffüllen mit False (Boolean) Wird verwendet, wenn das Fehlen eines Eintrags logisch als "nicht vorhanden" interpretiert werden kann.
#installation_haspvsystem, building_renovated_...,heatpump_installation_internetconnection


def fill_false(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).fill_null(False))


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

    if group_by_col:
        return df.with_columns([
            pl.col(c).fill_null(pl.col(c).median().over(group_by_col)) for c in cols
        ])
    return df.with_columns(pl.col(cols).fill_null(pl.col(cols).median()))



#4. Strategie: Interpolation & Carry-Over (Zeitlich/Logisch)
#Wird verwendet, um Kontinuität in Zeitreihen oder Experten-Einstellungen zu wahren.


def apply_interpolation(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).interpolate())

#5. Stratgie: Wenn 'aftervisit' null ist, nimm 'beforevisit

def apply_carry_over(df: pl.DataFrame, target_col: str, source_col: str) -> pl.DataFrame:

    return df.with_columns(pl.col(target_col).fill_null(pl.col(source_col)))
