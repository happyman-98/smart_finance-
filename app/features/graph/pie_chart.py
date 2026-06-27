import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("business_expenses_june2026.csv")

by_cat = (
    df.groupby("Category")["Amount_USD"]
      .sum()
      .sort_values(ascending=False)
) ##  features in accending order

total = by_cat.sum()

colors = plt.cm.Set3.colors

fig, ax = plt.subplots(figsize=(11,8))

wedges, _, _ = ax.pie(
    by_cat,
    startangle=90,
    counterclock=False,
    colors=plt.cm.Pastel1.colors,
    wedgeprops=dict(width=0.42, edgecolor="white"),
    autopct="%1.1f%%",
    pctdistance=0.78
)

ax.text(
    0, 0,
    f"${total:,.0f}\nTotal",
    ha="center",
    va="center",
    fontsize=18,
    weight="bold"
)

ax.legend(
    wedges,
    [f"{c}  (${v:,.0f})" for c, v in zip(by_cat.index, by_cat.values)],
    title="Categories",
    loc="center left",
    bbox_to_anchor=(1, 0.5),
    frameon=False
)

ax.set_title("Business Expenses by Category", fontsize=18, weight="bold")
ax.set_aspect("equal")

plt.tight_layout()
plt.show()