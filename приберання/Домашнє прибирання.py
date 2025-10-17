import os

# --------- конфіг ---------
FORMAT_MODE = "portal"  # "task" або "portal"
SEP_TASK, DEC_TASK = "|", ","   # умова
SEP_PORT, DEC_PORT = ";", "."   # для порталу

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(BASE_DIR, "мусорка.csv")


# --------- утиліти ---------
def detect_format(line: str):
    """Визначає (sep, dec) по рядку."""
    if SEP_TASK in line:
        return SEP_TASK, DEC_TASK
    if SEP_PORT in line:
        return SEP_PORT, DEC_PORT
    return SEP_TASK, DEC_TASK  # дефолт — умова задачі

def to_dec(x: float, dec: str) -> str:
    """Форматує 2 знаки і ставить потрібний десятковий роздільник."""
    s = f"{float(x):.2f}"
    return s.replace(".", dec)

def from_dec(s: str, dec: str) -> float:
    """Читає число з потрібним десятковим роздільником."""
    s = (s or "").replace(" ", "")
    if dec == ",":
        s = s.replace(",", ".")
    return float(s)

def norm_name(name: str) -> str:
    return " ".join((name or "").strip().lower().split())

def price_key(v: float) -> str:
    return f"{float(v):.2f}"


# --------- модель ---------
class JunkItem:
    def __init__(self, name: str, quantity: int, value: float):
        # захист від вбудованих роздільників у назві
        safe = (name or "").strip().replace("|", "/").replace(";", "/")
        self.name = safe
        self.quantity = int(quantity)
        self.value = float(value)

    def to_line(self, sep="|", dec=",") -> str:
        # Назва|К-сть|Ціна(десяткова: кома/крапка)
        return sep.join([self.name, str(self.quantity), to_dec(self.value, dec)])

    @staticmethod
    def from_line(line: str):
        sep, dec = detect_format(line)
        parts = [p.strip() for p in line.strip().split(sep)]
        if len(parts) != 3:
            return None
        name, q, v = parts
        try:
            q = int(q)
            v = from_dec(v, dec)
            return JunkItem(name, q, v)
        except:
            return None


# --------- злиття дублікатів ---------
def item_key(it: JunkItem) -> tuple[str, str]:
    # дубль = однакові (нормалізована назва, ціна з 2 знаками)
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


# --------- I/O ---------
def save_items(items: list[JunkItem], filename: str = DEFAULT_FILE) -> None:
    """Запис у один файл 'мусорка.csv' у вибраному форматі."""
    items = merge_all(items)
    if FORMAT_MODE == "portal":
        sep, dec = SEP_PORT, DEC_PORT
    else:
        sep, dec = SEP_TASK, DEC_TASK

    with open(filename, "w", encoding="utf-8", newline="") as f:
        # для порталу можна дати шапку — портали люблять
        if sep == SEP_PORT:
            f.write(f"name{sep}quantity{sep}value\n")
        for it in items:
            f.write(it.to_line(sep=sep, dec=dec) + "\n")

    print(f"Файл створено/оновлено: {filename}  (формат: {FORMAT_MODE})")

def load_items(filename: str = DEFAULT_FILE) -> list[JunkItem]:
    """Читає як 'task', так і 'portal' формат, шапку порталу ігнорує."""
    items: list[JunkItem] = []
    bad = 0
    try:
        with open(filename, "r", encoding="utf-8") as f:
            first = True
            for i, line in enumerate(f, 1):
                # пропустити шапку у 'portal'
                if first and (SEP_PORT in line) and line.lower().startswith(f"name{SEP_PORT}"):
                    first = False
                    continue
                first = False

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


# --------- вивід таблиці ---------
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
        # красивий вивід: десятковий роздільник під формат меню («кома» зручно візуально)
        price_view = to_dec(it.value, ",")
        sum_view = to_dec(s, ",")
        print(f"{it.name:<21} | {it.quantity:>5} | {price_view:>6} | {sum_view:>6}")
    print("------------------------------------------------")
    print(f"Разом: {to_dec(total, ',')}\n")


# --------- меню ---------
def menu():
    items: list[JunkItem] = []
    while True:
        print("Меню:")
        print("1. Додати предмет")
        print("2. Показати предмети")
        print("3. Зберегти у файл (мусорка.csv)")
        print("4. Відкрити з файлу (замінює список)")
        print("5. Демо (3 предмети, дублікати сумуються)")
        print("6. Вийти")
        ch = input("Ваш вибір: ").strip()

        if ch == "1":
            name = input("Назва: ").strip()
            q = input("Кількість (int): ").strip()
            v = input("Ціна (крапка або кома): ").strip()
            try:
                # приймаємо і кому, і крапку — перетворимо за портальним форматом
                # (неважливо, усе збережеться згідно FORMAT_MODE)
                dec = DEC_PORT if FORMAT_MODE == "portal" else DEC_TASK
                val = from_dec(v, dec) if ("," in v or "." in v) else float(v)
                it = JunkItem(name, int(q), float(val))
                merge_item(items, it)
                print("Додано/оновлено.\n")
            except:
                print("Помилка вводу.\n")

        elif ch == "2":
            show(items)

        elif ch == "3":
            save_items(items, DEFAULT_FILE)

        elif ch == "4":
            items = load_items(DEFAULT_FILE)
            show(items)

        elif ch == "5":
            merge_item(items, JunkItem("Бляшанка",    5, 2.50))
            merge_item(items, JunkItem("Стара плата", 3, 7.80))
            merge_item(items, JunkItem("Купка дротів",10, 1.20))
            print("Демо-додано (дублікати зведені).")
            show(items)

        elif ch == "6":
            print("Готово.")
            break
        else:
            print("Невірний вибір.\n")


if __name__ == "__main__":
    menu()