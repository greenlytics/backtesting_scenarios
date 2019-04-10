import psycopg2
import pandas as pd
import json
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
plt.interactive(False)

data_directory = 'data'
spot_prices_data_path = data_directory + '/spot_prices.csv'
regulation_prices_data_path = data_directory + '/regulation_prices.csv'

with open('credentials.json') as f:
    credentials = json.load(f)

connection = psycopg2.connect(host='34.76.166.203',
                              database=credentials['database'],
                              user=credentials['username'],
                              password=credentials['password'])
cursor = connection.cursor()

if not os.path.exists(data_directory):
    os.makedirs(data_directory)

def get_spot_prices():
    new_df = pd.DataFrame(columns=['Region', 'Unit', 'Datetime', 'Spot_price'])

    if os.path.exists(spot_prices_data_path):
        print("Updating spot prices.")
        df = pd.read_csv(spot_prices_data_path, parse_dates=True, index_col=0)
        df_last_date = pd.to_datetime(df.index[-1]).strftime('%Y-%m-%d')
        cursor.execute("select * from regional_elspot where data_date >= '{0}';".format(df_last_date))
    else:
        print("Fetching spot prices.")
        cursor.execute('select * from regional_elspot;')

    regions, units, datetimes, spot_prices = spot_price_parse_results(cursor)
    new_df['Datetime'] = datetimes
    new_df['Region'] = regions
    new_df['Unit'] = units
    new_df['Spot_price'] = spot_prices
    new_df = new_df.set_index('Datetime').sort_index()
    if os.path.exists(spot_prices_data_path):
        new_df = df.append(new_df)
    new_df = new_df.sort_index()

    # Prune if there is a series of unvalid ref times at the end, data not available
    # Only the latest because we want to make the distinction between invalid and unavailable
    new_df = new_df[:new_df[new_df['Spot_price'] != -1].index[-1]]

    new_df.to_csv(spot_prices_data_path)

    return new_df

def spot_price_parse_results(cursor):
    regions = []
    units = []
    datetimes = []
    spot_prices = []
    for query in cursor:

        region = query[0]
        unit = query[1]
        data_date = query[2]
        # fetch_date = query[3]
        # total = query[4]
        prices = query[5]

        for i, price in enumerate(prices):
            datetime = data_date + timedelta(hours=i)
            regions.append(region)
            units.append(unit)
            datetimes.append(datetime)
            spot_prices.append(price)

    return regions, units, datetimes, spot_prices

def get_regulation_prices():
    new_df = pd.DataFrame(columns=['Region', 'Unit', 'Datetime','Regulation_code', 'Regulation_price'])

    if os.path.exists(regulation_prices_data_path):
        print("Updating regulation prices.")
        df = pd.read_csv(regulation_prices_data_path, parse_dates=True, index_col=0)
        df_last_date = df.index[-1].strftime('%Y-%m-%d')
        cursor.execute("select * from regional_regulating where data_date >= '{0}' AND reg_code IN ('RO', 'RN');".format(df_last_date))
    else:
        print("Fetching regulation prices.")
        cursor.execute("select * from regional_regulating where reg_code IN ('RO', 'RN');")

    datetimes, area_codes, reg_codes, reg_prices = reg_price_parse_results(cursor)
    new_df['Datetime'] = datetimes
    new_df['Region'] = area_codes
    new_df['Unit'] = 'EUR'
    new_df['Regulation_code'] = reg_codes
    new_df['Regulation_price'] = reg_prices
    new_df = new_df.set_index('Datetime').sort_index()
    if os.path.exists(regulation_prices_data_path):
        new_df = df.append(new_df)
    new_df = new_df.sort_index()

    # Prune if there is a series of unvalid ref times at the end, data not available
    # Only the latest because we want to make the distinction between invalid and unavailable
    new_df = new_df[:new_df[new_df['Regulation_price'] != -1].index[-1]]

    new_df.to_csv(regulation_prices_data_path)

    return new_df

def reg_price_parse_results(cursor):
    reg_codes = []
    datetimes = []
    area_codes = []
    reg_prices = []
    for query in cursor:
        area_code = query[0]
        data_date = query[1]
        #fetch_date = query[2]
        #total=query[3]
        prices = query[4]
        # reg_type = query[5]
        reg_code = query[6]

        for i, price in enumerate(prices):
            datetime = data_date + timedelta(hours=i)
            datetimes.append(datetime)
            area_codes.append(area_code)
            reg_codes.append(reg_code)
            reg_prices.append(price)

    return datetimes, area_codes, reg_codes, reg_prices



df = get_spot_prices()
print(df.shape)
print(df.head())
print(df.tail())

print(df[df['Spot_price'] == -1].index)


df = get_regulation_prices()
print(df.shape)
print(df.head())
print(df.tail())
print(df[df['Regulation_price'] == -1])

# def build_df_from_db():
#
#     return df
#
# def update_local_data():
#     new_data = build_df_from_db()
#     df.append(new_data)
#     df.save
#     return
