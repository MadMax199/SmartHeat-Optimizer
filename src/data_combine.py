
import polars as pl
import os
import glob

def join_data(df1, join_ids: list, join_how:str ,df2, join_ids2: list,  join_how2:str ,df3, join_ids3: list, join_how3:str , df4, join_ids4: list, join_how4:str):


    df = df1.join(df2, on=join_ids, how="left", coalesce=True)

    df = df.join(df3,  on=join_ids3, how="left", coalesce=True)
    
    df = df.join(df4,  on=join_ids4, how="left", coalesce=True)

    return df
