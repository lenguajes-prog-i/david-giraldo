# Funciones que devuelven otras funciones
def crear_multiplicador(n):
    def multiplicar(x):
        return x * n
    return multiplicar

doble = crear_multiplicador(3)
print(doble(2))  # 10

#crear_multiplicador() devuelve una función nueva, por eso también es de orden superior.