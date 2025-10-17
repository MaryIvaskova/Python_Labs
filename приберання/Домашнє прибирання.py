import os, csv

# === Налаштування ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(BASE_DIR, "мусорка.csv")   # той самий файл, але тепер валідний CSV
SEP = ','     # єдиний сепаратор полів у файлі
PREC = 2      # кількість знаків після крапки на виводі

def norm_name(name: str) -> str:
    return " ".join(name.strip().lower().split())

def f2(x: float) -> str:
    return f"{float(x):.{PREC}f}"

# === Модель ===
class JunkItem:
    def __init__(self, name, quantity, value):
        self.name = name.strip()
        self.quantity = int(quantity)
        self.value = float(value)

# ключ для злиття дублікатів: (нормалізована назва, ціна у 2 знаки)
def item_key(it: JunkItem) -> tuple[str, str]:
    return (norm_name(it.name), f2(it.value))

def merge_item(items: list[JunkItem], new_item: JunkItem) -> None:
    k = item_key(new_item)
    for it in items:
        if item_key(it) == k:
            it.quantity += new_item.quantity
            return
    items.append(new_item)

def merge_all(items: list[JunkItem]) -> list[JunkItem]:
    acc: list[JunkItem] = []
    for it in items:
        merge_item(acc, it)
    return acc

# === Запис / Читання CSV (кома-сепаратор, крапка-десяткова) ===
def save_items(items: list[JunkItem], filename: str = DEFAULT_FILE) -> None:
    items = merge_all(items)
    with open(filename, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=SEP, quoting=csv.QUOTE_MINIMAL)
        # (необов’язково) шапка
        w.writerow(["name", "quantity", "value"])
        for it in items:
            w.writerow([it.name, it.quantity, f2(it.value)])
    print(f"Файл створено/оновлено: {filename}")

def load_items(filename: str = DEFAULT_FILE) -> list[JunkItem]:
    items: list[JunkItem] = []
    bad = 0
    try:
        with open(filename, "r", encoding="utf-8", newline="") as f:
            r = csv.reader(f, delimiter=SEP)
            header_skipped = False
            for row in r:
                # пропускаємо шапку, якщо є
                if not header_skipped and row and row[0].strip().lower() == "name":
                    header_skipped = True
                    continue
                if len(row) != 3:
                    bad += 1; continue
                name, q, v = row
                try:
                    it = JunkItem(name, int(q), float(str(v).replace(" ", "")))
                    merge_item(items, it)
                except:
                    bad += 1
        if bad:
            print(f"Імпорт: помилкових рядків пропущено: {bad}")
        print(f"Прочитано валідних записів: {len(items)}")
    except FileNotFoundError:
        print(f"Файл '{filename}' не знайдено — буде створено при збереженні.")
    return items

# === Вивід таблиці в консоль ===
def show_items(items: list[JunkItem]) -> None:
    if not items:
        print("(порожньо)\n"); return
    print("\nНазва                 | К-сть |  Ціна  |  Сума ")
    print("------------------------------------------------")
    total = 0.0
    for it in items:
        s = it.quantity * it.value
        total += s
        print(f"{it.name:<21} | {it.quantity:>5} | {f2(it.value):>6} | {f2(s):>6}")
    print("------------------------------------------------")
    print(f"Разом: {f2(total)}\n")

# === Меню ===
def menu():
    items: list[JunkItem] = []
    while True:
        print("Меню:")
        print("1. Додати предмет")
        print("2. Показати предмети")
        print("3. Зберегти у файл (CSV , .)")
        print("4. Відкрити з файлу (CSV , .)")
        print("5. Демо (3 предмети, сумується)")
        print("6. Вийти")
        choice = input("Ваш вибір: ").strip()

        if choice == "1":
            name = input("Назва: ").strip()
            q = input("Кількість (int): ").strip()
            v = input("Ціна (крапка як десяткова, напр. 2.5): ").strip()
            try:
                it = JunkItem(name, int(q), float(v))
                merge_item(items, it)
                print("Додано/оновлено.\n")
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
            merge_item(items, JunkItem("Бляшанка",   5, 2.50))
            merge_item(items, JunkItem("Стара плата", 3, 7.80))
            merge_item(items, JunkItem("Купка дротів",10, 1.20))
            print("Демо-набір додано (суми оновлено)")
            show_items(items)

        elif choice == "6":
            print("Готово."); break
        else:
            print("Невірний вибір.\n")

if __name__ == "__main__":
    menu()