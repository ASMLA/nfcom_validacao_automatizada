from decimal import Decimal, InvalidOperation


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


class CT012_TotIBSUF:
    """
    CT012 – Total VLR_TOT_IBSUF
    """

    def totalizar(self, invoice, resultados_itens):
        soma = Decimal("0.00")

        for r in resultados_itens:
            ct = r.get("CT007")
            if ct:
                esp = ct.get("esperado")
                if esp is not None:
                    soma += esp

        tot_json = _safe_decimal(
            invoice.get("TOTAL_REFORMA", {}).get("VLR_TOT_IBSUF")
        )

        if tot_json is None:
            return {"esperado": soma, "encontrado": None, "erro": True}

        erro = (soma != tot_json)

        return {"esperado": soma, "encontrado": tot_json, "erro": erro}
