import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODO = "202618" 
ARCHIVO_LISTA = "mis_clases.txt" # El archivo de tu imagen
README_FILE = "README.md"

DIAS_LABELS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
DIAS_MAP = {"L": 0, "M": 1, "W": 2, "I": 3, "V": 4, "S": 5}

def buscar_nrc(nrc):
    url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={PERIODO}&p_numb={nrc}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        cursos = data if isinstance(data, list) else data.get('courses', [])
        # Filtrar solo el NRC exacto por si la búsqueda devuelve parecidos
        return [c for c in cursos if str(c.get('nrc')) == str(nrc)]
    except:
        return []

def generar_horario():
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("No se encontró mis_clases.txt")
        return

    # Estructura para la tabla: horario[hora][dia_index]
    horario_grid = defaultdict(lambda: defaultdict(str))
    lista_detalles = []

    for nrc in nrcs:
        print(f"Procesando NRC: {nrc}...")
        resultados = buscar_nrc(nrc)
        
        for curso in resultados:
            cod_clase = curso.get('class', 'Clase')
            titulo = curso.get('course_title', '')
            lista_detalles.append(curso)
            
            for s in curso.get('schedules', []):
                dia = s.get('day')
                hora_str = s.get('time', '') # Formato "0800-0920"
                
                if dia in DIAS_MAP and hora_str and hora_str != 'TBA':
                    d_idx = DIAS_MAP[dia]
                    h_inicio = int(hora_str.split('-')[0][:2])
                    h_fin = int(hora_str.split('-')[1][:2])
                    
                    # Llenar todos los bloques de hora que ocupa la clase
                    for h in range(h_inicio, h_fin + 1):
                        # Evitar sobreescribir si hay cruces, mejor concatenar
                        if horario_grid[h][d_idx]:
                            horario_grid[h][d_idx] += f"<br>⚠️ **CRUCE:** {cod_clase}"
                        else:
                            horario_grid[h][d_idx] = f"**{cod_clase}**<br>({nrc})"

    # Escribir el README
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\n")
        f.write(f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        # Dibujar la tabla Markdown
        f.write("### 🕒 Cuadrícula Semanal\n\n")
        f.write("| Hora | L | M | W | I | V | S |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        
        for h in range(7, 21): # De 7 AM a 8 PM
            fila = [f"{h}:00"]
            for d_idx in range(6):
                celda = horario_grid[h].get(d_idx, " ")
                fila.append(celda)
            f.write("| " + " | ".join(fila) + " |\n")
        
        f.write("\n---\n### 📄 Detalle de Materias\n")
        for c in lista_detalles:
            f.write(f"- **{c.get('class')} {c.get('course_number')}:** {c.get('course_title')} (NRC: {c.get('nrc')})\n")
            for s in c.get('schedules', []):
                f.write(f"  - {s.get('day')} {s.get('time')} en {s.get('location')}\n")

if __name__ == "__main__":
    generar_horario()
