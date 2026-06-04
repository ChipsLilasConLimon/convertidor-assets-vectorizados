import cv2
import numpy as np
from skimage.feature import hog
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os

# categorias que el modelo puede reconocer, cada una debe tener su carpeta en el dataset
CATEGORIAS = ['personaje', 'item', 'background', 'enemigo']
# tamaño fijo al que se escalan todas las imagenes antes de procesarlas
TAMAÑO = (64, 64)


def resize_pixel_art(img, tamaño):
    # INTER_NEAREST toma el pixel mas cercano en lugar de promediar los vecinos
    # cualquier otro modo de interpolacion suaviza los bordes y arruina el pixel art
    return cv2.resize(img, tamaño, interpolation=cv2.INTER_NEAREST)


def extraer_features(img_bgr):
    # HOG (Histogram of Oriented Gradients) convierte la imagen en un vector numerico
    # que describe donde estan los bordes y en que direccion apuntan
    # sirve para capturar la forma general del sprite sin importar colores
    gris = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gris = resize_pixel_art(gris, TAMAÑO)
    feat_hog = hog(gris, pixels_per_cell=(8, 8), cells_per_block=(2, 2), orientations=9)

    # HSV separa el color (H), la intensidad del color (S) y el brillo (V)
    # es mejor que RGB para comparar colores porque el brillo no contamina el tono
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    hsv = resize_pixel_art(hsv, TAMAÑO)

    # calcular cuantos pixeles caen en cada rango de tono, saturacion y brillo
    # esto resume la paleta de colores del sprite en tres vectores chicos
    hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180]).flatten()  # 16 rangos de tono
    hist_s = cv2.calcHist([hsv], [1], None, [8],  [0, 256]).flatten()  # 8 rangos de saturacion
    hist_v = cv2.calcHist([hsv], [2], None, [8],  [0, 256]).flatten()  # 8 rangos de brillo

    # dividir entre el total para que el histograma sea una proporcion (0 a 1)
    # si no, una imagen mas grande tendria valores mas altos aunque sea el mismo sprite
    hist_h /= (hist_h.sum() + 1e-7)
    hist_s /= (hist_s.sum() + 1e-7)
    hist_v /= (hist_v.sum() + 1e-7)
    feat_color = np.concatenate([hist_h, hist_s, hist_v])  # 32 valores en total

    # el aspect ratio ayuda a distinguir categorias por su forma general
    # un personaje suele ser mas alto que ancho, un background mas ancho que alto
    # un item tiende a ser cuadrado
    h, w = img_bgr.shape[:2]
    aspect = np.array([w / (h + 1e-7)])

    # concatenar todo en un solo vector que representa la imagen numericamente
    return np.concatenate([feat_hog, feat_color, aspect])


def cargar_dataset(ruta_dataset):
    datos, etiquetas = [], []

    #recorre cada una de las categorias del dataset
    for categoria in CATEGORIAS:
        ruta = os.path.join(ruta_dataset, categoria)
        if not os.path.exists(ruta):
            print(f"Carpeta no encontrada: {ruta}")
            continue

        archivos = [f for f in os.listdir(ruta)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]

        for archivo in archivos:
            img = cv2.imread(os.path.join(ruta, archivo))
            if img is None:
                # cv2 falla silenciosamente con nombres que tienen caracteres especiales
                continue

            # imagen original
            datos.append(extraer_features(img))
            etiquetas.append(categoria)

            # espejo horizontal: el sprite viendo hacia el otro lado
            # es una imagen valida y distinta para el modelo sin cambiar la categoria
            datos.append(extraer_features(cv2.flip(img, 1)))
            etiquetas.append(categoria)

            # espejo vertical: util para items o backgrounds que pueden aparecer invertidos
            # no se usan rotaciones de 90/180 porque voltear un personaje de cabeza
            # ya no parece un personaje y confunde al modelo
            datos.append(extraer_features(cv2.flip(img, 0)))
            etiquetas.append(categoria)

        print(f"  '{categoria}': {len(archivos)} imagenes -> {len(archivos)*3} con augmentation")

    return np.array(datos), np.array(etiquetas)


def entrenar_modelo(ruta_dataset):
    X, y = cargar_dataset(ruta_dataset)
    print(f"Total de muestras: {len(X)}")

    # Pipeline encadena el scaler y el SVM para que siempre se apliquen juntos
    # esto evita el error comun de normalizar el entrenamiento pero olvidarlo al predecir
    modelo = Pipeline([
        # StandardScaler centra cada feature en 0 y la escala a varianza 1
        # el kernel RBF del SVM mide distancias entre vectores, si una feature
        # tiene valores 100x mas grandes que otra va a dominar el calculo injustamente
        ('scaler', StandardScaler()),
        ('svm', SVC(
            kernel='rbf',       # RBF puede separar clases con fronteras curvas, no solo lineas
            C=10,               # penalizacion por errores, mas alto = menos tolerancia a fallos
            gamma='scale',      # ajusta el radio de influencia de cada punto automaticamente
            probability=True,   # habilita predict_proba para obtener porcentaje de confianza
            class_weight='balanced'  # si una clase tiene menos imagenes, sus errores pesan mas
        ))
    ])

    # con pocos datos un solo split de train/test es poco confiable
    # cross-validation divide el dataset en 5 partes, entrena en 4 y prueba en 1,
    # repite 5 veces rotando cual parte es el test, y promedia los resultados
    print("Evaluando con cross-validation...")
    scores = cross_val_score(modelo, X, y, cv=StratifiedKFold(n_splits=5), scoring='accuracy')
    print(f"Precision promedio: {scores.mean()*100:.1f}% +/- {scores.std()*100:.1f}%")

    # entrenar ahora con todo el dataset para el modelo que se va a guardar
    # la evaluacion ya se hizo arriba, esto es solo para aprovechar todos los datos
    print("Entrenando modelo final...")
    modelo.fit(X, y)

    # guardar el modelo entrenado en un archivo para usarlo luego
    os.makedirs('models', exist_ok=True)
    joblib.dump(modelo, 'models/clasificador.pkl')
    print("Modelo guardado en models/clasificador.pkl")
    return modelo


def predecir(ruta_o_array):
    # cargar el modelo ya entrenado
    modelo = joblib.load('models/clasificador.pkl')

    if isinstance(ruta_o_array, str):
        img = cv2.imread(ruta_o_array)
    else:
        # si llega una imagen en gris (de procesar_imagen), convertir a BGR
        # porque extraer_features espera una imagen a color para el histograma HSV
        if len(ruta_o_array.shape) == 2:
            img = cv2.cvtColor(ruta_o_array, cv2.COLOR_GRAY2BGR)
        else:
            img = ruta_o_array

    descriptor = extraer_features(img)
    resultado = modelo.predict([descriptor])[0]
    probas = modelo.predict_proba([descriptor])[0]
    confianza = probas.max() * 100

    # imprimir todas las probabilidades para ver si el modelo dudo entre categorias
    clases = modelo.classes_
    for clase, prob in sorted(zip(clases, probas), key=lambda x: -x[1]):
        print(f"  {clase}: {prob*100:.1f}%")

    return resultado, confianza

# se ejecuta para entrenar por primera vez
if __name__ == "__main__":
    entrenar_modelo(r"C:\Users\norma\Downloads\prototipo_isr\dataset")