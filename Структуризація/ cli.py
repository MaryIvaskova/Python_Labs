#можна не звертати увагу просто тести
from models import Medicine, Antibiotic, Vitamin, Vaccine

KIND = {
    "1": ("Antibiotic", Antibiotic),
    "2": ("Vitamin",    Vitamin),
    "3": ("Vaccine",    Vaccine),
}

meds: list[Medicine] = []

def add_med():
    print("Тип: 1=Antibiotic, 2=Vitamin, 3=Vaccine")
    k = input("Обери тип (1/2/3): ").strip()
    if k not in KIND:
        print("Невідомий тип\n")
        return
    name = input("Назва: ").strip()

    q_raw = input("Кількість (int): ").strip()
    p_raw = input("Ціна за одиницю (float): ").strip()
    try:
        qty = int(q_raw)
        price = float(p_raw)
    except:
        print("Помилка даних: кількість має бути int, ціна — float\n")
        return

    _, cls = KIND[k]
    try:
        meds.append(cls(name, qty, price))
        print(" Додано\n")
    except TypeError as e:
        print(f"Помилка даних: {e}\n")

def print_table():
    if not meds:
        print("\nСписок порожній\n")
        return

    rows = []
    for m in meds:
        rows.append((
            m.__class__.__name__,
            m.name,
            str(m.quantity),
            f"{m.price:.2f}",
            f"{m.total_price():.2f}",
            "так" if m.requires_prescription() else "ні",
            m.storage_requirements(),
        ))

    headers = ("Тип", "Назва", "К-сть", "Ціна", "Разом", "Рецепт", "Зберігання")

    w = [
        max(len(headers[0]), *(len(r[0]) for r in rows)),
        max(len(headers[1]), *(len(r[1]) for r in rows)),
        max(len(headers[2]), *(len(r[2]) for r in rows)),
        max(len(headers[3]), *(len(r[3]) for r in rows)),
        max(len(headers[4]), *(len(r[4]) for r in rows)),
        max(len(headers[5]), *(len(r[5]) for r in rows)),
        max(len(headers[6]), *(len(r[6]) for r in rows)),
    ]

    line = (
        f"{headers[0]:<{w[0]}}  {headers[1]:<{w[1]}}  {headers[2]:>{w[2]}}  "
        f"{headers[3]:>{w[3]}}  {headers[4]:>{w[4]}}  {headers[5]:^{w[5]}}  "
        f"{headers[6]:<{w[6]}}"
    )
    print()
    print(line)
    print("-" * len(line))
    for r in rows:
        print(
            f"{r[0]:<{w[0]}}  {r[1]:<{w[1]}}  {r[2]:>{w[2]}}  "
            f"{r[3]:>{w[3]}}  {r[4]:>{w[4]}}  {r[5]:^{w[5]}}  "
            f"{r[6]:<{w[6]}}"
        )
    print()

def menu():
    while True:
        print("Меню:")
        print("1. Додати препарат")
        print("2. Показати партію")
        print("3. Вийти")
        cmd = input("Ваш вибір: ").strip()
        if cmd == "1":
            add_med()
        elif cmd == "2":
            print_table()
        elif cmd == "3":
            print("Готово.")
            break
        else:
            print("Невірний вибір\n")

if __name__ == "__main__":
    menu()