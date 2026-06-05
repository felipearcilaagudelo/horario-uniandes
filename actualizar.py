import requests
import datetime
import time
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODOS = ["202620", "202619", "202618"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]

def buscar_nrc(nrc):
    # Cabeceras completas imitando a un navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://ofertadecursos.uniandes.edu.co/',
        'X-Requested-With': 'XMLHttpRequest', # <--- Clave para APIs de Banner
        'Accept': 'application/json, text/plain, */*'
    }
    
    for p in PERIODOS:
        # Probamos la URL directa que usa el buscador interno
        url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={p}&p_numb={nrc}"
        try:
            time.sleep(0.5)
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                cursos = data if isinstance(data, list) else data.get('courses', [])
                for curso in cursos:
                    if str(curso.get('nrc')).strip() == str(nrc).strip():
                        curso['p_enc'] = p
                        return curso
        except Exception as e:
            print(f"DEBUG: Fallo en periodo {p} para NRC {nrc}: {e}")
    return None

def generar():
    print("Iniciando proceso...")
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error crítico abriendo {ARCHIVO_LISTA}: {e}")
        return

    horario_grid = defaultdict(lambda: defaultdict(list))
    encontrados = []
    no_encontrados = []

    for idx, nrc in enumerate(nrcs):
        print(f"Buscando NRC: {nrc}")
        c = buscar_nrc(nrc)
        
        if c:
            print(f"✅ Encontrado: {c.get('title', 'Sin título')}")
            info = {
                'dept': str(c.get('class', '???')),
                'num': str(c.get('course', '???')),
                'titulo': str(c.get('title') or "Materia").title(),
                'nrc': str(nrc),
                'color': COLORES[idx % len(COLORES)],
                'p': c.get('p_enc'),
                'tiene_horario': False
            }
            
            # Procesar horario
            schedules = c.get('schedules', [])
            for s in schedules:
                ti, tf = s.get('time_ini'), s.get('time_fin')
                if ti and tf and ti != "TBA":
                    try:
                        h_ini = int(str(ti)[:2])
                        h_fin = int(str(tf)[:2])
                        info['tiene_horario'] = True
                        for dia_key, col_idx in DIAS_API.items():
                            if s.get(dia_key):
                                for h in range(h_ini, h_fin + 1):
                                    if 7 <= h <= 21:
                                        horario_grid[h][col_idx].append(info)
                    except: continue
            encontrados.append(info)
        else:
            print(f"❌ No se encontró el NRC {nrc}")
            no_encontrados.append(nrc)

    # Crear README
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Horario Uniandes\nActualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d in range(6):
                clases = horario_grid[h][d]
                fila.append("<br>".join(list(set([f"**{m['dept']}**" for m in clases]))) if clases else " ")
            f.write("| " + " | ".join(fila) + " |\n")
        
        f.write("\n### 🔍 Detalle:\n")
        for m in encontrados:
            f.write(f"- {m['dept']}{m['num']} ({m['nrc']}): {'✅' if m['tiene_horario'] else '⚠️ Sin horario'}\n")
        for n in no_encontrados:
            f.write(f"- NRC {n}: ❌ No encontrado en periodos {PERIODOS}\n")

    # Crear HTML simple
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(f"<html><body><h1>Mi Horario</h1><p>Refresca el README para ver detalles.</p></body></html>")

if __name__ == "__main__":
    generar()
