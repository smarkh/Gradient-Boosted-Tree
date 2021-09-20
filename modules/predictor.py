import xgboost as xgb
import pandas as pd
from datetime import datetime as dt
from datetime import *
from dateutil.relativedelta import *
import matplotlib.pyplot as plt
from dateutil.relativedelta import *

class predictor:
    def __init__(self, reg):
        self.reg = reg
        self.future = []

    def predict(self, bottles, promos, days=200):
        self.bottles = bottles
        self.promos = promos

        today, yesterday, two_ago = self.get_start()

        new_dates = pd.DataFrame(pd.date_range(today, periods=days).tolist())

        new_dates.columns = ["Doc_Date"]
        new_dates["Doc_Date"] = pd.to_datetime(new_dates["Doc_Date"])
        new_dates.set_index("Doc_Date", inplace=True)
        x_future = self.create_features(new_dates, promos)
        new_dates = pd.DataFrame(pd.date_range(today, periods=days).tolist())

        # add first prev day sale from historical data
        x_future['prev_day_count'][today] = bottles["Bottle_Count"][yesterday]
        x_future['prev_2_day_count'][today] = bottles["Bottle_Count"][two_ago]
        x_future.reset_index(drop=True, inplace=True)

        # predict
        future_preds = []
        for i in range(days):
            pred = self.reg.predict(x_future[i:i+1])
            future_preds.append(pred[0])
            x_future["prev_day_count"][i+1] = pred[0]
            x_future["prev_2_day_count"][i+2] = pred[0]

        # put predictions into useful format
        future_preds = pd.DataFrame(future_preds, columns=["Future_Preds"])
        future_preds["Doc_Date"] = pd.date_range(today, periods=days).tolist()
        future_preds["Doc_Date"] = pd.to_datetime(future_preds["Doc_Date"])
        future_preds.set_index("Doc_Date", inplace=True)
        future_preds.to_excel(r'cache/future_preds.xlsx')

        bottles_train, bottles_test = self.split(bottles)

        bottles_all = pd.concat([future_preds, bottles_test, bottles_train], sort=False)
        bottles_all.sort_index(inplace=True)

        # make plots
        self.plots_and_metrics(bottles_all)
        self.future = future_preds

    def split(self, data):
        start_date = '2017-10-03'
        dates = pd.date_range(start_date, periods=len(data)).tolist()
        rw = round(len(data)*.7)
        split_date = dates[rw]
        data_train = data.loc[data.index <= split_date].copy()
        data_test = data.loc[data.index > split_date].copy()

        return data_train, data_test

    def plots_and_metrics(self, bottles_all):
        # add max ability for fulfilment team.
        bottles_all["Work_Load_Threshold"] = [800]*len(bottles_all)

        # plot predictions
        f, ax = plt.subplots(1)
        f.set_figheight(5)
        f.set_figwidth(15)
        _ = bottles_all[['Bottle_Count', 'Future_Preds', "Work_Load_Threshold"]].plot(ax=ax,
                                                    style=['.','-', ':'])
        #ax.set_xlim('06-01-2015', '04-01-2017') 
        ax.set_ylim(0, 2000)
        plt.suptitle('Predictions of Next 200 Days')
        plt.savefig(r'cache/future.png')

    def get_start(self):
        cur_day = datetime.date(dt.now())
        yesterday = cur_day- timedelta(days = 1) 
        two_ago = cur_day- timedelta(days = 2) 
        return str(cur_day), str(yesterday), str(two_ago)
        #return "2020-06-16", "2020-06-15"

    def predict_one(self, date):
        try:
            pred = self.future.loc[date]["Future_Preds"]
            return str(int(round(pred)))
        except:
            return False

        # possibly change to actually predict by using previous years count as previous days count

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
        print(X.head())
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