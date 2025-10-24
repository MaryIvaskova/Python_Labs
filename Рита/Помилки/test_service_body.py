import sys, os
import pytest
sys.path.append(os.path.dirname(__file__))  # дозволяє бачити локальний модуль
from service_body_test import Order
@pytest.fixture
def sample_order():
    return Order(1, [
        {"name": "apple", "price": 10.0, "quantity": 2},
        {"name": "banana", "price": 5.0, "quantity": 3},
        {"name": "cherry", "price": 20.0, "quantity": 1}
    ])

@pytest.fixture
def empty_order():
    return Order(2, [])

def most_expensive(self):
    if not self.items:
        return None
    return max(self.items, key=lambda x: x['price'])

# ---- total() ----
def test_total_basic(sample_order):
    assert sample_order.total() == pytest.approx(10*2 + 5*3 + 20*1)

def test_total_empty(empty_order):
    assert empty_order.total() == 0

# ---- most_expensive() ----
def test_most_expensive(sample_order):
    item = sample_order.most_expensive()
    assert item["name"] == "cherry"
    assert item["price"] == 20.0

def test_most_expensive_empty(empty_order):
    assert empty_order.most_expensive() is None

# ---- apply_discount() ----
def test_apply_discount_valid(sample_order):
    sample_order.apply_discount(10)
    prices = [item["price"] for item in sample_order.items]
    assert all(p <= orig for p, orig in zip(prices, [10, 5, 20]))

def test_apply_discount_invalid(sample_order):
    with pytest.raises(ValueError):
        sample_order.apply_discount(150)

# ---- repr() ----
def test_repr(sample_order):
    text = repr(sample_order)
    assert "Order" in text
    assert "items" in text