import socket

def parse_gripper_data(data_string):
    # Separar el string por comas
    values = data_string.split(',')

    # Verificar que haya exactamente 9 valores
    if len(values) != 9:
        raise ValueError(f"Se esperaban 9 valores, pero se recibieron {len(values)}: {data_string}")
    
    try:
        gripper_data = [
            int(values[0]),         # angulo (grados)
            float(values[1]),       # distancia (cm)
            float(values[2]),       # current (A)
            float(values[3]),       # fsr1ForceN (N)
            float(values[4]),       # fsr1WeightKg (kg)
            float(values[5]),       # fsr1PressurePsi (psi)
            float(values[6]),       # fsr2ForceN (N)
            float(values[7]),       # fsr2PressurePsi (psi)
            int(values[8])          # digitalOutputState (0 o 1)
        ]
    except ValueError as e:
        raise ValueError(f"Error al convertir los valores a números: {data_string} - {str(e)}")
    
    # Formatear los datos en un string etiquetado
    labeled_string = (
        f"Ángulo: {gripper_data[0]}° | "
        f"Distancia: {gripper_data[1]:.2f} cm | "
        f"Corriente: {gripper_data[2]:.3f} A | "
        f"FSR1 Fuerza: {gripper_data[3]:.3f} N | "
        f"FSR1 Peso: {gripper_data[4]:.3f} kg | "
        f"FSR1 Presión: {gripper_data[5]:.3f} psi | "
        f"FSR2 Fuerza: {gripper_data[6]:.3f} N | "
        f"FSR2 Presión: {gripper_data[7]:.3f} psi | "
        f"Salida Digital: {'GND' if gripper_data[8] == 1 else 'Flotante'}"
    )
    
    return labeled_string

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 1234))  # Escuchar en el puerto 1234
sock.settimeout(5.0)

print("Escuchando datos UDP...")
while True:
    try:
        data, addr = sock.recvfrom(1024)
        # Parsear y formatear los datos en un string etiquetado
        labeled_data = parse_gripper_data(data.decode())
        print(f"Datos recibidos de {addr}: {labeled_data}")
    except socket.timeout:
        print("No se recibieron datos en 5 segundos.")
        break
    except ValueError as e:
        print(f"Error al parsear los datos: {e}")

sock.close()
