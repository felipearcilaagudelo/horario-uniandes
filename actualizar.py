import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
# Estos son los periodos donde buscaremos cada NRC
PERIODOS = ["202620", "202619", "202618"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

# Mapeo de días basado en tu respuesta del diagnóstico
MAPA_DIAS = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]

def buscar_nrc(nrc):
    # Volvemos a la URL simple que funcionó en el diagnóstico
    headers = {'User-Agent': 'Mozilla/5.0'}
    for p in PERIODOS:
        url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={p}&p_numb={nrc}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                cursos = data if isinstance(data, list) else data.get('courses', [])
                for c in cursos:
                    if str(c.get('nrc')).strip() == str(nrc).strip():
                        c['p_enc'] = p # Guardamos el periodo
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

    for idx, nrc in enumerate(nrcs):
        print(f"Buscando NRC {nrc}...")
        c = buscar_nrc(nrc)
        if not c: continue

        # USAMOS LAS LLAVES QUE SALIERON EN TU DIAGNÓSTICO: class, course, title
        info = {
            'dept': c.get('class', '???'),
            'num': c.get('course', '???'),
            'titulo': (c.get('title') or "Materia").title(),
            'nrc': nrc,
            'color': COLORES[idx % len(COLORES)],
            'p': c.get('p_enc')
        }
        encontrados.append(info)

        # PROCESAR HORARIOS (basado en l, m, i, j, v, s del diagnóstico)
        schedules = c.get('schedules', [])
        for s in schedules:
            t_ini, t_fin = s.get('time_ini'), s.get('time_fin')
            if t_ini and t_fin:
                try:
                    h_ini = int(t_ini[:2])
                    h_fin = int(t_fin[:2])
                    # Revisamos cada columna de día que nos mostró el diagnóstico
                    for dia_key, col_idx in MAPA_DIAS.items():
                        if s.get(dia_key): # Si el valor no es null
                            for h in range(h_ini, h_fin + 1):
                                if 7 <= h <= 21:
                                    horario_grid[h][col_idx].append(info)
                except: continue

    # --- GENERAR README ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\nActualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d in range(6):
                clases = horario_grid[h][d]
                # Corregimos el error de "list found" convirtiendo a texto
                nombres = [f"**{m['dept']}**" for m in clases]
                fila.append("<br>".join(nombres) if nombres else " ")
            f.write("| " + " | ".join(fila) + " |\n")
        
        if not encontrados:
            f.write("\n⚠️ No se cargaron materias. Revisa si los NRCs en `mis_clases.txt` son correctos para 2026.")

    # --- GENERAR HTML ---
    html = f"<html><body style='font-family:sans-serif; padding:30px; background:#f4f4f9;'><div style='background:white; padding:20px; border-radius:10px; max-width:900px; margin:auto; box-shadow: 0 5px 15px rgba(0,0,0,0.1);'>"
    html += f"<h1 style='text-align:center'>🗓️ Mi Horario Profesional</h1>"
    html += "<table border='1' style='width:100%; border-collapse:collapse;'><thead><tr style='background:#2c3e50; color:white;'><th>Hora</th><th>L</th><th>M</th><th>W</th><th>J</th><th>V</th><th>S</th></tr></thead>"
    for h in range(7, 22):
        html += f"<tr><td style='background:#eee; text-align:center; font-weight:bold; width:70px;'>{h}:00</td>"
        for d_idx in range(6):
            html += "<td style='vertical-align:top; height:60px; padding:4px;'>"
            for m in horario_grid[h][d_idx]:
                html += f"<div style='background:{m['color']}; color:white; padding:4px; border-radius:4px; font-size:11px; margin-bottom:2px; font-weight:bold;'>{m['dept']}{m['num']}<br>{m['nrc']}</div>"
            html += "</td>"
        html += "</tr>"
    html += "</table></div></body></html>"
    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generar()
