import os
# формат рядка у файлі: Назва|Кількість|Ціна_з_комою  (напр. Бляшанка|5|2,50)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(BASE_DIR, "мусорка.csv")

def to_dec_comma(x: float) -> str:
    return f"{float(x):.2f}".replace(".", ",")

def from_dec_comma(s: str) -> float:
    return float((s or "").replace(" ", "").replace(",", "."))

def norm_name(name: str) -> str:
    return " ".join(name.strip().lower().split())

def price_str(v: float) -> str:
    return f"{float(v):.2f}"

#  модель 
class JunkItem:
    def __init__(self, name, quantity, value):
        self.name = name.strip()
        self.quantity = int(quantity)
        self.value = float(value)

    def line(self):
        return f"{self.name}|{self.quantity}|{to_dec_comma(self.value)}"

    @staticmethod
    def from_line(line):
        parts = line.strip().split("|")
        if len(parts) != 3:
            return None
        name, q, v = parts
        try:
            q = int(q)
            v = from_dec_comma(v)
            return JunkItem(name, q, v)
        except:
            return None

#  ключ 
def item_key(it: JunkItem) -> tuple[str, str]:
    return (norm_name(it.name), price_str(it.value))

def merge_item(items, new_item):
    """Об'єднати, якщо (нормалізована назва, ціна у 2 знаки) збігаються; інакше додати."""
    k = item_key(new_item)
    for it in items:
        if item_key(it) == k:
            it.quantity += new_item.quantity
            return
    items.append(new_item)

def merge_all(items):
    acc = []
    for it in items:
        merge_item(acc, it)
    return acc

#  читання та запис
def save_items(items, filename=DEFAULT_FILE):
    items = merge_all(items)
    with open(filename, "w", encoding="utf-8") as f:
        for it in items:
            f.write(it.line() + "\n")
    print(f"Файл створено або оновлено: {filename}")

def load_items(filename=DEFAULT_FILE):
    items = []
    bad = 0
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                it = JunkItem.from_line(line)
                if it:
                    merge_item(items, it)
                else:
                    bad += 1
                    print(f"Рядок {i} пропущено (зіпсовані дані)")
        print(f"Прочитано {len(items)} валідних записів, помилкових: {bad}")
    except FileNotFoundError:
        print(f"Файл '{filename}' не знайдено — буде створено після збереження.")
    return items

#  формат таблиці 
def show_items(items):
    if not items:
        print("(порожньо)\n")
        return
    print("\nНазва                 | К-сть |  Ціна  |  Сума ")
    print("------------------------------------------------")
    total = 0.0
    for it in items:
        s = it.quantity * it.value
        total += s
        print(f"{it.name:<21} | {it.quantity:>5} | {to_dec_comma(it.value):>6} | {to_dec_comma(s):>6}")
    print("------------------------------------------------")
    print(f"Разом: {to_dec_comma(total)}\n")

def menu():
    items = []
    while True:
        print("Меню:")
        print("1. Додати предмет")
        print("2. Показати предмети")
        print("3. Зберегти у файл")
        print("4. Відкрити з файлу (замінює поточний список)")
        print("5. Демо (3 предмети, сумується)")
        print("6. Вийти")
        choice = input("Ваш вибір: ").strip()

        if choice == "1":
            name = input("Назва: ").strip()
            q = input("Кількість (int): ").strip()
            v = input("Ціна (кома або крапка): ").strip()
            try:
                it = JunkItem(name, int(q), from_dec_comma(v))
                merge_item(items, it)
                print("Додано або оновлено.\n")
            except:
                print("Помилка вводу.\n")

        elif choice == "2":
            show_items(items)

        elif choice == "3":
            save_items(items, DEFAULT_FILE)

        elif choice == "4":
            items = load_items(DEFAULT_FILE)
            show_items(items)

        elif choice == "5":
            merge_item(items, JunkItem("Бляшанка", 5, 2.50))
            merge_item(items, JunkItem("Стара плата", 3, 7.80))
            merge_item(items, JunkItem("Купка дротів", 10, 1.20))
            print("Демо-набір додано (суми оновлено)")
            show_items(items)

        elif choice == "6":
            print("Готово.")
            break

        else:
            print("Невірний вибір.\n")

if __name__ == "__main__":
    menu()