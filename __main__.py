# import libraries
import modules.data_grabber as dg
import modules.formatter as fmt
import modules.trainer as trnr
import modules.predictor as prd

import matplotlib
import matplotlib.pyplot as plt
import yaml
from tkinter import *
from tkinter import messagebox
import pandas as pd
#import pkg_resources.py2_warn
from functools import partial

def main():
    start.destroy()
    step = Label(text="Gathering Data", font="Times 12")
    step.pack(anchor=W)
    window.update()
    # get config data
    with open(r'config/config.yml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # grab data from db and airtable
    fetcher = dg.data_grabber(config["server_info"]["server"], config["server_info"]["database"])
    bottles, promos = fetcher.get(config["sql"]["orders"], config["api_keys"]["air_table"])
    info = Label(text=f"{len(bottles)} days of data gathered", font="Times 15", fg="blue")
    info.pack(anchor=W)

    step = Label(text="Formatting Data", font="Times 12")
    step.pack(anchor=W)

    window.update()
    # format data
    formatter = fmt.formatter()
    bottles = formatter.prep(bottles)
    bottles.to_excel(r'cache/historical_actuals.xlsx')

    step = Label(text="Training Model", font="Times 12")
    step.pack(anchor=W)
    window.update()
    # train model
    trainer = trnr.trainer()
    mod, mse, rmse, mae = trainer.train(bottles, promos)
    full_mod = trainer.train_all(bottles, promos)

    info = Label(text=f"Model Metrics: MSE = {round(mse,2)}, RMSE = {round(rmse,2)}, MAE = {round(mae,2)}", font="Times 15", fg="blue")
    info.pack(anchor=W)

    step = Label(text="Saving Model", font="Times 12")
    step.pack(anchor=W)
    window.update()
    # save model and data
    mod.save_model(r"cache/model")
    full_mod.save_model(r"cache/full_model")
    bottles.to_csv(r"cache/bottles")

    step = Label(text="Predicting the Future (200 days)", font="Times 12")
    step.pack(anchor=W)
    window.update()
    # predict future
    global Gpredictor
    predictor = prd.predictor(full_mod)
    predictor.predict(bottles=bottles, promos=promos, days=200)
    Gpredictor = predictor

    # ask if user would like the plots to be shown
    inp = messagebox.askyesno(message="Prediction Complete.\nWould you like to see the model charts?", title="Plots")
    if inp == True:
        plt.ion()
        plt.show()

    # as if a specific day prediction is wanted
    Label(window,
        text="To predict a specific day enter a date in the format yyyy-mm-dd.", font="Times 15").pack()
    Label(window,
        text="Note: The date must be within 200 days", font="Times 12").pack()
    txt = Entry(window, width=10)
    global tmp 
    tmp = txt
    txt.pack()
    Button(window, text="Predict", command=pred_one, padx=10).pack()
    window.update()
    # change this to be in the gui

def pred_one():
    global tmp
    global Gpredictor
    txt = tmp
    predictor = Gpredictor

    prd = predictor.predict_one(txt.get()) 

    if prd:
        Label(window,
            text=f"{txt.get()}: {prd} orders", font="Times 12").pack(side="top", fill="both", expand=True, padx=0, pady=0)
    else:
        Label(window,
            text=f"That was not a valid date. It Needs to be in (yyyy-mm-dd) format and within the next 200 days", font="Times 12").pack(side="top", fill="both", expand=True, padx=0, pady=0)
    window.update()

def quit_process():
    window.quit()
    window.destroy()

# get tkinter module running
tmp = None
Gpredictor = None
window = Tk()
window.title("Forecaster")
window.geometry("600x500")
window.resizable(False, True)
header = Label(text="Forecaster", font="Times 22 bold underline", padx=20, pady=20)
header.pack()
start = Button(window, text="Begin", command=main, padx=2, bg="green")
end = Button(window, text="Exit", command=quit_process, padx=7, bg="red")
start.pack()
end.pack(anchor=S)

window.mainloop()
