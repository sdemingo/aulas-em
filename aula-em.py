#!/usr/bin/python3

from db import *
from sync import *
from search import *

import sys
import random
import time

RETRY_TIME=10



def show_sync_menu(session):
    while(True):
        os.system("clear")
        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("\t1 - Sincroniza categorias")
            print ("\t2 - Sincroniza índice de aulas para varias categorías")
            print ("\t3 - Sincroniza índice de aulas para una sola categoría")
            print ()
            print ("\t4 - Sincroniza partipantes de todas las aulas")
            print ("\t5 - Sincroniza los participantes de una sola aula")
            print ()
            print ("\t6 - Cargar profesores del actual claustro")
            print ()
            print ("\t0 - Menú principal")
            print()
            opcion=input("\tElige una opción: ")

            os.system("clear")
            print()
            print()
            
            while(True): # Reintentos de conexión por si falla
                try:
                    if (opcion == "1"):
                        sync_categories(session)
                        input ("\n\nPulsa intro para continuar ...")

                    if (opcion == "2"):
                        sync_list_courses(session)
                        input ("\n\nPulsa intro para continuar ...")

                    if (opcion == "3"):
                        sync_list_courses_one_category(session)
                        input ("\n\nPulsa intro para continuar ...")

                    if (opcion == "4"):
                        sync_users_courses(session)
                        input ("\n\nPulsa intro para continuar ...")

                    if (opcion == "5"):
                        sync_users_one_course(session)
                        input ("\n\nPulsa intro para continuar ...")

                    if (opcion == "6"):
                        load_users()
                        input ("\n\nPulsa intro para continuar ...")

                    if (opcion == "0"):
                        return

                    break # operación concluida. Salimos

                except ConnectionError as c_err:
                   print ("Error de conexión: "+str(c_err))
                   print (f"Se reintenta en {RETRY_TIME} segundos")
                   time.sleep(RETRY_TIME)

        except KeyboardInterrupt:
            return



def show_search_menu():
    while(True):
        os.system("clear")
        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("\t1 - Buscar categoria")
            print ("\t2 - Buscar usuario")
            print ()
            print ("\t0 - Menú principal")
            print()
            opcion=input("\tElige una opción: ")

            os.system("clear")
            print()
            print()

            if (opcion == "1"):
                search_category()
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "2"):
                search_user()
                input ("\n\nPulsa intro para continuar ...")


            if (opcion == "0"):
                return

        except KeyboardInterrupt:
            return


if (__name__=='__main__'):

    init_db()
    ses=init_session()
    
    if not any("MoodleSession" in cookie.name for cookie in ses.cookies):
        print("⚠️ No hay cookie de sesión; el login falló.")
        sys.exit()

    while(True):

        os.system("clear")

        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("\t1 - Sincronizar e importar datos")
            print ("\t2 - Buscar")
            print ("\t3 - Reiniciar base de datos")
            print ("\t4 - Exportar registros")
            print ("\t5 - Estadísticas")
            print ()
            print ("\t0 - Salir")
            print()
            opcion=input("\tElige una opción: ")

            os.system("clear")
            print()
            print()

            if (opcion == "1"):
                show_sync_menu(ses)
                #input ("\n\nPulsa intro para continuar ...")
                
            if (opcion == "2"):
                show_search_menu()
                #input ("\n\nPulsa intro para continuar ...")

            if (opcion == "3"):
                sync_reset()
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "4"):
                export_logs()
                input ("\n\nPulsa intro para continuar ...")

            if (opcion == "5"):
                db_stats()
                input ("\n\nPulsa intro para continuar ...")
                
            if (opcion == "0"):
                break

        except KeyboardInterrupt:
            print()
            sys.exit()
        except Exception as ex:
            print (f"ERROR: {ex}")
            sys.exit()
