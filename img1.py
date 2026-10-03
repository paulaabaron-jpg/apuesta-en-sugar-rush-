import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import random
import time

# Carpeta donde está el script; aquí se buscan las imágenes de los vehículos.
CARPETA = Path(__file__).resolve().parent
IMAGENES = sorted(CARPETA.glob("*.png"))

# Se valida que existan al menos 10 imágenes para los 10 vehículos.
if len(IMAGENES) < 10:
    raise FileNotFoundError("Se necesitan 10 imágenes .png en la carpeta del programa.")

IMAGENES = IMAGENES[:10]
# Ventana principal de la aplicación.
ventana = tk.Tk()
ventana.title("Apuesta en Sugar Rush!")
ventana.geometry("980x780")

# Variables que controlan la velocidad general, cantidad de vueltas y la apuesta del usuario.
velocidad_general = tk.DoubleVar(value=1.0)
rondas_var = tk.IntVar(value=3)
seleccion_var = tk.StringVar()
resultado = tk.StringVar(value="Aún no empieza la carrera")

# Canvas donde se dibuja la pista y los vehículos.
canvas = tk.Canvas(ventana, width=930, height=500, bg="#ffffff")
canvas.pack(padx=10, pady=10)
for i in range(10):
    y = 40 + i * 42 #linea de la pista para cada vehículo
    canvas.create_line(20, y + 18, 900, y + 18, fill="#555", width=2)   
frm = tk.Frame(ventana)
frm.pack(fill="x", padx=10, pady=(0, 10))
tk.Label(frm, text="Rondas:").grid(row=0, column=0, padx=5, pady=5)
tk.Spinbox(frm, from_=1, to=20, textvariable=rondas_var, width=8).grid(row=0, column=1, padx=5)

#muestra el nombre y guarda la selección del usuario
tk.Label(frm, text="Apuesta:").grid(row=0, column=2, padx=5, pady=5)
combo = ttk.Combobox(frm, values=[p.stem for p in IMAGENES], textvariable=seleccion_var, state="readonly", width=20)
combo.grid(row=0, column=3, padx=5)
combo.current(0)

#Este control permite acelerar o desacelerar la carrera.
slider = tk.Scale(frm, from_=0.5, to=2.0, variable=velocidad_general, orient="horizontal", resolution=0.1, length=220, label="Velocidad")
slider.grid(row=0, column=4, padx=10)

btn_iniciar = tk.Button(ventana, text="Iniciar", command=lambda: iniciar_carrera())
btn_iniciar.pack(side="left", padx=10, pady=10)

btn_reiniciar = tk.Button(ventana, text="Reiniciar", command=lambda: reiniciar_carrera())
btn_reiniciar.pack(side="left", padx=5, pady=10)

lbl_resultado = tk.Label(ventana, textvariable=resultado, fg="#1d3557", font=("Arial", 10, "bold"))
lbl_resultado.pack(side="left", padx=10, pady=10)

#Tabla de resultados de la carrera
ranking = ttk.Treeview(ventana, columns=("pos", "auto", "tiempo"), show="headings", height=10)
ranking.heading("pos", text="Posición")
ranking.heading("auto", text="Vehículo")
ranking.heading("tiempo", text="Tiempo")
ranking.column("pos", width=80, anchor="center")
ranking.column("auto", width=220, anchor="center")
ranking.column("tiempo", width=120, anchor="center")
ranking.pack(fill="x", padx=10, pady=(0, 10))

# Aquí se instancian los 10 vehículos con su imagen, nombre y estado inicial.
vehiculos = []
for i, ruta in enumerate(IMAGENES):
    nombre = ruta.stem   #nombre del archivo sin extensión
    foto = tk.PhotoImage(file=str(ruta)) #carga la imagen del vehículo
    foto = foto.subsample(5, 5) #reduce para el tamaño de la imagen (canvas)
    x = 20
    y = 40 + i * 42 #linea de la pista para cada vehículo
    label_x = 20
    label_y = y + 8
    img_id = canvas.create_image(x + 90, y, anchor="nw", image=foto)
    txt_id = canvas.create_text(label_x, label_y, anchor="w", text=nombre, font=("Arial", 9, "bold"))
    vehiculos.append({ #datos de cada vehículo
        "nombre": nombre,
        "foto": foto,
        "img_id": img_id,
        "txt_id": txt_id,
        "x": x + 90,
        "y": y,
        "label_x": label_x,
        "label_y": label_y,
        "vueltas": 0,
        "tiempo": 0.0,
        "inicio": 0.0,
        "timer": None,
        "terminado": False,
        # random se usa para dar velocidad distinta a cada vehículo en cada vuelta.
        "base_delay": random.randint(40, 120),
    })

carrera_activa = False

def limpiar_tabla():
    for fila in ranking.get_children():
        ranking.delete(fila) #borra los datos de la tabla de resultados

# Mueve visualmente el auto y deja fijo su nombre.
def actualizar_posicion(v): #v es un "cada vehículo"
    canvas.coords(v["img_id"], v["x"], v["y"])
    canvas.coords(v["txt_id"], v["label_x"], v["label_y"])

def terminar_carrera():
    global carrera_activa
    carrera_activa = False
    orden = sorted([v for v in vehiculos if v["terminado"]], key=lambda v: v["tiempo"])
    ganador = orden[0]["nombre"]
    apuesta = seleccion_var.get()

    if apuesta == ganador:
        resultado.set(f"Ganó: {ganador}. ¡Apostaste bien!")
    else:
        resultado.set(f"Ganó: {ganador}. Perdiste:(")

    limpiar_tabla()
    for i, v in enumerate(orden, start=1):
        ranking.insert("", "end", values=(i, v["nombre"], round(v["tiempo"], 2)))

# Función que hace avanzar cada vehículo con un timer independiente.
def tick(v):
    if not carrera_activa or v["terminado"]:
        return

    # random decide cuanto avanza en cada paso, para que no todos sean iguales.
    v["x"] += random.randint(10, 18)
    if v["x"] >= 850:
        v["x"] = 20
        v["vueltas"] += 1
        v["base_delay"] = random.randint(40, 120)

    if v["vueltas"] >= rondas_var.get():
        v["terminado"] = True
        v["tiempo"] = time.perf_counter() - v["inicio"]
        if all(v["terminado"] for v in vehiculos):
            terminar_carrera()
        return

    # El slider modifica la velocidad general del juego.
    actual = max(20, int(v["base_delay"] / velocidad_general.get()))
    actualizar_posicion(v)
    v["timer"] = ventana.after(actual, tick, v)


# Inicia la carrera: re-inicializa a los 10 vehículos y activa sus timers.
def iniciar_carrera():
    global carrera_activa
    if carrera_activa:
        return

    carrera_activa = True
    limpiar_tabla()
    resultado.set("Carrera en curso...")

    for v in vehiculos:
        v["x"] = 20
        v["vueltas"] = 0
        v["tiempo"] = 0.0
        v["terminado"] = False
        v["base_delay"] = random.randint(40, 120)
        v["inicio"] = time.perf_counter()
        actualizar_posicion(v)
        if v["timer"] is not None:
            ventana.after_cancel(v["timer"])
        v["timer"] = ventana.after(50, tick, v)
# Reinicia la carrera sin cerrar la ventana principal.
def reiniciar_carrera():
    global carrera_activa
    carrera_activa = False
    for v in vehiculos:
        if v["timer"] is not None:
            ventana.after_cancel(v["timer"])
            v["timer"] = None
        v["x"] = 20
        v["vueltas"] = 0
        v["tiempo"] = 0.0
        v["terminado"] = False
        actualizar_posicion(v)
    limpiar_tabla()
    resultado.set("Aún no empieza la carrera")

ventana.mainloop()
