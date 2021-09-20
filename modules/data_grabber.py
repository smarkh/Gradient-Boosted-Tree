import pandas as pd 
from sqlalchemy import create_engine
import urllib
import requests as req


class data_grabber:
    def __init__(self, server, db):
        params = urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server};'
                 f'SERVER={server};'
                 f'DATABASE={db};'
                 'Trusted_Connection=yes;')
        self.engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params) 

    def get(self, sql, key):
        data = self.get_bottles(sql)
        promos = self.get_promos(key)

        return data, promos

    def get_bottles(self, sql):
        data = pd.read_sql(con=self.engine, sql=sql)
        data["Doc_Date"] = pd.to_datetime(data["Doc_Date"])
        data.set_index("Doc_Date", inplace=True)
        
        return data
    
    def get_promos(self, key):
        # this may need to change in the future when there are more than 100 promotions to look at because api will only return 100 per page.
        param = {
            "api_key": key,
            "filterByFormula":'AND({Product or Promotion?}="Promotion", NOT(FIND("Avana", {Product/Promo Name})), NOT(FIND("Whiskware", {Product/Promo Name})), NOT(FIND("Owala", {Product/Promo Name})), NOT(FIND("Whiskware", {Product/Promo Name})))',
            "fields": ["Brand", "Product or Promotion?", "Product/Promo Name", "Promo End Date", "Promo Start Date"],
        }
        base_url = 'https://api.airtable.com/v0/appbEeMjuLcbmMWxB/Master%20View?'
        response = req.get(base_url, params=param)

        promos = self.parse_promos(response)
        return promos
        
    def parse_promos(self, response):
        records = response.json()["records"]
        promos = {}
        for i in range(len(records)):
            if "Promo End Date" in records[i]["fields"]:
                rec = records[i]["id"]
                start = records[i]["fields"]["Promo Start Date"][0:10]
                end = records[i]["fields"]["Promo End Date"]

                promos[rec] = {
                    "start": start,
                    "end": end,
                }
        return promos