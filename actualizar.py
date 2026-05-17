import requests
import datetime
import json

PERIODOS = ["202618", "202619"] 
ARCHIVO_LISTA = "mis_clases.txt"
README_FILE = "README.md"

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
                    return c, p
        except: continue
    return None, None

def generar():
    with open(ARCHIVO_LISTA, "r") as f:
        nrcs = [line.strip() for line in f if line.strip()]

    output = "# 🛠️ Diagnóstico de Horario\n\n"
    
    for nrc in nrcs:
        curso, p = buscar_nrc(nrc)
        if not curso:
            output += f"### ❌ NRC {nrc}: No encontrado en {PERIODOS}\n\n"
            continue
            
        output += f"### 📦 Datos para NRC {nrc} ({p})\n"
        output += f"**Nombre:** {curso.get('class')} {curso.get('course_number')} - {curso.get('course_title')}\n\n"
        
        # Aquí está el truco: vamos a ver qué hay dentro de 'curso'
        output += "#### Etiquetas encontradas en este curso:\n"
        output += f"```json\n{json.dumps(list(curso.keys()), indent=2)}\n```\n\n"
        
        # Intentamos ver qué hay en la parte de horarios específicamente
        posibles_horarios = curso.get('schedules') or curso.get('schedule') or curso.get('meetingsFaculty') or []
        output += "#### Contenido de la sección de horario:\n"
        output += f"```json\n{json.dumps(posibles_horarios, indent=2)}\n```\n"
        output += "\n---\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(output)

if __name__ == "__main__":
    generar()
