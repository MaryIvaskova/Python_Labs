from abc import ABC, abstractmethod

class Transport(ABC):
    def __init__(self, name: str, speed: int, capacity: int):
        if not isinstance(name, str) or not name.strip():
            raise TypeError("name must be non-empty str")
        if not isinstance(speed, int) or speed <= 0:
            raise TypeError("speed must be positive int")
        if not isinstance(capacity, int) or capacity < 0:
            raise TypeError("capacity must be non-negative int")
        self.name = name.strip()
        self.speed = speed
        self.capacity = capacity

    @abstractmethod
    def move(self, distance: int) -> float: ...
    @abstractmethod
    def fuel_consumption(self, distance: int) -> float: ...
    @abstractmethod
    def info(self) -> str: ...

    def calculate_cost(self, distance: int, price_per_unit: float) -> float:
        return self.fuel_consumption(distance) * float(price_per_unit)


class Car(Transport):
    def move(self, distance: int) -> float:
        return distance / self.speed
    def fuel_consumption(self, distance: int) -> float:
        return distance * 0.07
    def info(self) -> str:
        return f"Car: {self.name} | {self.speed} км/год | {self.capacity} місць"


class Bus(Transport):
    def __init__(self, name: str, speed: int, capacity: int, passengers: int):
        super().__init__(name, speed, capacity)
        if not isinstance(passengers, int) or passengers < 0:
            raise TypeError("passengers must be non-negative int")
        self.passengers = passengers

    def move(self, distance: int) -> float:
        return distance / self.speed

    def fuel_consumption(self, distance: int) -> float:
        if self.passengers > self.capacity:
            print("Перевантажено!")
        return distance * 0.15

    def info(self) -> str:
        return f"Bus: {self.name} | {self.speed} км/год | {self.capacity} місць | пасажирів: {self.passengers}"


class Bicycle(Transport):
    def move(self, distance: int) -> float:
        v = min(self.speed, 20)
        return distance / v
    def fuel_consumption(self, distance: int) -> float:
        return 0.0
    def info(self) -> str:
        return f"Bicycle: {self.name} | {self.speed} км/год (до 20) | 1 місце"


class ElectricCar(Car):
    def battery_usage(self, distance: int) -> float:
        return distance * 0.20
    def fuel_consumption(self, distance: int) -> float:
        return 0.0
    def calculate_cost(self, distance: int, price_per_unit: float) -> float:
        return self.battery_usage(distance) * float(price_per_unit)
    def info(self) -> str:
        return f"ElectricCar: {self.name} | {self.speed} км/год | {self.capacity} місць"