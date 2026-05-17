import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODOS = ["202618", "202619"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
DIAS_NOMBRES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]

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

    horario_grid = defaultdict(lambda: defaultdict(list))
    detalles = []

    for idx, nrc in enumerate(nrcs):
        c = buscar_nrc(nrc)
        if not c: continue

        dept = c.get('class', '???')
        num = c.get('course', '???')
        titulo = (c.get('title') or "Materia").title()
        color = COLORES[idx % len(COLORES)]
        
        materia_info = {'dept': dept, 'num': num, 'titulo': titulo, 'nrc': nrc, 'color': color}
        detalles.append(materia_info)

        for s in c.get('schedules', []):
            t_ini, t_fin = s.get('time_ini'), s.get('time_fin')
            if t_ini and t_fin:
                h_ini, h_fin = int(t_ini[:2]), int(t_fin[:2])
                for dia_key, col_idx in DIAS_API.items():
                    if s.get(dia_key):
                        for h in range(h_ini, h_fin + 1):
                            if 7 <= h <= 21:
                                horario_grid[h][col_idx].append(materia_info)

    # --- GENERAR HTML (PARA GITHUB PAGES) ---
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mi Horario Uniandes</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
    h1 {{ text-align: center; color: #1a1a1a; margin-bottom: 5px; }}
    .update {{ text-align: center; color: #666; font-size: 0.8em; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th {{ background: #1a1a1a; color: white; padding: 12px; font-size: 0.9em; }}
    td {{ border: 1px solid #e0e0e0; height: 60px; vertical-align: top; padding: 4px; position: relative; }}
    .time-col {{ background: #f8f9fa; font-weight: bold; width: 60px; text-align: center; vertical-align: middle; font-size: 0.8em; }}
    .event {{ border-radius: 4px; padding: 4px; color: white; font-size: 0.7em; font-weight: bold; margin-bottom: 2px; line-height: 1.1; }}
    .footer {{ margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
    .materia-item {{ display: inline-block; margin-right: 15px; font-size: 0.8em; }}
    .dot {{ height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }}
</style></head>
<body><div class="container">
    <h1>🗓️ Mi Horario Uniandes</h1>
    <div class="update">Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    <table><thead><tr><th style="width:70px">Hora</th><th>Lun</th><th>Mar</th><th>Mié</th><th>Jue</th><th>Vie</th><th>Sáb</th></tr></thead><tbody>"""

    for h in range(7, 22):
        html += f"<tr><td class='time-col'>{h}:00</td>"
        for d_idx in range(6):
            html += "<td>"
            for m in horario_grid[h][d_idx]:
                html += f"<div class='event' style='background:{m['color']}'>{m['dept']}{m['num']}<br>{m['nrc']}</div>"
            html += "</td>"
        html += "</tr>"

    html += """</tbody></table><div class="footer">"""
    for d in detalles:
        html += f"<div class='materia-item'><span class='dot' style='background:{d['color']}'></span><b>{d['dept']}{d['num']}</b>: {d['titulo']} ({d['nrc']})</div>"
    html += "</div></div></body></html>"

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html)

    # --- (Opcional) Mantenemos el README actualizado también ---
    # ... (Si quieres puedes poner aquí el código del README anterior para tener ambos)

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
