import csv, sys, uuid
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

COLS = ("id","name","category","quantity","price","location","created_at")

def gen_id() -> str:  # id
    return uuid.uuid4().hex[:8].upper()

def norm_price(s: str) -> float:  # ціна
    s = (s or "").replace(" ", "").replace(",", ".")
    return float(s)

class InventoryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Облік товарів")
        self.data: list[dict] = []
        self.filtered_idx: list[int] = []  # для пошуку
        self.current_path: Path | None = None
        self.sort_state: dict[str, bool] = {}  # колонки

        self._make_ui()
        self._binds()
        self._set_status("Готово")

    # UI
    def _make_ui(self):
        self.root.geometry("980x560")
        self.root.minsize(860, 520)

        # меню
        m = tk.Menu(self.root)
        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="Відкрити…", command=self.menu_open, accelerator="Ctrl+O")
        fm.add_command(label="Зберегти", command=self.menu_save, accelerator="Ctrl+S")
        fm.add_command(label="Зберегти як…", command=self.menu_save_as)
        fm.add_separator()
        fm.add_command(label="Вихід", command=self.root.quit)
        m.add_cascade(label="Файл", menu=fm)
        self.root.config(menu=m)

        # верх: пошук
        top = ttk.Frame(self.root, padding=(8,6))
        top.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(top, text="Пошук:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.search_var, width=40)
        e.pack(side=tk.LEFT, padx=(6,12))
        ttk.Label(top, text="(name/category)").pack(side=tk.LEFT)

        # центр
        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # таблиця
        left = ttk.Frame(body, padding=6)
        self.tree = ttk.Treeview(left, columns=COLS, show="headings", selectmode="browse", height=16)
        for c in COLS:
            self.tree.heading(c, text=c, command=lambda col=c: self.sort_by(col))
            w = 120 if c in ("name","category","location") else 90
            if c == "id": w = 90
            if c == "created_at": w = 150
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
        self.inputs = {}
        form_fields = [
            ("id","ID"), ("name","Назва"), ("category","Категорія"),
            ("quantity","Кількість"), ("price","Ціна"), ("location","Локація")
        ]
        for i,(key,label) in enumerate(form_fields):
            ttk.Label(right, text=label).grid(row=i, column=0, sticky="e", pady=4, padx=(0,6))
            # tk.Entry — щоб міняти bg при валід. помилці
            ent = tk.Entry(right, width=30)
            ent.grid(row=i, column=1, sticky="w", pady=4)
            self.inputs[key] = ent
        # кнопки
        btns = ttk.Frame(right)
        btns.grid(row=len(form_fields), column=0, columnspan=2, pady=(10,0))
        ttk.Button(btns, text="Додати", command=self.add_item).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Оновити", command=self.update_item).grid(row=0, column=1, padx=4)
        ttk.Button(btns, text="Видалити", command=self.delete_item).grid(row=0, column=2, padx=4)
        ttk.Button(btns, text="Очистити", command=self.clear_form).grid(row=0, column=3, padx=4)

        body.add(left, weight=3)
        body.add(right, weight=2)

        # статус
        self.status = tk.StringVar()
        sb = ttk.Label(self.root, textvariable=self.status, anchor="w", relief=tk.SUNKEN)
        sb.pack(side=tk.BOTTOM, fill=tk.X)

    # події
    def _binds(self):
        self.root.bind("<Control-o>", lambda e: self.menu_open())
        self.root.bind("<Control-s>", lambda e: self.menu_save())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())
        self.search_var.trace_add("write", lambda *_: self.apply_filter())

    # статус
    def _set_status(self, msg: str):
        self.status.set(msg)

    # валідація
    def _validate(self) -> dict | None:
        ok = True
        def mark(k, good):
            ent = self.inputs[k]
            ent.config(bg=("white" if good else "#ffd6d6"))
        # name/category
        name = self.inputs["name"].get().strip()
        cat = self.inputs["category"].get().strip()
        mark("name", bool(name))
        mark("category", bool(cat))
        ok &= bool(name and cat)
        # quantity
        q_s = self.inputs["quantity"].get().strip()
        try:
            q = int(q_s)
            mark("quantity", q >= 0)
            ok &= q >= 0
        except:
            mark("quantity", False); ok = False
        # price
        p_s = self.inputs["price"].get().strip()
        try:
            price = norm_price(p_s)
            mark("price", price >= 0)
            ok &= price >= 0
        except:
            mark("price", False); ok = False
        # id
        idv = self.inputs["id"].get().strip() or gen_id()
        if any(r["id"] == idv for r in self.data) and not self._is_selected_id(idv):
            mark("id", False); ok = False
        else:
            mark("id", True)
        if not ok:
            self._set_status("Перевірте поля")
            return None
        return {
            "id": idv,
            "name": name,
            "category": cat,
            "quantity": int(q_s),
            "price": float(f"{norm_price(p_s):.2f}"),
            "location": self.inputs["location"].get().strip(),
        }

    def _is_selected_id(self, idv: str) -> bool:
        sel = self.tree.selection()
        if not sel: return False
        iid = sel[0]
        row = self.tree.item(iid, "values")
        return row and row[0] == idv

    # CRUD
    def add_item(self):
        vals = self._validate()
        if not vals: return
        vals["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data.append(vals)
        self._refresh_table()
        self._select_by_id(vals["id"])
        self._set_status("Додано")

    def update_item(self):
        sel = self.tree.selection()
        if not sel:
            self._set_status("Не вибрано"); return
        vals = self._validate()
        if not vals: return
        # зберегти created_at старий
        idv = self.tree.item(sel[0], "values")[0]
        idx = self._data_index_by_id(idv)
        if idx is None: return
        vals["created_at"] = self.data[idx]["created_at"]
        self.data[idx] = vals
        self._refresh_table()
        self._select_by_id(vals["id"])
        self._set_status("Оновлено")

    def delete_item(self):
        sel = self.tree.selection()
        if not sel:
            self._set_status("Не вибрано"); return
        row = self.tree.item(sel[0], "values")
        if not messagebox.askyesno("Підтвердження", f"Видалити ID {row[0]}?"):
            return
        idx = self._data_index_by_id(row[0])
        if idx is not None:
            self.data.pop(idx)
        self._refresh_table()
        self.clear_form()
        self._set_status("Видалено")

    def clear_form(self):
        for k,e in self.inputs.items():
            e.config(bg="white")
            e.delete(0, tk.END)
        self._set_status("Форма очищена")

    # вибір
    def _on_select(self):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        for i,k in enumerate(COLS):
            if k in self.inputs:
                ent = self.inputs[k]
                ent.config(bg="white")
                ent.delete(0, tk.END)
                ent.insert(0, vals[i])

    # таблиця
    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        rows = self._filtered_rows() if self.search_var.get().strip() else self.data
        for r in rows:
            self.tree.insert("", tk.END, values=[r[c] for c in COLS])

    def _filtered_rows(self):
        q = self.search_var.get().strip().lower()
        if not q: return self.data
        return [r for r in self.data if q in r["name"].lower() or q in r["category"].lower()]

    def _data_index_by_id(self, idv: str) -> int | None:
        for i, r in enumerate(self.data):
            if r["id"] == idv: return i
        return None

    def _select_by_id(self, idv: str):
        for iid in self.tree.get_children():
            if self.tree.item(iid, "values")[0] == idv:
                self.tree.selection_set(iid)
                self.tree.see(iid)
                break

    # сортування
    def sort_by(self, col: str):
        asc = not self.sort_state.get(col, True)
        self.sort_state[col] = asc
        keyf = (lambda r: float(r[col])) if col in ("price","quantity") else (lambda r: r[col])
        self.data.sort(key=keyf, reverse=not asc)
        self._refresh_table()
        self._set_status(f"Сорт: {col} {'↑' if asc else '↓'}")

    # файли
    def menu_open(self):
        p = filedialog.askopenfilename(
            title="Відкрити CSV",
            filetypes=[("CSV файли","*.csv"),("Усі файли","*.*")]
        )
        if not p: return
        try:
            self._load_csv(Path(p))
            self.current_path = Path(p)
            self._set_status(f"Завантажено: {Path(p).name}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Неможливо прочитати файл:\n{e}")

    def menu_save(self):
        if not self.current_path:
            return self.menu_save_as()
        try:
            self._save_csv(self.current_path)
            self._set_status(f"Збережено: {self.current_path.name}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Неможливо зберегти:\n{e}")

    def menu_save_as(self):
        p = filedialog.asksaveasfilename(
            title="Зберегти CSV",
            defaultextension=".csv",
            filetypes=[("CSV файли","*.csv")]
        )
        if not p: return
        self.current_path = Path(p)
        self.menu_save()

    def _load_csv(self, path: Path):
        self.data.clear()
        with path.open("r", encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            need = set(COLS)
            if set(rd.fieldnames or []) != need:
                raise ValueError("Невірні колонки CSV")
            for row in rd:
                # нормалізація
                row["quantity"] = int(row["quantity"])
                row["price"] = float(f"{norm_price(row['price']):.2f}")
                self.data.append(row)
        self.clear_form()
        self.search_var.set("")
        self._refresh_table()

    def _save_csv(self, path: Path):
        with path.open("w", encoding="utf-8", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=COLS)
            wr.writeheader()
            for r in self.data:
                wr.writerow(r)

    # фільтр
    def apply_filter(self):
        self._refresh_table()
        self._set_status("Фільтр застосовано")

def main():
    root = tk.Tk()
    app = InventoryApp(root)
    # демо-дані
    app.data = [
        {"id": gen_id(), "name": "Гвинт М6", "category": "Кріплення", "quantity": 120, "price": 1.20, "location": "A-01",
         "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id": gen_id(), "name": "Підшипник 6204", "category": "Механіка", "quantity": 30, "price": 4.80, "location": "B-12",
         "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id": gen_id(), "name": "Кабель ВВГ", "category": "Електрика", "quantity": 85, "price": 2.10, "location": "E-03",
         "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]
    app._refresh_table()
    root.mainloop()

if __name__ == "__main__":
    main()