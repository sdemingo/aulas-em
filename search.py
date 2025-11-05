
from db import *

    
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



def search_user():
    mensaje="""

    Búsqueda de un usuario a partir de su nombre o apellidos

    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    patron=input("Introduce el patrón a buscar para el usuario: ")

    usuarios = {}

    resultados = cursor.execute("""
    SELECT id, nombre, apellidos
    FROM claustro
    WHERE nombre LIKE ? COLLATE NOCASE
       OR apellidos LIKE ? COLLATE NOCASE
    """, (f"%{patron}%", f"%{patron}%"))

    resultados = cursor.fetchall()
    conn.close()
    
    print()
    for u in resultados:
        usuarios[u[0]]=(u[1]+" "+u[2],"C")

    # Se indica con C que el usuario pertenece al claustro
    # Se indica con A que el usuario está en el aula virtual
    for k,v in usuarios.items():
        print(f"\t{v[1]} - {v[0]}")
