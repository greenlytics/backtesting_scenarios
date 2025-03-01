import os
import json
import pandas as pd
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
from get_data import get_spot_prices, get_regulation_prices
from wrapper_Ilias import wrapper_bidding_curve_Ilias, wrapper_production_Ilias
from utils import cet_to_utc

file_dir = os.path.dirname(os.path.realpath(__file__))
with open(file_dir + '/paths.json') as f:
    paths = json.load(f)

def backtesting_function(region,
                         bidding_curve,
                         production,
                         one_price=False,
                         optimal=False,
                         update=True,
                         producer=True,
                         convert_to_utc=False,
                         verbose=False):
    # Function for simulating the market and output the profit you would have made, as well as the imbalance costs.

    # ------ Required data structure --------
    # The bidding_curve should be a pandas dataframe with one row per hour, and for each point in the bidding curve
    # (sorted in increasing order), one column called bid_price_x for the price and one column called bid_vol_x for the volume.
    # NB: The bid prices should be strictly monotonically increasing and the bid volumes should be monotonically increasing.
    # The unit for the volumes (both for bidding curve and production) should be MWh and prices should be €/MWh.
    # As of now, this function does not support bidding_curves with variable number of points, this number must be
    # coherent throughout the whole dataset.

    # The bidding curve as well as the production should be pandas dataframes with pandas Datetime indices.
    # They should have the following content:

    # ---------- Production --------------
    # ╔══════════════════════╦════════════╗
    # ║ Datetime             ║ Production ║
    # ╠══════════════════════╬════════════╣
    # ║ 2017-01-01 00:00:00  ║ 633.787216 ║
    # ╠══════════════════════╬════════════╣
    # ║ 2017-01-01 01:00:00  ║ 588.438997 ║
    # ╠══════════════════════╬════════════╣
    # ║ 2017-01-01 02:00:00  ║ 543.984556 ║
    # ╠══════════════════════╬════════════╣
    # ║ ...                  ║ ...        ║
    # ╠══════════════════════╬════════════╣
    # ║ 2017-01-01 23:00:00  ║ 538.862199 ║
    # ╠══════════════════════╬════════════╣
    # ║ 2017-01-02 00:00:00  ║ 537.862199 ║
    # ╚══════════════════════╩════════════╝

    # ----------- Bidding curve ----------------
    # ╔══════════════════════╦═════════════╦══════════════╦═════════════╦══════════════╦═════╗
    # ║ Datetime             ║ bid_price_1 ║ bid_volume_1 ║ bid_price_2 ║ bid_volume_2 ║ ... ║
    # ╠══════════════════════╬═════════════╬══════════════╬═════════════╬══════════════╬═════╣
    # ║ 2017-01-01 00:00:00  ║ 19.636959   ║ 647.26274    ║ 24.635657   ║ 724.865927   ║ ... ║
    # ╠══════════════════════╬═════════════╬══════════════╬═════════════╬══════════════╬═════╣
    # ║ 2017-01-01 01:00:00  ║ 22.892855   ║ 0.00000      ║ 23.602505   ║ 479.413648   ║ ... ║
    # ╠══════════════════════╬═════════════╬══════════════╬═════════════╬══════════════╬═════╣
    # ║ 2017-01-01 02:00:00  ║ 21.944912   ║ 0.00000      ║ 22.753397   ║ 0.00000      ║ ... ║
    # ╠══════════════════════╬═════════════╬══════════════╬═════════════╬══════════════╬═════╣
    # ║ ...                  ║ ...         ║ ...          ║ ...         ║ ...          ║ ... ║
    # ╠══════════════════════╬═════════════╬══════════════╬═════════════╬══════════════╬═════╣
    # ║ 2017-01-01 23:00:00  ║ 27.575207   ║ 0.00000      ║ 28.761277   ║ 0.00000      ║ ... ║
    # ╠══════════════════════╬═════════════╬══════════════╬═════════════╬══════════════╬═════╣
    # ║ 2017-01-02 00:00:00  ║ 28.973810   ║ 501.375889   ║ 29.964015   ║ 540.663559   ║ ... ║
    # ╚══════════════════════╩═════════════╩══════════════╩═════════════╩══════════════╩═════╝


    # ------ Parameters description ----------
    # The one_price parameter allows to choose between a one-price system or a two-prices system.

    # The optimal parameter adds to the output the profits you would have made if you had had a perfect production forecast,
    # as well as the ratio between your current profit and this "optimal" profit.

    # The update parameter allows to refresh the data used for the simulations. It will slow down the function response time,
    # so only use it from time to time when you want to refresh the data.

    # The production parameter allows you to specify if you want the calculations to be made on the producer side
    # or on the retailer side.

    # ------- Usage example -------------
    # bidding_curve = wrapper_bidding_curve_Ilias('day_1_2017.npz')
    # production = wrapper_production_Ilias('day_1_2017.npz')
    # result = backtesting_function('SE1', bidding_curve, production, False, False, False, False)

    if update:
        spot_prices = get_spot_prices()
        regulation_prices = get_regulation_prices()
    else:
        spot_prices = pd.read_csv(paths['data_directory'] + '/' + paths['spot_prices_file_name'],
                                  parse_dates=True, index_col=0)
        regulation_prices = pd.read_csv(paths['data_directory'] + '/' + paths['regulation_prices_file_name'],
                                        parse_dates=True, index_col=0)


    spot_prices.index.name = 'Datetime'
    regulation_prices.index.name = 'Datetime'
    if convert_to_utc:
        spot_prices = cet_to_utc(spot_prices, 'Datetime')
        regulation_prices = cet_to_utc(regulation_prices, 'Datetime')
    # Filter out the data about the times which are not present in the bidding curve
    spot_prices = spot_prices[spot_prices.index.isin(bidding_curve.index)]
    regulation_prices = regulation_prices[regulation_prices.index.isin(bidding_curve.index)]
    spot_prices = spot_prices[spot_prices['Region'] == region]
    regulation_prices = regulation_prices[regulation_prices['Region'] == region]
    # Sometimes the most recent ref time will have duplicates for some reason, make sure to drop them
    regulation_prices = regulation_prices[~regulation_prices.index.duplicated(keep='first')]
    spot_prices = spot_prices[~spot_prices.index.duplicated(keep='first')]
    data = spot_prices.merge(regulation_prices, left_on=['Datetime', 'Region', 'Unit'], right_on=['Datetime', 'Region', 'Unit'])
    # Remove invalid values
    data = data[data['Spot_price'] != -1]
    data = data[data['Upregulation_price'] != -1]
    data = data[data['Downregulation_price'] != -1]
    # Select upregulation or downregulation to remove duplicate index,
    # and then merge with bidding curve and actual production
    bidding_price_cols = [col_name for col_name in bidding_curve.columns if 'price' in col_name]
    bidding_vol_cols = [col_name for col_name in bidding_curve.columns if 'volume' in col_name]


    bid_price_volumes = []
    for idx, row in data.iterrows():
        if producer:

            # If x is the volume we are trying to determine, x1 the bid volume directly smaller, x2 directly larger,
            # y being the spot price, y1 the bid price directly smaller and y2 directly larger,
            # then x = x2 - (y2 - y)/(y2-y1)*(x2-x1)
            # Here, we are trying to find the column containing y2, and then finding all the other values from their relative
            # position to y2 in the dataframe.
            # The prices/volumes are supposed to be sorted in the increasing order,
            # the bid price/volume columns supposed to be directly next one to another for a specific one,
            # and the first column is supposed to be the first bid price (followed by the first bid volume etc).

            bidding_curve_row = bidding_curve.loc[idx]
            # If spot price is above biggest bidding price, assign biggest bidding volume
            if row['Spot_price'] > bidding_curve_row[bidding_price_cols[-1]]:
                bid_price_volumes.append(bidding_curve_row[bidding_vol_cols[-1]])
                continue
            bid_price_idx = next(bidding_price_cols.index(col_name) for col_name in bidding_price_cols if row['Spot_price'] < bidding_curve_row[col_name])
            # If spot price is below smallest bidding price, assign 0 volume
            if bid_price_idx == 0:
                bid_price_volumes.append(0)
            else:
                bid_price_volumes.append(bidding_curve_row[bidding_vol_cols[bid_price_idx]] -
                                     ((bidding_curve_row[bidding_price_cols[bid_price_idx]] - row['Spot_price'])/
                                    (bidding_curve_row[bidding_price_cols[bid_price_idx]] - bidding_curve_row[bidding_price_cols[bid_price_idx - 1]]))*
                              (bidding_curve_row[bidding_vol_cols[bid_price_idx]] - bidding_curve_row[bidding_vol_cols[bid_price_idx - 1]]))
        else:

            # If x is the volume we are trying to determine, x1 the bid volume directly smaller, x2 directly larger,
            # y being the spot price, y1 the bid price directly smaller and y2 directly larger,
            # then x = x2 - (y1 - y)/(y1-y2)*(x2-x1) (NB: different than producer due to the trend of the curve)
            # Here, we are trying to find the column containing y2, and then finding all the other values from their relative
            # position to y2 in the dataframe.
            # The prices/volumes are supposed to be sorted in the increasing order,
            # the bid price/volume columns supposed to be directly next one to another for a specific one,
            # and the first column is supposed to be the first bid price (followed by the first bid volume etc).
            #

            bidding_curve_row = bidding_curve.loc[idx]
            # If spot price is under smallest bidding price, assign biggest bidding volume
            if row['Spot_price'] < bidding_curve_row[bidding_price_cols[0]]:
                bid_price_volumes.append(bidding_curve_row[bidding_vol_cols[0]])
                continue
            bid_price_idx = next((bidding_price_cols.index(col_name) for col_name in bidding_price_cols if
                                 row['Spot_price'] < bidding_curve_row[col_name]), -1)
            # If spot price is above biggest bidding price, assign 0 volume
            if bid_price_idx == -1:
                bid_price_volumes.append(0)
            else:
                bid_price_volumes.append(bidding_curve_row[bidding_vol_cols[bid_price_idx]] -
                                         ((bidding_curve_row[bidding_price_cols[bid_price_idx - 1]] - row['Spot_price']) /
                                          (bidding_curve_row[bidding_price_cols[bid_price_idx - 1]] - bidding_curve_row[bidding_price_cols[bid_price_idx]])) *
                                         (bidding_curve_row[bidding_vol_cols[bid_price_idx]] - bidding_curve_row[bidding_vol_cols[bid_price_idx - 1]]))

    data['Volume'] = bid_price_volumes
    if verbose:
        print(production.head())
    data = data.merge(production, left_index=True, right_index=True)
    if verbose:
        print(data.head())

    # Calculate positive and negative errors
    data['E+'] = np.maximum(data['Production'] - data['Volume'], 0)
    data['E-'] = np.minimum(data['Production'] - data['Volume'], 0)
    if one_price:
        # If one price system

        # If upregulation as dominating direction
        data.loc[data['Dominating_direction'] == 1,'Imbalance_cost'] = data['Upregulation_price'] * data['E+'] \
                                                                         + data['Upregulation_price'] * data['E-']
        # If downregulation as dominating direction
        data.loc[data['Dominating_direction'] == -1,'Imbalance_cost'] = data['Downregulation_price'] * data['E+'] \
                                                                        + data['Downregulation_price'] * data['E-']
        # If unregulation
        data.loc[data['Dominating_direction'] == 0, 'Imbalance_cost'] = data['Spot_price'] * data['E+'] \
                                                                        + data['Spot_price'] * data['E-']
    else:
        # If two prices system

        # If upregulation as dominating direction
        data.loc[data['Dominating_direction'] == 1, 'Imbalance_cost'] = data['Downregulation_price'] * data['E+'] \
                                                                         + data['Upregulation_price'] * data['E-']
        # If downregulation as dominating direction
        data.loc[data['Dominating_direction'] == -1, 'Imbalance_cost'] = data['Downregulation_price'] * data['E+'] \
                                                                        + data['Upregulation_price'] * data['E-']
        # If unregulation
        data.loc[data['Dominating_direction'] == 0, 'Imbalance_cost'] = data['Spot_price'] * data['E+'] \
                                                                        + data['Spot_price'] * data['E-']

    data['Profit'] = data['Spot_price'] * data['Volume'] + data['Imbalance_cost']
    if verbose:
        print(data[['Spot_price','Downregulation_price','Upregulation_price','Dominating_direction','Production','E+','E-','Imbalance_cost']])
    if optimal:
        data['Profit_no_error'] = data['Production'] * data['Spot_price']
        data['Optimization_ratio'] = data['Profit']/data['Profit_no_error']
        return data[['Imbalance_cost','Profit','Profit_no_error','Optimization_ratio']]
    else:
        return data[['Profit','Imbalance_cost']]
