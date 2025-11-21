import threading
import random
import time


class Warehouse:
    def __init__(self, name, meds):
        self.name = name
        self.meds = meds
        self.lock = threading.Lock()

    def steal(self, amount):
        # логіка крадіжки (0 ящо провальна)

        # 20% шанс, що злодія спіймають
        if random.random() < 0.2:
            return 0

        # 20% шанс, що крадіжка пройде частково (половина від суми)
        if random.random() < 0.2:
            amount = max(1, amount // 2)

        # склад не може піти в мінус
        stolen = min(amount, self.meds)
        self.meds -= stolen
        return stolen


class Runner(threading.Thread):
    def __init__(self, name, warehouse, price_per_unit=25):
        super().__init__()
        self.name = name
        self.warehouse = warehouse
        self.price_per_unit = price_per_unit
        self.total_profit = 0

    def run(self):
        for attempt in range(10):
            amount = random.randint(10, 30)

            # блокування складу
            with self.warehouse.lock:
                stolen = self.warehouse.steal(amount)
                self.total_profit += stolen * self.price_per_unit

            # візуальна “загрузочна полоса” для кожної спроби
            self._progress_bar(attempt + 1, 10)

            # пауза між спробами
            time.sleep(random.uniform(0.1, 0.5))

    def _progress_bar(self, current, total):
        filled = int((current / total) * 20)
        bar = "[" + "#" * filled + "-" * (20 - filled) + "]"
        print(f"{self.name}: {bar} {current}/{total}")


def run_simulation():
    # створюємо склади
    warehouses = [
        Warehouse("Склад A", random.randint(100, 300)),
        Warehouse("Склад B", random.randint(100, 300)),
        Warehouse("Склад C", random.randint(100, 300)),
        Warehouse("Склад D", random.randint(100, 300)),
        Warehouse("Склад E", random.randint(100, 300)),
    ]

    # створюємо бігунів (злодіїв)
    runners = []
    for i in range(5):
        w = random.choice(warehouses)
        r = Runner(name=f"Злодій_{i+1}", warehouse=w)
        runners.append(r)

    # запуск потоків
    for r in runners:
        r.start()

    # чекаємо завершення
    for r in runners:
        r.join()

    # звіт
    print("\n--- Звіт по складах ---")
    for w in warehouses:
        print(f"{w.name}: залишилось {w.meds} одиниць медикаментів")

    total_profit = sum(r.total_profit for r in runners)

    print("\n--- Прибуток бігунів ---")
    for r in runners:
        print(f"{r.name}: заробив {r.total_profit}")

    print(f"\nЗагальний заробіток: {total_profit}")
    print("-" * 40)
    return total_profit


if __name__ == "__main__":
    # запускаємо симуляцію кілька разів
    for i in range(3):
        print(f"\n==== Спроба №{i+1} ====")
        run_simulation()