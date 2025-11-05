#!/usr/bin/python3

from api import *
import sys
import os
import time
import random

registro_id=0    

def sync_users_courses(session):
    '''
    Sincroniza los accesos y los participantes a todas las aulas
    de una categoria.
    '''

    mensaje=""" 
    Se van a sincronizar todos los participantes y accesos de todas las
    aulas indexadas en cada categoría. 

    Se tomará el índice de aulas de una categoría y se sincronizará 
    la lista de participantes de cada una de estas aulas. Es recomendable
    haber sincronizado y actualizado antes el índice de aulas de todas
    las categorías.

    """

    ## Sacar todas las aulas de la tabla aulas
    ## Igual que antes ver si el proceso ya comenzó anteriomente  y hay aulas
    ## que ya han sido sincronizadas y seguir a partir de ellas
    

def sync_list_courses_one_category(session):
    mensaje="""
    Se van a sincronizar todos los cursos de una sola categoria. 

    Sincronizar cursos implica únicamente listar los cursos que se
    encuentran en cada categoría e indexar su nombre, su identificador
    y su URL.  """
    
    cat_id = input("Indique el ID de la categoría que quiere sincronizar: ")

    r_id=open_registry()
    print()
    error=False
    try:
        print (f"Sincronizando categoria {cat_id} ... ", end="")
        #
        # sync_courses_from_category(sesion,cat_id)
        #
        time.sleep(random.randint(3,8))
    except KeyboardInterrupt:
        print (f"AVISO: El proceso de sincronzación se ha interrumpido!")
        error=True

    if not error:
        print ("[OK]")
        close_registry(r_id,0,1)
    else:
        close_registry(r_id,0,0)


def sync_list_courses(session):
    '''
    Sincroniza todos los cursos de todas las categorias
    '''

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
    print (f"Se han encontrado {len(cat_sin_sync)} sin sincronizar de un total de {len(cat_all)}")
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
    if (opcion == 1):
        print ("Sincronizando las categorias pendientes")
        categorias=cat_sin_sync
    else:
        print ("Sincronizando todas las categorias")
        categorias=cat_all


    r_id=open_registry()
    print()
    synced=0
    for categoria in categorias:
        try:
            print (f"Sincronizando categorias {synced}/{len(categorias)} ...", end="\r")
            #
            # sync_courses_from_category(sesion,categoria.id)
            #
            synced = synced+1
            time.sleep(random.randint(3,8))
        except KeyboardInterrupt:
            print (f"AVISO: El proceso de sincronzación se ha interrumpido!")
            break
        
    close_registry(r_id,0,synced)



def show_sync_menu(session):
    while(True):
        os.system("clear")
        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("1 - Sincroniza categorias")
            print ("2 - Sincroniza indice de aulas por categorias")
            print ("3 - Sincroniza partipantes de aulas")
            print ("4 - Sincroniza una sola categoría")
            print ("5 - Sincroniza los participantes de una sola aula")
            print ("6 - Cargar profesores del actual claustro")
            print ()
            print ("0 - Menú principal")
            opcion=input("Elige una opción: ")

            os.system("clear")
            print()
            print()

            if (opcion == "1"):
                sync_categories(session)
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "2"):
                sync_list_courses(session)
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "3"):
                sync_users_courses(session)
                input ("\n\nPulsa intro para continuar ...")


            if (opcion == "4"):
                sync_list_courses_one_category(session)
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "5"):
                sync_users_one_course(session)
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "6"):
                load_users()
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "0"):
                return

        except KeyboardInterrupt:
            return



def show_search_menu():
    while(True):
        os.system("clear")
        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("1 - Buscar categoria")
            print ()
            print ("0 - Menú principal")
            opcion=input("Elige una opción: ")

            os.system("clear")
            print()
            print()

            if (opcion == "1"):
                search_category()
                input ("\n\nPulsa intro para continuar ...")


            if (opcion == "0"):
                return

        except KeyboardInterrupt:
            return

    
def search_category():

    mensaje="""

    Búsqueda de categorias a partir de su nombre.

    """

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    patron=input("Introduce el patrón a buscar en los nombres de las categorias: ")

    # Buscar con LIKE (insensible a mayúsculas si se usa COLLATE NOCASE)
    cursor.execute("""
        SELECT id, nombre, url, sync
        FROM categorias
        WHERE nombre LIKE ? COLLATE NOCASE
    """, (f"%{patron}%",))

    resultados = cursor.fetchall()
    conn.close()
    
    print()
    print (f"Se han encontrado {len(resultados)} resultados: ")
    print()
    for c in resultados:
        print (f"\t{c[0]} - {c[1]}")


if (__name__=='__main__'):

    init_db()
    session=init_session()

    while(True):

        os.system("clear")

        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("1 - Sincronizar e importar datos")
            print ("2 - Buscar")
            print ("3 - Reiniciar base de datos")
            print ()
            print ("0 - Salir")
            print()
            opcion=input("Elige una opción: ")

            os.system("clear")
            print()
            print()

            if (opcion == "1"):
                show_sync_menu(session)
                #input ("\n\nPulsa intro para continuar ...")
                
            if (opcion == "2"):
                show_search_menu()
                #input ("\n\nPulsa intro para continuar ...")

            if (opcion == "3"):
                sync_reset()
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "0"):
                break

        except KeyboardInterrupt:
            print()
            sys.exit()
