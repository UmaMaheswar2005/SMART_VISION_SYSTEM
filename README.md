# Intelligent Vision & Security System (M4 Optimized)

## 📌 Project Overview
A high-performance **AI Surveillance System** optimized for Apple Silicon (M4/M3/M2). This system integrates **Local Biometrics** (DeepFace), **Real-Time Object Detection** (YOLOv8), and **Multimodal Cloud AI** (Google Gemini 1.5 Flash) to provide a comprehensive security dashboard for enterprise monitoring.

## 🚀 Key Features
### 1. 🔒 Hardened Access Control
* **Biometric Lock:** System remains locked until the Administrator (e.g., "Mahi") is visually identified using the VGG-Face model.
* **Intruder Trap:** Automatically captures high-resolution photos of unauthorized users with a 5-second cooldown and saves them to a secure `intruders/` folder.

### 2. 📹 Multi-Source Surveillance
* **Live Stream:** Optimized threading for Mac M4 camera buffers to ensure zero-lag real-time monitoring.
* **Forensic Mode:** Capability to upload static images for deep forensic analysis using Generative AI.

### 3. 🧠 Hybrid AI Intelligence
* **Edge Detection:** YOLOv8 Medium model running on the M4 Neural Engine for real-time object classification.
* **Scene Reasoning:** Integrated with the **2026 Google GenAI SDK** for human-like descriptions of security events.
* **Voice Feedback:** Native macOS `say` command integration for real-time verbal security alerts.

## 🛠️ Tech Stack & M4 Optimization
* **Language:** Python 3.11
* **Engine:** TensorFlow 2.20.0 (Native ARM64 for Apple Silicon)
* **Vision:** OpenCV 4.13, DeepFace, YOLOv8
* **Generative AI:** Google GenAI SDK (Gemini 1.5 Flash)

## ⚙️ Installation & Setup
1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/UmaMaheswar2005/SMART_VISION_SYSTEM.git](https://github.com/UmaMaheswar2005/SMART_VISION_SYSTEM.git)
   cd SMART_VISION_SYSTEM