import tkinter as tk
from tkinter import ttk, scrolledtext
import cv2
import PIL.Image, PIL.ImageTk
import threading
import os
import csv
import datetime
import pyttsx3 
import time  # <--- NEW: For waiting
import google.generativeai as genai
from deepface import DeepFace

# --- CONFIGURATION ---
API_KEY = "KEY"
LOG_FILE = "project_logs.csv"

# Setup Google AI
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("System: Google AI Connected.")
except:
    print("Error: API Key is invalid.")

class FinalProjectApp:
    def __init__(self, root):
        self.window = root
        self.window.title("Smart Vision System")
        self.window.geometry("1300x750")
        self.window.configure(bg="#202124")
        self.is_running = True
        self.window.protocol("WM_DELETE_WINDOW", self.shutdown)

        # Voice
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)

        # Log File
        self.create_log_file()

        # --- GUI ---
        self.status = tk.StringVar()
        self.status.set("System Ready")
        tk.Label(root, textvariable=self.status, bg="#202124", fg="cyan", font=("Arial", 14)).pack(pady=10)

        self.frame_left = tk.Frame(root, bg="#202124")
        self.frame_left.pack(side=tk.LEFT, padx=20)
        
        self.cam_label = tk.Label(self.frame_left, bd=2, relief=tk.SOLID)
        self.cam_label.pack()
        
        self.name_label = tk.Label(self.frame_left, text="Identity: ---", bg="black", fg="white", 
                                   font=("Courier", 18, "bold"), width=20)
        self.name_label.pack(pady=10)

        self.btn_scan = tk.Button(self.frame_left, text="SCAN (Space)", command=self.run_scan, 
                                  bg="blue", fg="white", font=("Arial", 12, "bold"), width=20)
        self.btn_scan.pack(pady=5)

        self.btn_logs = tk.Button(self.frame_left, text="OPEN LOGS", command=self.open_excel, 
                                  bg="orange", fg="black", font=("Arial", 12, "bold"), width=20)
        self.btn_logs.pack(pady=5)

        self.frame_right = tk.Frame(root, bg="#303134")
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(self.frame_right, text="AI Analysis Output", font=("Arial", 16), bg="#303134", fg="white").pack(pady=5)
        
        self.text_box = scrolledtext.ScrolledText(self.frame_right, font=("Consolas", 11), bg="#1e1e1e", fg="white")
        self.text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.cap = cv2.VideoCapture(0)
        self.scanning = False
        
        self.window.bind('<space>', lambda e: self.run_scan())
        self.show_camera()

    def create_log_file(self):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Detected Person", "Description"])

    def show_camera(self):
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                cv2.rectangle(frame, (150, 100), (500, 380), (0, 255, 0), 2)
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(img)
                img_tk = PIL.ImageTk.PhotoImage(image=img)
                self.cam_label.imgtk = img_tk
                self.cam_label.configure(image=img_tk)
            self.window.after(10, self.show_camera)

    def shutdown(self):
        self.is_running = False
        self.cap.release()
        self.window.destroy()

    def open_excel(self):
        import platform
        if platform.system() == 'Darwin':
            os.system(f"open {LOG_FILE}")
        else:
            os.startfile(LOG_FILE)

    def speak(self, text):
        def voice_thread():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except: pass
        threading.Thread(target=voice_thread).start()

    def run_scan(self):
        if not self.scanning:
            self.scanning = True
            t = threading.Thread(target=self.process_image)
            t.start()

    def process_image(self):
        ret, frame = self.cap.read()
        if not ret: return

        self.update_status("Processing...")
        self.update_text("", clear=True)
        print("\n--- New Scan Started ---")

        person_name = "Unknown"

        # 1. Check Face
        try:
            print("Step 1: Checking Face...")
            dfs = DeepFace.find(img_path=frame, db_path="dataset", model_name="VGG-Face", 
                                enforce_detection=True, silent=True)
            if len(dfs) > 0 and not dfs[0].empty:
                path = dfs[0].iloc[0]['identity']
                person_name = path.split('/')[-2]
                print(f"Face Result: {person_name}")
            else:
                print("Face Result: Unknown Person")
                person_name = "Unknown"
        except:
            print("Face Result: No Face (Object)")
            person_name = "Object"

        color = "green" if person_name != "Object" and person_name != "Unknown" else "red"
        self.update_label(f"ID: {person_name}", color)

        # 2. Check Object (WITH RETRY LOGIC)
        try:
            self.update_status("Contacting Google AI...")
            print("Step 2: Sending to Gemini...")
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = PIL.Image.fromarray(rgb_frame)

            context = ""
            if person_name != "Object":
                context = f"Note: The person is identified as {person_name}."

            prompt = f"Describe the main subject in this image concisely in 2 sentences. {context}"

            # --- RETRY LOOP FOR ERROR 429 ---
            result = "Error"
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = model.generate_content([prompt, pil_img])
                    result = response.text
                    break # Success! Exit the loop
                except Exception as e:
                    if "429" in str(e):
                        print(f"Server Busy (429). Waiting 3 seconds... (Attempt {attempt+1}/{max_retries})")
                        self.update_status(f"Server busy... Retrying ({attempt+1})")
                        time.sleep(3) # Wait before trying again
                    else:
                        raise e # If it's another error, crash normally
            # --------------------------------

            # PRINT TO TERMINAL
            print(f"Gemini Result: {result}")

            self.update_text(f"RESULT:\n{result}")
            self.save_log(person_name, result)
            self.speak(result)

        except Exception as e:
            error_msg = f"Error: {e}"
            print(error_msg)
            self.update_text(error_msg)

        self.update_status("Ready")
        self.scanning = False

    def save_log(self, name, desc):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        clean_desc = desc.replace("\n", " ")

        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date_str, time_str, name, clean_desc])
        
        print(f"Log saved to {LOG_FILE}")

    # Helpers
    def update_label(self, text, color):
        if self.is_running: self.window.after(0, lambda: self.name_label.config(text=text, fg=color))

    def update_text(self, text, clear=False):
        if self.is_running:
            def task():
                if clear: self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, text)
            self.window.after(0, task)

    def update_status(self, text):
        if self.is_running: self.window.after(0, lambda: self.status.set(text))

if __name__ == "__main__":
    if not os.path.exists("dataset"):
        os.makedirs("dataset")
    root = tk.Tk()
    app = FinalProjectApp(root)
    root.mainloop()
