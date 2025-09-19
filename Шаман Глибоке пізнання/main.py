from models import Transport, Car, Bus, Bicycle, ElectricCar

def show_report(items: list[Transport], distance: int, price_per_unit: float):
    print(f"Дистанція: {distance} км | ціна одиниці пального/заряду: {price_per_unit:.2f}")
    print("Тип           Назва           Час (год)   Паливо    Вартість")
    print("------------------------------------------------------------------------------")
    for t in items:
        t_time = t.move(distance)
        t_fuel = t.fuel_consumption(distance)
        t_cost = t.calculate_cost(distance, price_per_unit)
        print(f"{t.__class__.__name__:<13} {t.name:<14} {t_time:>8.2f}   {t_fuel:>7.2f}   {t_cost:>8.2f}")

if __name__ == "__main__":
    fleet: list[Transport] = [
        Car("Sedan", 90, 5),
        Bus("City Bus", 60, 40, passengers=45),
        Bicycle("Road Bike", 25, 1),
        ElectricCar("Model 3", 110, 5),
    ]
    print("\nІНФО:")
    for t in fleet:
        print(" -", t.info())
    print()
    show_report(fleet, distance=100, price_per_unit=2.0)