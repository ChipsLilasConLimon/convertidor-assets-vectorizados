import cv2
import numpy as np
import clasificador
from PIL import Image, ImageTk
import vectorizar

def procesar_imagen(nombre_archivo):
    img = cv2.imread(nombre_archivo)
    imagen_gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gausiano = cv2.GaussianBlur(imagen_gris, (5, 5), 0)
    ret, img_binaria = cv2.threshold(gausiano, 117, 255, cv2.THRESH_BINARY)
    bordes = cv2.Canny(img_binaria, 100, 200)

    #1: clasificar con el gris ---
    categoria, confianza = clasificador.predecir(imagen_gris)
    print(f"Es un: {categoria} ({confianza:.1f}% de confianza)")



    contornos, _ = cv2.findContours(bordes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_resultado = img.copy()
    if contornos:
        todos = np.vstack(contornos)
        # agarrar el contorno más grande (el objeto principal)
        x, y, w, h = cv2.boundingRect(todos)
        color = (0, 0, 255)
        cv2.rectangle(img_resultado, (x, y), (x + w, y + h), color, 3)


    #2: vectorizar con los bordes ---
    cv2.imwrite(f"bordes_{nombre_archivo}.png", bordes)
    # aquí después va Potrace para generar el SVG
    svg = vectorizar.vectorizar(bordes, nombre_archivo.replace('.png', ''))

    # mostrar todo para el portafolio
    cv2.imshow('Gris', imagen_gris)
    cv2.imshow('Binaria', img_binaria)
    cv2.imshow('Bordes', bordes)
    cv2.imshow('Resultado', img_resultado)
    cv2.waitKey(0)
    cv2.destroyAllWindows()