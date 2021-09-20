import xgboost as xgb
from xgboost import plot_importance, plot_tree
from sklearn.metrics import mean_squared_error, mean_absolute_error
from datetime import datetime as dt
from datetime import *
from dateutil.relativedelta import *
from math import sqrt
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option("display.max_rows", None)

class trainer:
    def __init__(self):
        pass

    def train(self, data, promos):
        # split train and test
        train, test = self.split(data)

        # create featurs
        X_train, y_train = self.create_features(train, promos, label='Bottle_Count')
        X_test, y_test = self.create_features(test, promos, label='Bottle_Count')

        # create and train model
        param_dist = {
            "n_estimators":1000,
            "learing_rate":.01,
            "max_depth":10,
            "gamma":.3,
            "subsample":.7,
            "reg_lambda":3,
            "reg_alpha":0,
            "min_child_rate":7,
            "ntree":250,
        }

        reg = xgb.XGBRegressor(**param_dist)
        reg.fit(X_train, y_train,
                eval_metric=["error", "mae"],
                eval_set=[(X_train, y_train), (X_test, y_test)],
                early_stopping_rounds=50,
                verbose=False) # Change verbose to True if you want to see it train
        
        mse, rmse, mae = self.plots_and_metrics(reg, test, train, X_test)
        
        return reg, mse, rmse, mae

    def split(self, data):
        start_date = str(min(data.index.date))
        dates = pd.date_range(start_date, periods=len(data)).tolist()
        rw = round(len(data)*.7)
        split_date = dates[rw]
        data_train = data.loc[data.index <= split_date].copy()
        data_test = data.loc[data.index > split_date].copy()

        return data_train, data_test

    def create_features(self, df, promos, label=None):
        """
        Creates time series features from datetime index
        """
        df['date'] = df.index
        df['hour'] = df['date'].dt.hour
        df['dayofweek'] = df['date'].dt.dayofweek
        df['quarter'] = df['date'].dt.quarter
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['dayofyear'] = df['date'].dt.dayofyear
        df['dayofmonth'] = df['date'].dt.day
        df['weekofyear'] = df['date'].dt.weekofyear
        if 'Prev_Day_Count' in df:
            df['prev_day_count'] = df['Prev_Day_Count']
        else:
            df['prev_day_count'] = [385]*len(df)
        if 'Prev_2_Day_Count' in df:
            df['prev_2_day_count'] = df['Prev_Day_Count']
        else:
            df['prev_2_day_count'] = [385]*len(df)

        df = self.add_sales(df, promos)

        X = df[['hour','dayofweek','quarter','month','year',
            'dayofyear','dayofmonth','weekofyear','prev_day_count',
            'event','covid','prev_2_day_count']] 
        if label:
            y = df[label]
            return X, y
        return X

    def add_sales(self, df, promos):
        event = [0] * len(df)
        covid = [0] * len(df)

        for promo in promos:
            start = promos[promo]["start"]
            end = promos[promo]["end"]
            for i in range(len(df)):
                if df.index[i] >= pd.to_datetime(start) and df.index[i] <= pd.to_datetime(end):
                    event[i] = event[i] + 1 

        # add in black friday deals range
        for i in range(len(df)):
            years = df["date"].dt.year
            year = years[i]
            bf_start = str(datetime.date(dt(year, 11, 1) + relativedelta(weekday=TH(+4)) + timedelta(days=1)))
            bf_end = str(datetime.date(dt(year, 12, 7)))
            if df.index[i] >= pd.to_datetime(bf_start) and df.index[i] <= pd.to_datetime(bf_end):
                event[i] = event[i] + 1 

        # add in covid-19
        for i in range(len(df)):
            c_start = "2020-01-01"
            if df.index[i] >= pd.to_datetime(c_start):
                covid[i] = 1 

        df["event"] = event
        df["covid"] = covid
        return df
        

    def train_all(self, data, promos):
        X_full, y_full = self.create_features(data, promos, label="Bottle_Count")
        
        param_dist = {
            "n_estimators":1000,
            "learing_rate":.01,
            "max_depth":10,
            "gamma":.3,
            "subsample":.6,
            "reg_lambda":3,
            "reg_alpha":0,
            "min_child_weight":3,
            "ntree":500,
        }

        reg = xgb.XGBRegressor(**param_dist)
        reg.fit(X_full, y_full,
                eval_set=[(X_full, y_full), (X_full, y_full)],
                early_stopping_rounds=50,
                verbose=False)
        
        return reg

    def plots_and_metrics(self, mod, test, train, X_test):
        # forecast on test set
        test['Test_Preds'] = mod.predict(X_test)
        data_all = pd.concat([test, train], sort=False)

        _ = data_all[['Bottle_Count','Test_Preds']].plot(figsize=(15, 5), style=[".", "-"])
        plt.savefig(r'cache/model_test.png')

        _ = plot_importance(mod, height=0.9)
        plt.savefig(r'cache/importances.png')

        results = mod.evals_result()
        epochs = len(results['validation_0']['error'])
        x_axis = range(0, epochs)
        fig, ax = plt.subplots()
        ax.plot(x_axis, results['validation_0']['mae'], label='Train')
        ax.plot(x_axis, results['validation_1']['mae'], label='Test')
        ax.legend()
        plt.ylabel('Log Loss')
        plt.title('XGBoost Log Loss')
        
        mse = mean_squared_error(y_true=test['Bottle_Count'],
                        y_pred=test['Test_Preds'])
        rmse = sqrt(mean_squared_error(y_true=test['Bottle_Count'],
                        y_pred=test['Test_Preds']))
        mae = mean_absolute_error(y_true=test['Bottle_Count'],
                        y_pred=test['Test_Preds'])

        return mse, rmse, mae
        