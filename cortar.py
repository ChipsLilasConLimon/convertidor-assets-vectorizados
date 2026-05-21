from PIL import Image
import os

# Abrir imagen
imagen = Image.open(r"C:\Users\norma\Downloads\prototipo_isr\73213-OEHDT2-663.jpg")

# Tamaño del spritesheet
ancho_total, alto_total = imagen.size

# Grid
columnas = 4
filas = 4

# Tamaño de cada sprite
ancho_sprite = ancho_total // columnas
alto_sprite = alto_total // filas

# Carpeta de salida
os.makedirs("sprites", exist_ok=True)

contador = 0

for fila in range(filas):
    for columna in range(columnas):

        # Coordenadas del recorte
        izquierda = columna * ancho_sprite
        superior = fila * alto_sprite
        derecha = izquierda + ancho_sprite
        inferior = superior + alto_sprite

        # Recortar sprite
        sprite = imagen.crop((izquierda, superior, derecha, inferior))

        # Guardar
        sprite.save(f"sprites/sprite_{contador + 56}.png")

        contador += 1

print("Sprites exportados:", contador)