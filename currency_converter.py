import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
from datetime import datetime

DATA_FILE = "history.json"
API_URL = "https://api.exchangerate-api.com/v4/latest/"


class CurrencyConverter:
    def _init_(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("700x500")

        self.history = []
        self.rates = {}
        self.load_data()
        self.fetch_rates()

        # Интерфейс
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Выбор валют и сумма
        ttk.Label(main_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(main_frame, width=20)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Из валюты:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.from_currency = ttk.Combobox(main_frame, width=20)
        self.from_currency.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="В валюту:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.to_currency = ttk.Combobox(main_frame, width=20)
        self.to_currency.grid(row=2, column=1, padx=5, pady=5)

        self.convert_btn = ttk.Button(main_frame, text="Конвертировать", command=self.convert)
        self.convert_btn.grid(row=3, column=0, columnspan=2, pady=10)

        self.result_label = ttk.Label(main_frame, text="", font=("Arial", 12, "bold"))
        self.result_label.grid(row=4, column=0, columnspan=2, pady=5)

        # Таблица истории
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding=5)
        history_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky="nsew")

        self.tree = ttk.Treeview(history_frame, columns=("date", "amount", "from_curr", "to_curr", "result"), show="headings")
        self.tree.heading("date", text="Дата")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("from_curr", text="Из")
        self.tree.heading("to_curr", text="В")
        self.tree.heading("result", text="Результат")
        self.tree.column("date", width=140)
        self.tree.column("amount", width=80)
        self.tree.column("from_curr", width=60)
        self.tree.column("to_curr", width=60)
        self.tree.column("result", width=100)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопки управления историей
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="Очистить историю", command=self.clear_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Сохранить историю", command=self.save_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Загрузить историю", command=self.load_data).pack(side="left", padx=5)

        # Настройка сетки
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        self.display_history()
        self.update_currency_list()

    def fetch_rates(self):
        """Получение курсов валют с API"""
        try:
            response = requests.get(API_URL + "USD", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.rates = data["rates"]
                messagebox.showinfo("Успех", "Курсы валют успешно загружены!")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить курсы валют")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения к API: {e}")
    def update_currency_list(self):
        """Обновление списка валют в выпадающих списках"""
        currencies = list(self.rates.keys())
        currencies.sort()
        self.from_currency["values"] = currencies
        self.to_currency["values"] = currencies
        self.from_currency.set("USD")
        self.to_currency.set("EUR")

    def convert(self):
        """Конвертация валюты"""
        amount_str = self.amount_entry.get().strip()
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        # Валидация
        if not amount_str:
            messagebox.showerror("Ошибка", "Введите сумму!")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом!")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть числом!")
            return

        if not from_curr or not to_curr:
            messagebox.showerror("Ошибка", "Выберите валюты!")
            return

        if not self.rates:
            messagebox.showerror("Ошибка", "Курсы валют не загружены!")
            return

        # Конвертация
        try:
            usd_amount = amount / self.rates[from_curr]
            result = usd_amount * self.rates[to_curr]
            result = round(result, 2)

            self.result_label.config(text=f"{amount} {from_curr} = {result} {to_curr}")

            # Сохраняем в историю
            self.history.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "from_curr": from_curr,
                "to_curr": to_curr,
                "result": result
            })

            self.display_history()
            self.save_data()
            self.amount_entry.delete(0, tk.END)

        except KeyError:
            messagebox.showerror("Ошибка", "Выбрана неподдерживаемая валюта!")

    def display_history(self):
        """Отображение истории в таблице"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in self.history[-10:]:  # Показываем последние 10 записей
            self.tree.insert("", tk.END, values=(
                item["date"],
                item["amount"],
                item["from_curr"],
                item["to_curr"],
                item["result"]
            ))

    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.display_history()
            self.save_data()
            messagebox.showinfo("Успех", "История очищена!")

    def save_data(self):
        """Сохранение истории в JSON"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")

    def load_data(self):
        """Загрузка истории из JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                self.display_history()
                messagebox.showinfo("Успех", "История загружена!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить историю: {e}")
        else:
            self.history = []


if __name__ == "_main_":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()
