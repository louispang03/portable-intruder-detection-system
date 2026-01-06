# Portable Intruder Detection System

A robust, real-time intruder detection system powered by **YOLOv8** and **Face Recognition**. This project turns your webcam or IP camera into a smart security device that can distinguish between known individuals (owners) and potential intruders, sending instant notifications with snapshots to your phone.

## 🚀 Features

*   **Real-time Person Detection**: Utilizes the state-of-the-art YOLOv8 model for fast and accurate person detection.
*   **Face Recognition**: Identifies known individuals ("Owners") to prevent false alarms.
*   **Web Interface**: A user-friendly Flask-based dashboard to:
    *   View the live camera feed.
    *   Toggle detection on/off.
    *   Upload photos of known individuals.
    *   View a gallery of detected intruders.
    *   Check detection logs.
    *   Configure camera source (Webcam ID or IP URL).
*   **Instant Notifications**: Integrates with **Pushover** to send real-time alerts with images to your mobile device when an intruder is detected.
*   **Smart Logging**: Automatically saves images of intruders and logs detection events with timestamps.
*   **Performance Optimized**: Includes frame skipping and resizing for smooth operation on various hardware.

## 🛠️ Tech Stack

*   **Python 3.x**
*   **[Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)**: Object detection.
*   **[Face Recognition](https://github.com/ageitgey/face_recognition)**: Facial identity verification.
*   **[OpenCV](https://opencv.org/)**: Image processing and video capture.
*   **[Flask](https://flask.palletsprojects.com/)**: Web server and interface.
*   **[Pushover API](https://pushover.net/)**: Mobile notifications.

## 📋 Prerequisites

*   Python 3.8 or higher.
*   A webcam or IP camera stream.
*   (Optional) A [Pushover](https://pushover.net/) account for notifications.

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd portable_intruder_detection
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The `face_recognition` library requires `dlib`, which might need CMake and C++ compilers installed on your system.*

3.  **Download YOLO Model:**
    The system will automatically download `yolov8n.pt` on the first run, or you can place your own model file in the root directory.

## 🚀 Usage

1.  **Start the Application:**
    Run the Flask app to start the web server and the detection loop.
    ```bash
    python app.py
    ```

2.  **Access the Dashboard:**
    Open your web browser and navigate to:
    ```
    http://localhost:5000
    ```

3.  **Configure:**
    *   Go to the settings/config section in the web UI.
    *   Enter your **Pushover User Key** and **API Token** (if using notifications).
    *   Set your **Camera Source** (0 for default webcam, 1 for external, or an RTSP URL for IP cameras).

4.  **Add Owners:**
    *   Use the "Upload" feature in the web UI to add clear photos of known individuals.
    *   The system will learn these faces and label them as "Owner" instead of "Intruder".

## 📂 Project Structure

```
portable_intruder_detection/
├── app.py                          # Main Flask application entry point
├── portable_intruder_detection.py  # Core detection logic and IntruderDetector class
├── requirements.txt                # Python dependencies
├── config.json                     # Configuration file (auto-generated)
├── notifications.json              # Log history of detections
├── yolov8n.pt                      # YOLOv8 model weights
├── intruders/                      # Directory for saved intruder snapshots
├── known_faces/                    # Directory for owner reference images
├── static/                         # CSS, JS, and other static assets
└── templates/                      # HTML templates for the web interface
```

## 🔧 Configuration

The `config.json` file is created automatically. You can modify it via the Web UI or manually:

```json
{
    "pushover_user_key": "YOUR_USER_KEY",
    "pushover_api_token": "YOUR_API_TOKEN",
    "camera_source": 0,
    "confidence_threshold": 0.5,
    "notification_cooldown_seconds": 60,
    "known_faces_dir": "known_faces"
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)
