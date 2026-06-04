import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from datetime import datetime
import threading
import clasificador
import vectorizar


# ventana principal de la aplicación
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reconocimiento de Imagen")
        self.geometry("960x660")
        self.configure(bg="white")
        self.resizable(True, True)
        self.ruta_var = tk.StringVar()  # guarda la ruta de la imagen seleccionada
        self.img_refs = {}
        self.procesando = False
        self.svg_path = None
        self._build_ui()

    # construye todos los elementos visuales de la ventana
    def _build_ui(self):
        # barra superior
        hdr = tk.Frame(self, bg="#2563eb", pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Sistema de Reconocimiento de Imagen",
                 font=("Segoe UI", 13, "bold"), bg="#2563eb", fg="white").pack(side="left", padx=16)
        btn_gal = tk.Button(hdr, text="Galería", command=self._abrir_galeria,
                            font=("Segoe UI", 9, "bold"), bg="white", fg="#2563eb",
                            relief="flat", padx=14, pady=5, cursor="hand2", bd=0)
        btn_gal.pack(side="right", padx=16)

        body = tk.Frame(self, bg="white")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # columna izquierda con controles
        left = tk.Frame(body, bg="white", width=210)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        tk.Label(left, text="Imagen de entrada", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#374151").pack(anchor="w", pady=(0, 4))

        # vista previa de la imagen cargada
        self.lbl_preview = tk.Label(left, text="Sin imagen",
                                    font=("Segoe UI", 9), bg="#f3f4f6", fg="#9ca3af",
                                    width=26, height=9, relief="flat")
        self.lbl_preview.pack()

        # nombre del archivo cargado
        self.lbl_nombre = tk.Label(left, text="", font=("Segoe UI", 8),
                                   bg="white", fg="#6b7280", wraplength=200, anchor="w")
        self.lbl_nombre.pack(fill="x", pady=(4, 8))

        tk.Button(left, text="Cargar imagen", command=self._seleccionar,
                  font=("Segoe UI", 10), bg="#2563eb", fg="white",
                  relief="flat", padx=8, pady=6, cursor="hand2", bd=0).pack(fill="x")

        self.btn_procesar = tk.Button(left, text="Procesar", command=self._procesar,
                                      font=("Segoe UI", 10, "bold"), bg="#16a34a", fg="white",
                                      relief="flat", padx=8, pady=6, cursor="hand2",
                                      bd=0, state="disabled")
        self.btn_procesar.pack(fill="x", pady=(6, 0))

        tk.Frame(left, bg="#e5e7eb", height=1).pack(fill="x", pady=14)

        # muestra la categoría detectada y el porcentaje de confianza
        tk.Label(left, text="Clasificación", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#374151").pack(anchor="w")
        self.lbl_categoria = tk.Label(left, text="—",
                                      font=("Segoe UI", 17, "bold"), bg="white", fg="#2563eb")
        self.lbl_categoria.pack(pady=(6, 2))
        self.lbl_confianza = tk.Label(left, text="",
                                      font=("Segoe UI", 9), bg="white", fg="#6b7280")
        self.lbl_confianza.pack()

        tk.Frame(left, bg="#e5e7eb", height=1).pack(fill="x", pady=14)

        # sección de vectorización — muestra si se generó el SVG
        tk.Label(left, text="Vectorización", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#374151").pack(anchor="w")
        self.lbl_svg = tk.Label(left, text="Sin SVG generado",
                                font=("Segoe UI", 8), bg="white", fg="#9ca3af",
                                wraplength=200, anchor="w")
        self.lbl_svg.pack(anchor="w", pady=(4, 0))

        # botón para guardar el SVG, aparece solo cuando hay uno disponible
        self.btn_guardar_svg = tk.Button(left, text="Guardar imagen vectorizada",
                                         command=self._guardar_svg,
                                         font=("Segoe UI", 9), bg="#4eb8c6", fg="white",
                                         relief="flat", padx=8, pady=6, cursor="hand2", bd=0)

        # columna derecha con los 4 resultados del procesamiento
        right = tk.Frame(body, bg="white")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Resultados del procesamiento",
                 font=("Segoe UI", 9, "bold"), bg="white", fg="#374151").pack(anchor="w", pady=(0, 6))

        grid = tk.Frame(right, bg="white")
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=0)
        grid.rowconfigure(1, weight=0)

        # define los cuatro cuadros de resultados con su título y posición
        celdas = [
            ("Escala de grises",    "gris",      0, 0),
            ("Umbralización",       "binaria",   0, 1),
            ("Detección de bordes", "bordes",    1, 0),
            ("Resultado final",     "resultado", 1, 1),
        ]

        self.img_labels = {}
        for titulo, key, row, col in celdas:
            frame = tk.Frame(grid, bg="white", relief="solid", bd=1,
                             highlightbackground="#e5e7eb", highlightthickness=1)
            frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            tk.Label(frame, text=titulo, font=("Segoe UI", 8, "bold"),
                     bg="#f9fafb", fg="#6b7280", anchor="w", padx=8, pady=5).pack(fill="x")

            lbl = tk.Label(frame, text="—", font=("Segoe UI", 9),
                           bg="white", fg="#d1d5db")
            lbl.pack(fill="both", expand=True, padx=4, pady=4)
            self.img_labels[key] = lbl

        # barra de estado en la parte inferior
        tk.Frame(self, bg="#e5e7eb", height=1).pack(fill="x", padx=16)
        self.lbl_status = tk.Label(self, text="Listo.",
                                   font=("Segoe UI", 8), bg="white", fg="#9ca3af", anchor="w")
        self.lbl_status.pack(fill="x", padx=16, pady=5)

    # abre el explorador para seleccionar una imagen
    def _seleccionar(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if not ruta:
            return
        self.ruta_var.set(ruta)
        self.lbl_nombre.config(text=os.path.basename(ruta))

        img = Image.open(ruta)
        img.thumbnail((200, 150))
        foto = ImageTk.PhotoImage(img)
        self.lbl_preview.config(image=foto, text="", width=0, height=0)
        self.img_refs["preview"] = foto

        self.btn_procesar.config(state="normal")
        self.lbl_status.config(text="Imagen cargada. Presiona Procesar.")

        # limpia los resultados anteriores
        for lbl in self.img_labels.values():
            lbl.config(image="", text="—")
        self.lbl_categoria.config(text="—")
        self.lbl_confianza.config(text="")
        self.lbl_svg.config(text="Sin SVG generado", fg="#9ca3af")
        self.svg_path = None
        self.btn_guardar_svg.pack_forget()

    # inicia el procesamiento de la imagen
    def _procesar(self):
        if self.procesando:
            return
        self.procesando = True
        self.btn_procesar.config(state="disabled", text="Procesando...")
        self.lbl_status.config(text="Procesando...")
        threading.Thread(target=self._run, daemon=True).start()

    # aplica los filtros, clasifica y vectoriza la imagen
    def _run(self):
        import cv2
        import numpy as np
        ruta = self.ruta_var.get()
        try:
            # guarda una copia de la imagen con la fecha como nombre
            fecha = datetime.now().strftime("%d%m%y%H%M%S")
            dest  = f"imagen_{fecha}.png"
            Image.open(ruta).convert("RGB").save(dest)

            # pasos de procesamiento de imagen
            img      = cv2.imread(dest)
            gris     = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gauss    = cv2.GaussianBlur(gris, (5, 5), 0)
            _, binar = cv2.threshold(gauss, 117, 255, cv2.THRESH_BINARY)
            bordes   = cv2.Canny(binar, 100, 200)

            # dibuja un rectángulo alrededor del objeto detectado
            resultado = img.copy()
            contornos, _ = cv2.findContours(bordes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contornos:
                x, y, w, h = cv2.boundingRect(np.vstack(contornos))
                cv2.rectangle(resultado, (x, y), (x+w, y+h), (37, 99, 235), 3)

            # clasificación con el modelo entrenado
            try:
                cat, conf = clasificador.predecir(gris)
            except Exception:
                cat, conf = "sin modelo", 0.0

            # vectorización con Potrace
            svg_path = None
            try:
                svg_path = vectorizar.vectorizar(bordes, dest.replace(".png", ""))
            except Exception:
                pass

            # actualiza la interfaz con los resultados
            def update():
                self._mostrar(gris,      "gris",      cv2.COLOR_GRAY2RGB)
                self._mostrar(binar,     "binaria",   cv2.COLOR_GRAY2RGB)
                self._mostrar(bordes,    "bordes",    cv2.COLOR_GRAY2RGB)
                self._mostrar(resultado, "resultado", cv2.COLOR_BGR2RGB)
                self.lbl_categoria.config(text=cat.capitalize())
                self.lbl_confianza.config(text=f"{conf:.1f}% de confianza")
                if svg_path:
                    self.svg_path = svg_path
                    self.lbl_svg.config(text=f"✔ {svg_path}", fg="#16a34a")
                    self.btn_guardar_svg.pack(fill="x", pady=(6, 0))
                else:
                    self.svg_path = None
                    self.btn_guardar_svg.pack_forget()
                self.lbl_status.config(
                    text=f"Listo — '{cat}' con {conf:.1f}% de confianza.")
                self.btn_procesar.config(state="normal", text="Procesar")
                self.procesando = False

            self.after(0, update)

        except Exception as e:
            def err():
                self.lbl_status.config(text=f"Error: {e}", fg="#dc2626")
                self.btn_procesar.config(state="normal", text="Procesar")
                self.procesando = False
            self.after(0, err)

    # convierte un array de imagen y lo muestra en su cuadro correspondiente
    def _mostrar(self, arr, key, conv):
        import cv2
        pil  = Image.fromarray(cv2.cvtColor(arr, conv))
        pil.thumbnail((260, 170), Image.LANCZOS)
        foto = ImageTk.PhotoImage(pil)
        self.img_labels[key].config(image=foto, text="")
        self.img_refs[key] = foto

    # abre la ventana de galería con todas las imágenes procesadas
    def _abrir_galeria(self):
        import glob, io

        # busca todas las imágenes guardadas, las más recientes primero
        pngs = sorted(glob.glob("imagen_*.png"), reverse=True)

        top = tk.Toplevel(self)
        top.title("Galería")
        top.geometry("920x600")
        top.configure(bg="#f1f5f9")
        top.resizable(True, True)

        # encabezado con el total de imágenes
        hdr_g = tk.Frame(top, bg="#1e40af", pady=12)
        hdr_g.pack(fill="x")
        tk.Label(hdr_g, text="Galería de procesamiento",
                 font=("Segoe UI", 12, "bold"), bg="#1e40af", fg="white").pack(side="left", padx=20)
        badge_txt = f"{len(pngs)} imagen{'es' if len(pngs) != 1 else ''}"
        tk.Label(hdr_g, text=badge_txt, font=("Segoe UI", 8),
                 bg="#3b82f6", fg="white", padx=8, pady=3).pack(side="left")

        # área de scroll para las tarjetas
        container = tk.Frame(top, bg="#f1f5f9")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#f1f5f9", highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        frame = tk.Frame(canvas, bg="#f1f5f9")
        frame.img_refs = []
        win_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _scroll))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        top.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        if not pngs:
            tk.Label(frame, text="Aún no hay imágenes procesadas.",
                     font=("Segoe UI", 11), bg="#f1f5f9", fg="#94a3b8").pack(pady=80)
            return

        THUMB = (185, 130)  # tamaño máximo de cada miniatura
        COLS  = 2           # imágenes por fila

        # cuadrícula de 2 columnas
        grid_f = tk.Frame(frame, bg="#f1f5f9")
        grid_f.pack(fill="both", expand=True, padx=14, pady=14)
        grid_f.columnconfigure(0, weight=1)
        grid_f.columnconfigure(1, weight=1)

        # crea una columna con su etiqueta e imagen dentro de una tarjeta
        def _make_image_col(parent, label_text, label_bg, label_fg, img_path_or_none, svg_path_or_none):
            col = tk.Frame(parent, bg="white")
            col.pack(side="left", fill="both", expand=True)

            tk.Label(col, text=label_text, font=("Segoe UI", 7, "bold"),
                     bg=label_bg, fg=label_fg, padx=6, pady=3).pack(fill="x")

            tk.Frame(col, bg="#f1f5f9", height=6).pack()

            if img_path_or_none:
                try:
                    img = Image.open(img_path_or_none)
                    img.thumbnail(THUMB)
                    foto = ImageTk.PhotoImage(img)
                    frame.img_refs.append(foto)
                    tk.Label(col, image=foto, bg="white").pack(padx=8, pady=(0, 8))
                except Exception:
                    tk.Label(col, text="Error", bg="white", fg="#dc2626").pack(pady=20)

            elif svg_path_or_none and os.path.exists(svg_path_or_none):
                svg_loaded = False
                try:
                    from svglib.svglib import svg2rlg
                    from reportlab.graphics import renderPM
                    drawing = svg2rlg(os.path.abspath(svg_path_or_none))
                    if drawing:
                        buf = io.BytesIO()
                        renderPM.drawToFile(drawing, buf, fmt="PNG")
                        buf.seek(0)
                        img_svg = Image.open(buf)
                        img_svg.thumbnail(THUMB)
                        foto_svg = ImageTk.PhotoImage(img_svg)
                        frame.img_refs.append(foto_svg)
                        tk.Label(col, image=foto_svg, bg="white").pack(padx=8, pady=(0, 8))
                        svg_loaded = True
                except Exception:
                    pass
                if not svg_loaded:
                    tk.Label(col, text="instalar svglib\npara previsualizar",
                             font=("Segoe UI", 7), bg="#f8fafc", fg="#94a3b8",
                             width=16, height=5).pack(padx=8, pady=(0, 8))
            else:
                tk.Label(col, text="sin vectorización",
                         font=("Segoe UI", 7), bg="white", fg="#cbd5e1").pack(pady=20)

        # genera una tarjeta por cada imagen encontrada
        for i, png_path in enumerate(pngs):
            base       = png_path.replace(".png", "")
            svg_path_g = f"{base}.svg"
            row_i      = i // COLS
            col_i      = i % COLS

            shadow = tk.Frame(grid_f, bg="#cbd5e1")
            shadow.grid(row=row_i, column=col_i, padx=8, pady=8, sticky="nsew")

            card = tk.Frame(shadow, bg="white")
            card.pack(fill="both", expand=True, padx=1, pady=1)

            # nombre del archivo
            tk.Label(card, text=os.path.basename(base), font=("Segoe UI", 9, "bold"),
                     bg="white", fg="#111827").pack(anchor="w", padx=10, pady=(8, 4))

            tk.Frame(card, bg="#f1f5f9", height=1).pack(fill="x")

            pair = tk.Frame(card, bg="white")
            pair.pack(fill="both", expand=True)

            _make_image_col(pair, "  ORIGINAL",    "#dbeafe", "#1d4ed8", png_path,    None)
            tk.Frame(pair, bg="#f1f5f9", width=1).pack(side="left", fill="y")
            _make_image_col(pair, "  VECTORIZADA", "#dcfce7", "#15803d", None, svg_path_g)

    # guarda el SVG generado en la ubicación que elija el usuario
    def _guardar_svg(self):
        import shutil
        if not self.svg_path or not os.path.exists(self.svg_path):
            self.lbl_status.config(text="No hay SVG disponible para guardar.")
            return
        dest = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg"), ("Todos los archivos", "*.*")],
            initialfile=os.path.basename(self.svg_path)
        )
        if dest:
            shutil.copy2(self.svg_path, dest)
            self.lbl_status.config(text=f"SVG guardado en: {dest}")

if __name__ == "__main__":
    App().mainloop()
