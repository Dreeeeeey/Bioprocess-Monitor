import pandas as pd

import matplotlib.pyplot as plt

import matplotlib.ticker as ticker

import numpy as np

from constants import PH_LIMITS, TEMPERATURE_LIMITS


class BioprocessMonitor:

    def __init__(self, filepath, ph_lims=PH_LIMITS, temperature_lims=TEMPERATURE_LIMITS):

        self.Up_pH_Lims = ph_lims[1]
        self.Low_pH_Lims = ph_lims[0]
        self.Up_temp_Lims = temperature_lims[1]
        self.Low_temp_Lims = temperature_lims[0]

        self.filepath = filepath
        self.ph_lims = ph_lims
        self.temperature_lims = temperature_lims
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)

        self.df = pd.read_csv(filepath)

    def extract_batch(self, batch_id):

        df_batch = self.df[self.df["batch_id"] == batch_id]

        return df_batch

    def optimal_ph_mask(self, df_batch):

        High_ph_mask = df_batch["pH"] >= self.Low_pH_Lims
        Low_ph_mask = df_batch["pH"] <= self.Up_pH_Lims
        optimal_ph_mask = High_ph_mask & Low_ph_mask

        return optimal_ph_mask

    def optimal_temperature_mask(self, df_batch):

        High_temp_mask = df_batch["temperature_C"] >= self.Low_temp_Lims
        Low_temp_mask = df_batch["temperature_C"] <= self.Up_temp_Lims
        optimal_temperature_mask = High_temp_mask & Low_temp_mask

        return optimal_temperature_mask

    def get_n_batches(self):

        batch_column = self.df.loc[:, "batch_id"]

        n_batches = batch_column.nunique()

        return n_batches

    def export_dashboard(self, batch_id, filepath):

        df_batch = self.extract_batch(batch_id)
        temp_mask = self.optimal_temperature_mask(df_batch)
        ph_mask = self.optimal_ph_mask(df_batch)

        x = df_batch["time_h"]

        COLORS = ["tab:olive", "tab:blue", "tab:orange"]
        MARKERS = ["o", "p", "^"]
        kwargs_scatter = dict(s=20, edgecolors="black", linewidth=0.5)

        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 6), dpi=600, layout="constrained")

        # top right

        conc_columns = ["C_glucose_g_L^-1", "C_biomass_g_L^-1", "C_product_g_L^-1"]  # adjust names as needed
        for i, col in enumerate(conc_columns):
            axes[0, 0].scatter(
                x, df_batch[col],
                label=col,
                color=COLORS[i % len(COLORS)], marker=MARKERS[i % len(MARKERS)], **kwargs_scatter)
        axes[0, 0].set_ylabel("Concentration (g/L)")
        axes[0, 0].legend()

        # top right

        temp = df_batch["temperature_C"]
        axes[0, 1].scatter(x[temp_mask], temp[temp_mask], color="green", marker="o", label="Optimal", **kwargs_scatter)
        axes[0, 1].scatter(x[~temp_mask], temp[~temp_mask], color="red", marker="X", label="Out of Range",
                           **kwargs_scatter)
        axes[0, 1].set_ylabel("Temperature (°C)")
        axes[0, 1].legend()

        # bottom left

        ph = df_batch["pH"]
        axes[1, 0].scatter(x[ph_mask], ph[ph_mask], color="green", marker="o", label="Optimal", **kwargs_scatter)
        axes[1, 0].scatter(x[~ph_mask], ph[~ph_mask], color="red", marker="X", label="Out of Range", **kwargs_scatter)
        axes[1, 0].set_ylabel("pH")
        axes[1, 0].legend()

        # bottom right

        axes[1, 1].scatter(x, df_batch["DO_percent"], color="tab:purple", marker="o", label="DO",
                           **kwargs_scatter)
        axes[1, 1].set_ylabel("Dissolved Oxygen (%)")

        for ax in axes.flat:
            ax.set_xlabel("time(h)")
            ax.xaxis.set_major_locator(ticker.MultipleLocator(6))

        fig.savefig(filepath)
        plt.close(fig)

    def export_summary(self, filepath):
        records = []

        unique_batches = self.df["batch_id"].unique()

        for batch_id in unique_batches:
            df_batch = self.extract_batch(batch_id)
            ph_opt_pct = round(self.optimal_ph_mask(df_batch).mean() * 100, 2)
            temp_opt_pct = round(self.optimal_temperature_mask(df_batch).mean() * 100, 2)
            final_prod = df_batch["C_product_g_L^-1"].iloc[-1]

            records.append({
            "batch_id": batch_id,
            "ph_optimal_percent": ph_opt_pct,
            "temperature_optimal_percent": temp_opt_pct,
            "C_product_g_L^-1_final": final_prod
            })

        summary_df = pd.DataFrame(records)
        summary_df.to_csv(filepath, index=False)
