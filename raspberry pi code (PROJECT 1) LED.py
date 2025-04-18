#!/usr/bin/env python3
import requests
import time
import RPi.GPIO as GPIO
import pymongo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GPIO setup
LED_PIN = int(os.getenv("LED_PIN", 17))  # GPIO pin connected to the LED
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setwarnings(False)

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://scortal143:QSVgtxWjUqhEOpcJ@ledstatus.tr1ke.mongodb.net/")

# API settings
API_URL = os.getenv("API_URL", "https://cloud.mongodb.com/v2/67d91c52c4c995148cb789fd#/metrics/replicaSet/67db1ddcc9f4822325d52d5d/explorer/iot_db/led_status/find")

# Check interval
CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL", 2))

# Method 1: Connect directly to MongoDB
def setup_mongo_connection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client.iot_db
    return db.led_status

# Method 2: Connect via API
def get_led_status_from_api():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get("status", 0)
        else:
            print(f"Error: API responded with status code {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return 0

def get_led_status_from_mongo(collection):
    try:
        latest_status = collection.find_one(
            {"device_id": "raspberry_pi_1"},
            sort=[("timestamp", pymongo.DESCENDING)]
        )
        
        if latest_status and "status" in latest_status:
            return latest_status["status"]
        return 0
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return 0

def update_led(status):
    if status == 1:
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("LED turned ON")
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        print("LED turned OFF")

def main():
    print("Starting Raspberry Pi LED controller...")
    
    # Choose which method to use
    use_direct_mongo = os.getenv("USE_DIRECT_MONGO", "true").lower() == "true"
    
    if use_direct_mongo:
        print("Using direct MongoDB connection")
        led_collection = setup_mongo_connection()
    else:
        print("Using API connection")
    
    try:
        previous_status = None
        
        while True:
            if use_direct_mongo:
                current_status = get_led_status_from_mongo(led_collection)
            else:
                current_status = get_led_status_from_api()
            
            # Only update the LED if the status has changed
            if current_status != previous_status:
                update_led(current_status)
                previous_status = current_status
            
            time.sleep(CHECK_INTERVAL)  # Check based on configured interval
            
    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        GPIO.cleanup()  # Clean up GPIO on program exit

if __name__ == "__main__":
    main() 