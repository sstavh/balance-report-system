import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
from pathlib import Path

DB_NAME = "creditworthiness_p5.db"

DEFAULT_WEIGHTS = [9, 8, 10, 7, 6, 8, 5, 7, 8, 6, 10]

FORM_1_ROWS = [
    ("1000", "Нематеріальні активи"),
    ("1095", "Усього за розділом I"),
    ("1100", "Запаси"),
    ("1125", "Дебіторська заборгованість за продукцію"),
    ("1155", "Інша поточна дебіторська заборгованість"),
    ("1160", "Поточні фінансові інвестиції"),
    ("1165", "Гроші та їх еквіваленти"),
    ("1195", "Усього за розділом II"),
    ("1300", "Баланс (Актив)"),
    ("1400", "Зареєстрований капітал"),
    ("1495", "Усього за розділом I (Пасив)"),
    ("1525", "Цільове фінансування"),
    ("1595", "Усього за розділом II (Довгострокові зобов'язання)"),
    ("1695", "Усього за розділом III (Поточні зобов'язання)"),
    ("1900", "Баланс (Пасив)")
]

FORM_2_ROWS = [
    ("2000", "Чистий дохід від реалізації продукції"),
    ("2350", "Чистий фінансовий результат: прибуток"),
    ("2500", "Матеріальні затрати"),
    ("2505", "Витрати на оплату праці"),
    ("2510", "Відрахування на соціальні заходи"),
    ("2515", "Амортизація"),
    ("2520", "Інші операційні витрати")
]

EXTRA_LABELS = [
    "V17 — Термін існування підприємства, років",
    "V18 — Градація аналізу прибутків та збитків (0; 5]",
    "V19 — Найбільша сума отриманого і повернутого кредиту, Sk",
    "V20 — Сума запитуваного кредиту, S",
    "V21 — Кількість власних коштів в інвестицію, K",
    "V22 — Вартість власного ліквідного майна, M"
]

save_status = {
    "Form1": False,
    "Form2": False,
    "Extra": False
}


class CreditworthinessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Оцінювання кредитоспроможності підприємства")
        self.root.geometry("1180x780")
        self.root.configure(bg="#edf2f7")

        self.entries_f1 = {}
        self.entries_f2 = {}
        self.extra_entries = []
        self.weight_entries = []

        self.results = []
        self.credit_summary = None

        self.init_db()
        self.setup_style()
        self.build_ui()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#edf2f7")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Header.TLabel", background="#1e3a8a", foreground="white", font=("Arial", 20, "bold"))
        style.configure("SubHeader.TLabel", background="#1e3a8a", foreground="#dbeafe", font=("Arial", 10))
        style.configure("Title.TLabel", background="#ffffff", foreground="#111827", font=("Arial", 14, "bold"))
        style.configure("Text.TLabel", background="#ffffff", foreground="#374151", font=("Arial", 10))

        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=(18, 10))

        style.configure(
            "Accent.TButton",
            font=("Arial", 10, "bold"),
            padding=(14, 8),
            background="#2563eb",
            foreground="white"
        )

        style.configure(
            "Success.TButton",
            font=("Arial", 10, "bold"),
            padding=(14, 8),
            background="#16a34a",
            foreground="white"
        )

        style.configure("Treeview", font=("Arial", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def init_db(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_type TEXT,
                row_code TEXT,
                col1 REAL,
                col2 REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS additional_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                v17 REAL,
                v18 REAL,
                v19 REAL,
                v20 REAL,
                v21 REAL,
                v22 REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT,
                k_value TEXT,
                membership REAL,
                weight REAL,
                normalized_weight REAL,
                result_part REAL
            )
        """)

        conn.commit()
        conn.close()

    def build_ui(self):
        self.build_header()

        main = ttk.Frame(self.root, padding=16)
        main.pack(expand=True, fill="both")

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(expand=True, fill="both")

        self.build_form1_tab()
        self.build_form2_tab()
        self.build_extra_tab()
        self.build_weights_tab()
        self.build_results_tab()
        self.build_bottom_bar(main)

    def build_header(self):
        header = tk.Frame(self.root, bg="#1e3a8a", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        ttk.Label(
            header,
            text="Оцінювання кредитоспроможності підприємства",
            style="Header.TLabel"
        ).pack(anchor="w", padx=24, pady=(16, 0))

        ttk.Label(
            header,
            text="Нечітка модель на основі фінансових показників K1–K11",
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=26, pady=(4, 0))

    def build_bottom_bar(self, parent):
        bottom = ttk.Frame(parent, padding=(0, 14, 0, 0))
        bottom.pack(fill="x")

        self.status_label = ttk.Label(
            bottom,
            text="Збережіть Форму №1, Форму №2 та V17–V22",
            background="#edf2f7",
            foreground="#64748b",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left")

        ttk.Button(
            bottom,
            text="Тестування",
            style="Accent.TButton",
            command=self.test_program
        ).pack(side="right", padx=8)

        self.btn_calculate = ttk.Button(
            bottom,
            text="Оцінити кредитоспроможність",
            style="Success.TButton",
            command=self.calculate_creditworthiness,
            state="disabled"
        )
        self.btn_calculate.pack(side="right")

    def create_scrollable_card(self, parent):
        outer = ttk.Frame(parent, style="Card.TFrame", padding=14)
        outer.pack(expand=True, fill="both", padx=10, pady=10)

        canvas = tk.Canvas(outer, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame

    def build_form_grid(self, parent, rows, col1_name, col2_name):
        entries = {}
        headers = ["Код", "Стаття / назва", col1_name, col2_name]

        for col, text in enumerate(headers):
            label = ttk.Label(
                parent,
                text=text,
                background="#dbeafe",
                foreground="#1e3a8a",
                font=("Arial", 10, "bold"),
                padding=7
            )
            label.grid(row=1, column=col, padx=3, pady=5, sticky="ew")

        for i, (code, name) in enumerate(rows, start=2):
            ttk.Label(parent, text=code, background="#ffffff", width=10).grid(
                row=i, column=0, padx=3, pady=4
            )

            ttk.Label(parent, text=name, background="#ffffff", width=58).grid(
                row=i, column=1, padx=3, pady=4, sticky="w"
            )

            ent1 = ttk.Entry(parent, width=20, justify="center")
            ent1.insert(0, "0")
            ent1.grid(row=i, column=2, padx=3, pady=4)

            ent2 = ttk.Entry(parent, width=20, justify="center")
            ent2.insert(0, "0")
            ent2.grid(row=i, column=3, padx=3, pady=4)

            entries[code] = (ent1, ent2, name)

        return entries

    def build_form1_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Форма №1")

        card = self.create_scrollable_card(tab)

        ttk.Label(
            card,
            text="Форма №1 — Баланс",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self.entries_f1 = self.build_form_grid(
            card,
            FORM_1_ROWS,
            "На початок періоду",
            "На кінець періоду"
        )

        ttk.Button(
            tab,
            text="Зберегти Форму №1",
            style="Accent.TButton",
            command=lambda: self.save_data("Form1", self.entries_f1)
        ).pack(pady=(0, 14))

    def build_form2_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Форма №2")

        card = self.create_scrollable_card(tab)

        ttk.Label(
            card,
            text="Форма №2 — Звіт про фінансові результати",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self.entries_f2 = self.build_form_grid(
            card,
            FORM_2_ROWS,
            "За аналогічний період",
            "За звітний період"
        )

        ttk.Button(
            tab,
            text="Зберегти Форму №2",
            style="Accent.TButton",
            command=lambda: self.save_data("Form2", self.entries_f2)
        ).pack(pady=(0, 14))

    def build_extra_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Додаткові показники")

        card = ttk.Frame(tab, style="Card.TFrame", padding=24)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(
            card,
            text="Додаткова інформація V17–V22",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 18))

        for i, text in enumerate(EXTRA_LABELS, start=1):
            ttk.Label(
                card,
                text=text,
                style="Text.TLabel",
                width=74
            ).grid(row=i, column=0, padx=(0, 16), pady=9, sticky="w")

            ent = ttk.Entry(card, width=32, justify="center")
            ent.insert(0, "1")
            ent.grid(row=i, column=1, pady=9)

            self.extra_entries.append(ent)

        ttk.Button(
            card,
            text="Зберегти показники",
            style="Accent.TButton",
            command=self.save_extra
        ).grid(row=8, column=0, columnspan=2, pady=24)

    def build_weights_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Ваги критеріїв")

        card = ttk.Frame(tab, style="Card.TFrame", padding=24)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(
            card,
            text="Вагові коефіцієнти для K1–K11",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 18))

        ttk.Label(card, text="Критерій", background="#dbeafe", foreground="#1e3a8a",
                  font=("Arial", 10, "bold"), padding=7).grid(row=1, column=0, sticky="ew")
        ttk.Label(card, text="Назва", background="#dbeafe", foreground="#1e3a8a",
                  font=("Arial", 10, "bold"), padding=7).grid(row=1, column=1, sticky="ew")
        ttk.Label(card, text="Вага [1;10]", background="#dbeafe", foreground="#1e3a8a",
                  font=("Arial", 10, "bold"), padding=7).grid(row=1, column=2, sticky="ew")

        names = [
            "Коефіцієнт миттєвої ліквідності",
            "Коефіцієнт поточної ліквідності",
            "Коефіцієнт загальної ліквідності",
            "Коефіцієнт фінансової незалежності",
            "Коефіцієнт маневреності власних коштів",
            "Коефіцієнт рентабельності виробництва",
            "Коефіцієнт діяльності минулих років",
            "Коефіцієнт найбільшої суми повернутого кредиту",
            "Термін існування підприємства",
            "Питома вага коштів підприємства",
            "Коефіцієнт власного ліквідного майна"
        ]

        for i, name in enumerate(names, start=1):
            ttk.Label(card, text=f"K{i}", background="#ffffff", width=10).grid(
                row=i + 1, column=0, padx=3, pady=5
            )

            ttk.Label(card, text=name, background="#ffffff", width=62).grid(
                row=i + 1, column=1, padx=3, pady=5, sticky="w"
            )

            ent = ttk.Entry(card, width=16, justify="center")
            ent.insert(0, str(DEFAULT_WEIGHTS[i - 1]))
            ent.grid(row=i + 1, column=2, padx=3, pady=5)
            self.weight_entries.append(ent)

    def build_results_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Кредитоспроможність")

        card = ttk.Frame(tab, style="Card.TFrame", padding=14)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        ttk.Label(
            card,
            text="Результати оцінювання кредитоспроможності",
            style="Title.TLabel"
        ).pack(anchor="w", pady=(0, 12))

        self.tree_res = ttk.Treeview(
            card,
            columns=("K", "Indicator", "Value", "Mu", "Weight", "NormWeight", "Part"),
            show="headings",
            height=14
        )

        self.tree_res.heading("K", text="Критерій")
        self.tree_res.heading("Indicator", text="Показник")
        self.tree_res.heading("Value", text="K")
        self.tree_res.heading("Mu", text="μ(K)")
        self.tree_res.heading("Weight", text="Вага")
        self.tree_res.heading("NormWeight", text="Норм. вага")
        self.tree_res.heading("Part", text="Добуток")

        self.tree_res.column("K", width=70, anchor="center")
        self.tree_res.column("Indicator", width=360)
        self.tree_res.column("Value", width=90, anchor="center")
        self.tree_res.column("Mu", width=90, anchor="center")
        self.tree_res.column("Weight", width=90, anchor="center")
        self.tree_res.column("NormWeight", width=110, anchor="center")
        self.tree_res.column("Part", width=100, anchor="center")

        self.tree_res.pack(expand=True, fill="both")

        self.summary_label = ttk.Label(
            card,
            text="Агрегована оцінка ще не розрахована",
            background="#ffffff",
            foreground="#111827",
            font=("Arial", 12, "bold")
        )
        self.summary_label.pack(anchor="w", pady=12)

        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=8)

        ttk.Button(
            btn_frame,
            text="Розрахувати кредитоспроможність",
            style="Success.TButton",
            command=self.calculate_creditworthiness
        ).pack(side="left")

        ttk.Button(
            btn_frame,
            text="Експорт результатів у CSV",
            style="Accent.TButton",
            command=self.export_results
        ).pack(side="right")

    def check_all_saved(self):
        if all(save_status.values()):
            self.btn_calculate.config(state="normal")
            self.status_label.config(
                text="Усі дані збережено. Можна оцінити кредитоспроможність.",
                foreground="#16a34a"
            )
        else:
            self.btn_calculate.config(state="disabled")

    def to_float(self, value):
        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            return None

    def save_data(self, form_type, entries_dict):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM form_data WHERE form_type = ?", (form_type,))

        for code, (ent1, ent2, name) in entries_dict.items():
            val1 = self.to_float(ent1.get().strip())
            val2 = self.to_float(ent2.get().strip())

            if val1 is None or val2 is None:
                conn.close()
                messagebox.showerror("Помилка", f"Некоректне число у рядку {code}.")
                return

            cursor.execute("""
                INSERT INTO form_data (form_type, row_code, col1, col2)
                VALUES (?, ?, ?, ?)
            """, (form_type, code, val1, val2))

        conn.commit()
        conn.close()

        save_status[form_type] = True
        self.check_all_saved()

        messagebox.showinfo("Збережено", f"Дані для {form_type} успішно збережено.")

    def save_extra(self):
        values = []

        for entry in self.extra_entries:
            value = self.to_float(entry.get().strip())
            if value is None:
                messagebox.showerror("Помилка", "У додаткових показниках можна вводити тільки числа.")
                return
            values.append(value)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM additional_info")

        cursor.execute("""
            INSERT INTO additional_info (v17, v18, v19, v20, v21, v22)
            VALUES (?, ?, ?, ?, ?, ?)
        """, values)

        conn.commit()
        conn.close()

        save_status["Extra"] = True
        self.check_all_saved()

        messagebox.showinfo("Збережено", "Додаткову інформацію успішно збережено.")

    def get_val(self, cursor, form_type, row_code):
        cursor.execute(
            "SELECT col2 FROM form_data WHERE form_type = ? AND row_code = ?",
            (form_type, row_code)
        )
        result = cursor.fetchone()
        return result[0] if result else 0

    def safe_div(self, numerator, denominator):
        if denominator == 0:
            return 0
        return round(numerator / denominator, 4)

    def membership(self, value):
        if value <= 0:
            return 0
        if value >= 1:
            return 1
        return round(value, 4)

    def normalize_weights(self, weights):
        total = sum(weights)
        if total == 0:
            return [0 for _ in weights]
        return [round(w / total, 4) for w in weights]

    def get_rating(self, score):
        if score > 0.57:
            return (
                "І категорія якості",
                "AAA / AA",
                "Найвищий рівень кредитоспроможності"
            )
        elif score > 0.37:
            return (
                "ІІ категорія якості",
                "A / BBB",
                "Висока кредитоспроможність"
            )
        elif score > 0.19:
            return (
                "ІІІ категорія якості",
                "BB / B",
                "Спекулятивний рейтинг"
            )
        elif score > 0.11:
            return (
                "IV категорія якості",
                "CCC",
                "Можливий дефолт"
            )
        else:
            return (
                "V категорія якості",
                "C / RD / D",
                "Дефолт неминучий"
            )

    def get_weights(self):
        weights = []

        for i, entry in enumerate(self.weight_entries, start=1):
            value = self.to_float(entry.get().strip())

            if value is None or value < 1 or value > 10:
                messagebox.showerror(
                    "Помилка",
                    f"Вага для K{i} має бути числом від 1 до 10."
                )
                return None

            weights.append(value)

        return weights

    def calculate_k_values(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT v17, v18, v19, v20, v21, v22 FROM additional_info")
        extra = cursor.fetchone()

        if not extra:
            conn.close()
            messagebox.showwarning("Увага", "Спочатку збережіть додаткову інформацію.")
            return None

        v17, v18, v19_sk, v20_s, v21_k, v22_m = extra

        f1_1095 = self.get_val(cursor, "Form1", "1095")
        f1_1125 = self.get_val(cursor, "Form1", "1125")
        f1_1155 = self.get_val(cursor, "Form1", "1155")
        f1_1160 = self.get_val(cursor, "Form1", "1160")
        f1_1165 = self.get_val(cursor, "Form1", "1165")
        f1_1195 = self.get_val(cursor, "Form1", "1195")
        f1_1495 = self.get_val(cursor, "Form1", "1495")
        f1_1525 = self.get_val(cursor, "Form1", "1525")
        f1_1595 = self.get_val(cursor, "Form1", "1595")
        f1_1695 = self.get_val(cursor, "Form1", "1695")

        f2_2350 = self.get_val(cursor, "Form2", "2350")
        f2_2500 = self.get_val(cursor, "Form2", "2500")
        f2_2505 = self.get_val(cursor, "Form2", "2505")
        f2_2510 = self.get_val(cursor, "Form2", "2510")
        f2_2515 = self.get_val(cursor, "Form2", "2515")
        f2_2520 = self.get_val(cursor, "Form2", "2520")

        conn.close()

        costs = f2_2500 + f2_2505 + f2_2510 + f2_2515 + f2_2520

        k_values = [
            self.safe_div(f1_1160 + f1_1165, f1_1695),
            self.safe_div(f1_1125 + f1_1155 + f1_1160 + f1_1165, f1_1695),
            self.safe_div(f1_1195, f1_1695),
            self.safe_div(f1_1525 + f1_1595 + f1_1695, f1_1495),
            self.safe_div(f1_1495 - f1_1095, f1_1495),
            self.safe_div(f2_2350, costs),
            v18,
            self.safe_div(v19_sk, v20_s),
            v17,
            self.safe_div(v21_k, v20_s),
            self.safe_div(v22_m, v20_s)
        ]

        names = [
            "Коефіцієнт миттєвої ліквідності",
            "Коефіцієнт поточної ліквідності",
            "Коефіцієнт загальної ліквідності",
            "Коефіцієнт фінансової незалежності",
            "Коефіцієнт маневреності власних коштів",
            "Коефіцієнт рентабельності виробництва",
            "Коефіцієнт діяльності минулих років",
            "Коефіцієнт найбільшої суми повернутого кредиту",
            "Термін існування підприємства",
            "Питома вага коштів підприємства",
            "Коефіцієнт власного ліквідного майна"
        ]

        return k_values, names

    def calculate_creditworthiness(self):
        calculated = self.calculate_k_values()

        if calculated is None:
            return

        weights = self.get_weights()

        if weights is None:
            return

        k_values, names = calculated

        mu_values = [self.membership(value) for value in k_values]
        norm_weights = self.normalize_weights(weights)

        self.results = []

        score = 0

        for i in range(11):
            part = round(mu_values[i] * norm_weights[i], 4)
            score += part

            self.results.append((
                f"K{i + 1}",
                names[i],
                round(k_values[i], 4),
                mu_values[i],
                weights[i],
                norm_weights[i],
                part
            ))

        score = round(score, 4)
        category, rating, level = self.get_rating(score)

        self.credit_summary = {
            "score": score,
            "category": category,
            "rating": rating,
            "level": level
        }

        for item in self.tree_res.get_children():
            self.tree_res.delete(item)

        for row in self.results:
            self.tree_res.insert("", tk.END, values=row)

        self.summary_label.config(
            text=f"Агрегована оцінка: {score} | {category} | Рейтинг: {rating} | {level}"
        )

        self.save_credit_results_to_db()
        self.notebook.select(4)

        messagebox.showinfo("Готово", "Кредитоспроможність підприємства успішно оцінено.")

    def save_credit_results_to_db(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM credit_results")

        for row in self.results:
            _, indicator, k_value, mu, weight, norm_weight, part = row
            cursor.execute("""
                INSERT INTO credit_results (
                    indicator, k_value, membership, weight, normalized_weight, result_part
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (indicator, str(k_value), mu, weight, norm_weight, part))

        conn.commit()
        conn.close()

    def export_results(self):
        if not self.results or not self.credit_summary:
            messagebox.showwarning("Увага", "Спочатку оцініть кредитоспроможність.")
            return

        try:
            with open("Кредитоспроможність_Підприємства.csv", mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")

                writer.writerow([
                    "Критерій",
                    "Показник",
                    "Значення K",
                    "Функція належності μ(K)",
                    "Вага",
                    "Нормована вага",
                    "Добуток"
                ])

                for row in self.results:
                    writer.writerow(row)

                writer.writerow([])
                writer.writerow(["Агрегована оцінка", self.credit_summary["score"]])
                writer.writerow(["Категорія", self.credit_summary["category"]])
                writer.writerow(["Рейтинг", self.credit_summary["rating"]])
                writer.writerow(["Рівень", self.credit_summary["level"]])

            messagebox.showinfo(
                "Експорт завершено",
                "Результати збережено у файл Кредитоспроможність_Підприємства.csv"
            )

        except Exception as error:
            messagebox.showerror("Помилка експорту", str(error))

    def test_program(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM form_data")
        form_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM additional_info")
        extra_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM credit_results")
        credit_count = cursor.fetchone()[0]

        conn.close()

        csv_exists = Path("Кредитоспроможність_Підприємства.csv").exists()

        messagebox.showinfo(
            "Тестування програми",
            f"Записів у form_data: {form_count}\n"
            f"Записів у additional_info: {extra_count}\n"
            f"Записів у credit_results: {credit_count}\n\n"
            f"CSV з результатами: {'створено' if csv_exists else 'не створено'}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = CreditworthinessApp(root)
    root.mainloop()