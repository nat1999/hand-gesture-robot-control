# 🖐️ Detección de Manos y Dedos con MediaPipe

Este proyecto detecta la mano en tiempo real con la cámara usando **MediaPipe** y **OpenCV** en Python, cuenta cuántos dedos están levantados y usa ese número para **mover un robot TurtleBot2 con ROS 2**.

El proyecto tiene 4 scripts. Cada uno hace lo mismo que el anterior y le suma una cosa más:

1. Ver la mano en la cámara.
2. Saber qué dedos están levantados.
3. Contar cuántos dedos hay levantados.
4. Mover el robot según ese número.

<p align="center">
  <img src="https://github.com/user-attachments/assets/54ffccfe-7dff-40dd-b8ec-c37ab5c5e13f" height="250"/>
  <img src="https://github.com/user-attachments/assets/847667c8-f4ca-48d7-bba0-53d17f5979d5" height="250"/>
</p>

## 📁 Archivos

| Archivo | Qué hace |
|---|---|
| `Deteccion_Manos.py` | Paso 1: detecta hasta 2 manos y dibuja sus puntos |
| `Deteccion_Dedos.py` | Paso 2: dice qué dedo está levantado y cuál bajado |
| `Conteo_Dedos.py` | Paso 3: además cuenta el total de dedos levantados |
| `Control_Robot.py` | Paso 4: convierte los dedos en movimientos del robot con ROS 2 |
| `test/test_contar_dedos.py` | Pruebas del conteo de dedos sin usar la cámara |

## 🧠 Cómo funciona

MediaPipe encuentra la mano en cada imagen de la cámara y devuelve **21 puntos clave** (*landmarks*). Cada punto tiene un número:

```
        8   12  16  20      ← puntas
        |   |   |   |
        6   10  14  18      ← articulaciones
        |   |   |   |
   4    5---9---13--17
    \  /
     3        0             ← muñeca
```

- **Dedos índice, medio, anular y meñique:** si la punta está más arriba que la articulación (su `y` es menor), el dedo está levantado. Por ejemplo, el índice compara el punto 8 con el 6.
- **Pulgar:** se mueve de lado, entonces se compara en el eje `x`. Se mira si la punta (4) está más lejos del meñique (17) que el nudillo (3).

> En la imagen el eje `y` crece hacia abajo, por eso "más arriba" significa un `y` más pequeño.

## 🪜 Paso a paso

### Paso 1 — Detectar la mano (`Deteccion_Manos.py`)

1. Se abre la cámara con OpenCV (`cv2.VideoCapture(0)`).
2. Cada imagen se pasa de BGR a RGB, porque OpenCV usa BGR y MediaPipe espera RGB.
3. MediaPipe busca hasta 2 manos con una confianza mínima del 70 %.
4. Si encuentra manos, dibuja los 21 puntos y sus conexiones sobre la imagen.
5. Se cierra con la tecla `q`.

### Paso 2 — Ver cada dedo (`Deteccion_Dedos.py`)

1. Igual que el paso 1, pero con una sola mano.
2. Los puntos se pasan a coordenadas en píxeles (`x`, `y`) y se guardan en una lista.
3. Se revisa cada dedo con la regla de arriba y se escribe en pantalla, por ejemplo *"Indice levantado"* o *"Medio bajado"*.

> En este paso el pulgar solo se calcula bien con la **mano derecha**. En el paso 4 se corrigió para que sirva con las dos.

### Paso 3 — Contar los dedos (`Conteo_Dedos.py`)

1. Hace lo mismo que el paso 2.
2. Cada vez que un dedo está levantado suma 1.
3. Muestra el total en verde: *"Dedos levantados: 3"*.

### Paso 4 — Mover el robot (`Control_Robot.py`)

Aquí el número de dedos se convierte en una orden para el TurtleBot2:

| Dedos | Acción del robot |
|:---:|---|
| ✊ 0 | Detenido |
| ☝️ 1 | Avanzar |
| ✌️ 2 | Retroceder |
| 🤟 3 | Girar a la izquierda |
| 🖖 4 | Girar a la derecha |
| 🖐️ 5 | Detenido |
| Sin mano | Detenido |

Cómo lo hace:

1. Crea un nodo de ROS 2 llamado `gesture_teleop`.
2. Cuenta los dedos con la función `contar_dedos()`.
3. Para no reaccionar a un error de un solo cuadro, el gesto se acepta solo si se repite **3 cuadros seguidos**.
4. Según el gesto arma un mensaje `Twist` (velocidad lineal y angular) y lo publica en `/cmd_vel`.
5. También publica el número de dedos en el topic `dedos_levantados`.
6. En pantalla muestra los dedos, la acción y la velocidad.
7. Al salir (con `q` o `Ctrl+C`) manda velocidad 0 para que el robot quede quieto.

## ⚙️ Instalación

Probado en **Ubuntu 22.04** (también en WSL) con **Python 3.10**.

```bash
git clone https://github.com/nat1999/mediapipe-hand-tracking.git
cd mediapipe-hand-tracking
pip3 install -r requirements.txt
```

Para el paso 4 además se necesita **ROS 2 Humble** instalado ([guía oficial](https://docs.ros.org/en/humble/Installation.html)).

## ▶️ Cómo usarlo

### Pasos 1 a 3

```bash
python3 Deteccion_Manos.py
python3 Deteccion_Dedos.py
python3 Conteo_Dedos.py
```

### Paso 4 en simulación (Gazebo)

Con la simulación del TurtleBot abierta y escuchando en `/cmd_vel`:

```bash
source /opt/ros/humble/setup.bash
python3 Control_Robot.py
```

### Paso 4 con el robot real

El TurtleBot2 escucha en otro topic, entonces se cambia así:

```bash
source /opt/ros/humble/setup.bash
python3 Control_Robot.py --ros-args -p cmd_vel_topic:=/commands/velocity
```

### Parámetros que se pueden cambiar

Se cambian con `--ros-args -p nombre:=valor`:

| Parámetro | Valor por defecto | Para qué sirve |
|---|---|---|
| `cmd_vel_topic` | `/cmd_vel` | Topic donde se manda la velocidad |
| `linear_speed` | `0.15` | Velocidad para avanzar/retroceder (m/s) |
| `angular_speed` | `0.6` | Velocidad de giro (rad/s) |
| `camera_index` | `0` | Qué cámara usar |
| `camera_format` | `MJPG` | Formato de la cámara |
| `frame_width` / `frame_height` | `320` / `240` | Resolución de la cámara |
| `stable_frames` | `3` | Cuadros seguidos para aceptar un gesto |

Para ver lo que se publica, en otra terminal:

```bash
ros2 topic echo /cmd_vel
ros2 topic echo /dedos_levantados
```

## 💻 Cámara en WSL

WSL no ve la cámara del computador directamente. Se comparte con [usbipd-win](https://github.com/dorssel/usbipd-win) desde PowerShell como administrador:

```powershell
usbipd list                       # buscar el BUSID de la cámara
usbipd attach --wsl --busid <BUSID>
```

En WSL la cámara solo funcionó bien con formato **MJPG a 320x240**, por eso son los valores por defecto.

## ✅ Pruebas

Las pruebas revisan `contar_dedos()` con manos inventadas (puño, 1, 2, 4 y 5 dedos, y mano izquierda), así que no necesitan cámara:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test
```

## 🚀 Aplicaciones

- Control de robots por gestos
- Visión artificial
- Interacción humano-computador
