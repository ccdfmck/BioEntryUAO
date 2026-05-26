*BioEntry (Sistema de Reconocimiento Facial UAO)*

BioEntry es una aplicación web basada en inteligencia artificial diseñada para el control de acceso peatonal e identificación de estudiantes, docentes y personal administrativo en la Universidad Autónoma de Occidente (UAO).

El sistema actúa como una herramienta de apoyo directo al personal de seguridad del campus, reduciendo la carga operativa de los guardas al automatizar la verificación de identidad en tiempo real, esto les permite concentrarse en situaciones que requieren intervención humana, elevando el nivel general de seguridad institucional.

Adicionalmente, BioEntry elimina la necesidad de torniquetes u otras barreras físicas de control de acceso, como actualmente se realiza a través de una identificación de huella dactilar para que se active el torniquete y permita el paso del usuario, lo que reduce el tráfico en los puntos de ingreso, agiliza el flujo peatonal en horas pico y mejora la experiencia de toda la comunidad universitaria sin sacrificar el registro de accesos.

El sistema captura video en tiempo real, detecta rostros y realiza una búsqueda de características biométricas en una base de datos local de alta velocidad para autorizar o denegar el ingreso de forma automatizada.

*1. ARQUITECTURA Y TECNOLOGÍAS UTILIZADAS*
El proyecto combina un backend ágil en Python con algoritmos avanzados de visión computacional y aprendizaje profundo:

- Backend y Framework Web: Flask (Python 3.10)
- Procesamiento de Video y Visión Artificial: OpenCV
- Extracción de Características Faciales: DeepFace (con soporte de tf-keras y detector RetinaFace para máxima precisión en oclusiones y ángulos variables)
- Indexación y Búsqueda Biométrica Vectorial: FAISS (Facebook AI Similarity Search) para búsquedas de embeddings en microsegundos
- Almacenamiento de Datos: SQLite3 (Base de datos relacional ligera para metadatos de usuarios) y Pandas para la manipulación estructurada de registros


*2. REQUISITOS E INSTALACIÓN*
Siga rigurosamente estos pasos en su terminal para configurar el entorno local.

*Paso 2.0: Base de Datos de Muestra*
El repositorio de GitHub del proyecto incluye una carpeta `database/` con la base de datos que se compone de un conjunto de registros de prueba, lo que permite levantar el sistema sin necesidad de registrar usuarios desde cero durante la fase de evaluación o demostración.
*Paso 2.1: Requisitos Previos*
Asegúrese de tener instalado Python 3.10 en su sistema. Puede descargarlo desde el sitio oficial de Python.
*Paso 2.2: Configuración del Entorno Virtual e Instalación de Dependencias*
Abra la terminal en la raíz del proyecto y ejecute los siguientes comandos:

```
python -m venv venv
venv\Scripts\activate
pip install flask opencv-python deepface faiss-cpu numpy
pip install pandas
pip install pillow
pip install tf-keras
pip install retina-face
pip install deepface
pip install faiss
```

*Paso 2.3: Verificación de la Cámara de Video*
Antes de inicializar la base de datos, verifique que Python tenga acceso a su hardware de captura web con el siguiente comando de prueba:
```
"python -c "import cv2; print(cv2.VideoCapture(0).read())"
```
Si retorna `(True, <array_bi_dimensional>)`, su cámara está lista para operar.

*3. FLUJO DE INICIALIZACIÓN DEL SISTEMA*
Para arrancar el aplicativo por primera vez, se debe estructurar la base de datos y compilar los vectores de los rostros:

1. Crear el esquema de la base de datos relacional:
`python create_database.py`

2. Generar el índice de embeddings biométricos (FAISS):
`python create_embeddings.py`

3. Iniciar el servidor web del aplicativo:
`python aplicativo.py`

Una vez que el terminal indique que el servidor local está corriendo, abra su navegador web e ingrese a la dirección asignada (por lo general, la IP local por defecto): `http://127.0.0.1:5000`

*(Nota: Verifique la consola de comandos por si el framework asignó un puerto alternativo.)*

*4. FUNCIONALIDADES DEL APLICATIVO*
*Funcionalidad 4.1: Interfaz de Monitoreo en Vivo (Live Feed)*
Es la pantalla principal del software que gestiona el flujo continuo del punto de acceso:
- Detección en tiempo real: La cámara procesa el flujo a un promedio de 30 fps. Al encontrar una cara, dibuja un recuadro dinámico sobre el video.
- Verificación Exitosa (Aprobado): Si el rostro pertenece a un usuario registrado y supera el Umbral de aprobación (>= 60% de confianza), el recuadro se torna verde, mostrando el nombre completo en pantalla. En la barra lateral izquierda se cargará automáticamente su perfil (Foto, Rol, Código Estudiantil y Programa).
- Acceso Denegado (Desconocido): Si la confianza es menor al 60% o el rostro no se encuentra en el índice FAISS, el sistema despliega un estado de Denegado, guardando el log histórico como "Desconocido".

*Funcionalidad 4.2: Panel de Estadísticas y Analítica Lateral*
Ubicado en el margen izquierdo del dashboard, provee métricas clave en tiempo real:
- Cámaras Activas: Estado del hardware de captura de video (ej. 1/1).
- Usuarios Registrados: Muestra el total de plantillas biométricas almacenadas en el sistema (ej. 9 registrados).
- Métricas del Día: Contador acumulativo de ingresos "Aprobados Hoy" y accesos "Denegados Hoy".
- Historial Reciente: Una lista cronológica al pie del menú con las últimas identificaciones procesadas, detallando el porcentaje exacto de confianza y la estampa de tiempo (Hora: MM:SS PM).

*Funcionalidad 4.3: Panel de Administración y Gestión de Usuarios*
Diseñado para la administración segura del personal del campus. BioEntry opera con una única fotografía por usuario registrado; al momento del alta, el sistema extrae el vector de características faciales a partir de esa imagen y lo almacena en el índice FAISS, lo que simplifica el proceso de enrolamiento sin requerir sesiones fotográficas múltiples ni equipos especializados de captura.

- Acceso Restringido: Al dar clic en el botón superior Admin, emergerá una ventana modal de autenticación. La contraseña maestra por defecto es: `uao2026`
- Pestaña "Agregar Usuario": Permite dar de alta a nuevos estudiantes o colaboradores cargando una fotografía (.jpg o .png de máximo 5MB) y rellenando los campos mandatorios: Nombre Completo, Código, Rol (Estudiante, Docente, Administrativo) y Programa Académico. Al guardar, el backend actualiza de forma transparente la base de datos y regenera el vector descriptor.
- Pestaña "Usuarios Registrados": Lista completa de todas las identidades dentro del sistema, permitiendo auditar sus datos de manera rápida o eliminar registros antiguos para revocar inmediatamente su permiso de acceso biométrico.
- Actualización Automática: Al agregar o eliminar un usuario desde el panel de administración, el sistema actualiza el índice FAISS de forma automática, sin necesidad de ejecutar scripts adicionales ni reiniciar el servidor.

*Privacidad y Manejo de Datos Biométricos*
Toda la información biométrica, como fotografías y vectores de embeddings faciales, se almacena exclusivamente en la base de datos local de la universidad, los datos no se transmiten a servidores externos en ningún momento. El acceso al sistema está restringido al personal de seguridad autorizado mediante contraseña de administrador.

*5. LIMITACIONES*
BioEntry es un prototipo académico desarrollado en el marco del programa de ingeniería de la Universidad Autónoma de Occidente. Como tal, presenta las siguientes limitaciones conocidas:

- Iluminación: El sistema no fue evaluado bajo condiciones de baja iluminación como variable independiente; todas las pruebas se realizaron en ambientes con iluminación controlada, por lo que su desempeño en entornos oscuros o con luz artificial intensa no está garantizado.
- Imagen de referencia única: Cada usuario está registrado con una sola fotografía. Esto puede afectar la precisión en casos donde el rostro presente variaciones significativas respecto a la imagen original (accesorios, cambios de apariencia, ángulos extremos).
- Procesamiento por CPU: El sistema fue desarrollado y probado íntegramente sobre CPU, sin aceleración por GPU; esto puede representar una limitante de rendimiento si se escala a múltiples cámaras simultáneas.

Universidad Autónoma de Occidente, Proyecto BioEntry 2026