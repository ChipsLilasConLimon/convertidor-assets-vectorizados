import cv2
import subprocess
from PIL import Image
import os

def vectorizar(img_binaria, nombre_salida="output"):
    # rutas de los archivos temporales y de salida
    pbm_path = f"{nombre_salida}.pbm"
    svg_path = f"{nombre_salida}.svg"

    # Potrace necesita negro, pero THRESH_BINARY da blanco=objeto entonces se invierte
    invertida = cv2.bitwise_not(img_binaria)

    # convertir el array de numpy a imagen PIL y guardar como .pbm (formato que acepta Potrace)
    img_pil = Image.fromarray(invertida)
    img_pil.save(pbm_path)

    # llamar a Potrace desde la terminal
    resultado = subprocess.run(
        ["potrace", pbm_path, "-s", "-o", svg_path,
         "--fillcolor", "#000000",   # relleno negro
         "--color", "#000000"],      # trazo negro
        capture_output=True, text=True
    )

    # borrar el .pbm, ya no se necesita
    if os.path.exists(pbm_path):
        os.remove(pbm_path)

    # si Potrace terminó sin errores devuelve la ruta del SVG, si no None
    if resultado.returncode == 0:
        print(f"SVG generado: {svg_path}")
        return svg_path
    else:
        print(f"Error Potrace: {resultado.stderr}")
        return None