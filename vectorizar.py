import cv2
import subprocess
from PIL import Image
import os

def vectorizar(bordes, nombre_salida="output"):
    pbm_path = f"{nombre_salida}.pbm"
    svg_path = f"{nombre_salida}.svg"

    # Potrace: blanco=objeto, negro=fondo
    invertida = cv2.bitwise_not(bordes)
    img_pil = Image.fromarray(invertida)
    img_pil.save(pbm_path)

    resultado = subprocess.run(
        ["potrace", pbm_path, "-s", "-o", svg_path],
        capture_output=True, text=True
    )

    # Limpiar el .pbm temporal
    if os.path.exists(pbm_path):
        os.remove(pbm_path)

    if resultado.returncode == 0:
        print(f"SVG generado: {svg_path}")
        return svg_path
    else:
        print(f"Error Potrace: {resultado.stderr}")
        return None