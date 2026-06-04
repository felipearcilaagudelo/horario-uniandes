import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODOS = ["202618", "202619", "202620"] 
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
    detalles = []

    for idx, nrc in enumerate(nrcs):
        c = buscar_nrc(nrc)
        if not c: continue

        info = {
            'dept': c.get('class', '???'),
            'num': c.get('course', '???'),
            'titulo': (c.get('title') or "Materia").title(),
            'nrc': nrc,
            'color': COLORES[idx % len(COLORES)],
            'p': c.get('p_enc')
        }
        detalles.append(info)

        for s in c.get('schedules', []):
            t_ini, t_fin = s.get('time_ini'), s.get('time_fin')
            if t_ini and t_fin:
                h_ini, h_fin = int(t_ini[:2]), int(t_fin[:2])
                for dia_key, col_idx in DIAS_API.items():
                    if s.get(dia_key):
                        for h in range(h_ini, h_fin + 1):
                            if 7 <= h <= 21:
                                horario_grid[h][col_idx].append(info)

    # --- GENERAR README.md ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\nActualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d_idx in range(6):
                clases = horario_grid[h][d_idx]
                # Aquí corregimos el error: convertimos la lista de materias en un string
                txt = "<br>".join([f"**{m['dept']}**" for m in clases]) if clases else " "
                fila.append(txt)
            f.write("| " + " | ".join(fila) + " |\n")

    # --- GENERAR index.html (Página Web) ---
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Mi Horario</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #1a1a1a; color: white; padding: 10px; }}
        td {{ border: 1px solid #ddd; height: 50px; text-align: center; vertical-align: top; padding: 4px; width: 14%; }}
        .event {{ border-radius: 4px; padding: 3px; color: white; font-size: 10px; font-weight: bold; margin-bottom: 2px; }}
    </style></head>
    <body><div class="card">
        <h2 style="text-align:center">🗓️ Mi Horario</h2>
        <table><thead><tr><th>Hora</th><th>L</th><th>M</th><th>W</th><th>J</th><th>V</th><th>S</th></tr></thead><tbody>"""
    for h in range(7, 22):
        html += f"<tr><td style='background:#eee; font-weight:bold'>{h}:00</td>"
        for d_idx in range(6):
            html += "<td>"
            for m in horario_grid[h][d_idx]:
                html += f"<div class='event' style='background:{m['color']}'>{m['dept']}{m['num']}</div>"
            html += "</td>"
        html += "</tr>"
    html += "</tbody></table></div></body></html>"
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    generar()
