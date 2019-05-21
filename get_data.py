import psycopg2
import pandas as pd
import json
import os
from datetime import datetime, timedelta

desired_width=320
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns',10)

import matplotlib.pyplot as plt
plt.interactive(False)

file_dir = os.path.dirname(os.path.realpath(__file__))
with open(file_dir + '/paths.json') as f:
    paths = json.load(f)

data_directory = paths['data_directory']
spot_prices_data_path = data_directory + '/' + paths['spot_prices_file_name']
regulation_prices_data_path = data_directory + '/' + paths['regulation_prices_file_name']

with open(file_dir + '/credentials.json') as f:
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
            datetime = pd.to_datetime(data_date) + timedelta(hours=i)
            regions.append(region)
            units.append(unit)
            datetimes.append(datetime)
            spot_prices.append(price)

    return regions, units, datetimes, spot_prices

def get_regulation_prices():
    new_df = pd.DataFrame(columns=['Region', 'Unit', 'Datetime', 'Upregulation_price', 'Downregulation_price', 'Dominating_direction'])

    if os.path.exists(regulation_prices_data_path):
        print("Updating regulation prices.")
        df = pd.read_csv(regulation_prices_data_path, parse_dates=True, index_col=0)
        df_last_date = df.index[-1].strftime('%Y-%m-%d')
        cursor.execute("select * from regional_regulating where data_date >= '{0}' AND reg_code IN ('RO', 'RN', 'DD');".format(df_last_date))
    else:
        print("Fetching regulation prices.")
        cursor.execute("select * from regional_regulating where reg_code IN ('RO', 'RN', 'DD');")

    datetimes_dd, area_codes_dd, reg_prices_dd, \
    datetimes_ro, area_codes_ro, reg_prices_ro, \
    datetimes_rn, area_codes_rn, reg_prices_rn = reg_price_parse_results(cursor)

    df_dd = pd.DataFrame(columns=['Datetime', 'Region', 'Dominating_direction'])
    df_dd['Datetime'] = datetimes_dd
    df_dd['Region'] = area_codes_dd
    df_dd['Dominating_direction'] = reg_prices_dd

    df_ro = pd.DataFrame(columns=['Datetime', 'Region', 'Upregulation_price'])
    df_ro['Datetime'] = datetimes_ro
    df_ro['Region'] = area_codes_ro
    df_ro['Upregulation_price'] = reg_prices_ro


    df_rn = pd.DataFrame(columns=['Datetime', 'Region', 'Downregulation_price'])
    df_rn['Datetime'] = datetimes_rn
    df_rn['Region'] = area_codes_rn
    df_rn['Downregulation_price'] = reg_prices_rn

    new_df = df_rn.merge(df_ro, left_on=['Datetime', 'Region'], right_on=['Datetime', 'Region'])
    new_df = new_df.merge(df_dd, left_on=['Datetime', 'Region'], right_on=['Datetime', 'Region'])
    new_df['Unit'] = 'EUR'
    new_df = new_df.set_index('Datetime').sort_index()
    if os.path.exists(regulation_prices_data_path):
        new_df = df.append(new_df)
    new_df = new_df.sort_index()


    # Prune if there is a series of unvalid ref times at the end, data not available
    # Only the latest because we want to make the distinction between invalid and unavailable
    new_df = new_df[:new_df[new_df['Upregulation_price'] != -1].index[-1]]
    new_df = new_df[:new_df[new_df['Downregulation_price'] != -1].index[-1]]

    new_df.to_csv(regulation_prices_data_path)

    return new_df

def reg_price_parse_results(cursor):
    datetimes_dd = []
    datetimes_ro = []
    datetimes_rn = []

    area_codes_dd = []
    area_codes_ro = []
    area_codes_rn = []

    reg_prices_dd = []
    reg_prices_ro = []
    reg_prices_rn = []

    for query in cursor:
        area_code = query[0]
        data_date = query[1]
        #fetch_date = query[2]
        #total=query[3]
        prices = query[4]
        # reg_type = query[5]
        reg_code = query[6]

        # If this row only indicates the dominating direction
        if reg_code == 'DD':
            for i, price in enumerate(prices):
                datetime = pd.to_datetime(data_date) + timedelta(hours=i)
                datetimes_dd.append(datetime)
                area_codes_dd.append(area_code)
                reg_prices_dd.append(price)

        elif reg_code == 'RO':
            for i, price in enumerate(prices):
                datetime = pd.to_datetime(data_date) + timedelta(hours=i)
                datetimes_ro.append(datetime)
                area_codes_ro.append(area_code)
                reg_prices_ro.append(price)

        elif reg_code == 'RN':
            for i, price in enumerate(prices):
                datetime = pd.to_datetime(data_date) + timedelta(hours=i)
                datetimes_rn.append(datetime)
                area_codes_rn.append(area_code)
                reg_prices_rn.append(price)

    return datetimes_dd, area_codes_dd, reg_prices_dd,\
           datetimes_ro, area_codes_ro, reg_prices_ro,\
           datetimes_rn, area_codes_rn, reg_prices_rn

def get_range_prices(first_date, last_date, update=False, separate_df=True):
    # Get prices data for a specific range of dates
    # Example call: get_range_prices('2019-03-25','2019-03-30', separate_df=False)
    #
    # --- Arguments description --
    # You need to provide first date and last date in the following format: 2019-03-24 01:00:00
    # You can only provide the date, it will automatically assume 00:00:00 as the time
    # Set update to True if you want to refresh your data, slows down the response time
    # Set separate_df to True if you want one dataframe for the spot prices and one for the regulation prices
    # Set separate_df to False (or don't provide it) if you want all the prices in the same dataframe

    if update:
        spot = get_spot_prices()
        reg = get_regulation_prices()
    else:
        spot = pd.read_csv(spot_prices_data_path, parse_dates=True, index_col=0)
        reg = pd.read_csv(regulation_prices_data_path, parse_dates=True, index_col=0)

    spot = spot[pd.to_datetime(first_date):pd.to_datetime(last_date)]

    reg = reg[pd.to_datetime(first_date):pd.to_datetime(last_date)]

    if separate_df:
        return spot, reg
    else:
        cols_to_use = set(reg.columns) - set(spot.columns)
        spot = spot.merge(reg[list(cols_to_use) + ['Region']], left_on=['Datetime', 'Region'], right_on=['Datetime','Region'])
        return spot


# df = get_spot_prices()
# print(df.shape)
# print(df.head())
# print(df.tail())
#
# print(df[df['Spot_price'] == -1].index)
#
#
# df = get_regulation_prices()
# print(df.shape)
# print(df.head())
# print(df.tail())
# print(df[df['Upregulation_price'] == -1])
# print(df[df['Downregulation_price'] == -1])
#
# spot_prices = get_spot_prices()
# print(spot_prices.shape)
# print(spot_prices.head())
# print(spot_prices.tail())
# df = df.merge(spot_prices, left_on=['Datetime', 'Region', 'Unit'], right_on=['Datetime', 'Region', 'Unit'])
# print(df.shape)
# print(df.head(100))
# print(df.tail())

#
# df = get_regulation_prices().merge(get_spot_prices(), left_on=['Datetime', 'Region'], right_on=['Datetime', 'Region'])
# print(df.shape)
#
# print('Code 1')
# df_dd_1 = df[df['Dominating_direction'] == 1]
# print(df_dd_1.shape)
# matching_df_dd_1 = df_dd_1[df_dd_1['Regulation_price'] == df_dd_1['Spot_price']]
# print(matching_df_dd_1.shape)
# print('RN')
# print(matching_df_dd_1[matching_df_dd_1['Regulation_code'] == 'RN'].shape)
# print('RO')
# print(matching_df_dd_1[matching_df_dd_1['Regulation_code'] == 'RO'].shape)
#
# print('Code 0')
# df_dd_0 = df[df['Dominating_direction'] == 0]
# print(df_dd_0.shape)
# matching_df_dd_0 = df_dd_0[df_dd_0['Regulation_price'] == df_dd_0['Spot_price']]
# print(matching_df_dd_0.shape)
# print('Non-matching:')
# print(df_dd_0[df_dd_0['Regulation_price'] != df_dd_0['Spot_price']])
# print('RN')
# print(matching_df_dd_0[matching_df_dd_0['Regulation_code'] == 'RN'].shape)
# print('RO')
# print(matching_df_dd_0[matching_df_dd_0['Regulation_code'] == 'RO'].shape)
#
# print('Code -1')
# df_dd_minus_1 = df[df['Dominating_direction'] == -1]
# # Half of all the cases
# print(df_dd_minus_1.shape)
# # Almost half of those cases have matching spot price and regulation price
# # only few impossible to determine, back to the 2% noticed in the data
# matching_df_dd_minus_1 = df_dd_minus_1[df_dd_minus_1['Regulation_price'] == df_dd_minus_1['Spot_price']]
# print(matching_df_dd_minus_1.shape)
# print('RN')
# print(matching_df_dd_minus_1[matching_df_dd_minus_1['Regulation_code'] == 'RN'].shape)
# print('RO')
# print(matching_df_dd_minus_1[matching_df_dd_minus_1['Regulation_code'] == 'RO'].shape)
#
#
# print('Percentage of matching cases')
# total = 0
# matching = 0
# count_dict = {-1: 0, 0: 0, 1:0}
# for datetime in list(df.index.unique()):
#     total += 1
#     date_df = df.loc[datetime]
#     bad = 0
#     for region in ['SE1', 'SE2', 'SE3', 'SE4']:
#         # If for this datetime one of the regions has no match
#         regional_date_df = date_df[date_df['Region'] == region]
#         regional_matching_df = regional_date_df[regional_date_df['Spot_price'] == regional_date_df['Regulation_price']]
#         if not regional_matching_df.shape[0] > 0:
#             bad = 1
#             count_dict[regional_date_df['Dominating_direction'][0]] = count_dict[regional_date_df['Dominating_direction'][0]] + 1
#     if not bad:
#         matching += 1
#
# print(matching/total)
# print(count_dict)
