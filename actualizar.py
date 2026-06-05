import requests
import datetime
import time
import os
from collections import defaultdict

# --- CONFIGURACIÓN ---
# Periodos: 202620 (2do Semestre), 202619 (Verano), 202618 (Vacaciones)
PERIODOS = ["202620", "202619", "202618"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
HTML_FILE = "index.html"

# Mapeo de días según el JSON de Uniandes
# l=Lunes, m=Martes, i=Miércoles, j=Jueves, v=Viernes, s=Sábado
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
        # URL exacta con el parámetro p_numb que es donde vive el NRC
        url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={p}&p_numb={nrc}"
        try:
            print(f"Buscando NRC {nrc} en periodo {p}...")
            time.sleep(1) # Pequeña espera para no ser bloqueados
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                cursos = data if isinstance(data, list) else data.get('courses', [])
                for c in cursos:
                    if str(c.get('nrc')).strip() == str(nrc).strip():
                        c['periodo_encontrado'] = p
                        return c
        except Exception as e:
            print(f"Error de red: {e}")
            continue
    return None

def generar():
    # Leer lista de NRCs
    if not os.path.exists(ARCHIVO_LISTA):
        print(f"Error: No existe el archivo {ARCHIVO_LISTA}")
        return

    with open(ARCHIVO_LISTA, "r") as f:
        nrcs = [line.strip() for line in f if line.strip()]

    horario_grid = defaultdict(lambda: defaultdict(list))
    detalles_materias = []

    for idx, nrc in enumerate(nrcs):
        curso_data = buscar_nrc(nrc)
        if not curso_data:
            print(f"⚠️ No se encontró información para el NRC: {nrc}")
            continue

        # Extraer nombres con fallback
        clase_dept = curso_data.get('class') or "UNIT"
        clase_num = curso_data.get('course') or ""
        titulo = (curso_data.get('title') or "Materia").title()
        periodo = curso_data.get('periodo_encontrado')
        color = COLORES[idx % len(COLORES)]
        
        info = {
            'nrc': nrc,
            'nombre': f"{clase_dept} {clase_num}",
            'titulo': titulo,
            'color': color,
            'periodo': periodo
        }
        detalles_materias.append(info)

        # Procesar los bloques de horario
        schedules = curso_data.get('schedules', [])
        for s in schedules:
            t_ini = s.get('time_ini')
            t_fin = s.get('time_fin')
            
            if t_ini and t_fin:
                try:
                    # Convertir 0930 a 9, 1800 a 18
                    h_ini = int(str(t_ini)[:2])
                    h_fin = int(str(t_fin)[:2])
                    
                    # Revisar cada día (l, m, i, j, v, s)
                    for dia_key, col_idx in DIAS_API.items():
                        if s.get(dia_key): # Si el campo tiene contenido (ej: 'M', 'J')
                            for h in range(h_ini, h_fin + 1):
                                if 7 <= h <= 21:
                                    horario_grid[h][col_idx].append(info)
                except Exception as e:
                    print(f"Error procesando hora para NRC {nrc}: {e}")

    # --- 1. GENERAR README.md ---
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🗓️ Mi Horario Uniandes\n")
        f.write(f"Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        f.write("| Hora | L | M | W | J | V | S |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        
        for h in range(7, 22):
            fila = [f"{h}:00"]
            for d_idx in range(6):
                materias_en_bloque = horario_grid[h][d_idx]
                if materias_en_bloque:
                    # Evitar duplicados visuales y unir con saltos de línea
                    nombres = []
                    for m in materias_en_bloque:
                        if m['nombre'] not in nombres: nombres.append(f"**{m['nombre']}**")
                    fila.append("<br>".join(nombres))
                else:
                    fila.append(" ")
            f.write("| " + " | ".join(fila) + " |\n")

        if not detalles_materias:
            f.write("\n\n⚠️ No se cargaron materias. Revisa tus NRCs o los periodos configurados.")

    # --- 2. GENERAR index.html ---
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mi Horario</title>
        <style>
            body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
            .container {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 1000px; margin: auto; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
            th {{ background: #2c3e50; color: white; padding: 12px; font-size: 0.9em; }}
            td {{ border: 1px solid #eee; height: 60px; vertical-align: top; padding: 4px; position: relative; text-align: center; }}
            .time-col {{ background: #f8f9fa; font-weight: bold; width: 70px; color: #7f8c8d; vertical-align: middle; }}
            .event {{ border-radius: 4px; padding: 5px; color: white; font-size: 0.75em; font-weight: bold; margin-bottom: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align:center; color:#2c3e50;">🗓️ Mi Horario Profesional</h1>
            <table>
                <thead><tr><th>Hora</th><th>Lun</th><th>Mar</th><th>Mié</th><th>Jue</th><th>Vie</th><th>Sáb</th></tr></thead>
                <tbody>
    """
    for h in range(7, 22):
        html_template += f"<tr><td class='time-col'>{h}:00</td>"
        for d_idx in range(6):
            html_template += "<td>"
            for m in horario_grid[h][d_idx]:
                html_template += f"<div class='event' style='background:{m['color']}'>{m['nombre']}<br>{m['nrc']}</div>"
            html_template += "</td>"
        html_template += "</tr>"
    
    html_template += """
                </tbody>
            </table>
            <div class="footer">
    """
    for d in detalles_materias:
        html_template += f"<p>● <b>{d['nombre']}</b>: {d['titulo']} (NRC: {d['nrc']} - Periodo: {d['periodo']})</p>"
    
    html_template += "</div></div></body></html>"
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generar()
