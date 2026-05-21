import cv2
import numpy as np
from skimage.feature import hog
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

#CATEGORIAS = ['personaje', 'enemigo', 'plataforma', 'item']
CATEGORIAS = ['personaje', 'item']
TAMAÑO = (64, 64)  # todas las imágenes al mismo tamaño

def cargar_dataset(ruta_dataset):
    datos = []
    etiquetas = []
    
    for categoria in CATEGORIAS:
        ruta = os.path.join(ruta_dataset, categoria)
        for archivo in os.listdir(ruta):
            img = cv2.imread(os.path.join(ruta, archivo))
            if img is None:
                continue
            # Mismo preprocesamiento que ya tienes
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gris = cv2.resize(gris, TAMAÑO)
            # HOG extrae el descriptor de la forma
            descriptor = hog(gris, pixels_per_cell=(8,8), cells_per_block=(2,2))
            datos.append(descriptor)
            etiquetas.append(categoria)
    
    return np.array(datos), np.array(etiquetas)

def entrenar_modelo(ruta_dataset):
    print("Cargando imágenes...")
    X, y = cargar_dataset(ruta_dataset)
    
    # 80% entrena, 20% prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    print("Entrenando SVM...")
    modelo = SVC(kernel='rbf', probability=True)
    modelo.fit(X_train, y_train)
    
    # Ver qué tan bien quedó
    predicciones = modelo.predict(X_test)
    print(f"Precisión: {accuracy_score(y_test, predicciones)*100:.1f}%")
    
    # Guardar el modelo para no entrenar cada vez
    joblib.dump(modelo, 'models/clasificador.pkl')
    print("Modelo guardado en models/clasificador.pkl")

def predecir(ruta_o_array):
    modelo = joblib.load('models/clasificador.pkl')
    
    # Acepta ruta de archivo O array de numpy
    if isinstance(ruta_o_array, str):
        img = cv2.imread(ruta_o_array)
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gris = ruta_o_array  # ya viene en gris (los bordes)

    gris = cv2.resize(gris, TAMAÑO)
    descriptor = hog(gris, pixels_per_cell=(8,8), cells_per_block=(2,2))
    resultado = modelo.predict([descriptor])[0]
    confianza = modelo.predict_proba([descriptor]).max() * 100
    return resultado, confianza

if __name__ == "__main__":
    # Entrenar (solo la primera vez)
    entrenar_modelo('dataset/')

    categoria, confianza = predecir(r"C:\Users\norma\Downloads\prototipo_isr\imagen_160526195153.png")
    print(f"Es un: {categoria} ({confianza:.1f}% de confianza)")