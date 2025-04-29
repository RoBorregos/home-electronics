#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// 📡 Configuración de WiFi
const char *ssid = "Roborregos";  
const char *password = "RoBorregos2025";  

// 📡 Configuración UDP
WiFiUDP udp;
const unsigned int localPort = 1234;
char packetBuffer[255];

// 📌 Configuración del servomotor
Servo gripperServo;  
#define SERVO_PIN 12  
#define POS_ABIERTO 180  // Totalmente abierto
#define POS_CERRADO 0    // Totalmente cerrado

// 📌 Configuración del potenciómetro
#define POT_PIN 34  

// 📌 Configuración del sensor ACS712
#define ACS712_PIN 35  
const float ACS712_OFFSET = 2.5;      // Offset a 2.5V (calibrar si necesario)
const float ACS712_SENSITIVITY = 0.185; // 185 mV/A para ACS712-05B
#define UMBRAL_BLOQUEO 4.0  // Provisional para 9V, ajustar tras pruebas

// 📌 Configuración de los sensores FSR (opcional)
#define FSR1_PIN 32  
#define FSR2_PIN 33  
#define UMBRAL_FSR 500  

// 📌 IP de la PC
const char *PC_IP = "192.168.1.217";  
const unsigned int PC_PORT = 1234;   

// 📌 Modo de control
bool modoAuto = false;  
int servoAngle = POS_ABIERTO;  // Inicia abierto (180°)
bool closing = false;  
bool locked = false;   

void setup() {
  Serial.begin(115200);
  
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Conectado a WiFi");
  Serial.print("📡 IP del ESP32: ");
  Serial.println(WiFi.localIP());

  udp.begin(localPort);
  Serial.println("🌐 Servidor UDP iniciado.");

  gripperServo.attach(SERVO_PIN);
  gripperServo.write(servoAngle);
  
  Serial.println("🎛️ Sensores y servomotor listos (alimentado a 9V, parámetros a 7.4V).");
  delay(2000);
}

void loop() {
  // 📥 Leer sensores
  int potValue = analogRead(POT_PIN);  
  int fsr1Value = analogRead(FSR1_PIN);  
  int fsr2Value = analogRead(FSR2_PIN);  
  int rawValue = analogRead(ACS712_PIN);
  float voltage = (rawValue * 3.3) / 4095.0;
  float current = abs((voltage - ACS712_OFFSET) / ACS712_SENSITIVITY);

  // 📏 Calcular distancia del gripper
  float gripperDistance = (7.0 / 180.0) * (POS_ABIERTO - servoAngle) + 1.4;

  // 📡 Enviar datos por UDP
  char udpMessage[100];
  snprintf(udpMessage, sizeof(udpMessage), "%d,%.2f,%.3f,%d,%d", 
           servoAngle, gripperDistance, current, fsr1Value, fsr2Value);
  udp.beginPacket(PC_IP, PC_PORT);
  udp.print(udpMessage);
  udp.endPacket();

  // 📥 Recibir comandos UDP
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;  
    String command = String(packetBuffer);
    Serial.print("📥 Comando recibido: ");
    Serial.println(command);

    if (command.equalsIgnoreCase("AUTO")) {
      modoAuto = true;
      closing = false;
      locked = false;
      Serial.println("🔄 Modo AUTO activado.");
    } else if (command.equalsIgnoreCase("MANUAL")) {
      modoAuto = false;
      closing = false;
      locked = false;
      Serial.println("🔧 Modo MANUAL activado.");
    } else if (command.equalsIgnoreCase("CLOSE")) {
      modoAuto = false;
      closing = true;
      locked = false;
      servoAngle = POS_ABIERTO;  // Inicia en 180°
      gripperServo.write(servoAngle);
      Serial.println("🔽 Gripper movido a 180°, iniciando cierre progresivo hacia 0°.");
      delay(1000);  // Esperar a que llegue a 180°
    } else if (command.equalsIgnoreCase("OPEN")) {
      modoAuto = false;
      closing = false;
      locked = false;
      servoAngle = POS_ABIERTO;  // Abre a 180°
      gripperServo.write(servoAngle);
      Serial.println("🔼 Gripper abierto a 180°.");
    } else if (!modoAuto && !closing && !locked) {
      int receivedAngle = command.toInt();
      if (receivedAngle >= POS_CERRADO && receivedAngle <= POS_ABIERTO) {
        servoAngle = receivedAngle;
        gripperServo.write(servoAngle);
        Serial.print("📥 Ángulo recibido: ");
        Serial.println(servoAngle);
      } else {
        Serial.println("⚠️ Comando no válido.");
      }
    }
  }

  // 🎮 Control del servo
  if (modoAuto && !locked) {
    int targetAngle = map(potValue, 0, 4095, POS_CERRADO, POS_ABIERTO);
    if (current < UMBRAL_BLOQUEO) {
      servoAngle = targetAngle;
      gripperServo.write(servoAngle);
    } else {
      locked = true;
      gripperServo.write(servoAngle);
      Serial.println("⚡ Bloqueo detectado por corriente en modo AUTO.");
    }
  } else if (closing) {
    if (current < UMBRAL_BLOQUEO && servoAngle > POS_CERRADO) {
      servoAngle -= 4;  // Cierre hacia 0°
      gripperServo.write(servoAngle);
      Serial.print("🔽 Cerrando a: ");
      Serial.print(servoAngle);
      Serial.println("°");
      delay(100);
    } else {
      closing = false;
      locked = true;
      gripperServo.write(servoAngle);
      Serial.println("⚡ Gripper bloqueado, objeto agarrado.");
    }
  } else if (locked) {
    gripperServo.write(servoAngle);
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 1000) {
      Serial.println("🔒 Gripper permanece bloqueado.");
      lastPrint = millis();
    }
  } else {
    gripperServo.write(servoAngle);
  }

  // 📋 Depuración
  Serial.printf("Ángulo: %d° | Corriente: %.3f A | FSR1: %d | FSR2: %d\n", 
                servoAngle, current, fsr1Value, fsr2Value);
  delay(50);
}
