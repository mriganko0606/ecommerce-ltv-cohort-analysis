"""Monthly cohort retention grid, retention curves and cumulative LTV by cohort."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

from .config import TABLE_DIR
from .db import connect, read_table
from .plotting import ACCENT, MUTED, PRIMARY, save, set_style


def plot_retention_heatmap(grid):
    fig, ax = plt.subplots(figsize=(16, 10))
    sns.heatmap(grid, annot=True, fmt=".0f", cmap="YlGnBu", vmin=0, vmax=40,
                annot_kws={"fontsize": 7}, cbar_kws={"label": "Retention %"},
                linewidths=0.3, linecolor="white", ax=ax)
    ax.grid(False)
    ax.set_title("Monthly cohort retention (% of cohort purchasing in month N)")
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cohort (first purchase month)")
    save(fig, "cohort_retention_heatmap.png")


def plot_retention_curves(retention):
    avg = retention.groupby("month_number")["retention_pct"].mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    for cohort, df in retention.groupby("cohort_month"):
        ax.plot(df["month_number"], df["retention_pct"], color=MUTED, alpha=0.35, lw=1)
    ax.plot(avg.index, avg.values, color=PRIMARY, lw=3, label="Average across cohorts")
    ax.set_ylim(0, 40)
    ax.set_xlim(1, avg.index.max())
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Customers purchasing")
    ax.set_title("Retention curves by cohort (month 1 onwards)")
    ax.legend(frameon=False)
    save(fig, "retention_curves.png")


def plot_cohort_ltv(cohort_ltv):
    # Fill gaps so each cohort has a continuous cumulative curve
    pivot = (cohort_ltv.pivot(index="month_number", columns="cohort_month",
                              values="cumulative_revenue_per_customer").ffill())
    quarterly = [c for c in pivot.columns if c[-2:] in ("01", "04", "07", "10")]
    fig, ax = plt.subplots(figsize=(9, 5))
    palette = sns.color_palette("viridis", len(quarterly))
    for color, cohort in zip(palette, quarterly):
        series = pivot[cohort].dropna()
        last_month = 24 - (int(cohort[:4]) - 2023) * 12 - int(cohort[5:])
        series = series[series.index <= last_month]
        ax.plot(series.index, series.values, color=color, lw=2, label=cohort)
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cumulative revenue per customer")
    ax.set_title("Lifetime value build-up by acquisition cohort")
    ax.legend(title="Cohort", frameon=False, ncol=2, fontsize=9)
    save(fig, "cohort_cumulative_ltv.png")


def main():
    set_style()
    conn = connect()
    retention = read_table(conn, "cohort_retention")
    cohort_ltv = read_table(conn, "cohort_ltv")
    conn.close()

    grid = retention.pivot(index="cohort_month", columns="month_number", values="retention_pct")
    grid.to_csv(TABLE_DIR / "cohort_retention_grid.csv")
    cohort_ltv.to_csv(TABLE_DIR / "cohort_ltv.csv", index=False)

    plot_retention_heatmap(grid)
    plot_retention_curves(retention)
    plot_cohort_ltv(cohort_ltv)

    avg = retention.groupby("month_number")["retention_pct"].mean()
    ltv_12 = cohort_ltv[cohort_ltv["month_number"] <= 12]
    ltv_12 = ltv_12[ltv_12["cohort_month"] <= "2023-12"]  # cohorts with 12 full months observed
    return {
        "retention_m1": avg.get(1),
        "retention_m3": avg.get(3),
        "retention_m6": avg.get(6),
        "retention_m12": avg.get(12),
        "ltv_12m_per_customer": ltv_12.groupby("cohort_month")["cumulative_revenue_per_customer"].max().mean(),
    }


if __name__ == "__main__":
    main()
