from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent

#     ОДИН ПРЕДМЕТ (Item)
@dataclass(order=True)
class Item:
    sort_index: tuple = field(init=False, repr=False)

    name: str
    category: str
    quantity: int
    value: float
    condition: str
    location: str
    added_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __post_init__(self):
        # сортування за category → value
        self.sort_index = (self.category.lower(), self.value)

    def total_value(self) -> float:
        return self.quantity * self.value

    def __str__(self):
        return f"[{self.category}] {self.name} ({self.quantity} шт.) — {self.value} грн/шт, стан: {self.condition}"


#          ІНВЕНТАР
@dataclass
class Inventory:
    items: List[Item] = field(default_factory=list)

    # CRUD
    def add_item(self, item: Item):
        self.items.append(item)

    def remove_item(self, name: str):
        self.items = [i for i in self.items if i.name != name]

    def find_by_category(self, category: str) -> List[Item]:
        return [i for i in self.items if i.category.lower() == category.lower()]

    def total_inventory_value(self) -> float:
        return sum(i.total_value() for i in self.items)

    #     SAVE / LOAD CSV
    def save_to_csv(self, filename: str):
        filepath = BASE_DIR / filename
        with filepath.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "category", "quantity", "value",
                             "condition", "location", "added_at"])
            for item in self.items:
                writer.writerow([
                    item.name, item.category, item.quantity,
                    item.value, item.condition, item.location,
                    item.added_at
                ])

    def load_from_csv(self, filename: str):
        filepath = BASE_DIR / filename
        self.items.clear()
        with filepath.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.items.append(
                    Item(
                        name=row["name"],
                        category=row["category"],
                        quantity=int(row["quantity"]),
                        value=float(row["value"]),
                        condition=row["condition"],
                        location=row["location"],
                        added_at=row["added_at"]
                    )
                )

    #   ФІЛЬТРАЦІЯ ТА СОРТУВАННЯ
    def filter_items(self, **kwargs) -> List[Item]:
        """
        filter_items(name="...", category="...", condition="...")
        повертає предмети, де всі поля збігаються.
        """
        result = self.items
        for field_name, field_value in kwargs.items():
            result = [
                i for i in result
                if str(getattr(i, field_name)).lower() == str(field_value).lower()
            ]
        return result

    def sort_items(self):
        """Використовує Item.sort_index"""
        self.items.sort()

    #         SUMMARY
    def export_summary(self) -> str:
        categories = {}
        for i in self.items:
            categories[i.category] = categories.get(i.category, 0) + 1

        lines = ["ЗВІТ ЗА КАТЕГОРІЯМИ:"]
        for cat, count in categories.items():
            lines.append(f"{cat}: {count} предметів")

        return "\n".join(lines)

#     ДЕМОНСТРАЦІЯ
if __name__ == "__main__":
    inv = Inventory()

    inv.add_item(Item("Гаечний ключ", "інструменти", 3, 15.0, "уживаний", "гараж"))
    inv.add_item(Item("Провід", "електроніка", 10, 8.5, "новий", "комора"))
    inv.add_item(Item("Мідь", "металобрухт", 5, 30.0, "уживаний", "сарай"))

    print("--- Усі предмети ---")
    for i in inv.items:
        print(i)

    print("\nСумарна вартість:", inv.total_inventory_value())

    print("\n--- Інструменти ---")
    for i in inv.find_by_category("інструменти"):
        print(i)

    print("\n--- Summary ---")
    print(inv.export_summary())

    inv.save_to_csv("inventory.csv")
    print("\nФайл збережено → inventory.csv")