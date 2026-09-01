# digital_pet
A custom DIY handheld Tamagotchi built with ESP32 and MicroPython, featuring animated OLED graphics, rotary encoder controls, real-time Wi-Fi weather, and a custom soldered brass wire chassis.

# 🤖 DIY MicroPython ESP32 Tamagotchi

A custom, handheld virtual pet powered by an **ESP32**, **0.96" OLED display**, and a **rotary encoder** housed inside a free-form soldered brass wire chassis. 

Built completely from scratch in **MicroPython** using asynchronous tasks (`uasyncio`), custom bitmap graphics, real-time Wi-Fi weather integrations, and virtual pet stat management.

---

## ✨ Features

* **Virtual Pet State Engine:** Dynamic hunger ($H$), happiness ($P$), and energy ($E$) stat management with walking animations, idle states, and blinking eyes.
* **Rotary Encoder Interface:** Smooth menu navigation powered by hardware interrupt-driven Gray code decoding.
* **Wi-Fi Weather App:** Real-time temperature, condition updates, and custom animated particle effects (rain, snow, sun pulse) via OpenWeatherMap API.
* **Built-in Apps & Games:**
  * **Spin Match Game:** Interactive rotary game.
  * **Alarm & Stopwatch:** Built-in timer and alarm tools using RTC.
  * **MPU6050 Motion Support:** Hardware step tracking and motion sensing.

---

## 🛠️ Hardware Stack

* **MCU:** ESP32 Development Board
* **Display:** 0.96" 128x64 I2C OLED Display (`SSD1306`)
* **Controls:** Quadrature Rotary Encoder
* **Motion Sensor:** MPU6050 IMU
* **Audio:** Piezo Buzzer
* **Chassis:** Free-form brass wire exo-frame with keychain loop

---

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| `main.py` | Core async loop, initialization, and task scheduling |
| `pet_engine.py` | Tamagotchi state machine, stat decay, and rendering |
| `weather_ui.py` | OpenWeatherMap API parser & animated 16x16 weather bitmaps |
| `app_features.py` | Weather, Alarm, and Stopwatch logic |
| `eye_graphics.py` | Pixel-art eye graphics & deep-idle animations |
| `games.py` | Interactive mini-games (`SpinMatchGame`) |
| `startup.py` | Boot animation sequence |
| `config.py` | Wi-Fi credentials, API keys, and pin assignments |
| `mpu6050.py` | Driver for MPU6050 accelerometer/gyroscope |
| `ssd1306.py` | I2C SSD1306 OLED display driver |

---

## 🚀 Setup & Installation

1. **Flash MicroPython:** Install MicroPython firmware on your ESP32.
2. **Configure Settings:** Edit `config.py` with your Wi-Fi SSID, Password, and OpenWeatherMap API key:
   ```python
   WIFI_SSID = "Your_WiFi_Name"
   WIFI_PASS = "Your_WiFi_Password"
   WEATHER_API_KEY = "Your_OpenWeatherMap_API_Key"
   CITY = "Your_City"
   
## Video Link
https://youtu.be/udwHpw4VXUs
