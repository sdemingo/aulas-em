
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
    #conn.close()    


def export_logs():
    
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
    id_usuario TEXT,
    id_aula INTEGER,
    tiempo TEXT NOT NULL,
    PRIMARY KEY (id_usuario,id_aula)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    nombre TEXT,
    rol TEXT NOT NULL
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


