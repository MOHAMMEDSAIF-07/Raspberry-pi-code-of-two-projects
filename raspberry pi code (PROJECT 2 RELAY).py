import pymongo
from pymongo.errors import PyMongoError 
import RPi.GPIO as GPIO
import time
from bson.objectid import ObjectId

# Database configuration
MONGO_URI = "mongodb+srv://mdsaif123:22494008@iotusingrelay.vfu72n2.mongodb.net/"
DB_NAME = "test"
COLLECTION_NAME = "devices"

# Hardware configuration
LED_PINS = [17, 27, 22, 18]

class LEDController:
    def __init__(self):
        # Initialize MongoDB connection
        self.mongo_client = pymongo.MongoClient(MONGO_URI)
        self.database = self.mongo_client[DB_NAME]
        self.device_collection = self.database[COLLECTION_NAME]
        
        # Configure GPIO for LED control
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PINS, GPIO.OUT)
        
        # Initialize all LEDs to OFF state
        for pin in LED_PINS:
            GPIO.output(pin, GPIO.LOW)
        
        print("LED controller initialized")
    
    def fetch_led_status(self):
        """Retrieve LED data from the database"""
        return list(self.device_collection.find())
    
    def update_led_states(self):
        """Set GPIO pins to control LEDs based on database states"""
        leds = self.fetch_led_status()
        for led in leds:
            pin = led.get("pin")
            if pin in LED_PINS:
                state = led.get("state", False)
                # Invert the logic for relay module (relay modules are typically active-LOW)
                gpio_state = GPIO.LOW if state else GPIO.HIGH
                GPIO.output(pin, gpio_state)
                print(f"LED on pin {pin} set to {'ON' if state else 'OFF'}")
    
    def start_monitoring(self):
        """Begin listening for database changes"""
        try:
            print("Starting LED monitoring service...")
            print("Watching MongoDB for changes...")
            
            # Initial sync with database
            self.update_led_states()
            
            with self.device_collection.watch() as change_stream:
                for change in change_stream:
                    operation = change.get('operationType')
                    if operation in ['insert', 'update', 'replace', 'delete']:
                        print(f"Database change detected: {operation}")
                        self.update_led_states()
        except PyMongoError as error:
            print(f"MongoDB connection error: {error}")
        except KeyboardInterrupt:
            print("LED controller stopped by user")
        finally:
            # Clean up GPIO on exit
            GPIO.cleanup()
            print("GPIO resources released")
            
if __name__ == "__main__":
    controller = LEDController()
    controller.start_monitoring() 