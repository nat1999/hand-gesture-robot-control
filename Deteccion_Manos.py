# DETECCIÓN DE MANOS EN TIEMPO REAL

import cv2
import mediapipe as mp

# Inicializar el modelo de detección de manos
mp_hands = mp.solutions.hands
# Modo video en tiempo real 
hands = mp_hands.Hands(static_image_mode=False,
                       # Indica cuántas manos detecta
                       max_num_hands=2,
                       # Tolerancia mínima para detectar
                       min_detection_confidence=0.7,
                       # Tolerancia mínima para seguir en movimiento 
                       min_tracking_confidence=0.7)
# Dibuja puntos y conexiones de la mano
mp_draw = mp.solutions.drawing_utils

# Inicializar la cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
# Con MJPG y 320x240 la imagen no sale verde ni negra en WSL
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Se agranda para que el texto quepa
    frame = cv2.resize(frame, (640, 480))

    # Convertir la imagen de BGR a RGB
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Realizar la detección
    results = hands.process(img_rgb)

    # Dibujar detecciones
    if results.multi_hand_landmarks:
        # Verifica si hay manos detectadas 
        for hand_lms in results.multi_hand_landmarks:
            # Recorre cada mano detectada 
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

    # Mostrar la imagen
    cv2.imshow("Deteccion", frame)

    # Salir del bucle al presionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()
