import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DATA_FILE = "expenses.json"
DATE_FORMAT = "%Y-%m-%d"  # YYYY-MM-DD


CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Одежда", "Здоровье", "Другое"]

class ExpenseTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("800x500")
        self.expenses = []
        self.create_widgets()
        self.load_data()  # попытка загрузить при старте

    def create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=10, pady=8)

        ttk.Label(frm, text="Сумма:").grid(row=0, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.amount_var, width=12).grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="Категория:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(frm, textvariable=self.cat_var, values=CATEGORIES, state="readonly", width=18)
        cat_combo.grid(row=0, column=3, sticky="w")
        cat_combo.current(0)

        ttk.Label(frm, text="Дата (YYYY-MM-DD):").grid(row=0, column=4, sticky="w", padx=(10,0))
        self.date_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.date_var, width=12).grid(row=0, column=5, sticky="w")
        self.date_var.set(datetime.now().strftime(DATE_FORMAT))

        ttk.Button(frm, text="Добавить расход", command=self.add_expense).grid(row=0, column=6, padx=(10,0))

        # Filters & sum area
        f2 = ttk.Frame(self)
        f2.pack(fill="x", padx=10, pady=6)

        ttk.Label(f2, text="Фильтр по категории:").grid(row=0, column=0, sticky="w")
        self.filter_cat = tk.StringVar(value="Все")
        cat_values = ["Все"] + CATEGORIES
        ttk.Combobox(f2, textvariable=self.filter_cat, values=cat_values, state="readonly", width=18).grid(row=0, column=1, sticky="w")


        ttk.Label(f2, text="Период с:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.from_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self.from_var, width=12).grid(row=0, column=3, sticky="w")

        ttk.Label(f2, text="по:").grid(row=0, column=4, sticky="w", padx=(6,0))
        self.to_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self.to_var, width=12).grid(row=0, column=5, sticky="w")

        ttk.Button(f2, text="Применить фильтр", command=self.apply_filters).grid(row=0, column=6, padx=(10,0))
        ttk.Button(f2, text="Сбросить фильтры", command=self.reset_filters).grid(row=0, column=7, padx=(6,0))

        ttk.Label(f2, text="Сумма за период:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.sum_var = tk.StringVar(value="0.00")
        ttk.Label(f2, textvariable=self.sum_var, foreground="blue").grid(row=1, column=1, sticky="w", pady=(8,0))


        # Table
        cols = ("amount", "category", "date")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("category", text="Категория")
        self.tree.heading("date", text="Дата")
        self.tree.column("amount", width=100, anchor="center")
        self.tree.column("category", width=150, anchor="center")
        self.tree.column("date", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0,8))

        # Buttons bottom
        btm = ttk.Frame(self)
        btm.pack(fill="x", padx=10, pady=(0,10))

        ttk.Button(btm, text="Удалить выделенное", command=self.delete_selected).pack(side="left")
        ttk.Button(btm, text="Сохранить в JSON", command=self.save_data_dialog).pack(side="right")
        ttk.Button(btm, text="Загрузить из JSON", command=self.load_data_dialog).pack(side="right", padx=(0,6))


    def validate_amount(self, s):
        try:
            val = float(s)
            return val > 0
        except:
            return False

    def validate_date(self, s):
        try:
            datetime.strptime(s, DATE_FORMAT)
            return True
        except:
            return False
    def add_expense(self):
        amount_s = self.amount_var.get().strip()
        category = self.cat_var.get()
        date_s = self.date_var.get().strip()

        if not self.validate_amount(amount_s):
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом.")
            return
        if not self.validate_date(date_s):
            messagebox.showerror("Ошибка", f"Дата должна быть в формате {DATE_FORMAT}.")
            return

        exp = {
            "amount": float(amount_s),
            "category": category,
            "date": date_s
        }
        self.expenses.append(exp)
        self.refresh_table()
        self.clear_input()
    def clear_input(self):
        self.amount_var.set("")
        self.date_var.set(datetime.now().strftime(DATE_FORMAT))
    def refresh_table(self, items=None):
        for i in self.tree.get_children():
            self.tree.delete(i)
        to_show = items if items is not None else self.expenses
        for idx, e in enumerate(to_show):
            self.tree.insert("", "end", iid=str(idx), values=(f"{e['amount']:.2f}", e["category"], e["date"]))
        self.update_sum_display()
    def apply_filters(self):
        cat_f = self.filter_cat.get()
        from_s = self.from_var.get().strip()
        to_s = self.to_var.get().strip()

        # Validate dates if not empty
        from_dt = None
        to_dt = None
        try:
            if from_s:
                if not self.validate_date(from_s):
                    raise ValueError("Неверный формат даты 'с'")
                from_dt = datetime.strptime(from_s, DATE_FORMAT).date()
            if to_s:
                if not self.validate_date(to_s):
                    raise ValueError("Неверный формат даты 'по'")
                to_dt = datetime.strptime(to_s, DATE_FORMAT).date()
