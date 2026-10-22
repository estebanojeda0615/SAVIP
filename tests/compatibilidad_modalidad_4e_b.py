"""Comparación histórica exacta salvo el metadato de declaración exigido en 4E-B."""
def sin_modalidad(value):
    if isinstance(value,dict):return {k:sin_modalidad(v) for k,v in value.items() if k!='modalidad_importe'}
    if isinstance(value,list):return [sin_modalidad(v) for v in value]
    return value
