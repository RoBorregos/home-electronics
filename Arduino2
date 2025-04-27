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
#define SERVO_PIN 13  // GPIO13 (D13) - Pin superior derecho
#define POS_ABIERTO 180  // Totalmente abierto (98 mm)
#define POS_CERRADO 0    // Totalmente cerrado (0.3 mm)
#define MIN_PULSE_WIDTH 900   // PWM mínimo en microsegundos (0°)
#define MAX_PULSE_WIDTH 2100  // PWM máximo en microsegundos (180°)

// 📌 Configuración de la salida digital
#define DIGITAL_OUT_PIN 25  // GPIO25 (D25) - Pin superior derecho, para xArm6 (NPN)

// 📌 Configuración del sensor ACS712
#define ACS712_PIN 34  // GPIO34 (D34) - Pin superior derecho
const float ACS712_OFFSET = 2.496;  // Voltaje en reposo (calibrado previamente)
const float ACS712_SENSITIVITY = 0.185;  // Sensibilidad en V/A (para ACS712-05B)
#define UMBRAL_BLOQUEO 5.2  // Umbral de corriente para detectar bloqueo
#define INITIAL_DELAY 1000  // Retardo inicial en ms para ignorar corriente en 180°

// 📌 Configuración de los sensores FSR
#define FSR1_PIN 32  // GPIO32 (D32) - Pin superior derecho (FlexiForce 1)
#define FSR2_PIN 33  // GPIO33 (D33) - Pin superior derecho (FlexiForce 2)
#define FSR_PRESSURE_THRESHOLD 5.0  // Umbral de presión en psi para detener el gripper
float fsr1ForceN = 0.0, fsr2ForceN = 0.0;
float fsr1WeightKg = 0.0, fsr2WeightKg = 0.0;
float fsr1PressurePsi = 0.0, fsr2PressurePsi = 0.0;

// Coeficientes de calibración FSR
const float calibrationSlope = 0.000817991054;  // lbs por unidad de ADC
const float calibrationIntercept = 0.0;
const float alpha = 0.5;  // Filtro suavizado
int fsr1FilteredValue = 0, fsr2FilteredValue = 0;
int fsr1PreviousValue = 0, fsr2PreviousValue = 0;
unsigned long fsr1ValueChangeTime = 0, fsr2ValueChangeTime = 0;

// Área efectiva del sensor FSR 402 (12.7 mm de diámetro)
const float diameterMm = 12.7;
const float diameterInches = diameterMm / 25.4;
const float radiusInches = diameterInches / 2;
const float areaInSquareInches = 3.14159 * radiusInches * radiusInches;

// 📌 IP de la PC
const char *PC_IP = "192.168.137.1";  
const unsigned int PC_PORT = 1234;   

// 📌 Estado del gripper
int servoAngle = POS_ABIERTO;  
bool closing = false;  
bool locked = false;   
int digitalOutputState = 0; // Estado de la salida digital (0 o 1)
bool initialDelayDone = false; // Para manejar INITIAL_DELAY

void setup() {
  pinMode(2, OUTPUT); // LED azul en GPIO2 (D2) - Integrado en la placa
  pinMode(DIGITAL_OUT_PIN, OPEN_DRAIN); // Salida digital en colector abierto (D25)
  digitalWrite(DIGITAL_OUT_PIN, HIGH); // Inicialmente flotante (desactivado)
  Serial.begin(115200);
  
  // Conectar a WiFi
  Serial.println("Iniciando conexión WiFi...");
  WiFi.begin(ssid, password);
  Serial.print("Conectando");
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(2, HIGH); // LED encendido
    delay(250);
    digitalWrite(2, LOW); // LED apagado
    delay(250);
    Serial.print(".");
  }
  digitalWrite(2, HIGH); // LED fijo al conectar
  Serial.println("\n✅ Conectado a WiFi");
  Serial.print("📡 IP del ESP32: ");
  Serial.println(WiFi.localIP());

  // Iniciar servidor UDP
  udp.begin(localPort);
  Serial.println("🌐 Servidor UDP iniciado.");

  // Configurar el servo con rango PWM personalizado
  gripperServo.setPeriodHertz(50);
  gripperServo.attach(SERVO_PIN, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH);
  gripperServo.write(servoAngle);
  
  Serial.println("🎛️ Servo, sensores FSR, ACS712 y salida digital listos (alimentado a 7.4V, PWM 900-2100).");
  Serial.println("📋 Comandos: '1' para cerrar (D25 a GND), '0' para abrir (D25 flotante).");
  delay(2000);
}

void loop() {
  // 📥 Leer sensores
  int fsr1Raw = analogRead(FSR1_PIN);  
  int fsr2Raw = analogRead(FSR2_PIN);  
  int rawValue = analogRead(ACS712_PIN);
  float voltage = (rawValue * 3.3) / 4095.0; // Convertir a voltaje (ESP32 ADC es de 3.3V)
  float current = abs((voltage - ACS712_OFFSET) / ACS712_SENSITIVITY); // Calcular corriente

  // 📏 Calcular distancia del gripper (en cm)
  float gripperDistance = 0.03 + (servoAngle * 9.77 / 180.0);  // 0.3 mm a 0°, 98 mm a 180°

  // 📌 Filtrar valores FSR
  fsr1FilteredValue = alpha * fsr1Raw + (1 - alpha) * fsr1FilteredValue;
  fsr2FilteredValue = alpha * fsr2Raw + (1 - alpha) * fsr2FilteredValue;

  // Estabilización de valores FSR
  if (fsr1FilteredValue != fsr1PreviousValue) {
    if (millis() - fsr1ValueChangeTime >= 1000) {
      fsr1PreviousValue = fsr1FilteredValue;
      fsr1ValueChangeTime = millis();
    }
  } else {
    fsr1ValueChangeTime = millis();
  }
  if (fsr2FilteredValue != fsr2PreviousValue) {
    if (millis() - fsr2ValueChangeTime >= 1000) {
      fsr2PreviousValue = fsr2FilteredValue;
      fsr2ValueChangeTime = millis();
    }
  } else {
    fsr2ValueChangeTime = millis();
  }

  // 📏 Cálculos FSR
  float fsr1WeightLbs = calibrationSlope * fsr1PreviousValue + calibrationIntercept;
  fsr1ForceN = fsr1WeightLbs * 4.44822;
  fsr1WeightKg = fsr1ForceN / 9.80665;
  fsr1PressurePsi = fsr1WeightLbs / areaInSquareInches;

  float fsr2WeightLbs = calibrationSlope * fsr2PreviousValue + calibrationIntercept;
  fsr2ForceN = fsr2WeightLbs * 4.44822;
  fsr2WeightKg = fsr2ForceN / 9.80665;
  fsr2PressurePsi = fsr2WeightLbs / areaInSquareInches;

  // 📡 Enviar datos por UDP
  char udpMessage[120];
  snprintf(udpMessage, sizeof(udpMessage), "%d,%.2f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%d", 
           servoAngle, gripperDistance, current, 
           fsr1ForceN, fsr1WeightKg, fsr1PressurePsi, 
           fsr2ForceN, fsr2PressurePsi, digitalOutputState);
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

    if (command == "1") {
      closing = true;
      locked = false;
      servoAngle = POS_ABIERTO;
      gripperServo.write(servoAngle);
      digitalOutputState = 1;
      digitalWrite(DIGITAL_OUT_PIN, LOW); // Activar salida (GND)
      initialDelayDone = false; // Reiniciar el retardo inicial
      Serial.println("🔽 Gripper movido a 180°, iniciando cierre progresivo. D25 a GND.");
      delay(INITIAL_DELAY); // Esperar para ignorar corriente inicial
      initialDelayDone = true;
    } else if (command == "0") {
      closing = false;
      locked = false;
      servoAngle = POS_ABIERTO;
      gripperServo.write(servoAngle);
      digitalOutputState = 0;
      digitalWrite(DIGITAL_OUT_PIN, HIGH); // Desactivar salida (flotante)
      initialDelayDone = false;
      Serial.println("🔼 Gripper abierto a 180°. D25 flotante.");
    } else {
      Serial.println("⚠️ Comando no válido. Usa '1' para cerrar, '0' para abrir.");
    }
  }

  // 🎮 Control del servo
  if (closing && !locked) {
    if (servoAngle > POS_CERRADO && 
        fsr1PressurePsi < FSR_PRESSURE_THRESHOLD && fsr2PressurePsi < FSR_PRESSURE_THRESHOLD &&
        (current < UMBRAL_BLOQUEO || !initialDelayDone)) {
      servoAngle -= 5;
      if (servoAngle < POS_CERRADO) servoAngle = POS_CERRADO;
      gripperServo.write(servoAngle);
      Serial.print("🔽 Cerrando a: ");
      Serial.print(servoAngle);
      Serial.println("°");
      delay(20);
    } else {
      closing = false;
      locked = true;
      gripperServo.write(servoAngle);
      // Enviar estado por UDP
      if (fsr1PressurePsi >= FSR_PRESSURE_THRESHOLD || fsr2PressurePsi >= FSR_PRESSURE_THRESHOLD) {
        udp.beginPacket(PC_IP, PC_PORT);
        udp.print("grasped object");
        udp.endPacket();
        Serial.println("⚡ Objeto agarrado (presión FSR ≥ 5 psi detectada).");
      } else if (current >= UMBRAL_BLOQUEO && initialDelayDone) {
        udp.beginPacket(PC_IP, PC_PORT);
        udp.print("grasped object");
        udp.endPacket();
        Serial.println("⚡ Objeto agarrado (corriente alta detectada).");
      } else {
        udp.beginPacket(PC_IP, PC_PORT);
        udp.print("failed to grasp object");
        udp.endPacket();
        Serial.println("⚠️ Falló en agarrar objeto (llegó a 0°).");
      }
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
  Serial.printf("Ángulo: %d° | Distancia: %.2f cm | Corriente: %.3f A | FSR1: %.3f N, %.3f kg, %.3f psi | FSR2: %.3f N, %.3f psi | D25: %d\n", 
                servoAngle, gripperDistance, current, 
                fsr1ForceN, fsr1WeightKg, fsr1PressurePsi, 
                fsr2ForceN, fsr2PressurePsi, digitalOutputState);
  delay(50);
}
