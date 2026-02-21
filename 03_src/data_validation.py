import polars as pl
import polars.selectors as cs
import pandera

def double_numbers(df):

    df_doubles = (df.filter(df.is_duplicated(
    anzahl = df_doubles.height

    print(f"Anzahl der Zeilen die Duplikate sind: {anzahl}")
          


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
    

def check_data_quality(df, schema):
    try:
        validated_df = schema_class.validate(df.lazy()).collect()
        print("✅ Validierung erfolgreich: Der Dataframe entspricht dem Schema!")
        return validated_df
    
    except pa.errors.SchemaErrors as err:
        print("❌ Validierung fehlgeschlagen!")
        
       
        failure_report = err.failure_cases
        
        print(f"\nAnzahl gefundener Fehler: {len(failure_report)}")
        print("\nErste Fehler im Detail:")
        print(failure_report.head(15))
        
        return failure_report