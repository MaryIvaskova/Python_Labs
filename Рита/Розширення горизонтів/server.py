# server.py
from flask import Flask, request, jsonify, send_file
import csv
from datetime import datetime
from pathlib import Path
import uuid

app = Flask(__name__)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CSV_FILE = DATA_DIR / "inventory.csv"

COLS = ["id", "name", "category", "quantity", "price", "location", "created_at"]


def load_data() -> list[dict]:
    """Читаємо всі товари з CSV."""
    if not CSV_FILE.exists():
        return []
    with CSV_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict] = []
        for raw in reader:
            rows.append(normalize_item(raw))
        return rows


def save_data(data: list[dict]) -> None:
    """Записуємо всі товари в CSV."""
    with CSV_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLS)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def normalize_item(raw: dict) -> dict:
    """Приводимо типи полів до нормального вигляду."""
    return {
        "id": str(raw.get("id", "")).strip(),
        "name": str(raw.get("name", "")).strip(),
        "category": str(raw.get("category", "")).strip(),
        "quantity": int(raw.get("quantity", 0)),
        "price": float(raw.get("price", 0.0)),
        "location": str(raw.get("location", "")).strip(),
        "created_at": str(raw.get("created_at", "")).strip(),
    }


def validate_payload(payload: dict, *, partial: bool = False) -> dict:
    """
    Перевірка даних від клієнта.
    partial=True – для PUT, дозволяє не передавати всі поля.
    """
    if not isinstance(payload, dict):
        raise ValueError("Очікується JSON-об'єкт")

    fields = {}

    def need(key: str) -> bool:
        return (not partial) or (key in payload)

    # name
    if need("name"):
        name = str(payload.get("name", "")).strip()
        if not name:
            raise ValueError("Поле 'name' обов'язкове")
        fields["name"] = name

    # category
    if need("category"):
        cat = str(payload.get("category", "")).strip()
        if not cat:
            raise ValueError("Поле 'category' обов'язкове")
        fields["category"] = cat

    # quantity
    if need("quantity"):
        try:
            q = int(payload.get("quantity", 0))
        except Exception:
            raise ValueError("Поле 'quantity' має бути цілим числом")
        if q < 0:
            raise ValueError("Поле 'quantity' не може бути від'ємним")
        fields["quantity"] = q

    # price
    if need("price"):
        try:
            p = float(str(payload.get("price", "0")).replace(",", "."))
        except Exception:
            raise ValueError("Поле 'price' має бути числом")
        if p < 0:
            raise ValueError("Поле 'price' не може бути від'ємним")
        fields["price"] = p

    # location
    if need("location"):
        loc = str(payload.get("location", "")).strip()
        fields["location"] = loc

    return fields


# ---------- ROUTES ----------

@app.route("/items", methods=["GET"])
def get_items():
    data = load_data()
    return jsonify(data)


@app.route("/items", methods=["POST"])
def add_item():
    payload = request.get_json(silent=True) or {}
    try:
        fields = validate_payload(payload, partial=False)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    item = {
        "id": uuid.uuid4().hex[:8].upper(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **fields,
    }

    data = load_data()
    data.append(item)
    save_data(data)
    return jsonify(item), 201


@app.route("/items/<item_id>", methods=["PUT"])
def update_item(item_id):
    payload = request.get_json(silent=True) or {}
    data = load_data()
    for i, row in enumerate(data):
        if row["id"] == item_id:
            try:
                fields = validate_payload(payload, partial=True)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            row.update(fields)
            # нормалізуємо ще раз на всяк випадок
            data[i] = normalize_item(row)
            save_data(data)
            return jsonify(data[i])
    return jsonify({"error": "Товар не знайдено"}), 404


@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    data = load_data()
    new_data = [row for row in data if row["id"] != item_id]
    if len(new_data) == len(data):
        return jsonify({"error": "Товар не знайдено"}), 404
    save_data(new_data)
    return jsonify({"status": "deleted"})


@app.route("/sync", methods=["POST"])
def sync_items():
    """
    Примусова синхронізація: клієнт надсилає повний список товарів.
    Сервер повністю замінює CSV цими даними.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return jsonify({"error": "Очікується список елементів"}), 400

    new_data: list[dict] = []
    for raw in payload:
        if not isinstance(raw, dict):
            return jsonify({"error": "Невірний формат елементу"}), 400

        # якщо немає id/created_at – згенеруємо
        if not raw.get("id"):
            raw["id"] = uuid.uuid4().hex[:8].upper()
        if not raw.get("created_at"):
            raw["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            fields = validate_payload(raw, partial=False)
        except ValueError as e:
            return jsonify({"error": f"Невірні дані елементу: {e}"}), 400

        row = {
            "id": raw["id"],
            "created_at": raw["created_at"],
            **fields,
        }
        new_data.append(normalize_item(row))

    save_data(new_data)
    return jsonify({"status": "ok", "count": len(new_data)})


@app.route("/export", methods=["GET"])
def export_csv():
    """Повернути актуальний CSV-файл."""
    if not CSV_FILE.exists():
        # створимо порожній файл з заголовком
        save_data([])
    return send_file(
        CSV_FILE,
        mimetype="text/csv",
        as_attachment=True,
        download_name="inventory.csv",
    )


if __name__ == "__main__":
    # стандартний дев-сервер
    app.run(debug=True)