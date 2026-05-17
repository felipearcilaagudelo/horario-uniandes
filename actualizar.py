import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
# Agregamos todos los periodos donde quieres buscar
PERIODOS = ["202618", "202619"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"

DIAS_MAP = {"L": 0, "M": 1, "W": 2, "I": 3, "V": 4, "S": 5}

def buscar_nrc_en_periodos(nrc):
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Buscamos en cada periodo de la lista hasta encontrarlo
    for periodo in PERIODOS:
        url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={periodo}&p_numb={nrc}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            cursos = data if isinstance(data, list) else data.get('courses', [])
            for c in cursos:
                if str(c.get('nrc')) == str(nrc):
                    # Guardamos el periodo donde se encontró para mostrarlo luego
                    c['periodo_encontrado'] = periodo
                    return c
        except:
            continue
    return None

def generar_horario():
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except:
        return

    horario_grid = defaultdict(lambda: defaultdict(str))
    lista_detalles = []

    for nrc in nrcs:
        curso = buscar_nrc_en_periodos(nrc)
        if not curso:
            print(f"No se encontró el NRC {nrc} en ninguno de los periodos {PERIODOS}")
            continue

        # Extracción robusta de nombres
        dept = curso.get('class') or curso.get('subject') or "???"
        num = curso.get('course_number') or curso.get('course') or ""
        titulo = curso.get('course_title') or curso.get('title') or curso.get('courseTitle') or "Materia"
        periodo = curso.get('periodo_encontrado')
        
        lista_detalles.append({'dept': dept, 'num': num, 'titulo': titulo, 'nrc': nrc, 'periodo': periodo, 'raw': curso})

        # Procesar horarios
        schs = curso.get('schedules') or curso.get('schedule') or []
        if isinstance(schs, dict): schs = [schs]

        for s in schs:
            dia = s.get('day') or s.get('days') or ""
            hora_str = s.get('time') or s.get('hour') or ""
            
            if dia in DIAS_MAP and hora_str and "-" in hora_str:
                d_idx = DIAS_MAP[dia]
                try:
                    parts = hora_str.replace(":", "").split('-')
                    h_inicio = int(parts[0][:2])
                    h_fin = int(parts[1][:2])
                    
                    # Pintar bloques (Ampliado hasta las 10 PM / 22:00)
                    for h in range(h_inicio, h_fin + 1):
                        if 6 <= h <= 22: 
                            if horario_grid[h][d_idx]:
                                horario_grid[h][d_idx] += f"<br>---<br>**{dept}**"
                            else:
                                horario_grid[h][d_idx] = f"**{dept} {num}**<br>({periodo})"
                except:
                    continue

    # --- ESCRIBIR README ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes - Multisemestre\n")
        f.write(f"Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        f.write("### 🕒 Cuadrícula Semanal (Unificada)\n\n")
        f.write("| Hora | L | M | W | I | V | S |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        
        for h in range(7, 23): # Tabla de 7 AM a 10 PM
            fila = [f"{h}:00"]
            for d_idx in range(6):
                fila.append(horario_grid[h].get(d_idx, " "))
            f.write("| " + " | ".join(fila) + " |\n")
        
        f.write("\n---\n### 📄 Detalle de Materias Encontradas\n")
        for c in lista_detalles:
            f.write(f"#### {c['dept']} {c['num']} - {c['titulo']} (NRC: {c['nrc']})\n")
            f.write(f"- **Periodo:** {c['periodo']}\n")
            schs = c['raw'].get('schedules') or c['raw'].get('schedule') or []
            if isinstance(schs, dict): schs = [schs]
            for s in schs:
                dia = s.get('day') or s.get('days') or "?"
                hora = s.get('time') or s.get('hour') or "?"
                salon = s.get('location') or s.get('room') or "TBA"
                f.write(f"  - 🕒 {dia}: {hora} | 📍 {salon}\n")

if __name__ == "__main__":
    generar_horario()
