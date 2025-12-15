import pytest
from ERRORS import MathService, UserService
from ERRORS import ValidationError, NotFoundError


def test_divide_ok():
    s = MathService()
    assert s.divide(10, 2) == 5


def test_divide_by_zero():
    s = MathService()
    with pytest.raises(ValidationError):
        s.divide(10, 0)


def test_get_user_ok():
    s = UserService()
    user = s.get_user(1)
    assert user["name"] == "Alice"


def test_user_not_found():
    s = UserService()
    with pytest.raises(NotFoundError):
        s.get_user(99)