# CONTROL DEL TURTLEBOT2 CON LOS DEDOS

# Gestos:
# 0 dedos = detener
# 1 dedo  = avanzar
# 2 dedos = retroceder
# 3 dedos = girar a la izquierda
# 4 dedos = girar a la derecha
# 5 dedos = detener
# Si no hay mano el robot se queda quieto

# Para correrlo:
# source /opt/ros/humble/setup.bash
# python3 Control_Robot.py
# Con el robot real se cambia el topic:
# python3 Control_Robot.py --ros-args -p cmd_vel_topic:=/commands/velocity

import cv2
import mediapipe as mp
import rclpy
from geometry_msgs.msg import Twist
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Int32

# Punta y articulación de cada dedo (indice, medio, anular, meñique)
PUNTAS_DEDOS = [(8, 6), (12, 10), (16, 14), (20, 18)]

# Lo que se escribe en pantalla según el gesto
ACCIONES = {
    0: 'Detenido',
    1: 'Avanzar',
    2: 'Retroceder',
    3: 'Girar izquierda',
    4: 'Girar derecha',
    5: 'Detenido',
}


# Cuenta cuántos dedos están levantados
def contar_dedos(lm_list):
    dedos = 0

    # Pulgar: miro si la punta (4) está más lejos del meñique (17) que el nudillo (3)
    # Así sirve para mano derecha e izquierda
    if abs(lm_list[4][0] - lm_list[17][0]) > abs(lm_list[3][0] - lm_list[17][0]):
        dedos += 1

    # Los demás dedos: comparar en eje y, si la punta está más arriba está levantado
    for punta, articulacion in PUNTAS_DEDOS:
        if lm_list[punta][1] < lm_list[articulacion][1]:
            dedos += 1

    return dedos


# Según los dedos se arma la velocidad que se le manda al robot
def gesto_a_twist(dedos, linear_speed, angular_speed):
    # Empieza en 0, o sea quieto
    twist = Twist()
    if dedos == 1:
        twist.linear.x = linear_speed
    elif dedos == 2:
        twist.linear.x = -linear_speed
    elif dedos == 3:
        twist.angular.z = angular_speed
    elif dedos == 4:
        twist.angular.z = -angular_speed
    return twist


def main():
    # Iniciar ROS 2 (sin su manejo de Ctrl+C para poder frenar el robot al salir)
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = rclpy.create_node('gesture_teleop')

    # Parámetros, se pueden cambiar con --ros-args -p nombre:=valor
    node.declare_parameter('cmd_vel_topic', '/cmd_vel')
    node.declare_parameter('linear_speed', 0.15)    # m/s
    node.declare_parameter('angular_speed', 0.6)    # rad/s
    node.declare_parameter('camera_index', 0)
    # En WSL la cámara solo funcionó bien con MJPG a 320x240
    node.declare_parameter('camera_format', 'MJPG')
    node.declare_parameter('frame_width', 320)
    node.declare_parameter('frame_height', 240)
    # Cuántos cuadros seguidos tiene que repetirse un gesto para aceptarlo
    node.declare_parameter('stable_frames', 3)

    topic = node.get_parameter('cmd_vel_topic').value
    linear_speed = node.get_parameter('linear_speed').value
    angular_speed = node.get_parameter('angular_speed').value
    stable_frames = node.get_parameter('stable_frames').value

    # Publicadores: velocidad para el robot y número de dedos
    cmd_pub = node.create_publisher(Twist, topic, 10)
    dedos_pub = node.create_publisher(Int32, 'dedos_levantados', 10)

    # Inicializar el modelo de detección de manos
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False,
                           max_num_hands=1,
                           min_detection_confidence=0.7,
                           min_tracking_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils

    # Inicializar la cámara
    cap = cv2.VideoCapture(node.get_parameter('camera_index').value, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*node.get_parameter('camera_format').value))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, node.get_parameter('frame_width').value)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, node.get_parameter('frame_height').value)
    if not cap.isOpened():
        node.get_logger().error('No se pudo abrir la cámara')
        node.destroy_node()
        rclpy.shutdown()
        return

    # Variables para que el robot no cambie de gesto por un error de un solo cuadro
    ultimo_conteo = None
    repeticiones = 0
    gesto_activo = 0

    node.get_logger().info(f'Publicando velocidades en {topic}')

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                node.get_logger().warn('No se pudo leer la cámara, deteniendo robot')
                break

            # Voltear la imagen tipo espejo
            frame = cv2.flip(frame, 1)
            # Convertir de BGR a RGB y hacer la detección
            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            dedos = None
            if results.multi_hand_landmarks:
                hand_lms = results.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)
                # Coordenadas x, y de cada punto en pixeles
                h, w, _ = frame.shape
                lm_list = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms.landmark]
                dedos = contar_dedos(lm_list)

            if dedos is None:
                # No hay mano, se detiene
                gesto_activo = 0
                ultimo_conteo = None
                repeticiones = 0
            else:
                # Contar cuántas veces seguidas sale el mismo número
                repeticiones = repeticiones + 1 if dedos == ultimo_conteo else 1
                ultimo_conteo = dedos
                if repeticiones >= stable_frames:
                    gesto_activo = dedos
                dedos_pub.publish(Int32(data=dedos))

            # Mandar la velocidad al robot
            twist = gesto_a_twist(gesto_activo, linear_speed, angular_speed)
            cmd_pub.publish(twist)

            # Agrandar la imagen para verla mejor
            if frame.shape[1] < 640:
                escala = 640 / frame.shape[1]
                frame = cv2.resize(frame, None, fx=escala, fy=escala)
            # Mostrar en pantalla
            texto_dedos = '-' if dedos is None else str(dedos)
            cv2.putText(frame, f'Dedos: {texto_dedos}', (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Accion: {ACCIONES[gesto_activo]}', (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(frame, f'v={twist.linear.x:.2f} m/s  w={twist.angular.z:.2f} rad/s',
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow('Control por gestos', frame)

            # Salir al presionar 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        # Frenar el robot, liberar la cámara y cerrar todo
        cmd_pub.publish(Twist())
        cap.release()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
