# DETECCIÓN DE MANOS EN TIEMPO REAL

import cv2
import mediapipe as mp

# Inicializar el modelo de detección de manos
mp_hands = mp.solutions.hands
# Modo video en tiempo real 
hands = mp_hands.Hands(static_image_mode=False,
                       # Indica cuántas manos detecta
                       max_num_hands=1,
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

            # Lista para almacenar coordenadas de los landmarks
            lm_list = []
            h, w, _ = frame.shape

            # Obtener coordenadas x, y de cada punto
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))

            dedos_levantados = 0 

            # Verificar si el pulgar está levantado (ID 4 es la punta, ID 3 es el nudillo)
            # Comparar en eje x mano derecha(Pulgar) 
            if (lm_list[4][1] > lm_list[3][1]):
                
                    estado_pulgar = "Pulgar levantado"
                    dedos_levantados += 1
            else:
                    estado_pulgar = "Pulgar bajado"                    
            # Mostrar en pantalla y consola
            cv2.putText(frame, estado_pulgar, (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            print(estado_pulgar)
            
            # Comparar en eje y mano derecha(Indice) 
            if (lm_list[8][2]  < lm_list[6][2]):
                
                    estado_indice = "Indice levantado"
                    dedos_levantados += 1
            else:
                    estado_indice = "Indice bajado"                    
            # Mostrar en pantalla y consola
            cv2.putText(frame, estado_indice, (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            print(estado_indice)

             # Comparar en eje y mano derecha(Medio) 
            if (lm_list[12][2]  < lm_list[10][2]):
                
                    estado_medio = "Medio levantado"
                    dedos_levantados += 1
            else:
                    estado_medio = "Medio bajado"                    
            # Mostrar en pantalla y consola
            cv2.putText(frame, estado_medio, (10, 110),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            print(estado_medio)

             # Comparar en eje y mano derecha(Medio) 
            if (lm_list[16][2]  < lm_list[14][2]):
                
                    estado_anular = "Anular levantado"
                    dedos_levantados += 1
            else:
                    estado_anular = "Anular bajado"                    
            # Mostrar en pantalla y consola
            cv2.putText(frame, estado_anular, (10, 140),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            print(estado_anular)

            # Comparar en eje y mano derecha(Medio) 
            if (lm_list[20][2]  < lm_list[18][2]):
                
                    estado_menique = "Menique levantado"
                    dedos_levantados += 1
            else:
                    estado_menique = "Menique bajado"                    
            # Mostrar en pantalla y consola
            cv2.putText(frame, estado_menique, (10, 170),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            print(estado_menique)

            # Mostrar total de dedos levantados
            cv2.putText(frame, f"Dedos levantados: {dedos_levantados}", (10, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print("Total dedos levantados:", dedos_levantados)

    # Mostrar la imagen
    cv2.imshow("Deteccion", frame)

    # Salir del bucle al presionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()
