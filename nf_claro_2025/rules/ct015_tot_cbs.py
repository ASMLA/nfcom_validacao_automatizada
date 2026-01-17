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


class CT015_TotCBS:
    """
    CT015 – Total VLR_TOT_CBS
    Soma CT010.esperado apenas dos itens NÃO reduzidos.
    Se _DEVOLUCAO_ITEM=True => subtrai.
    """

    def totalizar(self, invoice, resultados_itens):
        soma = Decimal("0.00")

        for r in resultados_itens:
            if r.get("_EXCECAO_IMPOSTO_REFORMA_REDUZIDO"):
                continue

            ct = r.get("CT010")
            if not ct:
                continue

            esp = ct.get("esperado")
            if esp is None:
                continue

            if r.get("_DEVOLUCAO_ITEM"):
                soma -= esp
            else:
                soma += esp

        tot_json = _safe_decimal(invoice.get("TOTAL_REFORMA", {}).get("VLR_TOT_CBS"))
        if tot_json is None:
            return {"esperado": soma, "encontrado": None, "erro": True}

        return {"esperado": soma, "encontrado": tot_json, "erro": (soma != tot_json)}
