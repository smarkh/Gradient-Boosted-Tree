import matplotlib.pyplot as plt

class formatter:
    def __init__(self):
        pass

    def prep(self, data):
        prpt = self.add_prev_day_count(data)
        return prpt

    def add_prev_day_count(self, data):
        prv_dy = list(data["Bottle_Count"][1:])
        prv_dy = prv_dy + [None]
        prv_two_dy = list(data["Bottle_Count"][2:])
        prv_two_dy = prv_two_dy + [None] + [None]
        data["Prev_Day_Count"] = prv_dy
        data["Prev_2_Day_Count"] = prv_two_dy
        return data

    def plots(self, data):
        pass