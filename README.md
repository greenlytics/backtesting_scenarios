# Market modeling backtesting environment
This code provides you with a fully integrated function to test
 the performance of your model. 
 
#### First use
Replace the "XXX" in **credentials_example.json** with the
 database credentials you have been provided with, and then rename
 the file to **credentials.json**.
 
Install all the required dependencies with **pip** running 
`pip install -r requirements.txt`

You will then have to make sure that your data structure is aligned 
with the one required by the function. All the details can be found
as comments in the code, as well as a description of the 
different available parameters and a simple use example.

 
#### General usage
The only function you need is called "backtesting_function" and
is located in the file backtesting.py.

You need to call it at least once with the last parameter **update**
as **True** because it will allow you to locally fetch the data needed
for simulating the market. You should set this parameter to **False**
if you want to speed up the function return. Set it back to **True** 
anytime you want to refresh the data.

### Profit calculation equations implemented

![](https://github.com/greenlytics/backtesting_scenarios/blob/master/Terminology.png)
![](https://github.com/greenlytics/backtesting_scenarios/blob/master/one_price_equations.png)
![](https://github.com/greenlytics/backtesting_scenarios/blob/master/two_prices_equations.png)