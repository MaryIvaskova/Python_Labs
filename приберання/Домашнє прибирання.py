
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILENAME = os.path.join(BASE_DIR, "мусорка.csv")

# ---------- утиліти ----------
def to_dec_comma(x: float) -> str:
    return f"{float(x):.2f}".replace(".", ",")

def from_dec_comma(s: str) -> float:
    # приймаємо і кому, і крапку; зберігаємо завжди з комою
    s = (s or "").strip().replace(" ", "")
    return float(s.replace(",", "."))

def norm_name(name: str) -> str:
    return " ".join((name or "").strip().lower().split())

def price_key(v: float) -> str:
    return f"{float(v):.2f}"


# ---------- модель ----------
class JunkItem:
    def __init__(self, name: str, quantity: int, value: float):
        safe = (name or "").strip().replace("|", "/")
        self.name = safe
        self.quantity = int(quantity)
        self.value = float(value)

    def line(self) -> str:
        # Назва|К-сть|Ціна(з комою)
        return f"{self.name}|{self.quantity}|{to_dec_comma(self.value)}"

    @staticmethod
    def from_line(line: str):
        parts = [p.strip() for p in line.strip().split("|")]
        if len(parts) != 3:
            return None
        name, q, v = parts
        try:
            q = int(q)
            v = from_dec_comma(v)
            return JunkItem(name, q, v)
        except:
            return None


# ---------- мерж дублікатів (назва + ціна) ----------
def item_key(it: JunkItem) -> tuple[str, str]:
    return (norm_name(it.name), price_key(it.value))

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


# ---------- ЄДИНИЙ «сериалайзер» ----------
class JunkStorage:
    @staticmethod
    def serialize(items: list[JunkItem], filename: str = FILENAME) -> None:
        items = merge_all(items)
        with open(filename, "w", encoding="utf-8", newline="") as f:
            for it in items:
                f.write(it.line() + "\n")
        print(f"Файл збережено: {filename}  (формат: Назва|К-сть|Ціна_з_комою)")

    @staticmethod
    def parse(filename: str = FILENAME) -> list[JunkItem]:
        items: list[JunkItem] = []
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
            if bad:
                print(f"Помилкових рядків: {bad}")
            print(f"Прочитано валідних записів: {len(items)}")
        except FileNotFoundError:
            print(f"Файл '{filename}' не знайдено — буде створено при збереженні.")
        return items


# ---------- вивід таблиці ----------
def show(items: list[JunkItem]) -> None:
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


# ---------- меню ----------
def menu():
    items: list[JunkItem] = []
    while True:
        print("Меню:")
        print("1. Додати предмет")
        print("2. Показати предмети")
        print("3. Зберегти у файл (мусорка.csv)")
        print("4. Відкрити з файлу (замінює поточний список)")
        print("5. Демо (3 предмети; дублікати сумуються при кожному натисканні)")
        print("6. Вийти")
        ch = input("Ваш вибір: ").strip()

        if ch == "1":
            name = input("Назва: ").strip()
            q = input("Кількість (int): ").strip()
            v = input("Ціна (крапка або кома): ").strip()
            try:
                it = JunkItem(name, int(q), from_dec_comma(v))
                merge_item(items, it)
                print("Додано/оновлено.\n")
            except:
                print("Помилка вводу.\n")

        elif ch == "2":
            show(items)

        elif ch == "3":
            JunkStorage.serialize(items, FILENAME)

        elif ch == "4":
            items = JunkStorage.parse(FILENAME)
            show(items)

        elif ch == "5":
            # Фікс демо: кожен виклик додає цей самий набір, але через merge кількість сумується
            merge_item(items, JunkItem("Бляшанка",     5, 2.50))
            merge_item(items, JunkItem("Стара плата",  3, 7.80))
            merge_item(items, JunkItem("Купка дротів",10, 1.20))
            print("Демо-набір додано (суми оновлено).")
            show(items)

        elif ch == "6":
            print("Готово.")
            break
        else:
            print("Невірний вибір.\n")


if __name__ == "__main__":
    menu()