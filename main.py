import tkinter as tk
import psutil
import sqlite3
import time
from threading import Thread
from tkinter import messagebox

class ResourceMonitor:
    def __init__(self, interval=1):
        self.interval = interval
        self.recording = False
        self.start_time = None

    def start_recording(self):
        self.recording = True
        self.start_time = time.time()
        Thread(target=self.record).start()

    def stop_recording(self):
        self.recording = False

    def record(self):
        # Создаем соединение с базой данных в этом потоке
        db_connection = sqlite3.connect('resource_monitor.db')
        cursor = db_connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS resources
                          (timestamp TEXT, cpu REAL, memory REAL, disk REAL)''')
        db_connection.commit()

        while self.recording:
            try:
                cpu = psutil.cpu_percent()
                memory_info = psutil.virtual_memory()
                disk_info = psutil.disk_usage('/')
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO resources (timestamp, cpu, memory, disk) VALUES (?, ?, ?, ?)",
                               (timestamp, cpu, memory_info.percent, disk_info.percent))
                db_connection.commit()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Error while recording data: {e}")
                self.stop_recording()
                break

        db_connection.close()  # Закрываем соединение после завершения записи

    def get_resources(self):
        cpu = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        return cpu, memory_info, disk_info

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Resource Monitor")
        self.monitor = ResourceMonitor()
        self.is_recording = False
        self.timer_start_time = None

        # Интерфейс
        self.cpu_label = tk.Label(root, text="CPU: 0%")
        self.cpu_label.pack()

        self.memory_label = tk.Label(root, text="ОЗУ (Свободно/Всего): 0% / 0%")
        self.memory_label.pack()

        self.disk_label = tk.Label(root, text="ПЗУ (Свободно/Всего): 0% / 0%")
        self.disk_label.pack()

        self.interval_label = tk.Label(root, text="Интервал обновления (сек):")
        self.interval_label.pack()

        self.interval_entry = tk.Entry(root)
        self.interval_entry.insert(0, "1")  # Значение по умолчанию
        self.interval_entry.pack()

        self.record_button = tk.Button(root, text="Начать запись", command=self.start_recording)
        self.record_button.pack()

        self.stop_button = tk.Button(root, text="Остановить", command=self.stop_recording)
        self.stop_button.pack()
        self.stop_button.pack_forget()

        self.timer_label = tk.Label(root, text="Время записи: 0 сек")
        self.timer_label.pack()

        self.update_resources()

    def update_resources(self):
        cpu, memory_info, disk_info = self.monitor.get_resources()
        self.cpu_label.config(text=f"CPU: {cpu}%")
        self.memory_label.config(text=f"ОЗУ (Свободно/Всего): {memory_info.available / (1024 ** 2):.2f} MB / {memory_info.total / (1024 ** 2):.2f} MB")
        self.disk_label.config(text=f"ПЗУ (Свободно/Всего): {disk_info.free / (1024 ** 2):.2f} MB / {disk_info.total / (1024 ** 2):.2f} MB")
        self.root.after(1000, self.update_resources)

    def start_recording(self):
        try:
            interval = int(self.interval_entry.get())
            if interval <= 0:
                raise ValueError("Интервал должен быть положительным числом.")
            self.monitor.interval = interval
            self.monitor.start_recording()
            self.is_recording = True
            self.record_button.pack_forget()
            self.stop_button.pack()
            self.timer_start_time = time.time()
            self.update_timer()
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))

    def stop_recording(self):
        self.monitor.stop_recording()
        self.is_recording = False
        self.stop_button.pack_forget()
        self.record_button.pack()
        self.timer_label.config(text="Время записи: 0 сек")

    def update_timer(self):
        if self.is_recording:
            elapsed_time = int(time.time() - self.timer_start_time)
            self.timer_label.config(text=f"Время записи: {elapsed_time} сек")
            self.root.after(1000, self.update_timer)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
