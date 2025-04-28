#include <ESP32Servo.h>

// 📌 Configuración del servomotor
Servo gripperServo;
#define SERVO_PIN 13        // GPIO13
#define POS_ABIERTO 180     // Gripper totalmente abierto
#define POS_CERRADO 0       // Gripper totalmente cerrado

// 📌 Configuración de la señal de entrada
#define HIGH_Z_INPUT_PIN 21  // GPIO21 para leer señal

void setup() {
  Serial.begin(115200);
  
  // Inicializar servo
  gripperServo.setPeriodHertz(50);  // PWM de 50Hz
  gripperServo.attach(SERVO_PIN, 900, 2100);  // PWM de 900–2100 µs
  gripperServo.write(POS_ABIERTO);  // Inicialmente abierto

  // Configurar entrada con pull-up
  pinMode(HIGH_Z_INPUT_PIN, INPUT_PULLUP);

  Serial.println("✅ Sistema iniciado. Gripper abierto.");
}

void loop() {
  // Leer estado del pin
  bool signalActive = digitalRead(HIGH_Z_INPUT_PIN) == LOW;

  if (signalActive) {
    // Señal baja detectada ➔ Cerrar gripper
    gripperServo.write(POS_CERRADO);
    Serial.println("🔒 Señal detectada: Gripper cerrado.");
  } else {
    // Señal alta o flotante ➔ Mantener abierto
    gripperServo.write(POS_ABIERTO);
    Serial.println("🔓 No señal: Gripper abierto.");
  }

  delay(100); // Pequeño delay para evitar saturar el serial
}
