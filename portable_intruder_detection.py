import cv2
import requests
import time
import json
import os
import numpy as np
import threading
from ultralytics import YOLO
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try to import face_recognition, handle failure gracefully
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
import cv2
import requests
import time
import json
import os
import numpy as np
import threading
from ultralytics import YOLO
from datetime import datetime

# Try to import face_recognition, handle failure gracefully
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("Warning: 'face_recognition' library not found. Face recognition features will be disabled.")

CONFIG_FILE = 'config.json'
NOTIFICATIONS_FILE = 'notifications.json'
INTRUDERS_DIR = 'intruders'

class IntruderDetector:
    def __init__(self):
        self.config = self.load_config()
        self.model = YOLO('yolov8n.pt')
        self.known_face_encodings = []
        self.known_face_names = []
        self.last_notification_time = {}
        self.running = False
        self.active = True # Controls if detection is happening
        self.latest_frame = None
        self.lock = threading.Lock()
        
        # Ensure directories exist
        if not os.path.exists(INTRUDERS_DIR):
            os.makedirs(INTRUDERS_DIR)
            
        self.load_known_faces()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Override with environment variables if present
                if os.getenv("PUSHOVER_USER_KEY"):
                    config["pushover_user_key"] = os.getenv("PUSHOVER_USER_KEY")
                if os.getenv("PUSHOVER_API_TOKEN"):
                    config["pushover_api_token"] = os.getenv("PUSHOVER_API_TOKEN")
                return config
        return {
            "pushover_user_key": os.getenv("PUSHOVER_USER_KEY", ""),
            "pushover_api_token": os.getenv("PUSHOVER_API_TOKEN", ""),
            "camera_source": 0,
            "confidence_threshold": 0.5,
            "notification_cooldown_seconds": 60,
            "known_faces_dir": "known_faces"
        }

    def load_known_faces(self):
        if not FACE_REC_AVAILABLE:
            return

        print("Loading known faces...")
        self.known_face_encodings = []
        self.known_face_names = []
        
        known_faces_dir = self.config.get('known_faces_dir', 'known_faces')
        if not os.path.exists(known_faces_dir):
            os.makedirs(known_faces_dir)
            return

        for filename in os.listdir(known_faces_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(known_faces_dir, filename)
                try:
                    image = face_recognition.load_image_file(path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        name = os.path.splitext(filename)[0]
                        self.known_face_names.append(name)
                        print(f"Loaded face: {name}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def toggle_detection(self):
        self.active = not self.active
        return self.active

    def send_notification(self, title, message, image=None):
        current_time = time.time()
        if current_time - self.last_notification_time.get(title, 0) < self.config.get('notification_cooldown_seconds', 60):
            return

        print(f"Sending notification: {title} - {message}")
        
        # Save image locally
        image_filename = None
        if image is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{timestamp}.jpg"
            cv2.imwrite(os.path.join(INTRUDERS_DIR, image_filename), image)

        # Log notification
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "image": image_filename
        }
        self.log_notification(log_entry)

        # Send Pushover notification
        api_token = self.config.get('pushover_api_token')
        user_key = self.config.get('pushover_user_key')
        
        if api_token and user_key:
            payload = {
                "token": api_token,
                "user": user_key,
                "title": title,
                "message": message
            }
            
            files = {}
            if image is not None:
                _, img_encoded = cv2.imencode('.jpg', image)
                files = {
                    "attachment": ("image.jpg", img_encoded.tobytes(), "image/jpeg")
                }

            try:
                requests.post("https://api.pushover.net/1/messages.json", data=payload, files=files)
                self.last_notification_time[title] = current_time
            except Exception as e:
                print(f"Error sending Pushover notification: {e}")

    def log_notification(self, entry):
        logs = []
        if os.path.exists(NOTIFICATIONS_FILE):
            try:
                with open(NOTIFICATIONS_FILE, 'r') as f:
                    logs = json.load(f)
            except:
                pass
        logs.insert(0, entry) # Prepend new log
        with open(NOTIFICATIONS_FILE, 'w') as f:
            json.dump(logs, f, indent=4)

    def update_camera_source(self, new_source):
        self.config['camera_source'] = new_source
        # Save config to file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        # Restart the camera loop
        self.stop()
        time.sleep(1) # Wait for loop to exit
        self.start()

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _run_loop(self):
        source = self.config.get('camera_source', 0)
        if isinstance(source, str) and source.isdigit():
            source = int(source)

        cap = cv2.VideoCapture(source)
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                # If connection lost, try to reconnect
                cap.release()
                time.sleep(2)
                cap = cv2.VideoCapture(source)
                continue

            frame_count += 1
            
            # Only process every 3rd frame to reduce lag
            if self.active and frame_count % 3 == 0:
                # Resize for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                
                # YOLOv8 Detection on the original frame (or a resized version if needed, but YOLO is fast)
                # We'll use the original frame for YOLO as it handles resizing internally efficiently
                results = self.model(frame, verbose=False, classes=[0])

                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        conf = box.conf[0].cpu().numpy()
                        
                        if conf < self.config.get('confidence_threshold', 0.5):
                            continue

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        label = "Person"
                        color = (0, 0, 255)

                        if FACE_REC_AVAILABLE:
                            # Use the small frame for face recognition
                            # Scale coordinates for the small frame
                            y1_s, x1_s, y2_s, x2_s = int(y1*0.25), int(x1*0.25), int(y2*0.25), int(x2*0.25)
                            
                            # Ensure coordinates are within bounds
                            h, w, _ = small_frame.shape
                            y1_s = max(0, y1_s); x1_s = max(0, x1_s); y2_s = min(h, y2_s); x2_s = min(w, x2_s)

                            face_image_small = small_frame[y1_s:y2_s, x1_s:x2_s]
                            
                            if face_image_small.size != 0:
                                rgb_face_image = cv2.cvtColor(face_image_small, cv2.COLOR_BGR2RGB)
                                face_locations = face_recognition.face_locations(rgb_face_image)
                                face_encodings = face_recognition.face_encodings(rgb_face_image, face_locations)

                                if not face_encodings:
                                    label = "Person (No Face)"
                                else:
                                    for face_encoding in face_encodings:
                                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                                        name = "Unknown"

                                        if True in matches:
                                            first_match_index = matches.index(True)
                                            name = self.known_face_names[first_match_index]
                                            label = f"Owner: {name}"
                                            color = (255, 0, 0)
                                        
                                        if name != "Unknown":
                                            break
                        
                        cv2.putText(frame, f"{label} ({conf:.2f})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        if "Owner" not in label:
                            self.send_notification("Intruder Alert", f"Detected: {label}", image=frame)
            
            elif not self.active:
                # Visual indicator that detection is paused
                cv2.putText(frame, "DETECTION PAUSED", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            with self.lock:
                self.latest_frame = frame.copy()
        
        cap.release()