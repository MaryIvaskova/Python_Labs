# client_inventory.py
import csv
import uuid
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import requests

API_BASE = "http://127.0.0.1:5000"
API_ITEMS = f"{API_BASE}/items"
API_SYNC = f"{API_BASE}/sync"
API_EXPORT = f"{API_BASE}/export"

COLS = ("id", "name", "category", "quantity", "price", "location", "created_at")
CACHE_FILE = Path("cache.csv")


def gen_id() -> str:
    return uuid.uuid4().hex[:8].upper()


def norm_price(s: str) -> float:
    s = (s or "").replace(" ", "").replace(",", ".")
    return float(s)


class InventoryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Облік товарів (Flask)")
        self.data: list[dict] = []
        self.sort_state: dict[str, bool] = {}
        self.online: bool = False  # режим

        self._make_ui()
        self._binds()

        # спроба завантажитися з сервера, потім з кешу
        self.refresh_from_server(initial=True)

    # ---------- UI ----------

    def _make_ui(self):
        self.root.geometry("980x560")
        self.root.minsize(860, 520)

        m = tk.Menu(self.root)
        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="Синхронізувати зараз", command=self.sync_now)
        fm.add_command(label="Експорт CSV…", command=self.export_csv)
        fm.add_separator()
        fm.add_command(label="Вихід", command=self.root.quit)
        m.add_cascade(label="Файл", menu=fm)
        self.root.config(menu=m)

        # верх – пошук
        top = ttk.Frame(self.root, padding=(8, 6))
        top.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(top, text="Пошук:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.search_var, width=40)
        e.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(top, text="(name/category)").pack(side=tk.LEFT)

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # таблиця
        left = ttk.Frame(body, padding=6)
        self.tree = ttk.Treeview(
            left,
            columns=COLS,
            show="headings",
            selectmode="browse",
            height=16,
        )
        for c in COLS:
            self.tree.heading(c, text=c, command=lambda col=c: self.sort_by(col))
            w = 120 if c in ("name", "category", "location") else 90
            if c == "id":
                w = 90
            if c == "created_at":
                w = 150
            self.tree.column(c, width=w, anchor=tk.W)
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(left, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        # форма
        right = ttk.Frame(body, padding=10)
        self.inputs: dict[str, tk.Entry] = {}
        form_fields = [
            ("id", "ID"),
            ("name", "Назва"),
            ("category", "Категорія"),
            ("quantity", "Кількість"),
            ("price", "Ціна"),
            ("location", "Локація"),
        ]
        for i, (key, label) in enumerate(form_fields):
            ttk.Label(right, text=label).grid(
                row=i, column=0, sticky="e", pady=4, padx=(0, 6)
            )
            ent = tk.Entry(right, width=30)
            ent.grid(row=i, column=1, sticky="w", pady=4)
            self.inputs[key] = ent

        btns = ttk.Frame(right)
        btns.grid(row=len(form_fields), column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Додати", command=self.add_item).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(btns, text="Оновити", command=self.update_item).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(btns, text="Видалити", command=self.delete_item).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(btns, text="Очистити", command=self.clear_form).grid(
            row=0, column=3, padx=4
        )

        body.add(left, weight=3)
        body.add(right, weight=2)

        self.status_var = tk.StringVar()
        sb = ttk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            relief=tk.SUNKEN,
        )
        sb.pack(side=tk.BOTTOM, fill=tk.X)

    def _binds(self):
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())
        self.search_var.trace_add("write", lambda *_: self.apply_filter())

    # ---------- helpers ----------

    def _set_status(self, msg: str):
        mode = "Онлайн" if self.online else "Офлайн"
        self.status_var.set(f"{mode}: {msg}")

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        rows = self._filtered_rows()
        for r in rows:
            self.tree.insert("", tk.END, values=[r[c] for c in COLS])

    def _filtered_rows(self):
        q = self.search_var.get().strip().lower()
        if not q:
            return self.data
        return [
            r
            for r in self.data
            if q in r["name"].lower() or q in r["category"].lower()
        ]

    def _data_index_by_id(self, idv: str):
        for i, r in enumerate(self.data):
            if r["id"] == idv:
                return i
        return None

    def _select_by_id(self, idv: str):
        for iid in self.tree.get_children():
            if self.tree.item(iid, "values")[0] == idv:
                self.tree.selection_set(iid)
                self.tree.see(iid)
                break

    # ---------- cache ----------

    def save_cache(self):
        with CACHE_FILE.open("w", encoding="utf-8", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=COLS)
            wr.writeheader()
            for r in self.data:
                wr.writerow(r)

    def load_cache(self):
        if not CACHE_FILE.exists():
            self.data = []
        else:
            with CACHE_FILE.open("r", encoding="utf-8", newline="") as f:
                rd = csv.DictReader(f)
                self.data = []
                for row in rd:
                    row["quantity"] = int(row["quantity"])
                    row["price"] = float(row["price"])
                    self.data.append(row)
        self._refresh_table()
        self._set_status("дані з локального кешу")

    # ---------- validation ----------

    def _validate(self) -> dict | None:
        ok = True

        def mark(k, good):
            ent = self.inputs[k]
            ent.config(bg=("white" if good else "#ffd6d6"))

        name = self.inputs["name"].get().strip()
        cat = self.inputs["category"].get().strip()
        mark("name", bool(name))
        mark("category", bool(cat))
        ok &= bool(name and cat)

        q_s = self.inputs["quantity"].get().strip()
        try:
            q = int(q_s)
            mark("quantity", q >= 0)
            ok &= q >= 0
        except Exception:
            mark("quantity", False)
            ok = False

        p_s = self.inputs["price"].get().strip()
        try:
            price = norm_price(p_s)
            mark("price", price >= 0)
            ok &= price >= 0
        except Exception:
            mark("price", False)
            ok = False

        idv = self.inputs["id"].get().strip()
        if not idv:
            idv = gen_id()
        mark("id", True)

        if not ok:
            self._set_status("Перевірте поля форми")
            return None

        return {
            "id": idv,
            "name": name,
            "category": cat,
            "quantity": int(q_s),
            "price": float(f"{price:.2f}"),
            "location": self.inputs["location"].get().strip(),
        }

    # ---------- online / offline loading ----------

    def refresh_from_server(self, initial: bool = False):
        try:
            resp = requests.get(API_ITEMS, timeout=3)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            items = resp.json()
            # нормалізуємо типи
            self.data = []
            for r in items:
                r["quantity"] = int(r["quantity"])
                r["price"] = float(r["price"])
                self.data.append(r)
            self.online = True
            self._refresh_table()
            self.save_cache()
            self._set_status("дані з сервера")
        except Exception as e:
            self.online = False
            self.load_cache()
            if not initial:
                messagebox.showwarning(
                    "Офлайн",
                    f"Сервер недоступний, працюємо з кешем.\n{e}",
                )

    # ---------- CRUD ----------

    def add_item(self):
        vals = self._validate()
        if not vals:
            return

        if self.online:
            try:
                payload = {
                    "name": vals["name"],
                    "category": vals["category"],
                    "quantity": vals["quantity"],
                    "price": vals["price"],
                    "location": vals["location"],
                }
                resp = requests.post(API_ITEMS, json=payload, timeout=3)
                if resp.status_code != 201:
                    err = resp.json().get("error", f"HTTP {resp.status_code}")
                    raise RuntimeError(err)
                item = resp.json()
                item["quantity"] = int(item["quantity"])
                item["price"] = float(item["price"])
                self.data.append(item)
                self.save_cache()
                self._refresh_table()
                self._select_by_id(item["id"])
                self._set_status("додано (сервер)")
                return
            except Exception as e:
                self.online = False
                self._set_status(f"помилка сервера, офлайн: {e}")

        # офлайн режим
        vals["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data.append(vals)
        self.save_cache()
        self._refresh_table()
        self._select_by_id(vals["id"])
        self._set_status("додано (офлайн)")

    def update_item(self):
        sel = self.tree.selection()
        if not sel:
            self._set_status("Не вибрано елемент")
            return
        vals = self._validate()
        if not vals:
            return
        idv = self.tree.item(sel[0], "values")[0]
        idx = self._data_index_by_id(idv)
        if idx is None:
            return

        if self.online:
            try:
                payload = {
                    "name": vals["name"],
                    "category": vals["category"],
                    "quantity": vals["quantity"],
                    "price": vals["price"],
                    "location": vals["location"],
                }
                resp = requests.put(f"{API_ITEMS}/{idv}", json=payload, timeout=3)
                if resp.status_code != 200:
                    err = resp.json().get("error", f"HTTP {resp.status_code}")
                    raise RuntimeError(err)
                item = resp.json()
                item["quantity"] = int(item["quantity"])
                item["price"] = float(item["price"])
                self.data[idx] = item
                self.save_cache()
                self._refresh_table()
                self._select_by_id(item["id"])
                self._set_status("оновлено (сервер)")
                return
            except Exception as e:
                self.online = False
                self._set_status(f"помилка сервера, офлайн: {e}")

        # офлайн
        vals["created_at"] = self.data[idx].get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.data[idx] = vals
        self.save_cache()
        self._refresh_table()
        self._select_by_id(vals["id"])
        self._set_status("оновлено (офлайн)")

    def delete_item(self):
        sel = self.tree.selection()
        if not sel:
            self._set_status("Не вибрано елемент")
            return
        row = self.tree.item(sel[0], "values")
        item_id = row[0]
        if not messagebox.askyesno("Підтвердження", f"Видалити ID {item_id}?"):
            return
        idx = self._data_index_by_id(item_id)
        if idx is None:
            return

        if self.online:
            try:
                resp = requests.delete(f"{API_ITEMS}/{item_id}", timeout=3)
                if resp.status_code not in (200, 204):
                    err = resp.json().get("error", f"HTTP {resp.status_code}")
                    raise RuntimeError(err)
                self.data.pop(idx)
                self.save_cache()
                self._refresh_table()
                self.clear_form()
                self._set_status("видалено (сервер)")
                return
            except Exception as e:
                self.online = False
                self._set_status(f"помилка сервера, офлайн: {e}")

        # офлайн
        self.data.pop(idx)
        self.save_cache()
        self._refresh_table()
        self.clear_form()
        self._set_status("видалено (офлайн)")

    # ---------- selection & form ----------

    def clear_form(self):
        for k, e in self.inputs.items():
            e.config(bg="white")
            e.delete(0, tk.END)
        self._set_status("форма очищена")

    def _on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        for i, k in enumerate(COLS):
            if k in self.inputs:
                ent = self.inputs[k]
                ent.config(bg="white")
                ent.delete(0, tk.END)
                ent.insert(0, vals[i])

    # ---------- sort / filter ----------

    def sort_by(self, col: str):
        asc = not self.sort_state.get(col, True)
        self.sort_state[col] = asc
        keyf = (
            (lambda r: float(r[col]))
            if col in ("price", "quantity")
            else (lambda r: r[col])
        )
        self.data.sort(key=keyf, reverse=not asc)
        self._refresh_table()
        self._set_status(f"Сорт: {col} {'↑' if asc else '↓'}")

    def apply_filter(self):
        self._refresh_table()
        self._set_status("фільтр застосовано")

    # ---------- sync & export ----------

    def sync_now(self):
        """Надсилаємо поточні дані на сервер /sync."""
        try:
            resp = requests.post(API_SYNC, json=self.data, timeout=5)
            if resp.status_code != 200:
                err = resp.json().get("error", f"HTTP {resp.status_code}")
                raise RuntimeError(err)
            self.online = True
            self.refresh_from_server()
            messagebox.showinfo("Синхронізація", "Дані успішно синхронізовано із сервером.")
        except Exception as e:
            self.online = False
            self._set_status(f"Не вдалося синхронізувати: {e}")
            messagebox.showwarning("Синхронізація", f"Помилка синхронізації:\n{e}")

    def export_csv(self):
        """Запитуємо у сервера актуальний CSV і зберігаємо куди скаже користувач."""
        path = filedialog.asksaveasfilename(
            title="Зберегти CSV",
            defaultextension=".csv",
            filetypes=[("CSV файли", "*.csv")],
        )
        if not path:
            return
        try:
            resp = requests.get(API_EXPORT, timeout=5)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            with open(path, "wb") as f:
                f.write(resp.content)
            self._set_status(f"CSV експортовано: {Path(path).name}")
            messagebox.showinfo("Експорт", "CSV успішно збережено.")
        except Exception as e:
            self._set_status(f"Помилка експорту: {e}")
            messagebox.showerror("Експорт", f"Не вдалося експортувати CSV:\n{e}")


def main():
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()