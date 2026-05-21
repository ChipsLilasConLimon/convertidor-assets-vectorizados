import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import shutil
import os
import preprocesamiento
from datetime import datetime

IMAGEN_DESTINO = "imagen_seleccionada.png"

def seleccionar_imagen():
    ruta = filedialog.askopenfilename(
        title="Selecciona una imagen",
        filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPG", "*.jpg *.jpeg")]
    )
    if not ruta:
        return

    # Guardar ruta en la variable global y mostrar en etiqueta
    ruta_var.set(ruta)
    lbl_ruta.config(text=os.path.basename(ruta))

    # Mostrar vista previa
    img = Image.open(ruta)
    img.thumbnail((300, 300))
    foto = ImageTk.PhotoImage(img)
    lbl_preview.config(image=foto, text="")
    lbl_preview.image = foto  # referencia para evitar garbage collection

    # Habilitar botón de confirmar
    btn_confirmar.config(state="normal")


def confirmar_imagen():
    ruta = ruta_var.get()
    if not ruta:
        messagebox.showwarning("Sin imagen", "Primero selecciona una imagen.")
        return

    # Copiar la imagen al archivo destino (siempre como PNG para OpenCV)
    fecha_actual = datetime.now()
    formato = fecha_actual.strftime("%d%m%y%H%M%S")
    IMAGEN_DESTINO = f"imagen_{formato}.png"
    img = Image.open(ruta).convert("RGB")
    img.save(IMAGEN_DESTINO, "PNG")

    messagebox.showinfo(
        "Listo",
        f"Imagen guardada como:\n{os.path.abspath(IMAGEN_DESTINO)}\n\nYa puedes usarla con OpenCV."
    )
    lbl_estado.config(text=f"✔ Imagen lista: {IMAGEN_DESTINO}", fg="#2ecc71")
    preprocesamiento.procesar_imagen(IMAGEN_DESTINO)


# ── Ventana principal ──────────────────────────────────────────────────────────
ventana = tk.Tk()
ventana.title("Selector de Imagen")
ventana.geometry("420x520")
ventana.resizable(False, False)
ventana.configure(bg="#1e1e2e")

ruta_var = tk.StringVar()

# Título
tk.Label(
    ventana, text="Selector de Imagen",
    font=("Helvetica", 16, "bold"),
    bg="#1e1e2e", fg="#cdd6f4"
).pack(pady=(20, 5))

tk.Label(
    ventana, text="Selecciona una imagen PNG o JPG",
    font=("Helvetica", 10),
    bg="#1e1e2e", fg="#a6adc8"
).pack()

# Área de vista previa
lbl_preview = tk.Label(
    ventana,
    text="Sin imagen seleccionada",
    bg="#313244", fg="#585b70",
    width=30, height=12,
    relief="flat", font=("Helvetica", 10)
)
lbl_preview.pack(pady=15, padx=20)

# Nombre del archivo
lbl_ruta = tk.Label(
    ventana, text="",
    font=("Helvetica", 9), bg="#1e1e2e", fg="#89b4fa",
    wraplength=380
)
lbl_ruta.pack()

# Botón seleccionar
btn_seleccionar = tk.Button(
    ventana, text="📂  Elegir imagen",
    command=seleccionar_imagen,
    font=("Helvetica", 11, "bold"),
    bg="#89b4fa", fg="#1e1e2e",
    activebackground="#74c7ec", activeforeground="#1e1e2e",
    relief="flat", cursor="hand2", padx=16, pady=8
)
btn_seleccionar.pack(pady=(15, 6))

# Botón confirmar (deshabilitado hasta elegir imagen)
btn_confirmar = tk.Button(
    ventana, text="✔  Confirmar y guardar",
    command=confirmar_imagen,
    font=("Helvetica", 11, "bold"),
    bg="#78f16d", fg="#1e1e2e",
    activebackground="#2aeccb", activeforeground="#1e1e2e",
    relief="flat", cursor="hand2", padx=16, pady=8,
    state="disabled"
)
btn_confirmar.pack(pady=4)

# Estado final
lbl_estado = tk.Label(
    ventana, text="",
    font=("Helvetica", 9), bg="#1e1e2e", fg="#a6adc8"
)
lbl_estado.pack(pady=(10, 0))

ventana.mainloop()