
import os
import requests
from bs4 import BeautifulSoup
import re
import json
import sqlite3
from datetime import datetime
import csv
import unicodedata
import key     # credenciales de moodle
from key import BASE_URL

import report


DATE_LAYOUT='%d/%m/%Y %H:%M'
DATABASE="moodle.db"
LOG_FILE="/tmp/sync.log"



def db_stats():
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    n_registros=0
    n_cursos_sync=0
    n_cursos=0
    n_categorias=0
    n_categorias_sync=0

    cursos_casi_vacios=[]
    cursos_vacios=[]
    profesores_claustro={}

    try:
            cursor.execute("SELECT COUNT(*) FROM registros")
            n_registros=cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cursos where sync=True")
            n_cursos_sync= cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cursos")
            n_cursos= cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM categorias")
            n_categorias= cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM categorias where sync=True")
            n_categorias_sync= cursor.fetchone()[0]

            cursor.execute("SELECT id,nombre FROM cursos where sync=True")
            cursos_synced= cursor.fetchall()

            cursor.execute("SELECT id,nombre,apellidos FROM claustro")
            claustro=cursor.fetchall()

            for profesor in claustro:
                nombre_completo=profesor[1]+profesor[2]
                nombre_saneado = sanea_nombre(nombre_completo)
                profesores_claustro[nombre_saneado]=nombre_completo


            for curso in cursos_synced:
                curso_id=curso[0]
                curso_name=curso[1]
                accesos_por_aula = cursor.execute("SELECT id,usuario,aula,info FROM accesos WHERE aula="+str(curso_id)).fetchall()
                if (len(accesos_por_aula)==0):
                    cursos_vacios.append(curso)
                elif (aula_abandonada(accesos_por_aula)):          
                    participantes=nombre_participantes(accesos_por_aula)
                    fuera=participantes_fuera_de_claustro(participantes, profesores_claustro)
                    curso = curso + (len(accesos_por_aula), participantes, dias_acceso_mas_reciente(accesos_por_aula), fuera)
                    cursos_casi_vacios.append(curso)
            
    except Exception as ex:
        print (ex)


    print()
    print()
    print(f"\t * Número de categorias indexadas: {n_categorias}")
    print(f"\t * Número de categorias cuyos índices de aulas se han descargado: {n_categorias_sync}")
    print()
    print(f"\t * Número aulas virtuales indexadas: {n_cursos}")
    print(f"\t * Número aulas virtuales con usuarios y accesos sincronizados: {n_cursos_sync}")
    print()
    print(f"\t * Número aulas virtuales abandonadas: {len(cursos_casi_vacios)}")
    print(f"\t * Número aulas virtuales totalmente vacías: {len(cursos_vacios)}")
    print()
    print(f"\t * Número de registros almacenados en eventos: {n_registros}")

    report.generate_report(cursos_vacios,cursos_casi_vacios)


def participantes_fuera_de_claustro(participantes, claustro):
    """
    Esta función retorna True si todos los participantes de un aula no pertenecen al claustro
    """
    
    part=participantes.split(",")
    for nombre in part:
        if sanea_nombre(nombre) in claustro:
            return "No"
    
    return "Si"


def sanea_nombre(nombre):
    """
    Dado un nombre de profesor lo sanea eliminando tildes, espacios, puntos, guiones etc.
    """
    if not nombre:
        return ""

    nombre = nombre.lower()

    # Quitar tildes/acentos
    nombre = ''.join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    )

    nombre = re.sub(r'[\s\.\,\-_/]+', '', nombre)
    nombre = re.sub(r'[^a-z0-9]', '', nombre)

    return nombre



def dias_acceso_mas_reciente(accesos):
    """
    Esta función retorna el número de días cuando se produjo el acceso
    mas reciente a un aula.
    """

    reciente=1000000
    for acceso in accesos:
        info=acceso[3]
        if "nunca" in info.lower():
            reciente=1000000
        elif ("horas" in info.lower()) and ("minutos" in info.lower()):
            reciente=1
        else: 
            tiempo=reciente
            # 1) Caso con años y días
            patron_completo = r'(\d+)\s*años?\s+(\d+)\s*días?'
            m = re.search(patron_completo, info, re.IGNORECASE)
            if m:
                años = int(m.group(1))
                dias = int(m.group(2))
                tiempo = años * 365 + dias

            # 2) Caso solo días — PERO evitando que capture algo que ya pertenece al patrón anterior
            patron_solo_dias = r'(\d+)\s*días?'
            m = re.search(patron_solo_dias, info, re.IGNORECASE)
            if m:
                dias = int(m.group(1))

                # Verificamos si este "X días" NO viene de un patrón de "años Y días"
                texto_antes = info[:m.start()]
                if not re.search(r'\d+\s*años?\s*$', texto_antes, re.IGNORECASE):
                    tiempo =  dias


            if (tiempo < reciente):
                reciente = tiempo

    return reciente


def nombre_participantes(accesos):
    """
    Esta función retorna el nombre de los participantes
    en los accesos de un aula en forma de string
    """
    lista=[]
    for acceso in accesos:
        lista.append(acceso[1])

    return ", ".join(lista)




def aula_abandonada(accesos):
    """
    Recibe la lista de accesos de un aula y comprueba los criterios para considerarla abandonada
    Ver criterios en los comentarios de cada condición.
    """
    
    ## Condición 1: Que tenga menos de tres accesos o participantes
    cond1 = (len(accesos) <= 3)

    ## Condición 2: El acceso mas recientes es de hace más de dos años
    if (dias_acceso_mas_reciente(accesos) > 2*365):
        cond2=True
    else:
        cond2=False

    return cond1 and cond2



    
def log(conn, texto):
    """
    Crea un apunte en la tabla de registros
    """
    
    #conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    fecha=datetime.today().strftime(DATE_LAYOUT)
    cursor.execute("""
    INSERT INTO registros (fecha, texto)
    VALUES (?, ?)
    """, (fecha, texto))

    conn.commit()


def export_logs():
    """
    Esta función exporta los eventos a un fichero de texto
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT fecha,texto FROM registros")
    logs = cursor.fetchall()

    with open(LOG_FILE, "w+", encoding='utf-8') as logfile:
        for l in logs:
            logfile.write(l[0]+"\t"+l[1]+"\n")
        
    logfile.close()

    os.system("less "+LOG_FILE)




def load_users():
    """
    Carga profesores del claustro a partir de un csv
    con, al menos, tres columnas [educa_id; Nombre; Apellidos ]
    """
    mensaje=""" 
    Se procederá a cargar los usuarios del claustro a partir de un
    fichero CSV externo. Este fichero ha de estar formateado a, como
    mínimo tres columnas. De tal forma que la primera de ella incluya
    el usuario de Educamadrid del profesor y la segunda su nombre y la
    tercera sus apellidos.

    Si desea proceder a la carga escriba a continuación la ruta
    completa del fichero CSV.
    """
    print (mensaje)
    ruta = input("Ruta del fichero: ")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print ("___________________________________________________________________\n")
    
    with open(ruta, newline='', encoding='utf-8') as archivo_csv:
        lector_csv = csv.reader(archivo_csv, delimiter=',', quotechar='"')
        nfila=1
        cargados=0
        for fila in lector_csv:
            if len(fila)<3:
                print (f"Fila {nfila} con mal formato")
            else:
                cursor.execute("""
                INSERT OR REPLACE INTO claustro (id, nombre, apellidos)
                VALUES (?, ?, ?)
                """, (fila[0], fila[1], fila[2]))

                cargados+=1
            nfila+=1

    print (f"Se han cargado {cargados} profesores del claustro en la base de datos")
    conn.commit()
    conn.close()
                
        




def sync_reset():
    
    mensaje=""" 
    Se va a eliminar toda la base de datos. Tras esto, el proceso de
    sincronización debe de comenzar desde cero.

    Confirme el borrado de la base de datos.

    """
    print (mensaje)
    while (True):
        opcion = input("¿Desea borrar la base de datos por completo?[S/N]: ")
        if (opcion == "s") or (opcion == "n") or (opción == "S") or (opcion=="N"):
            break

    print ("___________________________________________________________________\n")
    if (opcion == "s") or (opcion == "S"):
        os.remove(DATABASE)
        print ("Se ha eliminado toda la base de datos")
    
    


def init_session():
    session = requests.Session()
    login_page = session.get(f"{BASE_URL}/login/index.php")
    soup = BeautifulSoup(login_page.text, "html.parser")
    token = soup.find("input", {"name": "logintoken"})["value"]
    key.CREDENTIALS["logintoken"]=token
    resp = session.post(f"{BASE_URL}/login/index.php", data=key.CREDENTIALS)
    return session




def init_db():
#    print ("Inicializando la base de datos ... ")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    url TEXT,
    sync BOOLEAN
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY,
    categoria INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    url TEXT,
    sync BOOLEAN
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accesos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    aula INTEGER,
    info TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claustro (
    id TEXT PRIMARY KEY,
    nombre TEXT,
    apellidos TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    texto TEXT
    )
    """)
    

    conn.commit()
    conn.close()


