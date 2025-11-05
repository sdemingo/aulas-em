#!/usr/bin/python3


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


def sync_users_from_course(sesion, aula_id):
    '''
    Sincroniza los profesores de un aula 
    '''

    curso_url = f"{BASE_URL}/user/index.php?page=0&perpage=50&contextid=0&id="+str(aula_id)
    curso_page = sesion.get(curso_url)
    curso_soup = BeautifulSoup(curso_page.text, "html.parser")
    table = curso_soup.find("table",{"id":"participants"})
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    usuarios=[]
    accesos=[]

    if table:
        filas = table.find_all("tr")
        for i, fila in enumerate(filas, start=1):
            celdas = fila.find_all(["td", "th"])  # captura tanto encabezados como celdas
            valores = [celda.get_text(strip=True) for celda in celdas]
            usuarios.append({"id":valores[2],"nombre":valores[1],"rol":valores[3]})
            accesos.append({"id_usuario":valores[2],"id_aula":aula_id,"tiempo":valores[5]})

    for usuario in usuarios:
        cursor.execute("""
        INSERT OR REPLACE INTO usuarios (id, nombre, rol)
        VALUES (:id, :nombre, :rol)
        """, usuario)

    print (f"Sincronizando {len(accesos)} accesos al aula {aula_id}  ... ",end="")
    for acceso in accesos:
        cursor.execute("""
        INSERT OR REPLACE INTO accesos (id_usuario, id_aula, tiempo)
        VALUES (:id_usuario, :id_aula, :tiempo)
        """, acceso)

    print ("[OK]")
    conn.commit()
    conn.close()



def sync_courses_from_category(sesion, cid):
    '''
    Extrae todas las aulas (visibles o no) de una categoria
    '''

    url = f"{BASE_URL}/course/index.php?categoryid="+str(cid)
    page = session.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    aulas = []
    for li in soup.select("div.coursename > a"):
        nombre = li.text.strip()
        enlace = li["href"]
        match = re.search(r"id=(\d+)", enlace)
        if match:
            course_id = int(match.group(1))
        aulas.append({"nombre": nombre, "url": enlace, "id":course_id, "categoria":cid})

    print (f"Sincronizando {len(aulas)} aulas de la categoria {cid}  ... ",end="")
    for aula in aulas:
        cursor.execute("""
        INSERT OR REPLACE INTO cursos (id, nombre, url, categoria, sync)
        VALUES (:id, :nombre, :url, :categoria, False)
        """, aula)

    conn.commit()
    conn.close()
    print ("[OK]")



    


def sync_categories(sesion):
    '''
    Extrae todas las categorias del aula virtual
    y las introduce en la base de datos
    '''    
    page = sesion.get(f"{BASE_URL}/course/index.php")
    soup = BeautifulSoup(page.text, "html.parser")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    categorias = []
    select = soup.find("select")
    if select:
        for option in select.find_all("option"):
            url = option.get("value", "").strip()
            texto = option.text.strip()
            match = re.search(r"id=(\d+)", url)
            cat_id=-1
            if match:
                cat_id = int(match.group(1))

            categorias.append({"nombre": texto, "url": url,"id":cat_id})

    print (f"Sincronizando {len(categorias)} categorias  ... ",end="")
    for cat in categorias:
        cursor.execute("""
        INSERT OR REPLACE INTO categorias (id, nombre, url, sync)
        VALUES (:id, :nombre, :url, False)
        """, cat)

    conn.commit()
    conn.close()
    print ("[OK]")



def open_registry():
    """
    Abre un registro en la tabla registros indicando cuando ha comenzado
    una sincronización
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    fecha=datetime.today().strftime(DATE_LAYOUT)
    cursor.execute("""
    INSERT INTO registros (inicio, fin, aulas_sync, categorias_sync)
    VALUES (?, ?, ?, ?)
    """, (fecha, "-", 0, 0))

    conn.commit()
    conn.close()    
    return cursor.lastrowid



def close_registry(r_id, aulas_sync, categorias_sync):
    """
    Cierra un registro en la base de datos indicando cuando ha
    finalizado una sincronización y cuantas aulas y categorias
    se han sincronizado con éxito.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    fecha=datetime.today().strftime(DATE_LAYOUT)
    cursor.execute("""
    UPDATE registros
    SET fin = ?, aulas_sync = ?, categorias_sync = ?
    WHERE id = ?
    """, (fecha, aulas_sync, categorias_sync, r_id))

    conn.commit()
    conn.close()    



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
#    print ("Inicializando la base de datos ... ",end="")

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
    inicio TEXT NOT NULL,
    fin TEXT,
    aulas_sync INTEGER,
    categorias_sync INTEGER
    )
    """)
    

    conn.commit()
    conn.close()

#    print ("[OK]")

