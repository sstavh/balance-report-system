import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
from pathlib import Path

DB_NAME = "balance_report_full.db"

FORM_1_ROWS = [
    ("1000", "Нематеріальні активи"),
    ("1001", "первісна вартість"),
    ("1002", "накопичена амортизація"),
    ("1010", "Основні засоби"),
    ("1011", "первісна вартість"),
    ("1012", "знос"),
    ("1095", "Усього за розділом I"),
    ("1100", "Запаси"),
    ("1195", "Усього за розділом II"),
    ("1300", "Баланс (Актив)"),
    ("1400", "Зареєстрований капітал"),
    ("1495", "Усього за розділом I (Пасив)"),
    ("1900", "Баланс (Пасив)")
]

FORM_2_ROWS = [
    ("2000", "Чистий дохід від реалізації продукції"),
    ("2050", "Валовий прибуток"),
    ("2055", "Валовий збиток"),
    ("2130", "Адміністративні витрати"),
    ("2290", "Фінансовий результат до оподаткування: прибуток"),
    ("2295", "Фінансовий результат до оподаткування: збиток"),
    ("2350", "Чистий фінансовий результат: прибуток"),
    ("2355", "Чистий фінансовий результат: збиток")
]

EXTRA_LABELS = [
    "V17 — Термін існування підприємства, років",
    "V18 — Градація аналізу прибутків та збитків (0; 5]",
    "V19 — Найбільша сума кредиту, Sk",
    "V20 — Сума запитуваного кредиту, S",
    "V21 — Власні кошти в інвестицію, K",
    "V22 — Вартість ліквідного майна, M"
]

save_status = {
    "Form1": False,
    "Form2": False,
    "Extra": False
}


class BalanceReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Фінансова звітність підприємства")
        self.root.geometry("1040x720")
        self.root.configure(bg="#edf2f7")

        self.entries_f1 = {}
        self.entries_f2 = {}
        self.extra_entries = []

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

        style.configure("Accent.TButton", font=("Arial", 10, "bold"), padding=(14, 8),
                        background="#2563eb", foreground="white")

        style.configure("Success.TButton", font=("Arial", 10, "bold"), padding=(14, 8),
                        background="#16a34a", foreground="white")

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
                col1 TEXT,
                col2 TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS additional_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                v17 TEXT,
                v18 TEXT,
                v19 TEXT,
                v20 TEXT,
                v21 TEXT,
                v22 TEXT
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
        self.build_bottom_bar(main)

    def build_header(self):
        header = tk.Frame(self.root, bg="#1e3a8a", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        ttk.Label(
            header,
            text="Введення та друк балансових звітів",
            style="Header.TLabel"
        ).pack(anchor="w", padx=24, pady=(16, 0))

        ttk.Label(
            header,
            text="Форма №1 «Баланс» та Форма №2 «Звіт про фінансові результати»",
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=26, pady=(4, 0))

    def build_bottom_bar(self, parent):
        bottom = ttk.Frame(parent, padding=(0, 14, 0, 0))
        bottom.pack(fill="x")

        self.status_label = ttk.Label(
            bottom,
            text="Збережіть усі вкладки, щоб активувати попередній перегляд",
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

        self.btn_show_tables = ttk.Button(
            bottom,
            text="Попередній перегляд / друк",
            style="Success.TButton",
            command=self.show_preview_window,
            state="disabled"
        )
        self.btn_show_tables.pack(side="right")

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

            ttk.Label(parent, text=name, background="#ffffff", width=48).grid(
                row=i, column=1, padx=3, pady=4, sticky="w"
            )

            ent1 = ttk.Entry(parent, width=20, justify="center")
            ent1.grid(row=i, column=2, padx=3, pady=4)

            ent2 = ttk.Entry(parent, width=20, justify="center")
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
            "За звітний період",
            "За аналогічний період"
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
                width=64
            ).grid(row=i, column=0, padx=(0, 16), pady=9, sticky="w")

            ent = ttk.Entry(card, width=32, justify="center")
            ent.grid(row=i, column=1, pady=9)

            self.extra_entries.append(ent)

        ttk.Button(
            card,
            text="Зберегти показники",
            style="Accent.TButton",
            command=self.save_extra
        ).grid(row=8, column=0, columnspan=2, pady=24)

    def check_all_saved(self):
        if all(save_status.values()):
            self.btn_show_tables.config(state="normal")
            self.status_label.config(
                text="Усі дані збережено. Можна переглянути та експортувати звіт.",
                foreground="#16a34a"
            )
        else:
            self.btn_show_tables.config(state="disabled")

    def save_data(self, form_type, entries_dict):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM form_data WHERE form_type = ?", (form_type,))

        for code, (ent1, ent2, name) in entries_dict.items():
            val1 = ent1.get().strip()
            val2 = ent2.get().strip()

            if val1 or val2:
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
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM additional_info")

        cursor.execute("""
            INSERT INTO additional_info (v17, v18, v19, v20, v21, v22)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [entry.get().strip() for entry in self.extra_entries])

        conn.commit()
        conn.close()

        save_status["Extra"] = True
        self.check_all_saved()

        messagebox.showinfo("Збережено", "Додаткову інформацію успішно збережено.")

    def export_csv(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            self.write_form_csv(
                cursor,
                "Form1",
                FORM_1_ROWS,
                "Вивід_Форма_1.csv",
                ["Код рядка", "Назва статті", "На початок звітного періоду", "На кінець звітного періоду"]
            )

            self.write_form_csv(
                cursor,
                "Form2",
                FORM_2_ROWS,
                "Вивід_Форма_2.csv",
                ["Код рядка", "Назва статті", "За звітний період", "За аналогічний період"]
            )

            messagebox.showinfo("Експорт завершено", "CSV-файли створено у папці з програмою.")

        except Exception as error:
            messagebox.showerror("Помилка експорту", str(error))

        finally:
            conn.close()

    def write_form_csv(self, cursor, form_type, rows, filename, header):
        names = {code: name for code, name in rows}

        with open(filename, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(header)

            cursor.execute(
                "SELECT row_code, col1, col2 FROM form_data WHERE form_type = ?",
                (form_type,)
            )

            for row_code, col1, col2 in cursor.fetchall():
                writer.writerow([row_code, names.get(row_code, ""), col1, col2])

    def show_preview_window(self):
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Попередній перегляд звіту")
        preview_win.geometry("980x580")
        preview_win.configure(bg="#edf2f7")

        ttk.Label(
            preview_win,
            text="Попередній перегляд перед друком",
            background="#edf2f7",
            foreground="#111827",
            font=("Arial", 17, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 8))

        notebook_prev = ttk.Notebook(preview_win)
        notebook_prev.pack(expand=True, fill="both", padx=20, pady=10)

        self.create_preview_table(
            notebook_prev,
            "Форма №1",
            "Form1",
            FORM_1_ROWS,
            ("Code", "Name", "Start", "End"),
            ("Код", "Назва статті", "На початок", "На кінець")
        )

        self.create_preview_table(
            notebook_prev,
            "Форма №2",
            "Form2",
            FORM_2_ROWS,
            ("Code", "Name", "Period", "PrevPeriod"),
            ("Код", "Назва статті", "Звітний період", "Аналогічний період")
        )

        ttk.Button(
            preview_win,
            text="Експорт у CSV",
            style="Success.TButton",
            command=self.export_csv
        ).pack(pady=14)

    def create_preview_table(self, notebook, title, form_type, rows, columns, headings):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text=title)

        tree = ttk.Treeview(frame, columns=columns, show="headings")

        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)

        tree.column(columns[0], width=90, anchor="center")
        tree.column(columns[1], width=440)
        tree.column(columns[2], width=170, anchor="center")
        tree.column(columns[3], width=170, anchor="center")

        tree.pack(expand=True, fill="both")

        names = {code: name for code, name in rows}

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT row_code, col1, col2 FROM form_data WHERE form_type = ?",
            (form_type,)
        )

        for row_code, col1, col2 in cursor.fetchall():
            tree.insert("", tk.END, values=(row_code, names.get(row_code, ""), col1, col2))

        conn.close()

    def test_database_and_export(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM form_data")
        form_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM additional_info")
        extra_count = cursor.fetchone()[0]

        conn.close()

        csv1_exists = Path("Вивід_Форма_1.csv").exists()
        csv2_exists = Path("Вивід_Форма_2.csv").exists()

        messagebox.showinfo(
            "Тестування програми",
            f"Записів у таблиці form_data: {form_count}\n"
            f"Записів у таблиці additional_info: {extra_count}\n\n"
            f"CSV Форма №1: {'створено' if csv1_exists else 'не створено'}\n"
            f"CSV Форма №2: {'створено' if csv2_exists else 'не створено'}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = BalanceReportApp(root)
    root.mainloop()
