import os

SEP = '|'  # єдиний роздільник полів
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(BASE_DIR, "мусорка.csv")

def dec_to_comma(x: float) -> str:
    return f"{float(x):.2f}".replace('.', ',')

def comma_to_dec(s: str) -> float:
    # "2,50" -> 2.5, також прибираємо пробіли
    return float((s or '').replace(' ', '').replace(',', '.'))

def norm_name(name: str) -> str:
    # нижній регістр + єдиний пробіл між словами
    return ' '.join(name.strip().lower().split())

def price_key(v: float) -> str:
    # ключ ціни у 2 знаки (щоб стабільно порівнювати)
    return f"{float(v):.2f}"

class JunkItem:
    def __init__(self, name: str, quantity: int, value: float):
        name = (name or '').strip().replace(SEP, '/')
        self.name = name
        self.quantity = int(quantity)
        self.value = float(value)

    def to_line(self) -> str:
        # Назва|Кількість|Ціна(з комою)
        return f"{self.name}{SEP}{self.quantity}{SEP}{dec_to_comma(self.value)}"

    @staticmethod
    def from_line(line: str):
        # розбір "Назва|Кількість|Ціна_з_комою"
        if not line or SEP not in line:
            return None
        parts = [p.strip() for p in line.strip().split(SEP)]
        if len(parts) != 3:
            return None
        name, q, v = parts
        try:
            q = int(q)
            v = comma_to_dec(v)
            return JunkItem(name, q, v)
        except:
            return None

def item_key(it: JunkItem) -> tuple[str, str]:
    # дубль = однакове (нормалізована назва, ціна у 2 знаки)
    return (norm_name(it.name), price_key(it.value))

class JunkStorage:
    @staticmethod
    def serialize(items: list[JunkItem], filename: str = DEFAULT_FILE) -> None:
        # перед записом зливаємо дублікати
        items = JunkStorage._merge_all(items)
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            for it in items:
                f.write(it.to_line() + '\n')
        print(f"Файл створено/оновлено: {filename}")

    @staticmethod
    def parse(filename: str = DEFAULT_FILE) -> list[JunkItem]:
        items: list[JunkItem] = []
        bad = 0
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    it = JunkItem.from_line(line)
                    if it:
                        JunkStorage._merge_one(items, it)
                    else:
                        bad += 1
                        print(f"Рядок {i} пропущено (зіпсовані дані)")
            if bad:
                print(f"Помилкових рядків: {bad}")
            print(f"Прочитано валідних записів: {len(items)}")
        except FileNotFoundError:
            print(f"Файл '{filename}' не знайдено — буде створено при збереженні.")
        return items

    @staticmethod
    def _merge_one(items: list[JunkItem], new_item: JunkItem) -> None:
        k = item_key(new_item)
        for it in items:
            if item_key(it) == k:
                it.quantity += new_item.quantity
                return
        items.append(new_item)

    @staticmethod
    def _merge_all(items: list[JunkItem]) -> list[JunkItem]:
        acc: list[JunkItem] = []
        for it in items:
            JunkStorage._merge_one(acc, it)
        return acc

# ——— вивід у консоль (для демонстрації) ———
def show(items: list[JunkItem]) -> None:
    if not items:
        print("(порожньо)\n"); return
    print("\nНазва                 | К-сть |  Ціна  |  Сума ")
    print("------------------------------------------------")
    total = 0.0
    for it in items:
        s = it.quantity * it.value
        total += s
        print(f"{it.name:<21} | {it.quantity:>5} | {dec_to_comma(it.value):>6} | {dec_to_comma(s):>6}")
    print("------------------------------------------------")
    print(f"Разом: {dec_to_comma(total)}\n")

# ——— просте меню ———
def menu():
    items: list[JunkItem] = []
    while True:
        print("Меню:")
        print("1. Додати предмет")
        print("2. Показати предмети")
        print("3. Зберегти у файл (|, кома у дробах)")
        print("4. Відкрити з файлу (замінює список)")
        print("5. Демо (3 предмети, дублікати сумуються)")
        print("6. Вийти")
        ch = input("Ваш вибір: ").strip()

        if ch == "1":
            name = input("Назва: ").strip()
            q = input("Кількість (int): ").strip()
            v = input("Ціна (крапка або кома): ").strip()
            try:
                it = JunkItem(name, int(q), comma_to_dec(v))
                JunkStorage._merge_one(items, it)
                print("Додано/оновлено.\n")
            except:
                print("Помилка вводу.\n")

        elif ch == "2":
            show(items)

        elif ch == "3":
            JunkStorage.serialize(items, DEFAULT_FILE)

        elif ch == "4":
            items = JunkStorage.parse(DEFAULT_FILE)
            show(items)

        elif ch == "5":
            JunkStorage._merge_one(items, JunkItem("Бляшанка",    5, 2.50))
            JunkStorage._merge_one(items, JunkItem("Стара плата", 3, 7.80))
            JunkStorage._merge_one(items, JunkItem("Купка дротів",10, 1.20))
            print("Демо-додано (дублікати зведені).")
            show(items)

        elif ch == "6":
            print("Готово.")
            break
        else:
            print("Невірний вибір.\n")

if __name__ == "__main__":
    menu()