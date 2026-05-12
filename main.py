import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
from pathlib import Path

DB_NAME = "balance_report_p4.db"

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


class BalanceReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Розрахунок показників платоспроможності")
        self.root.geometry("1100x760")
        self.root.configure(bg="#edf2f7")

        self.entries_f1 = {}
        self.entries_f2 = {}
        self.extra_entries = []
        self.results = []

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
        self.build_results_tab()
        self.build_bottom_bar(main)

    def build_header(self):
        header = tk.Frame(self.root, bg="#1e3a8a", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        ttk.Label(
            header,
            text="Розрахунок фінансових показників підприємства",
            style="Header.TLabel"
        ).pack(anchor="w", padx=24, pady=(16, 0))

        ttk.Label(
            header,
            text="Показники платоспроможності K1–K11 на основі Форми №1, Форми №2 та V17–V22",
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=26, pady=(4, 0))

    def build_bottom_bar(self, parent):
        bottom = ttk.Frame(parent, padding=(0, 14, 0, 0))
        bottom.pack(fill="x")

        self.status_label = ttk.Label(
            bottom,
            text="Збережіть Форму №1, Форму №2 та додаткові показники",
            background="#edf2f7",
            foreground="#64748b",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left")

        ttk.Button(
            bottom,
            text="Тестування",
            style="Accent.TButton",
            command=self.test_database_and_export
        ).pack(side="right", padx=8)

        self.btn_calculate = ttk.Button(
            bottom,
            text="Розрахувати K1–K11",
            style="Success.TButton",
            command=self.calculate_indicators,
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

            ttk.Label(parent, text=name, background="#ffffff", width=55).grid(
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
                width=70
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

    def build_results_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Фінансові показники")

        card = ttk.Frame(tab, style="Card.TFrame", padding=14)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        ttk.Label(
            card,
            text="Результати розрахунку показників платоспроможності",
            style="Title.TLabel"
        ).pack(anchor="w", pady=(0, 12))

        self.tree_res = ttk.Treeview(
            card,
            columns=("Group", "Indicator", "Formula", "Value"),
            show="headings",
            height=16
        )

        self.tree_res.heading("Group", text="Група")
        self.tree_res.heading("Indicator", text="Показник")
        self.tree_res.heading("Formula", text="Формула")
        self.tree_res.heading("Value", text="Значення")

        self.tree_res.column("Group", width=70, anchor="center")
        self.tree_res.column("Indicator", width=360)
        self.tree_res.column("Formula", width=310)
        self.tree_res.column("Value", width=140, anchor="center")

        self.tree_res.pack(expand=True, fill="both")

        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=12)

        ttk.Button(
            btn_frame,
            text="Розрахувати показники",
            style="Success.TButton",
            command=self.calculate_indicators
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
                text="Усі дані збережено. Можна розрахувати фінансові показники.",
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
            return "Ділення на 0"
        return round(numerator / denominator, 4)

    def calculate_indicators(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT v17, v18, v19, v20, v21, v22 FROM additional_info")
        extra = cursor.fetchone()

        if not extra:
            conn.close()
            messagebox.showwarning("Увага", "Спочатку збережіть додаткову інформацію.")
            return

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

        costs = f2_2500 + f2_2505 + f2_2510 + f2_2515 + f2_2520

        k1 = self.safe_div(f1_1160 + f1_1165, f1_1695)
        k2 = self.safe_div(f1_1125 + f1_1155 + f1_1160 + f1_1165, f1_1695)
        k3 = self.safe_div(f1_1195, f1_1695)
        k4 = self.safe_div(f1_1525 + f1_1595 + f1_1695, f1_1495)
        k5 = self.safe_div(f1_1495 - f1_1095, f1_1495)

        k6 = self.safe_div(f2_2350, costs)
        k7 = v18
        k8 = self.safe_div(v19_sk, v20_s)

        k9 = v17
        k10 = self.safe_div(v21_k, v20_s)
        k11 = self.safe_div(v22_m, v20_s)

        self.results = [
            ("G1", "K1 — Коефіцієнт миттєвої ліквідності", "(1160 + 1165) / 1695", k1),
            ("G1", "K2 — Коефіцієнт поточної ліквідності", "(1125 + 1155 + 1160 + 1165) / 1695", k2),
            ("G1", "K3 — Коефіцієнт загальної ліквідності", "1195 / 1695", k3),
            ("G1", "K4 — Коефіцієнт фінансової незалежності", "(1525 + 1595 + 1695) / 1495", k4),
            ("G1", "K5 — Коефіцієнт маневреності власних коштів", "(1495 - 1095) / 1495", k5),

            ("G2", "K6 — Коефіцієнт рентабельності виробництва", "2350 / (2500 + 2505 + 2510 + 2515 + 2520)", k6),
            ("G2", "K7 — Коефіцієнт діяльності минулих років", "V18", k7),
            ("G2", "K8 — Коефіцієнт найбільшої суми повернутого кредиту", "V19 / V20", k8),

            ("G3", "K9 — Термін існування підприємства", "V17", k9),
            ("G3", "K10 — Питома вага коштів підприємства", "V21 / V20", k10),
            ("G3", "K11 — Коефіцієнт власного ліквідного майна", "V22 / V20", k11)
        ]

        for item in self.tree_res.get_children():
            self.tree_res.delete(item)

        for row in self.results:
            self.tree_res.insert("", tk.END, values=row)

        conn.close()

        self.notebook.select(3)
        messagebox.showinfo("Готово", "Фінансові показники K1–K11 успішно розраховано.")

    def export_results(self):
        if not self.results:
            messagebox.showwarning("Увага", "Спочатку розрахуйте показники.")
            return

        try:
            with open("Фінансові_Показники_K1_K11.csv", mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(["Група", "Показник", "Формула", "Значення"])

                for row in self.results:
                    writer.writerow(row)

            messagebox.showinfo(
                "Експорт завершено",
                "Результати збережено у файл Фінансові_Показники_K1_K11.csv"
            )

        except Exception as error:
            messagebox.showerror("Помилка експорту", str(error))

    def test_database_and_export(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM form_data")
        form_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM additional_info")
        extra_count = cursor.fetchone()[0]

        conn.close()

        csv_exists = Path("Фінансові_Показники_K1_K11.csv").exists()

        messagebox.showinfo(
            "Тестування програми",
            f"Записів у таблиці form_data: {form_count}\n"
            f"Записів у таблиці additional_info: {extra_count}\n\n"
            f"CSV з фінансовими показниками: {'створено' if csv_exists else 'не створено'}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = BalanceReportApp(root)
    root.mainloop()