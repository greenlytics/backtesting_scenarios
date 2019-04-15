import numpy as np
import pandas as pd


def wrapper_bidding_curve_Ilias(file_name):
    bidding_curve = np.load(file_name)
    bidding_curves = {}
    for x in bidding_curve:
        if 'bidcurves' in x:
            bidding_curves[x.split('s')[1]] = bidding_curve[x]
    df = pd.DataFrame()
    for time in range(24):
        line_dic = {}
        for i, element in enumerate(bidding_curve['bidcurves' + str(time + 1)]):
            line_dic['bid_price_' + str(i+1)] = element[0]
            line_dic['bid_volume_' + str(i+1)] = element[1]
        one_time_df = pd.DataFrame(line_dic, index=[pd.to_datetime('2017-1-1 ' + str(time) + ':00:00')])
        df = df.append(one_time_df)
    df.index.name = 'Datetime'
    return df

def wrapper_production_Ilias(file_name):
    bidding_curve = np.load(file_name)
    production = bidding_curve['actualgen']
    df = pd.DataFrame()

    for i, value in enumerate(production[0]):
        df = df.append(pd.DataFrame({'Production': value},index=[pd.to_datetime('2017-1-1 ' + str(i) + ':00:00')]))
    df.index.name = ('Datetime')
    return df