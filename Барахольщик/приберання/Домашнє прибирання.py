import os

# --- конфігурація ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_FILE = os.path.join(BASE_DIR, "мусорка.csv")
PREVIEW_FILE = os.path.join(BASE_DIR, "мусорка_preview.csv")


# --- утиліти ---
def to_dec_comma(x: float) -> str:
    """Формат числа з двома знаками після коми, кома як десятковий роздільник."""
    return f"{float(x):.2f}".replace(".", ",")


def from_dec_comma(s: str) -> float:
    """Читає число, приймаючи і кому, і крапку."""
    s = (s or "").strip().replace(" ", "")
    return float(s.replace(",", "."))


def norm_name(name: str) -> str:
    """Нормалізація імені для пошуку дублікатів."""
    return " ".join((name or "").strip().lower().split())


def price_key(v: float) -> str:
    """Округлення ціни до 2 знаків для ключа дубліката."""
    return f"{float(v):.2f}"


# --- модель предмету ---
class JunkItem:
    def __init__(self, name: str, quantity: int, value: float):
        safe = (name or "").strip().replace("|", "/").replace(";", "/")
        self.name = safe
        self.quantity = int(quantity)
        self.value = float(value)

    def line(self) -> str:
        """Рядок у форматі задачі: Назва|К-сть|Ціна(з комою)"""
        return f"{self.name}|{self.quantity}|{to_dec_comma(self.value)}"

    @staticmethod
    def from_line(line: str):
        """Парсинг рядка у форматі задачі."""
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


# --- робота з дублями ---
def item_key(it: JunkItem) -> tuple[str, str]:
    """Ключ для об'єднання — (нормалізована назва, округлена ціна)."""
    return (norm_name(it.name), price_key(it.value))


def merge_item(items: list[JunkItem], new_item: JunkItem) -> None:
    """Додає або сумує, якщо дубль."""
    k = item_key(new_item)
    for it in items:
        if item_key(it) == k:
            it.quantity += new_item.quantity
            return
    items.append(new_item)


def merge_all(items: list[JunkItem]) -> list[JunkItem]:
    """Об'єднує всі дублікати у списку."""
    acc = []
    for it in items:
        merge_item(acc, it)
    return acc


# --- сховище ---
class JunkStorage:
    @staticmethod
    def serialize(items: list[JunkItem], main_file: str = MAIN_FILE, preview_file: str = PREVIEW_FILE) -> None:
        """Зберігає два файли: основний (| і кома) + превʼю (коми і крапки)."""
        items = merge_all(items)

        # 1️⃣ Основний файл — за умовою задачі
        with open(main_file, "w", encoding="utf-8", newline="") as f:
            f.write("Назва|Кількість|Ціна\n")
            for it in items:
                f.write(it.line() + "\n")

        # 2️⃣ Превʼю — для зручного перегляду у Numbers / Excel / GitHub
        with open(preview_file, "w", encoding="utf-8", newline="") as f:
            f.write("name,quantity,value\n")
            for it in items:
                f.write(f"{it.name},{it.quantity},{it.value:.2f}\n")

        print("✅ Файли збережено:")
        print(f" - Основний: {main_file}  (Назва|Кількість|Ціна з комою)")
        print(f" - Превʼю:   {preview_file} (3 стовпці для Numbers/Excel/GitHub)")

    @staticmethod
    def parse(filename: str = MAIN_FILE) -> list[JunkItem]:
        """Читає як 'мусорка.csv' (| + кома), так і 'мусорка_preview.csv' (коми + крапка)."""
        items = []
        bad = 0

        def try_take(line: str) -> bool:
            it = JunkItem.from_line(line)
            if it:
                merge_item(items, it)
                return True
            # можливо CSV-варіант (коми + крапка)
            if "," in line and line.lower().startswith(("name,", "назва,")):
                return True  # шапка
            parts = [p.strip() for p in line.strip().split(",")]
            if len(parts) == 3:
                name, q, v = parts
                try:
                    it = JunkItem(name, int(q), float(v))
                    merge_item(items, it)
                    return True
                except:
                    return False
            return False

        try:
            with open(filename, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if not try_take(line):
                        bad += 1
                        print(f"⚠️ Рядок {i} пропущено (помилка формату)")
        except FileNotFoundError:
            print(f"Файл '{filename}' не знайдено — буде створено при збереженні.")

        if bad:
            print(f"Помилкових рядків: {bad}")
        print(f"📦 Прочитано валідних записів: {len(items)}")
        return items


# --- вивід таблиці ---
def show(items: list[JunkItem]) -> None:
    """Форматований вивід у консоль."""
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


# --- меню ---
def menu():
    items = []
    while True:
        print("Меню:")
        print("1. Додати предмет")
        print("2. Показати предмети")
        print("3. Зберегти у файл")
        print("4. Відкрити з файлу")
        print("5. Демо-набір (суми додаються)")
        print("6. Вийти")
        ch = input("Ваш вибір: ").strip()

        if ch == "1":
            name = input("Назва: ").strip()
            q = input("Кількість (int): ").strip()
            v = input("Ціна (кома або крапка): ").strip()
            try:
                it = JunkItem(name, int(q), from_dec_comma(v))
                merge_item(items, it)
                print("✅ Додано або оновлено.\n")
            except:
                print("⚠️ Помилка вводу.\n")

        elif ch == "2":
            show(items)

        elif ch == "3":
            JunkStorage.serialize(items)

        elif ch == "4":
            items = JunkStorage.parse(MAIN_FILE)
            show(items)

        elif ch == "5":
            # демо: дублікати не створюються, а додаються
            merge_item(items, JunkItem("Бляшанка", 5, 2.50))
            merge_item(items, JunkItem("Стара плата", 3, 7.80))
            merge_item(items, JunkItem("Купка дротів", 10, 1.20))
            print("🧹 Демо-набір додано (суми оновлено).")
            show(items)

        elif ch == "6":
            print("👋 Готово.")
            break

        else:
            print("Невірний вибір.\n")


# --- запуск ---
if __name__ == "__main__":
    menu()