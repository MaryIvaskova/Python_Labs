from abc import ABC, abstractmethod

class Medicine(ABC):
    def __init__(self, name: str, quantity: int, price: float):
        if not isinstance(name, str) or not name.strip():
            raise TypeError("name must be non-empty str")
        if not isinstance(quantity, int):
            raise TypeError("quantity must be int")
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            raise TypeError("price must be float or int")
        self.name = name.strip()
        self.quantity = quantity
        self.price = float(price)

    @abstractmethod
    def requires_prescription(self) -> bool: ...

    @abstractmethod
    def storage_requirements(self) -> str: ...

    @abstractmethod
    def total_price(self) -> float:
        return self.quantity * self.price

    @abstractmethod
    def info(self) -> str:
        rp = "так" if self.requires_prescription() else "ні"
        return (
            f"{self.__class__.__name__}: {self.name} | "
            f"кількість: {self.quantity} | ціна: {self.price:.2f} | "
            f"разом: {self.total_price():.2f} | рецепт: {rp} | "
            f"зберігання: {self.storage_requirements()}"
        )


class Antibiotic(Medicine):
    def requires_prescription(self) -> bool: return True
    def storage_requirements(self) -> str:   return "8–15°C, темне місце"
    def total_price(self) -> float:          return super().total_price()
    def info(self) -> str:                   return super().info()


class Vitamin(Medicine):
    def requires_prescription(self) -> bool: return False
    def storage_requirements(self) -> str:   return "15–25°C, сухо"
    def total_price(self) -> float:          return super().total_price()
    def info(self) -> str:                   return super().info()


class Vaccine(Medicine):
    def requires_prescription(self) -> bool: return True
    def storage_requirements(self) -> str:   return "2–8°C, холодильник"
    def total_price(self) -> float:          return super().total_price() * 1.10
    def info(self) -> str:                   return super().info()