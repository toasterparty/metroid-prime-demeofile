from time import time, sleep
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

from recorder import connect, disconnect, take_sample
from demofile import Demofile

# Config #
DEFAULT_SAMPLE_RATE = 10

class MetroidPrimeDemofileGUI:
    def __init__(self, root):
        self.root = root
        self.sample_rate_hz = tk.IntVar(value=DEFAULT_SAMPLE_RATE)
        self.recording = False
        self.record_thread = None
        self.object_count_var = tk.StringVar(value="Object Count: 0")
        self.recording_done_var = tk.StringVar(value="")

        self.setup_ui()

    def setup_ui(self):
        self.root.title("Metroid Prime Demofile")

        explanation_text = """This application allows you to record short movement segments using Dolphin and play them back in-game. This implementation is limited by the number of objects avaiable for the playback. Each room in the game can hold a maximum of 1024 objects and this application will stop recording early when most of that is used. If you are running into this limit your options are:\n    1. Use a slower sample rate\n    2. Reduce the length of the recording.\n    3. Record in a more \"simple\" room."""
        tk.Label(self.root, text=explanation_text, wraplength=500, anchor='w', justify='left').pack(pady=15)

        sample_rate_options = [0.5, 1, 2, 3, 5, 10, 15, 20]
        tk.Label(self.root, text="Sample Rate (Hz)").pack()
        ttk.Combobox(self.root, textvariable=self.sample_rate_hz, values=sample_rate_options, state="readonly").pack()

        tk.Label(self.root, textvariable=self.object_count_var).pack(pady=10)
        tk.Label(self.root, textvariable=self.recording_done_var).pack(pady=10)

        self.start_button = tk.Button(self.root, text="Start Recording", command=self.start_recording)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.root, text="Stop Recording", command=self.stop_recording)

    def record(self):
        try:
            self.filename = f"demos/demofile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            demofile = None
            sample = None
            connect()
            demofile = Demofile(self.sample_rate_hz.get(), self.filename)

            while self.recording:
                start_time = time()
                sample = take_sample()

                demofile.process_sample(sample)

                self.object_count_var.set(f"Object Count: {demofile.object_count()}")

                elapsed_time = time() - start_time
                remaining_time = max(0, (1/self.sample_rate_hz.get()) - elapsed_time)
                sleep(remaining_time)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during recording: {e}")
        finally:
            disconnect()
            self.recording = False
            if demofile and sample:
                demofile.commit(sample)

    def start_recording(self):
        if self.recording:
            return

        self.recording = True

        self.recording_done_var.set("")
        self.start_button.pack_forget()

        self.stop_button.pack(pady=5)

        threading.Thread(target=self.record).start()

    def stop_recording(self):
        self.recording = False
        self.stop_button.pack_forget()
        self.start_button.pack(pady=5)
        self.recording_done_var.set(f"Saved to \"{self.filename}\"")
        self.filename = None

if __name__ == "__main__":
    root = tk.Tk()
    app = MetroidPrimeDemofileGUI(root)
    root.mainloop()
