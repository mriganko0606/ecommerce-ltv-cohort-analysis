"""Monthly revenue trend, month-over-month growth and new vs returning customers."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from .config import TABLE_DIR
from .db import connect, read_table
from .plotting import ACCENT, PRIMARY, save, set_style


def plot_revenue_mom(kpis):
    fig, ax = plt.subplots(figsize=(12, 5))
    x = range(len(kpis))
    ax.bar(x, kpis["revenue"], color=PRIMARY, alpha=0.85, label="Revenue")
    ax.plot(x, kpis["revenue_3m_avg"], color="black", lw=1.5, ls="--", label="3-month avg")
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax.set_xticks(list(x), kpis["order_month"], rotation=60, fontsize=8)
    ax.set_ylabel("Revenue")

    ax2 = ax.twinx()
    ax2.plot(x, kpis["revenue_mom_pct"], color=ACCENT, marker="o", lw=2, label="MoM growth %")
    ax2.axhline(0, color=ACCENT, lw=0.8, alpha=0.5)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax2.grid(False)
    ax2.set_ylabel("Month-over-month growth")

    lines = ax.get_legend_handles_labels()
    lines2 = ax2.get_legend_handles_labels()
    ax.legend(lines[0] + lines2[0], lines[1] + lines2[1], loc="upper left", frameon=False)
    ax.set_title("Monthly revenue and month-over-month growth")
    save(fig, "monthly_revenue_mom.png")


def plot_new_vs_returning(kpis):
    fig, ax = plt.subplots(figsize=(12, 5))
    x = range(len(kpis))
    ax.bar(x, kpis["new_customers"], color=ACCENT, label="New customers")
    ax.bar(x, kpis["returning_customers"], bottom=kpis["new_customers"], color=PRIMARY,
           label="Returning customers")
    ax.set_xticks(list(x), kpis["order_month"], rotation=60, fontsize=8)
    ax.set_ylabel("Active customers")
    ax.set_title("Active customers per month: new vs returning")
    ax.legend(frameon=False, loc="upper left")
    save(fig, "new_vs_returning.png")


def main():
    set_style()
    conn = connect()
    kpis = read_table(conn, "monthly_kpis")
    conn.close()
    kpis.to_csv(TABLE_DIR / "monthly_kpis.csv", index=False)

    plot_revenue_mom(kpis)
    plot_new_vs_returning(kpis)

    by_year = kpis.groupby(kpis["order_month"].str[:4])["revenue"].sum()
    return {
        "revenue_total": kpis["revenue"].sum(),
        "orders_total": kpis["orders"].sum(),
        "aov": kpis["revenue"].sum() / kpis["orders"].sum(),
        "gross_margin_pct": kpis["gross_profit"].sum() / kpis["revenue"].sum() * 100,
        "revenue_2023": by_year.get("2023"),
        "revenue_2024": by_year.get("2024"),
        "yoy_growth_pct": (by_year.get("2024") / by_year.get("2023") - 1) * 100,
        "avg_mom_growth_2024": kpis.loc[kpis["order_month"].str.startswith("2024"), "revenue_mom_pct"].mean(),
    }


if __name__ == "__main__":
    main()
