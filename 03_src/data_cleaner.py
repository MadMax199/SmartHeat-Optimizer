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

#6. FUnktion um Label infos mit Unbekannt zu belabeln: 

def apply_unbekannt(df, cols: list[str]) -> pl.DataFrame:
    return df.with_columns(pl.col(cols).fill_null("Unbekannt"))

#Checkt ob die Innputations Funktionen den gwünschten effekt hatten

def compare_imputation(
    df_before: pl.DataFrame,
    df_after: pl.DataFrame,
    col_lists: dict[str, list[str]],
) -> pl.DataFrame:
    """
    Vergleicht Nulls zwischen df_before und df_after fuer alle uebergebenen Spaltenlisten.
    Gibt eine Tabelle mit Vorher/Nachher/Differenz pro Spalte aus.

    Args:
        df_before:  DataFrame vor der Imputation (z.B. data_combined).
        df_after:   DataFrame nach der Imputation (z.B. data_combined_filled).
        col_lists:  Dict mit Label -> Spaltenliste, z.B.:
                    {
                        "building_type":   ["building_type"],
                        "fill_false_list":  fill_false_list,
                        "fill_null_list":   fill_null_list,
                        "fill_median_list": fill_median_list,
                        "fill_unbekannt":   fill_unbekannt_list,
                        "fill_inter_list":  fill_inter_list,
                    }

    Returns:
        pl.DataFrame: Vergleichstabelle mit einer Zeile pro Spalte.
    """
    rows = []
    n = df_before.height

    for list_name, cols in col_lists.items():
        existing = [c for c in cols if c in df_before.columns and c in df_after.columns]
        for col in existing:
            nulls_before = df_before[col].null_count()
            nulls_after  = df_after[col].null_count()
            diff         = nulls_before - nulls_after
            rows.append({
                "liste":         list_name,
                "spalte":        col,
                "nulls_vorher":  nulls_before,
                "pct_vorher":    round(nulls_before / n * 100, 2),
                "nulls_nachher": nulls_after,
                "pct_nachher":   round(nulls_after  / n * 100, 2),
                "behoben":       diff,
                "status":        "OK" if nulls_after == 0 else ("BEHOBEN" if diff > 0 else "UNVERAENDERT"),
            })

    result = pl.DataFrame(rows)

    # Zusammenfassung pro Liste
    sep = "-" * 65
    print(f"\n{sep}")
    print("IMPUTATION VERGLEICH: data_combined vs. data_combined_filled")
    print(sep)

    for list_name in col_lists:
        sub = result.filter(pl.col("liste") == list_name)
        total_before = sub["nulls_vorher"].sum()
        total_after  = sub["nulls_nachher"].sum()
        n_fixed      = sub.filter(pl.col("status") == "OK").height
        n_remaining  = sub.filter(pl.col("nulls_nachher") > 0).height

        status_icon = "OK" if total_after == 0 else "WARNUNG"
        print(f"\n  [{list_name}]  {status_icon}")
        print(f"   Nulls vorher  : {total_before:>8,}")
        print(f"   Nulls nachher : {total_after:>8,}  ({total_before - total_after:,} behoben)")
        if n_remaining > 0:
            still_open = sub.filter(pl.col("nulls_nachher") > 0).select(
                ["spalte", "nulls_vorher", "nulls_nachher", "pct_nachher", "status"]
            )
            print(f"   Noch offen ({n_remaining} Spalten):")
            with pl.Config(tbl_rows=50, tbl_cols=-1, fmt_str_lengths=60):
                print(still_open)

    total_before_all = result["nulls_vorher"].sum()
    total_after_all  = result["nulls_nachher"].sum()
    print(f"\n{sep}")
    print(f"GESAMT  Nulls vorher: {total_before_all:,}  |  "
          f"Nulls nachher: {total_after_all:,}  |  "
          f"Behoben: {total_before_all - total_after_all:,} "
          f"({(total_before_all - total_after_all) / max(total_before_all,1) * 100:.1f}%)")
    print(sep)

    return result


# Checkt nochmal welche Features die miesten Fehlenden Werte hatten

def check_amount_nulls(df: pl.DataFrame, top_n: int = 20, only_with_nulls: bool = True) -> pl.DataFrame:
    """
    Zeigt die Spalten mit den meisten Nulls, sortiert nach Prozentsatz.

    Args:
        df:              DataFrame der geprueft werden soll.
        top_n:           Wie viele Spalten angezeigt werden (default: 20).
        only_with_nulls: Nur Spalten mit mind. einem Null (default: True).
    """
    result = (
        df.null_count()
        .transpose(include_header=True, column_names=["null_count"])
        .with_columns(
            (pl.col("null_count") / df.height * 100).round(2).alias("pct")
        )
        .rename({"column": "spalte"})
        .sort("pct", descending=True)
    )

    if only_with_nulls:
        result = result.filter(pl.col("null_count") > 0)

    result = result.head(top_n)

    sep = "-" * 45
    print(f"\n{sep}")
    print(f"TOP {top_n} SPALTEN MIT MEISTEN NULLS")
    print(f"Datensatz: {df.height:,} Zeilen | {df.width} Spalten")
    print(f"Spalten mit Nulls: {result.height}")
    print(sep)

    if result.height == 0:
        print("Keine Nulls gefunden.")
    else:
        with pl.Config(tbl_rows=top_n, tbl_cols=-1):
            print(result)

    return result

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