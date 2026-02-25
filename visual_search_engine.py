import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import cv2
import PIL.Image, PIL.ImageTk
import threading
import os
import csv
import datetime
import pyttsx3 
import time
from deepface import DeepFace
from ultralytics import YOLO 
from google import genai      # Modern 2026 Library
from google.genai import types

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
API_KEY = "PASTE_YOUR_AIza_KEY_HERE"
LOG_FILE = "project_logs.csv"
CAMERA_SOURCE = 0 
ADMIN_FOLDER_NAME = "Mahi_admin" 
# ==========================================

class SimpleVisionSystem:
    def __init__(self, root):
        self.window = root
        self.window.title(f"Security System | Admin: {ADMIN_FOLDER_NAME}")
        self.window.geometry("1250x750")
        self.window.configure(bg="#202124")
        
        self.is_running = True
        self.system_locked = True
        self.static_mode = False
        self.static_image = None
        self.current_user = "Unknown"
        self.last_intruder_time = 0
        self.scanning = False 
        
        # Rate Limiting
        self.last_api_call = 0 
        self.api_cooldown = 10 
        
        # --- NEW GENAI CLIENT SETUP ---
        self.client = None
        try:
            self.client = genai.Client(api_key=API_KEY)
        except Exception as e:
            print(f"AI Connection Error: {e}")

        self.engine = pyttsx3.init()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # M4 Optimization: Load YOLO
        self.yolo = YOLO("yolov8m.pt") 
        
        self.create_log_file()
        self.window.protocol("WM_DELETE_WINDOW", self.shutdown)

        # --- GUI LAYOUT ---
        self.window.columnconfigure(0, weight=3)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)

        self.frame_cam = tk.Frame(root, bg="black", bd=2, relief=tk.RIDGE)
        self.frame_cam.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.lbl_info = tk.Label(self.frame_cam, text="🔒 SYSTEM LOCKED - SCANNING...", 
                                 bg="black", fg="red", font=("Arial", 20, "bold"))
        self.lbl_info.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.lbl_video = tk.Label(self.frame_cam, bg="black")
        self.lbl_video.pack(expand=True, fill=tk.BOTH)

        self.frame_ctrl = tk.Frame(root, bg="#333333", bd=2, relief=tk.RAISED)
        self.frame_ctrl.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(self.frame_ctrl, text="CONTROL PANEL", bg="#333", fg="white", font=("Arial", 14, "bold")).pack(pady=15)

        frame_set = tk.LabelFrame(self.frame_ctrl, text="Settings", bg="#333", fg="white")
        frame_set.pack(fill=tk.X, padx=10, pady=10)
        
        self.var_face = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_set, text="Show Identity Boxes", variable=self.var_face, bg="#333", fg="white", selectcolor="black").pack(anchor="w", padx=5)
        
        self.var_obj = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_set, text="Show Object Boxes", variable=self.var_obj, bg="#333", fg="white", selectcolor="black").pack(anchor="w", padx=5)
        
        self.var_voice = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_set, text="Enable Voice", variable=self.var_voice, bg="#333", fg="white", selectcolor="black").pack(anchor="w", padx=5)

        self.btn_gemini = tk.Button(self.frame_ctrl, text="✨ ASK AI (Spacebar)", command=self.ask_gemini, 
                                    bg="gray", fg="white", font=("Arial", 12, "bold"), state="disabled", height=2)
        self.btn_gemini.pack(fill=tk.X, padx=10, pady=20)

        self.txt_log = scrolledtext.ScrolledText(self.frame_ctrl, height=15, font=("Consolas", 9), bg="black", fg="#00ff00")
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.btn_cam = tk.Button(self.frame_ctrl, text="Switch to Live Camera", command=self.use_camera, state="disabled")
        self.btn_cam.pack(fill=tk.X, padx=10, pady=2)
        self.btn_file = tk.Button(self.frame_ctrl, text="Upload Image for Analysis", command=self.use_file, state="disabled")
        self.btn_file.pack(fill=tk.X, padx=10, pady=2)

        self.cap = cv2.VideoCapture(CAMERA_SOURCE)
        self.window.bind('<space>', lambda e: self.ask_gemini())
        
        self.update_video()
        threading.Thread(target=self.security_loop, daemon=True).start()

    def safe_log(self, text):
        if not self.is_running: return
        self.window.after(0, lambda: self._log_impl(text))

    def _log_impl(self, text):
        t = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{t}] {text}\n")
        self.txt_log.see(tk.END)

    def safe_unlock_ui(self):
        self.window.after(0, self._unlock_impl)

    def _unlock_impl(self):
        self.lbl_info.config(text=f"🔓 ACCESS GRANTED: {ADMIN_FOLDER_NAME}", fg="#00ff00")
        self.btn_gemini.config(state="normal", bg="#007acc")
        self.btn_cam.config(state="normal")
        self.btn_file.config(state="normal")

    def create_log_file(self):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', newline='') as f:
                csv.writer(f).writerow(["Date", "Time", "Event", "Detail"])

    def unlock_system(self):
        self.system_locked = False
        self.speak(f"Welcome Administrator {ADMIN_FOLDER_NAME}")
        self.safe_unlock_ui()
        self.safe_log(f"System Unlocked by {ADMIN_FOLDER_NAME}")

    def security_loop(self):
        intruder_dir = os.path.abspath("intruders")
        if not os.path.exists(intruder_dir): os.makedirs(intruder_dir)

        while self.is_running:
            if self.static_mode: 
                time.sleep(1); continue
            
            ret, frame = self.cap.read()
            if not ret or frame is None: continue

            # --- CRITICAL RESET ---
            # Every loop starts with the assumption that no one is found
            is_admin_found = False
            self.current_user = "Unknown" 

            try:
                if self.system_locked or self.var_face.get():
                    dfs = DeepFace.find(img_path=frame, 
                                       db_path="dataset", 
                                       model_name="VGG-Face", 
                                       distance_metric="cosine", 
                                       enforce_detection=False, 
                                       silent=True)
                    
                    if len(dfs) > 0 and not dfs[0].empty:
                        result = dfs[0].iloc[0]
                        dist = result['distance']
                        folder_name = os.path.basename(os.path.dirname(result['identity']))
                        
                        # Strict check: Must be admin AND must be high confidence
                        if folder_name == ADMIN_FOLDER_NAME and dist < 0.30: # Tightened to 0.30
                            self.current_user = ADMIN_FOLDER_NAME
                            is_admin_found = True
                            if self.system_locked:
                                self.unlock_system()

                # --- AUTO-LOCK LOGIC ---
                # If we are unlocked but the admin is no longer visible
                if not self.system_locked and not is_admin_found:
                    # Optional: Add a timer here if you want it to wait 5 seconds 
                    # before locking again, otherwise it locks the instant you move.
                    pass 

                # --- INTRUDER CAPTURE ---
                if self.system_locked and not is_admin_found:
                    # Only capture if a physical face is detected by the camera
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    if len(faces) > 0:
                        if time.time() - self.last_intruder_time > 5:
                            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            full_path = os.path.join(intruder_dir, f"Intruder_{ts}.jpg")
                            cv2.imwrite(full_path, frame)
                            self.safe_log(f"⚠️ BLOCKED UNKNOWN USER")
                            self.last_intruder_time = time.time()

            except Exception as e:
                self.current_user = "Unknown"
            
            time.sleep(0.4)

    def update_video(self):
        if not self.is_running: return
        frame = self.static_image.copy() if self.static_mode and self.static_image is not None else None
        if not self.static_mode:
            ret, cam_frame = self.cap.read()
            if ret: frame = cam_frame
        if frame is not None:
            h, w, _ = frame.shape
            if self.var_face.get() or self.system_locked:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 8)
                for (x, y, wb, hb) in faces:
                    label = self.current_user
                    color = (0, 255, 0) if label == ADMIN_FOLDER_NAME else (0, 255, 255)
                    if label == "Unknown": color = (0, 0, 255)
                    cv2.rectangle(frame, (x, y), (x+wb, y+hb), color, 2)
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            if not self.system_locked and self.var_obj.get():
                results = self.yolo(frame, verbose=False, conf=0.60)
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        label = self.yolo.names[int(box.cls[0])].title()
                        if label == "Person": continue 
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(img)
            img.thumbnail((800, 600))
            imgtk = PIL.ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)
        self.window.after(30, self.update_video)

    def ask_gemini(self):
        if self.system_locked or self.scanning: return
        if time.time() - self.last_api_call < self.api_cooldown:
            self.safe_log(f"⚠️ Cooldown active.")
            return
        self.scanning = True
        threading.Thread(target=self.run_gemini).start()

    def run_gemini(self):
        self.safe_log("Analyzing with Gemini...")
        self.last_api_call = time.time()
        ret, frame = self.cap.read() if not self.static_mode else (True, self.static_image)
        if not ret or frame is None: 
            self.scanning = False
            return
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = PIL.Image.fromarray(rgb)
            pil_img.thumbnail((640, 640))
            
            # MODERN 2026 API CALL
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=["Describe this scene concisely. List key objects.", pil_img]
            )
            self.safe_log(f"AI: {response.text}")
            self.speak(response.text)
        except Exception as e:
            self.safe_log(f"AI Error: {e}")
        self.scanning = False

    def use_file(self):
        path = filedialog.askopenfilename()
        if path:
            img = cv2.imread(path)
            if img is not None:
                self.static_image, self.static_mode = img, True
                self.safe_log("Image Loaded.")

    def use_camera(self):
        self.static_mode = False
        self.safe_log("Live Camera Active.")

    def speak(self, text):
        if not self.var_voice.get(): return
        def t():
            import platform
            clean = text.replace("*", "")
            if platform.system() == 'Darwin': os.system(f'say "{clean}"')
            else: 
                try:
                    self.engine.say(clean)
                    self.engine.runAndWait()
                except: pass
        threading.Thread(target=t).start()

    def shutdown(self):
        self.is_running = False
        self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleVisionSystem(root)
    root.mainloop()