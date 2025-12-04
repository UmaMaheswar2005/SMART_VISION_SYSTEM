# Intelligent Vision & Security System (Final Year Project)

## 📌 Project Overview
A state-of-the-art **AI Surveillance System** designed for enterprise security. It integrates **Local Biometrics** (DeepFace), **Real-Time Object Detection** (YOLOv8), and **Generative Cloud AI** (Google Gemini 2.0) into a single dashboard.

The system features a **Secure Admin Login**, capability to connect with **CCTV/IP Cameras** via RTSP, and forensic auditing tools.

## 🚀 Key Features
### 1. 🔒 Secure Access Control
* **Biometric Lock:** System remains locked until the Administrator (e.g., "Mahi") is visually identified by the camera.
* **Intruder Trap:** Automatically captures photos of unauthorized users attempting to breach the system and saves them to an `intruders/` folder.

### 2. 📹 Multi-Source Surveillance
* **CCTV Compatible:** Supports RTSP streams for connecting to IP Cameras and NVRs.
* **Webcam Support:** Default compatibility with laptop/USB cameras.
* **Static Forensic Mode:** Allows users to upload images for deep forensic analysis using AI.

### 3. 🧠 Hybrid AI Intelligence
* **Live Monitoring:** Uses YOLOv8 to detect objects (Phones, Weapons, Bags) in real-time.
* **Deep Analysis:** Integrates Google Gemini 2.0 to provide detailed, human-like descriptions of any scene (e.g., "A man in a red shirt holding a suspicious package").
* **Voice Feedback:** Uses Text-to-Speech to verbally warn the admin or describe scenes.

### 4. 📂 Audit & Logging
* **Event Logs:** Automatically saves every interaction (Access Granted, Intruder Detected, Object Found) to `project_logs.csv`.
* **Evidence Collection:** Stores timestamps and high-res snapshots of security events.

## 🛠️ Tech Stack
* **Language:** Python 3.11
* **Computer Vision:** OpenCV, DeepFace (VGG-Face), YOLOv8 Medium
* **Generative AI:** Google Gemini 2.0 Flash API
* **Interface:** Custom Tkinter Dashboard (Grid Layout)
* **Automation:** Pyttsx3 (Voice), CSV (Database), Threading

## ⚙️ How to Run
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yourusername/smart-vision-system.git](https://github.com/yourusername/smart-vision-system.git)
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Security:**
    * Open `main.py`.
    * Set `ADMIN_FOLDER_NAME` to match your face folder in `dataset/`.
    * Set `CAMERA_SOURCE` to `0` (Webcam) or `"rtsp://..."` (CCTV).
4.  **Run:**
    ```bash
    python main.py
    ```

## 📸 Screenshots
*(Upload a screenshot of your new GUI here)*
