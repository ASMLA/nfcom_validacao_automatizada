from decimal import Decimal


def _safe_decimal(v):
    if isinstance(v, Decimal):
        return v
    if isinstance(v, dict) and "$numberDecimal" in v:
        try:
            return Decimal(v["$numberDecimal"])
        except:
            return None
    try:
        return Decimal(str(v))
    except:
        return None


class CT014_TotIBS:
    """
    CT014 – Total VLR_TOT_IBS
    Soma CT008.esperado apenas dos itens NÃO reduzidos.
    Se _DEVOLUCAO_ITEM=True => subtrai.

    Robustez:
      - Se CT008.esperado vier não numérico, ignora (equivalente a 0).
    """

    def totalizar(self, invoice, resultados_itens):
        soma = Decimal("0.00")

        for r in resultados_itens:
            if r.get("_EXCECAO_IMPOSTO_REFORMA_REDUZIDO"):
                continue

            ct = r.get("CT008")
            if not ct:
                continue

            esp_raw = ct.get("esperado")
            esp = _safe_decimal(esp_raw)
            if esp is None:
                continue

            if r.get("_DEVOLUCAO_ITEM"):
                soma -= esp
            else:
                soma += esp

        tot_json = _safe_decimal(invoice.get("TOTAL_REFORMA", {}).get("VLR_TOT_IBS"))
        if tot_json is None:
            return {"esperado": soma, "encontrado": None, "erro": True}

        return {"esperado": soma, "encontrado": tot_json, "erro": (soma != tot_json)}
