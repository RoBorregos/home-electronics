#include <ESP32Servo.h>
#include "BluetoothSerial.h"

// 📌 Configuración del servomotor
Servo gripperServo;
#define SERVO_PIN 13         // GPIO13
#define POS_ABIERTO 180      // Gripper abierto
#define POS_CERRADO 0        // Gripper cerrado

// 📡 Bluetooth Serial
BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);

  // Inicializar Bluetooth
  if (!SerialBT.begin("ESP32_Gripper", true)) { // Nombre del dispositivo Bluetooth
    Serial.println("⚠️ Error iniciando Bluetooth");
    while (true); // Detener
  }
  SerialBT.setPin("1234", 4);  // ← ESTO ES MUY IMPORTANTE
  
  Serial.println("✅ Bluetooth iniciado con PIN 1234");

  // Inicializar Servo
  gripperServo.setPeriodHertz(50);
  gripperServo.attach(SERVO_PIN, 900, 2100);
  gripperServo.write(POS_ABIERTO);  // Empezar abierto

  Serial.println("✅ Sistema iniciado. Gripper abierto.");
}

void loop() {
  // 📥 Revisar si llega un dato por Bluetooth
  if (SerialBT.available()) {
    char incomingChar = SerialBT.read();
    Serial.print("📩 Comando recibido por Bluetooth: ");
    Serial.println(incomingChar);

    if (incomingChar == '1') {
      // Mandaron '1' --> cerrar gripper
      gripperServo.write(POS_CERRADO);
      Serial.println("🔒 Gripper cerrado.");
    } 
    else if (incomingChar == '0') {
      // Mandaron '0' --> abrir gripper
      gripperServo.write(POS_ABIERTO);
      Serial.println("🔓 Gripper abierto.");
    }
  }

  delay(50); // Pequeño delay para estabilidad
}
