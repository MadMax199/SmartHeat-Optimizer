import polars as pl
import polars.selectors as cs


#Strategie zur Behandlung von Missing Values (Übersicht)
#1. Strategie: Auffüllen mit False (Boolean) Wird verwendet, wenn das Fehlen eines Eintrags logisch als "nicht vorhanden" interpretiert werden kann.
#installation_haspvsystem, building_renovated_...,heatpump_installation_internetconnection


def fill_false(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:

    return df.with_columns(pl.col(cols).cast(pl.Boolean).fill_null(False))


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


def detect_outliers(df: pl.DataFrame, method='iqr', top_n=10):
    """
    Erkennt Ausreißer, berechnet Quoten und gibt die extremsten Werte 
    absteigend sortiert in einer Liste aus.
    """
    print(f"\n--- Detaillierte Ausreißer-Analyse ({method.upper()}) ---")
    
    # Alle numerischen Spalten auswählen
    num_cols = df.select(cs.numeric()).columns
    ausreisser_liste = []

    for col in num_cols:
        # Falls Spalte komplett leer ist -> überspringen
        if df[col].null_count() == df.height:
            continue
            
        # 1. Ausreißer-Filter definieren
        if method == 'iqr':
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_filter = (pl.col(col) < lower) | (pl.col(col) > upper)
        else: # Z-Score
            mean = df[col].mean()
            std = df[col].std()
            if std == 0 or std is None: continue
            outlier_filter = ((pl.col(col) - mean) / std).abs() > 3
            
        # 2. Ausreißer-Daten extrahieren
        outlier_data = df.filter(outlier_filter).select(col).drop_nulls()
        count = outlier_data.height
        
        if count > 0:
            perc = (count / df.height) * 100
            
            # 3. Werte in Liste schreiben und absteigend sortieren
            top_values = (
                outlier_data
                .sort(col, descending=True)
                .head(top_n)
                .to_series()
                .to_list()
            )
            
            ausreisser_liste.append({
                "spalte": col,
                "anzahl": count,
                "prozent": perc,
                "extremwerte": top_values
            })

    # 4. Gesamtergebnis nach Prozent absteigend sortieren
    ausreisser_liste = sorted(ausreisser_liste, key=lambda x: x['prozent'], reverse=True)

    # 5. Ausgabe
    for entry in ausreisser_liste:
        print(f"{entry['spalte']:45} | {entry['anzahl']:8} ({entry['prozent']:6.2f}%)")
        print(f"   -> Extremwerte (Top {top_n} absteigend): {entry['extremwerte']}\n")

    return ausreisser_liste