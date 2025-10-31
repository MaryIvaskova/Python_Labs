import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

# аргументи
parser = argparse.ArgumentParser(description="Аналіз постачань")
parser.add_argument("file", nargs="?", default="supplies.csv", help="CSV з даними")
args = parser.parse_args()

# завантаження
df = pd.read_csv(args.file)

# numpy обчислення
mean_price = np.mean(df["price_per_unit"])
median_quantity = np.median(df["quantity"])
std_price = np.std(df["price_per_unit"])

# pandas обчислення
df["total_price"] = df["quantity"] * df["price_per_unit"]
top_supplier = df.groupby("supplier")["total_price"].sum().idxmax()
category_sum = df.groupby("category")["quantity"].sum()

# фільтр
low_supply = df[df["quantity"] < 100]
low_supply.to_csv("low_supply.csv", index=False)

# сортування
df_sorted = df.sort_values(by="total_price", ascending=False)
top3 = df_sorted.head(3)

# звіт
report = f"""
АНАЛІТИКА ПОСТАЧАНЬ
-------------------
Середня ціна: {mean_price:.2f}
Медіана кількості: {median_quantity:.2f}
Стандартне відхилення ціни: {std_price:.2f}
Файл з дефіцитними поставками: low_supply.csv
Постачальник з найбільшим прибутком: {top_supplier}

Топ-3 за прибутком:
{top3[['supplier','total_price']].to_string(index=False)}
"""
with open("report.txt", "w", encoding="utf-8") as f:
    f.write(report)

# графік
plt.bar(category_sum.index, category_sum.values, color="steelblue")
plt.title("Кількість препаратів за категоріями")
plt.xlabel("Категорія")
plt.ylabel("Кількість")
plt.tight_layout()
plt.savefig("category_distribution.png")
plt.show()