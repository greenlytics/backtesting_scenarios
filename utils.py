def cet_to_utc(df, col_name, index=False):
    # Convert pandas dataframe CET/CEST datetimes column to UTC datetimes
    # Example call: cet_to_utc(dataframe, 'Datetime', index=True)
    #
    # --- Arguments description --
    # You need to provide as first argument the dataframe you want to modify,
    # and as second argument the column you want to modify.
    # If you want to modify the index, call the function the same way, with the
    # name of the index column, and set index=True.
    if index:
        df = df.reset_index()
    df[col_name] = df[col_name].dt.tz_localize('Europe/Brussels').dt.tz_convert('UTC')
    if index:
        df = df.set_index(col_name)
    return df