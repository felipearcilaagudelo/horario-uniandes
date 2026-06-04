import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
# He agregado 2025 por si acaso los NRCs son del año pasado
PERIODOS = ["202619", "202618", "202610", "202620"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]

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
                    c['p_enc'] = p
                    return c
        except: continue
    return None

def generar():
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except: return

    horario_grid = defaultdict(lambda: defaultdict(list))
    encontrados = []
    no_encontrados = []

    for idx, nrc in enumerate(nrcs):
        c = buscar_nrc(nrc)
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

        schedules = c.get('schedules', [])
        for s in schedules:
            t_ini, t_fin = s.get('time_ini'), s.get('time_fin')
            if t_ini and t_fin and t_ini != "TBA":
                info['tiene_horario'] = True
                h_ini, h_fin = int(t_ini[:2]), int(t_fin[:2])
                for dia_key, col_idx in DIAS_API.items():
                    if s.get(dia_key):
                        for h in range(h_ini, h_fin + 1):
                            if 7 <= h <= 21:
                                horario_grid[h][col_idx].append(info)
        
        encontrados.append(info)

    # ESCRIBIR README
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\nActualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        # Tabla
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d_idx in range(6):
                clases = horario_grid[h][d_idx]
                txt = "<br>".join([f"**{m['dept']}**" for m in clases]) if clases else " "
                fila.append(txt)
            f.write("| " + " | ".join(fila) + " |\n")

        f.write("\n---\n### 🔍 Estado de tus NRCs:\n")
        for m in encontrados:
            status = "✅ Encontrada" if m['tiene_horario'] else "⚠️ Sin horario asignado (Virtual/TBA)"
            f.write(f"- **{m['dept']}{m['num']}** ({m['nrc']}): {status} [Periodo: {m['p']}]\n")
        
        for nrc in no_encontrados:
            f.write(f"- **NRC {nrc}**: ❌ No se encontró en ningún periodo (2025/2026).\n")

    # GENERAR HTML (Web)
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Horario</title>
    <style>body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
    .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }}
    table {{ width: 100%; border-collapse: collapse; }} th {{ background: #1a1a1a; color: white; padding: 10px; }}
    td {{ border: 1px solid #ddd; height: 50px; text-align: center; vertical-align: top; padding: 4px; }}
    .event {{ border-radius: 4px; padding: 3px; color: white; font-size: 10px; font-weight: bold; margin-bottom: 2px; }}
    </style></head
