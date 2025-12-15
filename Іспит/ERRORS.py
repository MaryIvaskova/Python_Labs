from flask import Flask, jsonify, request

app = Flask(__name__)


class ApiError(Exception):
    def __init__(self, message, status_code=400, error_code="bad_request", details=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationError(ApiError):
    def __init__(self, message="Validation error", details=None):
        super().__init__(message, 422, "validation_error", details)


class NotFoundError(ApiError):
    def __init__(self, message="Not found", details=None):
        super().__init__(message, 404, "not_found", details)


class MathService:
    def divide(self, a, b):
        if b == 0:
            raise ValidationError("Division by zero", {"b": b})
        return a / b


class UserService:
    users = {
        1: {"id": 1, "name": "Alice"},
        2: {"id": 2, "name": "Bob"},
    }

    def get_user(self, user_id):
        if user_id not in self.users:
            raise NotFoundError("User not found", {"user_id": user_id})
        return self.users[user_id]


math_service = MathService()
user_service = UserService()


@app.route("/divide")
def divide():
    a = request.args.get("a", type=float)
    b = request.args.get("b", type=float)

    if a is None or b is None:
        raise ValidationError("Params a and b are required")

    result = math_service.divide(a, b)
    return jsonify({"success": True, "data": {"result": result}})


@app.route("/users/<int:user_id>")
def get_user(user_id):
    user = user_service.get_user(user_id)
    return jsonify({"success": True, "data": user})


@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({
        "success": False,
        "error": {
            "code": error.error_code,
            "message": error.message,
            "details": error.details
        }
    }), error.status_code


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "internal_error",
            "message": "Internal server error"
        }
    }), 500


if __name__ == "__main__":
    app.run(debug=True)