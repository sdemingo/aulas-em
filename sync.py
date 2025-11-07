
from db import *

import os
import time
import random

wait_times=0

def wait():
    """
    Algoritmo de espera artificial para evitar sobrecargar el servidor.
    Se esperará siempre entre 4 y 8 segundos. Un 25% de las veces además 
    se doblará esta cantidad de tiempo

    """
    wait_times=+1

    sleep_time=random.randint(4,8)
    delta=random.randint(1,5)
    if (delta == 4):
        sleep_time=sleep_time*2

    if ((wait_time % 7) == 0):
        sleep_time = sleep_time + 30

    print (f"\t ..........[esperando {sleep_time} segundos] ..........")
    time.sleep(sleep_time)


def sync_users_courses(session):
    """
    Sincroniza los accesos y los participantes a todas las aulas
    de una categoria.
    """

    mensaje=""" 
    Se van a sincronizar todos los participantes y accesos de todas las
    aulas indexadas en cada categoría. 

    Se tomará el índice de aulas de una categoría y se sincronizará 
    la lista de participantes de cada una de estas aulas. Es recomendable
    haber sincronizado y actualizado antes el índice de aulas de todas
    las categorías.

    """

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, categoria, nombre, url, sync FROM cursos where sync=False")
    cursos_sin_sync= cursor.fetchall()

    cursor.execute("SELECT id, categoria, nombre, url, sync FROM cursos")
    cursos_all= cursor.fetchall()

    os.system("clear")
    print (mensaje)
    print()
    print()
    print (f"Se han encontrado {len(cat_sin_sync)} cursos sin sincronizar de un total de {len(cat_all)}")
    while (True):
        print (f"Indique si desea sincronizar todos o solo los que están pendientes")
        print ()
        print ("1 - Sincroniza solo los pendientes")
        print ("2 - Sincroniza todos los cursos")
        print ()
        opcion = input("Elige una opción: ")
        if (opcion == "1") or (opcion == "2"):
            break


    cursos=[]
    print ("___________________________________________________________________\n")
    if (opcion == "1"):
        print ("Sincronizando los cursos pendientes")
        cursos=cursos_sin_sync
    else:
        print ("Sincronizando todos los cursos")
        cursos=cursos_all

    print()
    log(conn, f"Inicio de la sincronización de {len(cursos)} cursos y de sus participantes")
    
    synced=0
    for curso in cursos:
        try:
            print (f"Sincronizando curso {synced}/{len(categorias)} ...")
            sync_users_from_course(conn,session,curso[0])
            synced = synced+1
            wait()
        except KeyboardInterrupt:
            log(conn, f"El proceso de sincronización de los cursos se ha interrumpido. Se han sincronizado {synced} cursos")
            print (f"AVISO: El proceso de sincronzación se ha interrumpido!")
            break
        
    conn.close()
    







def sync_list_courses_one_category(session):
    """
    Esta función pide el id de una categoría y llama a 
    sync_courses_from_category pasándole ese id
    """
    mensaje="""
    Se van a sincronizar todos los cursos de una sola categoria. 

    Sincronizar cursos implica únicamente listar los cursos que se
    encuentran en cada categoría e indexar su nombre, su identificador
    y su URL.  """

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cat_id = input("Indique el ID de la categoría que quiere sincronizar: ")

    print()
    error=False
    try:
        print (f"Sincronizando categoria {cat_id} ... ")
        sync_courses_from_category(conn, session,cat_id)
    except KeyboardInterrupt:
        print (f"AVISO: El proceso de sincronzación se ha interrumpido!")
        error=True

    conn.commit()
    conn.close()
    

def sync_list_courses(session):
    """
    Esta función recorre la tabla de categorias y va llamando a sync_courses_from_category
    para descargar el índice de cursos de todas las categorias.
    """

    mensaje="""
    Se van a sincronizar todos los cursos de cada categoria. 

    Sincronizar cursos implica únicamente listar los cursos que se
    encuentran en cada categoría e indexar su nombre, su identificador
    y su URL.  """

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre, url, sync FROM categorias where sync=False")
    cat_sin_sync= cursor.fetchall()

    cursor.execute("SELECT id, nombre, url, sync FROM categorias")
    cat_all= cursor.fetchall()

    os.system("clear")
    print (mensaje)
    print()
    print()
    print (f"Se han encontrado {len(cat_sin_sync)} categorias sin sincronizar de un total de {len(cat_all)}")
    while (True):
        print (f"Indique si desea sincronizar todas o solo las que están pendientes")
        print ()
        print ("1 - Sincroniza solo las pendientes")
        print ("2 - Sincroniza todas las categorias")
        print ()
        opcion = input("Elige una opción: ")
        if (opcion == "1") or (opcion == "2"):
            break

    categorias=[]
    print ("___________________________________________________________________\n")
    if (opcion == "1"):
        print ("Sincronizando las categorias pendientes")
        categorias=cat_sin_sync
    else:
        print ("Sincronizando todas las categorias")
        categorias=cat_all


    print()
    log(conn, f"Inicio de la sincronización de {len(categorias)} categorias y los índices de aulas que contienen")
    
    synced=0
    for categoria in categorias:
        try:
            print (f"Sincronizando categorias {synced}/{len(categorias)} ...")
            sync_courses_from_category(conn, session, categoria[0])
            synced = synced+1
            wait()
        except KeyboardInterrupt:
            log(conn, f"El proceso de sincronización de los índices de categorias se ha interrumpido. Se han sincronizado {synced} categorias")
            print (f"AVISO: El proceso de sincronzación se ha interrumpido!")
            break
        
    conn.close()


def sync_users_from_course(conn, sesion, aula_id):
    """
    Esta función descarga los participantes de un curso concreto
    indicado en aula_id. La información irá a parar a la tabla "usuarios"
    y a la tabla "accesos" donde se incluyen los últimos accesos de cada usuario
    a ese aula
    """

    curso_url = f"{BASE_URL}/user/index.php?page=0&perpage=50&contextid=0&id="+str(aula_id)
    curso_page = sesion.get(curso_url)
    curso_soup = BeautifulSoup(curso_page.text, "html.parser")
    table = curso_soup.find("table",{"id":"participants"})

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

    print (f"Sincronizando {len(accesos)} accesos al aula {aula_id}  ... ")
    for acceso in accesos:
        cursor.execute("""
        INSERT OR REPLACE INTO accesos (id_usuario, id_aula, tiempo)
        VALUES (:id_usuario, :id_aula, :tiempo)
        """, acceso)

    log(conn, f"Se sincronizan los usuarios y accesos del aula {aula_id}")

    conn.commit()




def sync_courses_from_category(conn, session, cid):
    """
    Esta función descarga la lista de cursos de una categoria
    y los introduce en la tabla "cursos". Aunque un curso esté oculto
    en una categoría también lo listará y lo añadirá
    """

    url = f"{BASE_URL}/course/index.php?categoryid="+str(cid)
    page = session.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    # conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    aulas = []
    for li in soup.select("div.coursename > a"):
        nombre = li.text.strip()
        enlace = li["href"]
        match = re.search(r"id=(\d+)", enlace)
        if match:
            course_id = int(match.group(1))
        aulas.append({"nombre": nombre, "url": enlace, "id":course_id, "categoria":cid})

    print (f"Sincronizando {len(aulas)} aulas de la categoria {cid}  ... ")
    for aula in aulas:
        cursor.execute("""
        INSERT OR REPLACE INTO cursos (id, nombre, url, categoria, sync)
        VALUES (:id, :nombre, :url, :categoria, False)
        """, aula)

    # Actualizo la categoria como sincronizada
    cursor.execute("""
    UPDATE categorias
    SET sync = ?
    WHERE id = ?;
    """, (True, cid))

    log(conn, f"Se sincroniza el índice de la categoria {cid}. Se han importado {len(aulas)} nombres de aulas")

    conn.commit()
    #conn.close()




def sync_categories(sesion):
    """
    Esta función extrae del Moodle la lista de categorias
    creadas por el administrador y las guarda en la tabla
    "categorias"
    """

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

    print (f"Sincronizando {len(categorias)} categorias  ... ")
    for cat in categorias:
        cursor.execute("""
        INSERT OR REPLACE INTO categorias (id, nombre, url, sync)
        VALUES (:id, :nombre, :url, False)
        """, cat)

    log(conn, f"Se sincronizan {len(categorias)} nombres de categorias")


    conn.commit()
    conn.close()

    
