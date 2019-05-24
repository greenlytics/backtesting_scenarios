import pandas as pd
def cet_to_utc(df, col_name):
    # Convert dataframe CET/CEST datetimes column to UTC datetimes
    # Example call: cet_to_utc(dataframe, 'Datetime')
    #
    # --- Arguments description --
    # You need to provide as first argument the dataframe you want to modify,
    # and as second argument the column you want to modify.
    idx_name = df.index.name
    df = df.reset_index()
    idx = 0
    while idx != df.index[-1] + 1:
        try:
            df.loc[idx, 'temp'] = pd.to_datetime(df.loc[idx, col_name]).tz_localize('CET').tz_convert('UTC')
            idx += 1
        except:

            # AmbiguousTimeError
            if df.loc[idx, col_name].month == 10:
                # Duplicate the single value we had at 2 am
                df = df.iloc[:idx, ].append(df.iloc[idx]).append(df.iloc[idx:, ]).reset_index(drop=True)
                # Convert both rows to UTC
                df.loc[idx, 'temp'] = pd.to_datetime(
                    pd.to_datetime(df.loc[idx, col_name]) - pd.Timedelta(hours=2)).tz_localize('UTC')
                df.loc[idx + 1, 'temp'] = pd.to_datetime(
                    pd.to_datetime(df.loc[idx, col_name]) - pd.Timedelta(hours=1)).tz_localize('UTC')
                idx += 2

            # InconsistentTimeError
            else:
                # Delete the 3 am row
                df.drop(idx, inplace=True)
                df = df.sort_index().reset_index(drop=True)

    df[col_name] = df['temp']
    df = df.drop(labels='temp', axis=1)
    if idx_name:
        df = df.set_index(idx_name)
        df.index.name = idx_name
    else:
        df = df.set_index('index')
        df.index.name = None
    return df