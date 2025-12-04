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
import google.generativeai as genai
from deepface import DeepFace
from ultralytics import YOLO 

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
API_KEY = "KEY"
LOG_FILE = "project_logs.csv"
CAMERA_SOURCE = 0 
ADMIN_FOLDER_NAME = "admin" 
# ==========================================

# Setup Google AI (Global Variable)
model = None
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"AI Warning: {e}")

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
        self.scanning = False # Prevents double-clicking
        
        # Init Engines
        self.engine = pyttsx3.init()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.yolo = YOLO("yolov8m.pt") 
        
        self.create_log_file()
        self.window.protocol("WM_DELETE_WINDOW", self.shutdown)

        # --- GRID LAYOUT ---
        self.window.columnconfigure(0, weight=3)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)

        # === LEFT: CAMERA FEED ===
        self.frame_cam = tk.Frame(root, bg="black", bd=2, relief=tk.RIDGE)
        self.frame_cam.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Overlay Status Label
        self.lbl_info = tk.Label(self.frame_cam, text="🔒 SYSTEM LOCKED - SCANNING...", 
                                 bg="black", fg="red", font=("Arial", 20, "bold"))
        self.lbl_info.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.lbl_video = tk.Label(self.frame_cam, bg="black")
        self.lbl_video.pack(expand=True, fill=tk.BOTH)

        # === RIGHT: CONTROL PANEL ===
        self.frame_ctrl = tk.Frame(root, bg="#333333", bd=2, relief=tk.RAISED)
        self.frame_ctrl.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(self.frame_ctrl, text="CONTROL PANEL", bg="#333", fg="white", font=("Arial", 14, "bold")).pack(pady=15)

        # 1. Settings
        frame_set = tk.LabelFrame(self.frame_ctrl, text="Settings", bg="#333", fg="white")
        frame_set.pack(fill=tk.X, padx=10, pady=10)
        
        self.var_face = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_set, text="Show Identity Boxes", variable=self.var_face, 
                       bg="#333", fg="white", selectcolor="black").pack(anchor="w", padx=5)
        
        self.var_obj = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_set, text="Show Object Boxes", variable=self.var_obj, 
                       bg="#333", fg="white", selectcolor="black").pack(anchor="w", padx=5)
        
        self.var_voice = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_set, text="Enable Voice", variable=self.var_voice, 
                       bg="#333", fg="white", selectcolor="black").pack(anchor="w", padx=5)

        # 2. AI Action
        self.btn_gemini = tk.Button(self.frame_ctrl, text="✨ ASK AI (Spacebar)", command=self.ask_gemini, 
                                    bg="gray", fg="white", font=("Arial", 12, "bold"), state="disabled", height=2)
        self.btn_gemini.pack(fill=tk.X, padx=10, pady=20)

        # 3. Logs
        tk.Label(self.frame_ctrl, text="System Log:", bg="#333", fg="white").pack(anchor="w", padx=10)
        self.txt_log = scrolledtext.ScrolledText(self.frame_ctrl, height=15, font=("Consolas", 9), bg="black", fg="#00ff00")
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 4. Source Buttons
        self.btn_cam = tk.Button(self.frame_ctrl, text="Switch to Live Camera", command=self.use_camera, state="disabled")
        self.btn_cam.pack(fill=tk.X, padx=10, pady=2)
        self.btn_file = tk.Button(self.frame_ctrl, text="Upload Image for Analysis", command=self.use_file, state="disabled")
        self.btn_file.pack(fill=tk.X, padx=10, pady=2)

        # START SYSTEM
        self.cap = cv2.VideoCapture(CAMERA_SOURCE)
        self.window.bind('<space>', lambda e: self.ask_gemini())
        
        self.update_video()
        threading.Thread(target=self.security_loop, daemon=True).start()

    # --- CRITICAL FIX: THREAD-SAFE UI UPDATES ---
    def safe_log(self, text):
        if not self.is_running: return
        # This forces the update to happen on the Main Thread
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

    # -------------------------------------------

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
        """Background Thread: Checks Identity & Traps Intruders"""
        if not os.path.exists("intruders"): os.makedirs("intruders")

        while self.is_running:
            if self.static_mode: 
                time.sleep(1)
                continue

            ret, frame = self.cap.read()
            if not ret: continue

            try:
                if self.system_locked or self.var_face.get():
                    dfs = DeepFace.find(img_path=frame, db_path="dataset", model_name="VGG-Face", 
                                        enforce_detection=True, silent=True)
                    
                    if len(dfs) > 0 and not dfs[0].empty:
                        path = dfs[0].iloc[0]['identity']
                        folder_name = path.split('/')[-2] if '/' in path else path.split('\\')[-2]
                        self.current_user = folder_name
                        
                        if self.system_locked and folder_name == ADMIN_FOLDER_NAME:
                            self.unlock_system()
                    else:
                        self.current_user = "Unknown"
                        
                        # Intruder Logic
                        if self.system_locked:
                            if time.time() - self.last_intruder_time > 5:
                                timestamp = datetime.datetime.now().strftime("%H-%M-%S")
                                filename = f"intruders/Intruder_{timestamp}.jpg"
                                cv2.imwrite(filename, frame)
                                
                                self.safe_log(f"⚠️ INTRUDER! Photo saved.")
                                self.save_csv("SECURITY ALERT", f"Saved to {filename}")
                                self.speak("Warning. Intruder detected.")
                                self.last_intruder_time = time.time()
            except:
                self.current_user = "None"
            
            time.sleep(0.5)

    def update_video(self):
        if not self.is_running: return
        
        frame = None
        if self.static_mode:
            frame = self.static_image.copy() if self.static_image is not None else None
        else:
            ret, cam_frame = self.cap.read()
            if ret: frame = cam_frame

        if frame is not None:
            h, w, _ = frame.shape
            
            # 1. FACES
            if self.var_face.get() or self.system_locked:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 8)
                for (x, y, wb, hb) in faces:
                    label = "Human"
                    color = (0, 255, 255)
                    if self.current_user not in ["Unknown", "None"]:
                        label = self.current_user
                        color = (0, 255, 0) if label == ADMIN_FOLDER_NAME else (255, 165, 0)
                    elif self.current_user == "Unknown":
                        label = "Unknown"
                        color = (0, 0, 255)

                    cv2.rectangle(frame, (x, y), (x+wb, y+hb), color, 2)
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # 2. OBJECTS
            if not self.system_locked and self.var_obj.get():
                results = self.yolo(frame, verbose=False, conf=0.60)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        if (x2-x1)*(y2-y1) > (h*w * 0.70): continue

                        cls = int(box.cls[0])
                        label = self.yolo.names[cls].title()
                        if label == "Person": continue 

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(img)
            
            display_w = self.frame_cam.winfo_width()
            display_h = self.frame_cam.winfo_height()
            if display_w > 10 and display_h > 10:
                img.thumbnail((display_w, display_h))
            
            imgtk = PIL.ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)

        self.window.after(30, self.update_video)

    def ask_gemini(self):
        if self.system_locked or self.scanning: return
        self.scanning = True
        # Safety Check: Is model loaded?
        if model is None:
            self.safe_log("Error: Google AI not connected.")
            self.scanning = False
            return
            
        threading.Thread(target=self.run_gemini).start()

    def run_gemini(self):
        self.safe_log("Sending to AI...")
        
        frame = None
        if self.static_mode: frame = self.static_image
        else:
            ret, f = self.cap.read()
            if ret: frame = f

        if frame is None: 
            self.scanning = False
            return

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = PIL.Image.fromarray(rgb)
            prompt = "Describe this image concisely. List people and objects."
            
            response = model.generate_content([prompt, pil_img])
            text = response.text
            
            self.safe_log(f"AI: {text}")
            self.save_csv("AI Analysis", text)
            self.speak(text)
            
        except Exception as e:
            self.safe_log(f"Error: {e}")

        self.scanning = False

    def use_file(self):
        path = filedialog.askopenfilename()
        if path:
            img = cv2.imread(path)
            if img is not None:
                self.static_image = img
                self.static_mode = True
                self.safe_log("Image Loaded.")
                threading.Thread(target=self.manual_deepface_check, args=(img,)).start()

    def manual_deepface_check(self, img):
        try:
            dfs = DeepFace.find(img_path=img, db_path="dataset", model_name="VGG-Face", silent=True)
            if len(dfs) > 0 and not dfs[0].empty:
                path = dfs[0].iloc[0]['identity']
                self.current_user = path.split('/')[-2]
            else:
                self.current_user = "Unknown"
        except:
            self.current_user = "Unknown"

    def use_camera(self):
        self.static_mode = False
        self.safe_log("Switched to Live Camera.")

    def save_csv(self, event, detail):
        now = datetime.datetime.now()
        with open(LOG_FILE, 'a', newline='') as f:
            csv.writer(f).writerow([now.date(), now.time(), event, detail.replace('\n', ' ')])

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

    def open_logs(self):
        import platform
        if platform.system() == 'Darwin': os.system(f"open {LOG_FILE}")
        else: os.startfile(LOG_FILE)

    def shutdown(self):
        self.is_running = False
        self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    if not os.path.exists("dataset"): os.makedirs("dataset")
    root = tk.Tk()
    app = SimpleVisionSystem(root)
    root.mainloop()
