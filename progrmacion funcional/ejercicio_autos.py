import pickle

# Clase corregida
class Auto:
    def __init__(self, modelo, placa):
        self.modelo = modelo
        self.placa = placa

    def __repr__(self):
        return f"El auto {self.modelo} tiene la placa {self.placa}"


# Función pura (como tu código 1)
def adicionar(lista, elemento):
    return lista + [elemento]


# Crear auto (función pura)
def crear_auto(modelo, placa):
    return Auto(modelo, placa)


# Guardar en pickle (efecto secundario)
def guardar_autos(ruta, autos):
    with open(ruta, "wb") as archivo:
        pickle.dump(autos, archivo)


# Leer autos (efecto secundario)
def leer_autos(ruta):
    with open(ruta, "rb") as archivo:
        return pickle.load(archivo)


# Transformación funcional (como código 2 y 3)
def transformar_auto(auto):
    return str(auto)


# Programa principal (estilo funcional)
autos = []

autos = adicionar(autos, crear_auto("Mazda Cx-5", "AVC123"))
autos = adicionar(autos, crear_auto("Chevrolet Camaro ZL1", "XYZ789"))
autos = adicionar(autos, crear_auto("Ford Mustang GT40,", "LMN456"))
autos = adicionar(autos, crear_auto("BMW Kia K3", "ZRT789"))
autos = adicionar(autos, crear_auto("lamborghini veneno","DGH190"))

guardar_autos("file_auto", autos)

autos_recuperados = leer_autos("file_auto")

resultado = list(map(transformar_auto, autos_recuperados))

print("\n".join(resultado))