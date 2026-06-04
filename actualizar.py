import requests
import datetime
import time
from collections import defaultdict

# --- CONFIGURACIÓN ---
# Lista de periodos ultra-ampliada para no fallar
PERIODOS = ["202620"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]

def buscar_nrc(nrc, session):
    # Simulamos un navegador real al 100%
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Referer': 'https://ofertadecursos.uniandes.edu.co/',
        'Origin': 'https://ofertadecursos.uniandes.edu.co',
        'Connection': 'keep-alive',
    }
    
    for p in PERIODOS:
        # El endpoint con todos los campos que envía el formulario de la web
        url = "https://ofertadecursos.uniandes.edu.co/api/courses"
        params = {
            "term": p,
            "ptrm": "",
            "p_level": "",
            "p_dept": "",
            "p_subj": "",
            "p_numb": nrc, # NRC se busca en este campo en la web
            "p_instructor": "",
            "p_crse": "",
            "p_day": "",
            "p_hour": "",
            "p_hour_end": ""
        }
        
        try:
            time.sleep(1.5) # Esperamos 1.5 segundos entre búsquedas para evitar bloqueos
            r = session.get(url, params=params, headers=headers, timeout=15)
            
            if r.status_code != 200:
                print(f"Log: Error {r.status_code} en {p} para NRC {nrc}")
                continue
                
            data = r.json()
            cursos = data if isinstance(data, list) else data.get('courses', [])
            
            for c in cursos:
                if str(c.get('nrc', '')).strip() == str(nrc).strip():
                    c['p_enc'] = p
                    return c
        except Exception as e:
            print(f"Log: Error en {nrc} - {p}: {e}")
            continue
    return None

def generar():
    session = requests.Session()
    # "Engañamos" al servidor entrando primero a la página principal
    try:
        session.get("https://ofertadecursos.uniandes.edu.co/", timeout=10)
    except: pass

    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except: return

    horario_grid = defaultdict(lambda: defaultdict(list))
    encontrados = []
    no_encontrados = []

    for idx, nrc in enumerate(nrcs):
        print(f"Buscando NRC {nrc}...")
        c = buscar_nrc(nrc, session)
        
        if not c:
            no_encontrados.append(nrc)
            continue

        info = {
            'dept': c.get('class', '???'),
            'num': c.get('course', '???'),
            'titulo': (c.get('title') or "Materia").title(),
            'nrc': nrc,
            'color': COLORES[idx % len(COLORES)],
            'p': c.get('p_enc'),
            'tiene_horario': False
        }

        # Lógica de horario basada en el diagnóstico exitoso que tuvimos
        schedules = c.get('schedules', [])
        for s in schedules:
            t_ini, t_fin = s.get('time_ini'), s.get('time_fin')
            if t_ini and t_fin:
                try:
                    h_ini = int(str(t_ini)[:2])
                    h_fin = int(str(t_fin)[:2])
                    info['tiene_horario'] = True
                    for dia_key, col_idx in DIAS_API.items():
                        if s.get(dia_key):
                            for h in range(h_ini, h_fin + 1):
                                if 7 <= h <= 21:
                                    horario_grid[h][col_idx].append(info)
                except: continue
        
        encontrados.append(info)

    # --- ESCRIBIR README.md ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\n")
        f.write(f"Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} (GMT)\n\n")
        
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d_idx in range(6):
                clases = horario_grid[h][d_idx]
                nombres = list(set([f"**{m['dept']}**" for m in clases]))
                txt = "<br>".join(nombres) if nombres else " "
                fila.append(txt)
            f.write("| " + " | ".join(fila) + " |\n")

        f.write("\n---\n### 🔍 Estado de tus NRCs:\n")
        for m in encontrados:
            status = "✅ Cargado" if m['tiene_horario'] else "⚠️ Sin horario fijo (Virtual/TBA)"
            f.write(f"- **{m['dept']}{m['num']}** ({m['nrc']}): {status} [Periodo: {m['p']}]\n")
        for nrc in no_encontrados:
            f.write(f"- **NRC {nrc}**: ❌ No se encontró. Revisa el número o que no esté cerrado.\n")

    # --- GENERAR index.html (Página Web) ---
    # ... código simplificado para la web ...
    html = f"<html><head><meta charset='UTF-8'><style>body{{font-family:sans-serif;padding:20px;background:#f0f2f5}} .card{{background:white;padding:20px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.1);max-width:900px;margin:auto}} table{{width:100%;border-collaps
