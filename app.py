import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os

class ECGGraphWindow(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title("💓 گراف ۳۰ روزه عملکرد و رشد (طرح نوار قلب)")
        self.geometry("900x550")
        self.configure(bg="#0a0a0a")
        self.data = data
        
        lbl = tk.Label(self, text="💓 گراف نبض عملکرد و رشد ۳۰ روزه شما", font=("Tahoma", 13, "bold"), fg="#00FF66", bg="#0a0a0a")
        lbl.pack(pady=10)

        self.canvas = tk.Canvas(self, bg="#050d08", highlightthickness=1, highlightbackground="#00FF66")
        self.canvas.pack(fill="both", expand=True, padx=20, pady=10)

        self.draw_ecg_graph()

    def draw_ecg_graph(self):
        self.update()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        margin_left = 60
        margin_right = 30
        margin_top = 40
        margin_bottom = 60

        graph_w = w - margin_left - margin_right
        graph_h = h - margin_top - margin_bottom

        # ۱. رسم شبکه شطرنجی پس‌زمینه (Grid)
        for i in range(0, 31, 5):
            x = margin_left + (i / 30 * graph_w)
            self.canvas.create_line(x, margin_top, x, h - margin_bottom, fill="#0f2617", width=1)

        for y_val in range(0, 101, 20):
            y = (h - margin_bottom) - (y_val / 100 * graph_h)
            self.canvas.create_line(margin_left, y, w - margin_right, y, fill="#0f2617", width=1)
            # درجه‌بندی Y (0% to 100%)
            self.canvas.create_text(margin_left - 25, y, text=f"{y_val}%", font=("Tahoma", 9, "bold"), fill="#00FF66")

        # ۲. محورهای اصلی (Axes)
        self.canvas.create_line(margin_left, margin_top, margin_left, h - margin_bottom, fill="#00FF66", width=2)
        self.canvas.create_line(margin_left, h - margin_bottom, w - margin_right, h - margin_bottom, fill="#00FF66", width=2)

        # ۳. نمایش شماره روزهای ۱ تا ۳۰ در پایین
        step_x = graph_w / 30
        for day_num in range(1, 31):
            x = margin_left + (day_num - 1) * step_x + (step_x / 2)
            self.canvas.create_text(x, h - margin_bottom + 18, text=str(day_num), font=("Tahoma", 8, "bold"), fill="#00FF66")

        dates = sorted(list(self.data.keys()))
        if not dates:
            return

        points = []
        for idx, d in enumerate(dates):
            p = self.data[d]["percent"]
            # نگاشت هر ثبت بر روی روزهای ۱ تا ۳۰
            day_index = min(idx, 29) # بر اساس ترتیب ثبت روزها
            x = margin_left + (day_index) * step_x + (step_x / 2)
            y = (h - margin_bottom) - (p / 100 * graph_h)
            points.append((x, y, p, d))

        # ۴. رسم خط پیوسته نوار قلب و نقاط رشد
        for i in range(len(points)):
            x, y, p, d = points[i]

            if i == 0:
                # خط اولیه از محور تا اولین روز
                start_y = h - margin_bottom
                self.canvas.create_line(margin_left, start_y, x, y, fill="#00FF66", width=2.5)
            else:
                prev_x, prev_y, prev_p, _ = points[i-1]
                line_color = "#00FF66" if p >= prev_p else "#FF2233" # سبز برای صعود، قرمز برای نزول
                
                # رسم حالت نبض‌دار نوار قلب
                mid_x = (prev_x + x) / 2
                self.canvas.create_line(prev_x, prev_y, mid_x - 5, prev_y, fill=line_color, width=2)
                self.canvas.create_line(mid_x - 5, prev_y, mid_x, y, fill=line_color, width=3) # قله ضربان
                self.canvas.create_line(mid_x, y, x, y, fill=line_color, width=2.5)

            # دایره نقطه عملکرد
            node_color = "#00FF66" if p >= 50 else "#FF2233"
            self.canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill=node_color, outline="white", width=1.5)

            # متن درصد بالای نقطه
            self.canvas.create_text(x, y - 16, text=f"{p}%", font=("Tahoma", 9, "bold"), fill=node_color)
            # نمایش تاریخ زیر شماره روز
            self.canvas.create_text(x, h - margin_bottom + 35, text=d[-5:], font=("Tahoma", 7), fill="#888888")


class AdvancedTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("برنامه هوشمند مدیریت فعالیت‌ها و رشد روزانه")
        self.root.geometry("850x720")
        self.filename = "advanced_tracker_data.json"
        self.config_file = "activities_config.json"
        
        self.activities = self.load_activities()
        self.data = self.load_data()

        title = tk.Label(root, text="جدول پیگیری کارهای روزانه و میزان رشد", font=("Tahoma", 13, "bold"), fg="#1A237E")
        title.pack(pady=5)

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_today = ttk.Frame(notebook)
        notebook.add(self.tab_today, text="ثبت عملکرد امروز")
        
        self.tab_manage = ttk.Frame(notebook)
        notebook.add(self.tab_manage, text="مدیریت فعالیت‌ها (افزودن/حذف)")

        self.setup_today_tab()
        self.setup_manage_tab()

        # Bottom Report and Graph
        frame_report = tk.LabelFrame(root, text=" جدول عملکرد و وضعیت رشد ", font=("Tahoma", 10, "bold"), padx=10, pady=5)
        frame_report.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("date", "total_acts", "percent", "status")
        self.tree = ttk.Treeview(frame_report, columns=columns, show="headings", height=5)
        
        self.tree.heading("date", text="تاریخ")
        self.tree.heading("total_acts", text="تعداد فعالیت‌ها")
        self.tree.heading("percent", text="میزان رشد (درصد کل)")
        self.tree.heading("status", text="وضعیت نسبت به قبل")

        self.tree.column("date", anchor="center", width=110)
        self.tree.column("total_acts", anchor="center", width=100)
        self.tree.column("percent", anchor="center", width=130)
        self.tree.column("status", anchor="center", width=200)

        self.tree.pack(fill="both", expand=True)

        btn_graph = tk.Button(root, text="💓 مشاهده گراف ۳۰ روزه نوار قلب رشد (ECG)", bg="#00897B", fg="white", font=("Tahoma", 11, "bold"), command=self.show_graph)
        btn_graph.pack(fill="x", padx=10, pady=8)

        self.update_report_table()

    def load_activities(self):
        default = ["نماز پنج‌گانه", "تلاوت قرآن", "ورزش روزانه", "مطالعه انگلیسی", "مطالعه چینی", "کارهای شخصی / کاری"]
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_activities(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.activities, f, ensure_ascii=False, indent=4)

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def setup_today_tab(self):
        for widget in self.tab_today.winfo_children():
            widget.destroy()

        today_str = datetime.now().strftime("%Y-%m-%d")
        lbl_date = tk.Label(self.tab_today, text=f"ثبت فعالیت‌های روز: {today_str}", font=("Tahoma", 10, "bold"), fg="#2E7D32")
        lbl_date.pack(pady=3)

        canvas = tk.Canvas(self.tab_today)
        scrollbar = ttk.Scrollbar(self.tab_today, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5)
        scrollbar.pack(side="right", fill="y")

        self.sliders = {}
        for act in self.activities:
            f = ttk.Frame(scroll_frame)
            f.pack(fill="x", expand=True, pady=3, padx=10)

            lbl = tk.Label(f, text=act, font=("Tahoma", 9), width=22, anchor="e")
            lbl.pack(side="right", padx=5)

            val_lbl = tk.Label(f, text="0%", font=("Tahoma", 9, "bold"), width=6, fg="#1565C0")
            val_lbl.pack(side="left", padx=5)

            scale = ttk.Scale(f, from_=0, to=100, orient="horizontal", command=lambda v, l=val_lbl: l.config(text=f"{int(float(v))}%"))
            scale.set(0)
            scale.pack(side="right", fill="x", expand=True, padx=5)

            self.sliders[act] = scale

        btn_save = tk.Button(self.tab_today, text="💾 ثبت نهایی عملکرد امروز", bg="#2E7D32", fg="white", font=("Tahoma", 10, "bold"), command=self.save_today)
        btn_save.pack(fill="x", padx=15, pady=5)

    def setup_manage_tab(self):
        for widget in self.tab_manage.winfo_children():
            widget.destroy()

        frame_add = tk.LabelFrame(self.tab_manage, text=" افزودن فعالیت جدید ", font=("Tahoma", 9, "bold"), padx=10, pady=5)
        frame_add.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_add, text="نام فعالیت جدید:", font=("Tahoma", 9)).pack(side="right", padx=5)
        self.entry_new_act = tk.Entry(frame_add, font=("Tahoma", 9), justify="right")
        self.entry_new_act.pack(side="right", fill="x", expand=True, padx=5)

        btn_add = tk.Button(frame_add, text="افزودن", bg="#1976D2", fg="white", font=("Tahoma", 9, "bold"), command=self.add_activity)
        btn_add.pack(side="left", padx=5)

        frame_list = tk.LabelFrame(self.tab_manage, text=" لیست فعالیت‌های فعلی ", font=("Tahoma", 9, "bold"), padx=10, pady=5)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(frame_list, font=("Tahoma", 9), justify="right")
        self.listbox.pack(fill="both", expand=True, side="right", padx=5)

        btn_del = tk.Button(frame_list, text="حذف انتخاب‌شده", bg="#D32F2F", fg="white", font=("Tahoma", 9), command=self.delete_activity)
        btn_del.pack(side="left", anchor="n", padx=5)

        self.refresh_activities_list()

    def add_activity(self):
        name = self.entry_new_act.get().strip()
        if name and name not in self.activities:
            self.activities.append(name)
            self.save_activities()
            self.entry_new_act.delete(0, tk.END)
            self.refresh_activities_list()
            self.setup_today_tab()
            messagebox.showinfo("موفقیت", f"فعالیت '{name}' اضافه شد.")

    def delete_activity(self):
        try:
            index = self.listbox.curselection()[0]
            removed = self.activities.pop(index)
            self.save_activities()
            self.refresh_activities_list()
            self.setup_today_tab()
            messagebox.showinfo("حذف شد", f"فعالیت '{removed}' حذف گردید.")
        except IndexError:
            messagebox.showwarning("خطا", "لطفاً یک کار را برای حذف انتخاب کنید.")

    def refresh_activities_list(self):
        self.listbox.delete(0, tk.END)
        for act in self.activities:
            self.listbox.insert("end", act)

    def save_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if not self.activities:
            messagebox.showwarning("خطا", "هیچ فعالیتی تعریف نشده است.")
            return

        total_score = sum(scale.get() for scale in self.sliders.values())
        avg_percent = round(total_score / len(self.activities), 1)

        self.data[today] = {
            "total_acts": len(self.activities),
            "percent": avg_percent
        }

        self.save_data()
        self.update_report_table()
        
        status_msg = "رشد عالی داشتید 🟢👍" if avg_percent >= 60 else "افت عملکرد داشته‌اید 🔴👎"
        messagebox.showinfo("ثبت موفق", f"اطلاعات امروز ثبت شد!\nدرصد کل عملکرد امروز: {avg_percent}%\nوضعیت: {status_msg}")

    def update_report_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        dates = sorted(list(self.data.keys()))
        prev_percent = None

        for d in dates:
            p = self.data[d]["percent"]
            acts = self.data[d]["total_acts"]
            
            if prev_percent is None:
                status = "شروع ثبت ⚪"
            else:
                diff = round(p - prev_percent, 1)
                if diff > 0:
                    status = f"رشد (+{diff}%) 🟢👍"
                elif diff < 0:
                    status = f"افت ({diff}%) 🔴👎"
                else:
                    status = "بدون تغییر 🟡"

            prev_percent = p
            self.tree.insert("", "end", values=(d, acts, f"{p}%", status))

    def show_graph(self):
        if not self.data:
            messagebox.showwarning("هشدار", "هنوز هیچ داده‌ای برای نمایش گراف ثبت نشده است.")
            return
        ECGGraphWindow(self.root, self.data)

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedTrackerApp(root)
    root.mainloop()