import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
# Ponemos el 202620 de primero que es el que te interesa ahora
PERIODOS = ["202620", "202619", "202618", "202610", "202520"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

# Mapeo de días de la API
DIAS_API = {'l': 0, 'm': 1, 'i': 2, 'j': 3, 'v': 4, 's': 5}
COLORES = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]

def buscar_nrc(nrc):
    # User-Agent y Referer para que la API nos deje entrar
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://ofertadecursos.uniandes.edu.co/'
    }
    
    for p in PERIODOS:
        # Intentamos buscar por dos parámetros diferentes: 'p_numb' y 'nrc'
        # Uniandes a veces prefiere uno u otro dependiendo del semestre
        intentos_urls = [
            f"https://ofertadecursos.uniandes.edu.co/api/courses?term={p}&p_numb={nrc}",
            f"https://ofertadecursos.uniandes.edu.co/api/courses?term={p}&nrc={nrc}"
        ]
        
        for url in intentos_urls:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200: continue
                data = r.json()
                cursos = data if isinstance(data, list) else data.get('courses', [])
                for c in cursos:
                    # Comprobación estricta del NRC
                    if str(c.get('nrc', '')).strip() == str(nrc).strip():
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
        print(f"Buscando NRC {nrc}...")
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
            if t_ini and t_fin:
                try:
                    h_ini = int(str(t_ini)[:2])
                    h_fin = int(str(t_fin)[:2])
                    info['tiene_horario'] = True
                    for dia_key, col_idx in DIAS_API.items():
                        if s.get(dia_key):
                            # Marcamos desde la hora de inicio hasta la de fin
                            for h in range(h_ini, h_fin + 1):
                                if 7 <= h <= 21:
                                    horario_grid[h][col_idx].append(info)
                except: continue
        
        encontrados.append(info)

    # --- GENERAR README.md ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\n")
        f.write(f"Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} (UTC)\n\n")
        
        f.write("| Hora | L | M | W | J | V | S |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d_idx in range(6):
                clases = horario_grid[h][d_idx]
                # Evitamos duplicados visuales en la misma celda
                nombres = list(set([f"**{m['dept']}**" for m in clases]))
                txt = "<br>".join(nombres) if nombres else " "
                fila.append(txt)
            f.write("| " + " | ".join(fila) + " |\n")

        f.write("\n---\n### 🔍 Estado de tus NRCs:\n")
        for m in encontrados:
            status = "✅ Cargado" if m['tiene_horario'] else "⚠️ Sin horario en sistema"
            f.write(f"- **{m['dept']}{m['num']}** ({m['nrc']}): {status} [Periodo: {m['p']}]\n")
        for nrc in no_encontrados:
            f.write(f"- **NRC {nrc}**: ❌ No se encontró. Verifica el número o el periodo.\n")

    # --- GENERAR index.html ---
    # (Misma lógica simplificada para la web)
    html = f"<html><head><meta charset='UTF-8'><style>body{{font-family:sans-serif;padding:20px;background:#f0f2f5}} .box{{background:white;padding:20px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);max-width:900px;margin:auto}} table{{width:100%;border-collapse:collapse}} td,th{{border:1px solid #ddd;padding:8px;text-align:center;height:50px}} .event{{background:#3498db;color:white;border-radius:4px;padding:4px;font-size:11px;font-weight:bold}}</style></head><body><div class='box'><h2>🗓️ Mi Horario</h2><table><thead><tr><th>Hora</th><th>L</th><th>M</th><th>W</th><th>J</th><th>V</th><th>S</th></tr></thead>"
    for h in range(7, 22):
        html += f"<tr><td style='background:#eee'><b>{h}:00</b></td>"
        for d_idx in range(6):
            html += "<td>"
            for m in horario_grid[h][d_idx]:
                html += f"<div class='event' style='background:{m['color']}'>{m['dept']}{m['num']}</div>"
            html += "</td>"
        html += "</tr>"
    html += "</table></div></body></html>"
    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generar()
