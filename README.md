# 🖐️ Detección de Manos y Dedos con MediaPipe

Este proyecto permite detectar y reconocer los movimientos de la mano en tiempo real mediante una cámara, utilizando MediaPipe y OpenCV en Python. A partir de esta detección, identifica y cuenta la cantidad de dedos levantados, utilizando este número como señal de control para mover un robot TurtleBot2 mediante ROS 2.

El proyecto está compuesto por cuatro scripts:

1. **Detección de la mano:** captura y visualización de la mano en tiempo real mediante la cámara.
2. **Identificación de dedos:** reconoce cuáles dedos se encuentran levantados.
3. **Conteo de dedos:** determina la cantidad de dedos levantados.
4. **Control del robot:** utiliza el número de dedos detectados para generar los comandos de movimiento del TurtleBot2 mediante ROS 2.


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

### 1. MediaPipe marca la mano con puntos

En cada imagen de la cámara, MediaPipe encuentra la mano y le pone **21 puntos** (*landmarks*): uno en la muñeca y cuatro en cada dedo. Cada punto tiene un número y una posición en la imagen (`x`, `y`).

Para saber si un dedo está levantado solo se usan algunos de esos puntos: la **punta** de cada dedo y una **articulación** más abajo.

```
         8   12   16   20      ← puntas
         |    |    |    |
         6   10   14   18      ← articulaciones
         |    |    |    |
   4     5----9---13---17
    \   /
     3 /
      \       0                ← muñeca
```

### 2. Se revisa cada dedo

**Índice, medio, anular y meñique.** Cuando el dedo está estirado, la punta queda por encima de la articulación. Cuando está doblado, la punta baja.

Entonces se compara la altura (`y`) de los dos puntos:

| Dedo | Punta | Articulación |
|---|:---:|:---:|
| Índice | 8 | 6 |
| Medio | 12 | 10 |
| Anular | 16 | 14 |
| Meñique | 20 | 18 |

Si la punta está más arriba que la articulación, el dedo cuenta como **levantado**.

**Pulgar.** El pulgar no sube y baja como los otros, se abre hacia el lado. Por eso no se mira la altura sino la distancia horizontal (`x`):

- Se mide qué tan lejos está la punta del pulgar (4) del meñique (17).
- Se mide qué tan lejos está el nudillo del pulgar (3) del meñique (17).
- Si la punta está más lejos que el nudillo, el pulgar está **abierto**.

Como se mide una distancia y no un lado, funciona igual con la mano derecha y con la izquierda.

### 3. Se suman los dedos

Cada dedo levantado suma 1. El resultado es un número del 0 al 5, y ese número es el que se usa para mover el robot.

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

### Paso 3 — Contar los dedos (`Conteo_Dedos.py`)

1. Hace lo mismo que el paso 2.
2. Cada vez que un dedo está levantado suma 1.
3. Muestra el total en verde: *"Dedos levantados: 3"*.

### Paso 4 — Mover el robot (`Control_Robot.py`)

Aquí el número de dedos se convierte en una orden para el TurtleBot2. Solo importa **cuántos** dedos hay arriba, no cuáles. Cada número tiene una velocidad fija:

| Dedos | `linear.x` (m/s) | `angular.z` (rad/s) | Acción del robot |
|:---:|:---:|:---:|---|
| ✊ 0 | 0 | 0 | Detenido |
| ☝️ 1 | 0.15 | 0 | Avanzar |
| ✌️ 2 | -0.15 | 0 | Retroceder |
| 🤟 3 | 0 | 0.6 | Girar a la izquierda |
| 🖖 4 | 0 | -0.6 | Girar a la derecha |
| 🖐️ 5 | 0 | 0 | Detenido |
| Sin mano | 0 | 0 | Detenido |

- `linear.x` es la velocidad hacia adelante. Si es negativa, el robot va hacia atrás.
- `angular.z` es la velocidad de giro. Si es positiva gira a la izquierda, si es negativa a la derecha.
- La velocidad no cambia con la mano, siempre es la misma. Para cambiarla se usan los parámetros `linear_speed` y `angular_speed`.
- El robot se mueve mientras mantengas el gesto. Si bajas la mano, se detiene.

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

La prueba está en [`test/test_contar_dedos.py`](test/test_contar_dedos.py). No usa la cámara: arma a mano los 21 puntos de una mano falsa (función `mano()`), se los pasa a `contar_dedos()` de `Control_Robot.py` y revisa que el número sea el correcto (puño = 0, índice = 1, índice y medio = 2, cuatro dedos = 4, mano abierta = 5, y también la mano izquierda con `espejo()`).

Para correrla:

```bash
source /opt/ros/humble/setup.bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test -v
```

Resultado en la terminal:

```
collected 6 items

test/test_contar_dedos.py::test_puno PASSED                              [ 16%]
test/test_contar_dedos.py::test_un_dedo PASSED                           [ 33%]
test/test_contar_dedos.py::test_dos_dedos PASSED                         [ 50%]
test/test_contar_dedos.py::test_cuatro_dedos PASSED                      [ 66%]
test/test_contar_dedos.py::test_palma_abierta PASSED                     [ 83%]
test/test_contar_dedos.py::test_mano_izquierda PASSED                    [100%]

============================== 6 passed in 2.79s ===============================
```

## 🚀 Aplicaciones

- Control de robots por gestos
- Visión artificial
- Interacción humano-computador
