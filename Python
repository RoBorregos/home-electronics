import socket

ESP32_IP = "192.168.1.188"  
ESP32_PORT = 1234  

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("📡 Transmisor UDP listo.")
print("⚡ Comandos: 'AUTO', 'MANUAL', 'CLOSE', 'OPEN', 'q'")

modo_actual = "AUTO"

while True:
    comando = input("Escribe un comando: ").strip().lower()
    if comando == "q":
        break

    if comando in ["auto", "manual", "close", "open"]:
        modo_actual = comando.upper()
        sock.sendto(comando.upper().encode(), (ESP32_IP, ESP32_PORT))
        print(f"📤 Comando enviado: {modo_actual}")
    elif modo_actual == "MANUAL":
        try:
            angulo = int(comando)
            if 0 <= angulo <= 180:
                sock.sendto(str(angulo).encode(), (ESP32_IP, ESP32_PORT))
                print(f"📤 Ángulo enviado: {angulo}°")
            else:
                print("⚠️ Ángulo debe estar entre 0 y 180.")
        except ValueError:
            print("⚠️ Entrada inválida.")
    else:
        print("⚠️ Cambia a modo MANUAL para enviar ángulos.")

sock.close()
print("🔴 Conexión cerrada.")
