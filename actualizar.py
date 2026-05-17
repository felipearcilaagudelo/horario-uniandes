import requests
import datetime
from collections import defaultdict

# --- CONFIGURACIÓN ---
PERIODO = "202618" # Cambia esto cada semestre
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"
# ---------------------

def buscar_datos(query):
    url = f"https://ofertadecursos.uniandes.edu.co/api/courses?term={PERIODO}&p_numb={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        return data if isinstance(data, list) else data.get('courses', [])
    except Exception as e:
        print(f"Error buscando {query}: {e}")
        return []

def generar_reporte():
    try:
        with open(ARCHIVO_LISTA, "r") as f:
            busquedas = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        busquedas = []

    materias_agrupadas = defaultdict(list)
    for item in busquedas:
        print(f"Buscando: {item}...")
        resultados = buscar_datos(item)
        for curso in resultados:
            nombre = f"{curso.get('class')} - {curso.get('course_title')}"
            materias_agrupadas[nombre].append(curso)

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🛰️ Monitor de Oferta Uniandes\n")
        f.write(f"Actualizado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} (Hora servidor)\n\n")
        f.write("Pulsa en cada materia para ver sus secciones y cupos:\n\n")
        
        if not materias_agrupadas:
            f.write("⚠️ No se encontraron materias. Revisa tu archivo mis_clases.txt")
        
        for nombre_materia, secciones in materias_agrupadas.items():
            f.write(f"<details>\n<summary><b>{nombre_materia} ({len(secciones)} secciones)</b></summary>\n\n")
            f.write("| Sec | NRC | Horario | Salón | Profesor | Cupos |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            for s in secciones:
                nrc = s.get('nrc', 'N/A')
                sec = s.get('section', 'N/A')
                profe = s.get('instructor', 'Por asignar')
                cupos_max = int(s.get('max_enrol', 0))
                cupos_act = int(s.get('enrolled', 0))
                disp = cupos_max - cupos_act
                
                status = "🟢" if disp > 0 else "🔴"
                h_list = [f"{h.get('day')}: {h.get('time')}" for h in s.get('schedules', [])]
                l_list = [h.get('location', 'N/A') for h in s.get('schedules', [])]
                
                f.write(f"| {sec} | {nrc} | {'<br>'.join(h_list)} | {'<br>'.join(l_list)} | {profe} | {status} {disp}/{cupos_max} |\n")
            f.write("\n</details>\n\n")

if __name__ == "__main__":
    generar_reporte()
