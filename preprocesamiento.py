import cv2
import numpy as np
import clasificador
from PIL import Image, ImageTk
import vectorizar

# el metodo se encarga de obtener un archivo para su procesamiento
def procesar_imagen(nombre_archivo):
    # se lee la imagen con opencv
    img = cv2.imread(nombre_archivo)
    #convierte la imagen a escala de grises
    imagen_gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #se le aplica un filtro gausiano para reducir el ruido
    gausiano = cv2.GaussianBlur(imagen_gris, (5, 5), 0)
    #se binariza la imagen para separar el objeto del fondo
    ret, img_binaria = cv2.threshold(gausiano, 117, 255, cv2.THRESH_BINARY)
    #se detectan los bordes con el algoritmo Canny
    bordes = cv2.Canny(img_binaria, 100, 200)

    # se clasifica con el gris. LLama al clasificador entrenado
    categoria, confianza = clasificador.predecir(imagen_gris)
    print(f"Es un: {categoria} ({confianza:.1f}% de confianza)")
    
    #1: se dibuja un rectángulo alrededor del objeto detectado usando los bordes
    contornos, _ = cv2.findContours(bordes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # se copia la imagen original para dibujar el resultado
    img_resultado = img.copy()
    # si se encontraron contornos, se obtiene el contorno más grande (el objeto principal) y se dibuja un rectángulo rojo alrededor de él
    if contornos:
        # se combinan todos los contornos en uno solo la  box del objeto
        todos = np.vstack(contornos)
        # agarrar el contorno más grande (el objeto principal)
        x, y, w, h = cv2.boundingRect(todos)
        # se declara el color rojo para el rectángulo
        color = (0, 0, 255)
        # se dibuja el rectángulo en img_resultado, NO en img
        cv2.rectangle(img_resultado, (x, y), (x + w, y + h), color, 3)

    #2: vectorizar con los bordes
    cv2.imwrite(f"bordes_{nombre_archivo}.png", bordes)
    # Potrace es llamdo para generar el SVG
    svg = vectorizar.vectorizar(img_binaria, nombre_archivo.replace('.png', ''))
    