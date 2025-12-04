# Smart Vision System (Final Year Project)

## 📌 Project Overview
This project is an advanced computer vision application that integrates **Local Biometric Authentication** (DeepFace) with **Cloud-Based Generative AI** (Google Gemini 2.0). It functions as a context-aware security system that can identify authorized users and describe unknown objects or scenes in real-time.

## 🚀 Key Features
* **Hybrid AI Architecture:** Combines local face recognition for speed/privacy with cloud AI for general intelligence.
* **Smart Detection:** Automatically switches between "Identity Mode" (for people) and "Object Mode" (for items).
* **Audit Logging:** Saves every scan to a CSV database (`project_logs.csv`) for security tracking.
* **Voice Feedback:** Uses Text-to-Speech to announce results audibly.
* **Retry Logic:** Includes auto-retry systems to handle network limits.

## 🛠️ Tech Stack
* **Language:** Python 3.11
* **AI Core:** Google Gemini 2.0 Flash API, DeepFace (VGG-Face)
* **Libraries:** OpenCV, Pyttsx3, Pillow
* **GUI:** Tkinter

## ⚙️ How to Run
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Add API Key:**
    Open `main.py` and paste your Google Gemini API Key.
3.  **Run the App:**
    ```bash
    python main.py
    ```

## 📄 License
Created for educational purposes.
