"""RFM segmentation analysis: segment value, RFM score heatmap and Pareto curve."""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

from .config import TABLE_DIR
from .db import connect, read_table
from .plotting import ACCENT, PRIMARY, save, set_style

HIGH_VALUE_SEGMENTS = ["Champions"]


def plot_segment_share(segments):
    df = segments.sort_values("pct_revenue")
    y = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(y + 0.2, df["pct_revenue"], height=0.4, color=PRIMARY, label="% of revenue")
    ax.barh(y - 0.2, df["pct_customers"], height=0.4, color=ACCENT, label="% of customers")
    ax.set_yticks(y, df["segment"])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title("RFM segments: share of customers vs share of revenue")
    ax.legend(loc="lower right", frameon=False)
    for yi, v in zip(y, df["pct_revenue"]):
        ax.text(v + 0.5, yi + 0.2, f"{v:.1f}%", va="center", fontsize=9)
    save(fig, "rfm_segment_share.png")


def plot_rfm_heatmap(rfm):
    pivot = rfm.pivot_table(index="r_score", columns="f_score", values="monetary", aggfunc="mean")
    pivot = pivot.sort_index(ascending=False)
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="Blues", cbar_kws={"label": "Avg revenue ($)"}, ax=ax)
    ax.grid(False)
    ax.set_title("Average customer revenue by Recency x Frequency score")
    ax.set_xlabel("Frequency score (5 = most orders)")
    ax.set_ylabel("Recency score (5 = most recent)")
    save(fig, "rfm_heatmap.png")


def plot_pareto(rfm):
    spend = np.sort(rfm["monetary"].to_numpy())[::-1]
    cum_rev = np.cumsum(spend) / spend.sum() * 100
    cum_cust = np.arange(1, len(spend) + 1) / len(spend) * 100
    top20 = cum_rev[int(len(spend) * 0.2) - 1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(cum_cust, cum_rev, color=PRIMARY, lw=2.5)
    ax.plot([0, 100], [0, 100], color="grey", ls="--", lw=1, label="Equal spend")
    ax.axvline(20, color=ACCENT, ls=":", lw=1.5)
    ax.annotate(f"Top 20% of customers\n= {top20:.1f}% of revenue", xy=(20, top20),
                xytext=(35, top20 - 20), arrowprops={"arrowstyle": "->", "color": ACCENT})
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_xlabel("Customers (ranked by revenue)")
    ax.set_ylabel("Cumulative revenue")
    ax.set_title("Revenue concentration (Pareto curve)")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "pareto_curve.png")
    return top20


def main():
    set_style()
    conn = connect()
    rfm = read_table(conn, "rfm_segments")
    segments = read_table(conn, "segment_summary")
    deciles = read_table(conn, "customer_deciles")
    conn.close()

    segments.to_csv(TABLE_DIR / "segment_summary.csv", index=False)
    deciles.to_csv(TABLE_DIR / "customer_deciles.csv", index=False)

    plot_segment_share(segments)
    plot_rfm_heatmap(rfm)
    top20 = plot_pareto(rfm)

    high = segments[segments["segment"].isin(HIGH_VALUE_SEGMENTS)]
    return {
        "customers": len(rfm),
        "high_value_pct_customers": high["pct_customers"].sum(),
        "high_value_pct_revenue": high["pct_revenue"].sum(),
        "top20_pct_revenue": top20,
        "top10_pct_revenue": deciles.loc[deciles["decile"] == 1, "pct_revenue"].item(),
        "segments": segments,
    }


if __name__ == "__main__":
    main()
