from tkinter import *
import pandas as pd
import matplotlib
import matplotlib.figure as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from os import listdir
from os.path import isfile, join, exists
import re

matplotlib.use('TkAgg')


class MainClass:
    def __init__(self, window):
        self.get_filenames()
        self.window = window
        self.dd_1_value = StringVar()
        self.dd_1_value.set("2012 Triumph Street Triple R")
        self.dd_1 = OptionMenu(window, self.dd_1_value, *self.bikes.keys()).pack()
        self.plot_button_1 = Button(window, text="Plot", command=self.plot_button_1_pressed).pack()
        self.clear_plot_button_1 = Button(window, text="Clear", command=self.clear_plot_button_1_pressed).pack()
        self.dd_2_value = StringVar()
        self.dd_2_value.set("Choose Bike")
        self.dd_2 = OptionMenu(window, self.dd_2_value, *self.bikes.keys()).pack()
        self.plot_button_2 = Button(window, text="Plot", command=self.plot_button_2_pressed).pack()
        self.clear_plot_button_2 = Button(window, text="Clear", command=self.clear_plot_button_2_pressed).pack()
        self.init_plot()

    def init_plot(self):
        self.fig = plt.Figure(figsize=(12, 6))

        self.a = self.fig.add_subplot(121)
        self.a.set_xlim(0, 18000)
        self.a.set_ylim(0, 200)
        self.a.set_xlabel("RPM")
        self.a.set_ylabel("Power/Torque (hp, ft-lb)")
        self.a.set_title("Horsepower Torque Curves")
        self.power_1, = self.a.plot([], [], 'r-')
        self.torque_1, = self.a.plot([], [], 'r--')
        self.power_2, = self.a.plot([], [], 'b-')
        self.torque_2, = self.a.plot([], [], 'b--')

        self.b = self.fig.add_subplot(122)
        self.b.set_xlim(0, 180)
        self.b.set_ylim(0, 1.8)
        self.b.set_xlabel("Speed (mph)")
        self.b.set_ylabel("Thrust (gs)")
        self.b.set_title("Thrust Curves")

        self.thrust_1_1, = self.b.plot([], [], 'r-')
        self.thrust_1_2, = self.b.plot([], [], 'r-')
        self.thrust_1_3, = self.b.plot([], [], 'r-')
        self.thrust_1_4, = self.b.plot([], [], 'r-')
        self.thrust_1_5, = self.b.plot([], [], 'r-')
        self.thrust_1_6, = self.b.plot([], [], 'r-')

        self.thrust_2_1, = self.b.plot([], [], 'b-')
        self.thrust_2_2, = self.b.plot([], [], 'b-')
        self.thrust_2_3, = self.b.plot([], [], 'b-')
        self.thrust_2_4, = self.b.plot([], [], 'b-')
        self.thrust_2_5, = self.b.plot([], [], 'b-')
        self.thrust_2_6, = self.b.plot([], [], 'b-')

        self.power_wheelies, = self.b.plot(range(200), 200 * [1], 'k:')
        self.power_wheelies.set_label("Power Wheelie Line")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def get_filenames(self):
        filenames = [f for f in listdir("./dyno_csvs") if isfile(join("./dyno_csvs", f))]
        print(filenames)
        displaynames = []
        for name in filenames:
            if re.split(r"[.]", name, maxsplit=1)[1] == "csv":
                displaynames.append(name.replace("_", " ").rstrip(".csv"))
            else:
                filenames.remove(name)

        self.bikes = dict(zip(displaynames, filenames))

    def get_dyno(self, filename):
        df = pd.read_csv(r"./dyno_csvs/" + filename, names=["rpm", "hp"])
        df["torque"] = df["hp"] * 5252 / df["rpm"]
        return df

    def get_specs(self, filename):
        df = pd.read_csv(r"./bike_specs/" + filename)
        return df

    def build_thrust(self, filename):
        if exists("./bike_specs/" + filename):
            dyno = self.get_dyno(filename)
            specs = self.get_specs(filename)
            gears = [specs.loc[0, "primary"] * specs.loc[0, "final"] * g for g in [
                specs.loc[0, "gear1"],
                specs.loc[0, "gear2"],
                specs.loc[0, "gear3"],
                specs.loc[0, "gear4"],
                specs.loc[0, "gear5"],
                specs.loc[0, "gear6"]
            ]]
            rider_mass = 180
            diameter = specs.loc[0, "diam"] + 2 * specs.loc[0, "width"] * (specs.loc[0, "side"] / 100) / 25.4
            circumference = 3.1415 * diameter
            speed_factor = 60 * circumference / 12 / 5280
            min_rpm = min(dyno["rpm"])
            max_rpm = max(dyno["rpm"])
            min_speeds = []
            max_speeds = []
            for g in gears:
                min_speeds.append(speed_factor * min_rpm / g)
                max_speeds.append(speed_factor * max_rpm / g)
            min_speed = min_speeds[0]
            max_speed = max_speeds[5]

            resolution = 2

            thrust_df = pd.DataFrame(
                index=[n / resolution for n in range(int(min_speed) * resolution, int(max_speed) * resolution)],
                columns=range(6)
            )
            for speed in range(int(min_speed) * resolution, int(max_speed) * resolution):
                speed = speed / resolution
                for gear in range(6):
                    rpm = speed / speed_factor * gears[gear]
                    if min_rpm <= rpm <= max_rpm:
                        engine_torque = np.interp(rpm, dyno["rpm"], dyno["torque"])
                        wheel_torque = engine_torque * gears[gear]
                        wheel_force = wheel_torque / (diameter / 24)
                        engine_thrust = wheel_force / (rider_mass + specs.loc[0, "mass"])
                        drag_force = 0.5 * 1.293 * speed ** 2 * specs.loc[0, "drag"] * 0.04493
                        drag_thrust = drag_force / (rider_mass + specs.loc[0, "mass"])
                        thrust_df.at[speed, gear] = engine_thrust - drag_thrust

            return thrust_df
        else:
            thrust_df = pd.DataFrame(
                index=range(0, 200, 1),
                columns=range(6)
            )
            return thrust_df

    def plot_button_1_pressed(self):
        filename = self.bikes[self.dd_1_value.get()]
        self.dyno_df_1 = self.get_dyno(filename)
        self.thrust_df_1 = self.build_thrust(filename)

        self.power_1.set_data(self.dyno_df_1["rpm"], self.dyno_df_1["hp"])
        self.torque_1.set_data(self.dyno_df_1["rpm"], self.dyno_df_1["torque"])
        self.power_1.set_label(self.dd_1_value.get() + " -- Power")
        self.torque_1.set_label(self.dd_1_value.get() + " -- Torque")

        self.thrust_1_1.set_data(self.thrust_df_1.index, self.thrust_df_1[0])
        self.thrust_1_2.set_data(self.thrust_df_1.index, self.thrust_df_1[1])
        self.thrust_1_3.set_data(self.thrust_df_1.index, self.thrust_df_1[2])
        self.thrust_1_4.set_data(self.thrust_df_1.index, self.thrust_df_1[3])
        self.thrust_1_5.set_data(self.thrust_df_1.index, self.thrust_df_1[4])
        self.thrust_1_6.set_data(self.thrust_df_1.index, self.thrust_df_1[5])
        self.thrust_1_1.set_label(self.dd_1_value.get())

        self.a.legend()
        self.b.legend()
        self.canvas.draw()

    def clear_plot_button_1_pressed(self):
        self.power_1.set_data([], [])
        self.torque_1.set_data([], [])

        self.thrust_1_1.set_data([], [])
        self.thrust_1_2.set_data([], [])
        self.thrust_1_3.set_data([], [])
        self.thrust_1_4.set_data([], [])
        self.thrust_1_5.set_data([], [])
        self.thrust_1_6.set_data([], [])

        self.canvas.draw()

    def plot_button_2_pressed(self):
        filename = self.bikes[self.dd_2_value.get()]
        self.dyno_df_2 = self.get_dyno(filename)
        self.thrust_df_2 = self.build_thrust(filename)

        self.power_2.set_data(self.dyno_df_2["rpm"], self.dyno_df_2["hp"])
        self.torque_2.set_data(self.dyno_df_2["rpm"], self.dyno_df_2["torque"])
        self.power_2.set_label(self.dd_2_value.get() + " -- Power")
        self.torque_2.set_label(self.dd_2_value.get() + " -- Torque")

        self.thrust_2_1.set_data(self.thrust_df_2.index, self.thrust_df_2[0])
        self.thrust_2_2.set_data(self.thrust_df_2.index, self.thrust_df_2[1])
        self.thrust_2_3.set_data(self.thrust_df_2.index, self.thrust_df_2[2])
        self.thrust_2_4.set_data(self.thrust_df_2.index, self.thrust_df_2[3])
        self.thrust_2_5.set_data(self.thrust_df_2.index, self.thrust_df_2[4])
        self.thrust_2_6.set_data(self.thrust_df_2.index, self.thrust_df_2[5])
        self.thrust_2_1.set_label(self.dd_2_value.get())

        self.a.legend()
        self.b.legend()
        self.canvas.draw()

    def clear_plot_button_2_pressed(self):
        self.power_2.set_data([], [])
        self.torque_2.set_data([], [])

        self.thrust_2_1.set_data([], [])
        self.thrust_2_2.set_data([], [])
        self.thrust_2_3.set_data([], [])
        self.thrust_2_4.set_data([], [])
        self.thrust_2_5.set_data([], [])
        self.thrust_2_6.set_data([], [])

        self.canvas.draw()


if __name__ == "__main__":
    window = Tk()
    start = MainClass(window)
    window.mainloop()

# Ideas
# Implement final drive adjustments
# add x-y speed curves
