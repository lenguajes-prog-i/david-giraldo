# Funciones que reciben otras funciones
def saludar():
    print("Hola")

def ejecutar(funcion):
    funcion()

ejecutar(saludar)

#Aquí ejecutar() es una función de orden superior porque recibe saludar como argumento.