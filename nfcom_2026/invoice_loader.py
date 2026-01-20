import json
from decimal import Decimal


def _tratar_number_decimal(obj):
    """
    Converte estruturas {"$numberDecimal": "valor"} para Decimal(valor).
    Recursivo para listas e dicionários.
    """

    if isinstance(obj, dict):
        # Caso especial: {$numberDecimal: "valor"}
        if "$numberDecimal" in obj:
            return Decimal(obj["$numberDecimal"])

        # Caso geral: dicionário comum
        return {k: _tratar_number_decimal(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [_tratar_number_decimal(v) for v in obj]

    else:
        return obj


def carregar_invoice(caminho_json):
    """
    Carrega o arquivo JSON da NF e converte valores "$numberDecimal".
    """

    with open(caminho_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # converter todos os decimals
    data = _tratar_number_decimal(data)

    return data
