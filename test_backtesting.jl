# How to use backtesting_function in Julia

using PyCall
using DataFrames


machinery = pyimport("importlib.machinery");

loader1 = machinery.SourceFileLoader("wrapper_Ilias","wrapper_Ilias.py");
wrapper = loader1.load_module("wrapper_Ilias");

loader2 = machinery.SourceFileLoader("get_data","get_data.py");
getdata = loader2.load_module("get_data");

loader3 = machinery.SourceFileLoader("backtesting","backtesting.py");
backtest = loader3.load_module("backtesting");


bidding_curve = wrapper.wrapper_bidding_curve_Ilias("day_1_2017.npz");
production = wrapper.wrapper_production_Ilias("day_1_2017.npz");
result = backtest.backtesting_function("SE1", bidding_curve, production, false, false, false);


colnames = map(Symbol, result.columns);
results = DataFrame(Any[collect(result[c]) for c in colnames], colnames);

totalProfit = sum(results.Profit);
