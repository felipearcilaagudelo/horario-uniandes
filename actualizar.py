import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODOS = ["202618", "202619"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"

# Mapeo según lo que vimos en el diagnóstico
# l=Lunes, m=Martes, i=Miércoles, j=Jueves, v=Viernes, s=Sábado
DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
DIAS_NOMBRES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

def buscar_nrc(nrc):
    headers = {'User-Agent': 'Mozilla/5.0'}
    for p in PERIODOS:
        url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={p}&p_numb={nrc}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            cursos = data if isinstance(data, list) else data.get('courses', [])
            for c in cursos:
                if str(c.get('nrc')) == str(nrc):
                    c['periodo_encontrado'] = p
                    return c
        except: continue
    return None

def generar():
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except: return

    horario_grid = defaultdict(lambda: defaultdict(str))
    detalles = []

    for nrc in nrcs:
        c = buscar_nrc(nrc)
        if not c: continue

        # Extraer datos según el nuevo formato
        dept = c.get('class', '???')
        num = c.get('course', '???')
        titulo = c.get('title', 'Materia')
        p_enc = c.get('periodo_encontrado')
        
        detalles.append({'dept': dept, 'num': num, 'titulo': titulo, 'nrc': nrc, 'p': p_enc, 'raw': c})

        # Procesar horarios con el nuevo formato de columnas (l, m, i, j, v, s)
        schedules = c.get('schedules', [])
        for s in schedules:
            t_ini = s.get('time_ini')
            t_fin = s.get('time_fin')
            
            if t_ini and t_fin:
                h_inicio = int(t_ini[:2])
                h_fin = int(t_fin[:2])
                
                # Revisar cada columna de día
                for dia_key, col_idx in DIAS_API.items():
                    if s.get(dia_key): # Si el valor no es null (ej: "L", "M", "S")
                        for h in range(h_inicio, h_fin + 1):
                            if 7 <= h <= 21:
                                if horario_grid[h][col_idx]:
                                    if dept not in horario_grid[h][col_idx]:
                                        horario_grid[h][col_idx] += f"<br>---<br>**{dept}**"
                                else:
                                    horario_grid[h][col_idx] = f"**{dept} {num}**"

    # --- ESCRIBIR README ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\n")
        f.write(f"Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        f.write("### 🕒 Cuadrícula Semanal\n\n")
        f.write("| Hora | L | M | W | J | V | S |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d_idx in range(6):
                fila.append(horario_grid[h].get(d_idx, " "))
            f.write("| " + " | ".join(fila) + " |\n")
        
        f.write("\n---\n### 📄 Detalle de Materias\n")
        for d in detalles:
            f.write(f"#### {d['dept']} {d['num']} - {d['titulo']} (NRC: {d['nrc']})\n")
            f.write(f"- **Periodo:** {d['p']}\n")
            for s in d['raw'].get('schedules', []):
                dias = [v for k, v in s.items() if k in DIAS_API and v]
                f.write(f"  - 🕒 {''.join(dias)}: {s.get('time_ini')}-{s.get('time_fin')} | 📍 {s.get('building')} {s.get('classroom')}\n")

if __name__ == "__main__":
    generar()
