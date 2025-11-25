
import os
import requests
from bs4 import BeautifulSoup
import re
import json
import sqlite3
from datetime import datetime
import csv

import key     # credenciales de moodle
from key import BASE_URL

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

            cursor.execute("SELECT id,nombre,url FROM cursos where sync=True")
            cursos_synced= cursor.fetchall()            
            
            for curso in cursos_synced:
                curso_id=curso[0]
                curso_name=curso[1]
                accesos_por_aula = cursor.execute("SELECT id,usuario,aula,info FROM accesos WHERE aula="+str(curso_id)).fetchall()
                if (len(accesos_por_aula)==0):
                    cursos_vacios.append(curso)
                elif (aula_abandonada(accesos_por_aula)):                    
                    curso = curso + (len(accesos_por_aula), nombre_participantes(accesos_por_aula), dias_acceso_mas_reciente(accesos_por_aula))
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

    export_courses(cursos_vacios,cursos_casi_vacios)



def dias_acceso_mas_reciente(accesos):
    """
    Esta función retorna el número de días cuando se produjo el acceso
    mas reciente a un aula.
    """

    reciente=1000000
    for acceso in accesos:
        info=acceso[3]
        if "nunca" in info.lower():
            reciente=10*365
        else:
            patron = r'(\d+)\s*años?\s+(\d+)\s*días?'
            m = re.search(patron, info, re.IGNORECASE)
            if m:
                años = int(m.group(1))
                dias = int(m.group(2))
                tiempo = años * 365 + dias
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

    ## Condición 2: Todos los accesos son desde hace dos años o mas
    cond2=True
    for acceso in accesos:
        info=acceso[3]
        if "nunca" in info.lower():
            cond2=cond2 and True 
        else:
            patron = r'(\d+)\s*año?'
            m = re.search(patron, info, re.IGNORECASE)    
            if m:
                años = int(m.group(1))
                if (años >=2):
                    cond2=cond2 and True
                else:
                    cond2=cond2 and False

    return cond1 and cond2



def export_courses(vacias, casi_vacias):
    
    with open("aulas_vacias.csv", "w", encoding='utf-8') as vaciasfile:
        vaciasfile.write("ID;NOMBRE;URL\n")
        for a in vacias:
            vaciasfile.write(";".join(str(i) for i in a)+"\n")
        
    vaciasfile.close()

    with open("aulas_casi_vacias.csv", "w", encoding='utf-8') as casivaciasfile:
        casivaciasfile.write("ID;NOMBRE;URL;Nº PARTICIPANTES;LISTA PARTICIPANTES;ACCESO MÁS RECIENTE;\n")
        for a in casi_vacias:
            casivaciasfile.write(";".join(str(i) for i in a)+"\n")
        
    casivaciasfile.close()
        

    
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


