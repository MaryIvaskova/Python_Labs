LIMIT = 300            # зміни тут ну щоб не шукати декоратор
STOP_AT_LIMIT = True   # True  зупиняємось при першому перевищенні; False  лише виводимо повідомлення

def shadow(limit=200, stop_at_limit=False):
    def deco(gen_func):
        def wrapper(*args, **kwargs):
            total = 0.0
            alerted = False
            add = {"payment", "transfer", "bonus", "payout", "deposit"}
            sub = {"refund", "fee", "charge", "withdraw"}

            for raw in gen_func(*args, **kwargs):
                s = str(raw).strip()
                print(s)  # показуємо кожен елемент

                parts = s.split()
                if len(parts) != 2:
                    continue

                kind = parts[0].lower()
                num  = parts[1].strip()

                # число: 10 / 10.5 / 10,5; мікс "," і "." — відсікаємо
                if "," in num and "." in num:
                    continue
                try:
                    val = float(num.replace(",", "."))
                except:
                    continue
                if val < 0:
                    continue

                # ефект транзакції
                if kind in add:
                    total += val
                elif kind in sub:
                    total -= val
                else:
                    continue

                # перевищення ліміту
                if not alerted and total > float(limit):
                    print("Тіньовий ліміт перевищено. Активую схему")
                    alerted = True
                    if stop_at_limit:
                        return total

                yield s
            return total
        return wrapper
    return deco


@shadow(limit=LIMIT, stop_at_limit=STOP_AT_LIMIT)  # тут декоратор
def transaction_stream(lines):
    for line in lines:
        yield line


def consume(gen):
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


if __name__ == "__main__":
    data = [
        "payment 120",
        "refund 50",
        "transfer 300",
        "bonus 25",
        "fee 10",
        "payout 40",
        "deposit 35",
        "withdraw 15",
        "oops x",
        "payment 10,5",
        "payment -5",
        "payment 1,000.5",
    ]
    total = consume(transaction_stream(data))
    print("Фінальна сума:", total)