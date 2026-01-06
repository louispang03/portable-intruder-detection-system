import os
import json
from dotenv import load_dotenv
from portable_intruder_detection import IntruderDetector

# Load env vars
load_dotenv()

# Create instance (this will load config)
# We mock the camera source to avoid opening camera
with open('config.json', 'r') as f:
    config = json.load(f)

# Mocking the __init__ to avoid full initialization which might fail without camera
# Actually, let's just test the load_config method directly if possible, 
# but it's an instance method.
# We can instantiate it, but it might try to open camera.
# The __init__ calls load_config first, then YOLO, then load_known_faces.
# It doesn't open camera in __init__.
# It does create IntruderDetector object.

try:
    detector = IntruderDetector()
    print(f"Loaded User Key: {detector.config['pushover_user_key']}")
    print(f"Loaded API Token: {detector.config['pushover_api_token']}")

    expected_user_key = os.getenv("PUSHOVER_USER_KEY")
    expected_api_token = os.getenv("PUSHOVER_API_TOKEN")

    if detector.config['pushover_user_key'] == expected_user_key and \
       detector.config['pushover_api_token'] == expected_api_token:
        print("SUCCESS: Keys loaded correctly from environment variables.")
    else:
        print("FAILURE: Keys do not match environment variables.")
        print(f"Expected User Key: {expected_user_key}")
        print(f"Expected API Token: {expected_api_token}")

except Exception as e:
    print(f"Error during verification: {e}")
