import requests
import datetime
import time
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODOS = ["202620", "202619", "202618", "202520"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]

def buscar_nrc(nrc):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://ofertadecursos.uniandes.edu.co/'
    }
    
    for p in PERIODOS:
        # URL Exacta del buscador oficial
        url = f"https://ofertadecursos.uniandes.edu.co/#"
        try:
            time.sleep(1) # Delay para evitar bloqueos
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                cursos = data if isinstance(data, list) else data.get('courses', [])
                for c in cursos:
                    if str(c.get('nrc')).strip() == str(nrc).strip():
                        c['periodo_encontrado'] = p
                        return c
        except Exception as e:
            print(f"Error en NRC {nrc} periodo {p}: {e}")
    return None

def generar():
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            nrcs = [line.strip() for line in f if line.strip()]
    except: return

    horario_grid = defaultdict(lambda: defaultdict(list))
    detalles = []

    for idx, nrc in enumerate(nrcs):
        print(f"Procesando NRC {nrc}...")
        c = buscar_nrc(nrc)
        if not c: continue

        # Extraer nombres (Uniandes a veces los manda como null si la petición es externa)
        dept = c.get('class') or "MAT"
        num = c.get('course') or ""
        titulo = c.get('title') or "Materia Seleccionada"
        color = COLORES[idx % len(COLORES)]
        
        info = {'dept': dept, 'num': num, 'titulo': titulo, 'nrc': nrc, 'color': color, 'p': c.get('periodo_encontrado')}
        detalles.append(info)

        # Procesar horarios (Formato l, m, i, j, v, s)
        schs = c.get('schedules', [])
        for s in schs:
            t_ini = str(s.get('time_ini', ''))
            t_fin = str(s.get('time_fin', ''))
            
            if len(t_ini) >= 3 and len(t_fin) >= 3:
                try:
                    # Extraer hora (ej: 0930 -> 09, 1800 -> 18)
                    h_ini = int(t_ini[:-2])
                    h_fin = int(t_fin[:-2])
                    
                    for dia_key, col_idx in DIAS_API.items():
                        if s.get(dia_key):
                            for h in range(h_ini, h_fin + 1):
                                if 7 <= h <= 21:
                                    horario_grid[h][col_idx].append(info)
                except: continue

    # --- ESCRIBIR README.md ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\nActualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d in range(6):
                clases = horario_grid[h][d]
                # Convertimos a texto para el README
                txt = "<br>".join([f"**{m['dept']}**" for m in clases]) if clases else " "
                fila.append(txt)
            f.write("| " + " | ".join(fila) + " |\n")
        
        if not detalles:
            f.write("\n⚠️ No se encontraron los NRCs. Verifica el archivo mis_clases.txt.")

    # --- GENERAR index.html (Pagina Web) ---
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
        body {{ font-family: sans-serif; background: #f4f4f9; padding: 20px; }}
        .card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 1000px; margin: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #2c3e50; color: white; padding: 12px; }}
        td {{ border: 1px solid #eee; height: 65px; vertical-align: top; padding: 5px; width: 14%; text-align: center; }}
        .event {{ border-radius: 6px; padding: 6px; color: white; font-size: 11px; font-weight: bold; margin-bottom: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
        .time {{ background: #f8f9fa; font-weight: bold; width: 70px; color: #7f8c8d; }}
    </style></head>
    <body><div class="card">
    <h1 style="text-align:center; color:#2c3e50;">🗓️ Mi Horario Profesional</h1>
    <table><thead><tr><th>Hora</th><th>L</th><th>M</th><th>W</th><th>J</th><th>V</th><th>S</th></tr></thead><tbody>"""
    
    for h in range(7, 22):
        html += f"<tr><td class='time'>{h}:00</td>"
        for d_idx in range(6):
            html += "<td>"
            for m in horario_grid[h][d_idx]:
                html += f"<div class='event' style='background:{m['color']}'>{m['dept']}{m['num']}<br>{m['nrc']}</div>"
            html += "</td>"
        html += "</tr>"
    
    html += "</tbody></table></div></body></html>"
    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generar()
