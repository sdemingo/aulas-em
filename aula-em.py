#!/usr/bin/python3

from db import *
from sync import *
from search import *

import sys
import random




def show_sync_menu(session):
    while(True):
        os.system("clear")
        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("1 - Sincroniza categorias")
            print ("2 - Sincroniza índice de aulas para varias categorías")
            print ("3 - Sincroniza índice de aulas para una sola categoría")
            print ("4 - Sincroniza partipantes de todas las aulas")
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

        except KeyboardInterrupt:
            return



def show_search_menu():
    while(True):
        os.system("clear")
        try:
            print ("\n\n\t GESTIÓN DEL AULA VIRTUAL")
            print ()
            print ("1 - Buscar categoria")
            print ("2 - Buscar usuario")
            print ()
            print ("0 - Menú principal")
            opcion=input("Elige una opción: ")

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
            print ("1 - Sincronizar e importar datos")
            print ("2 - Buscar")
            print ("3 - Reiniciar base de datos")
            print ("4 - Exportar registros")
            print ("5 - Estadísticas")
            print ()
            print ("0 - Salir")
            print()
            opcion=input("Elige una opción: ")

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
