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


class CT011_TotBC:
    """
    CT011 – Total VLR_TOT_BC_IBS_CBS
    Soma de todos os valores CT006_BC esperados.
    """

    def totalizar(self, invoice, resultados_itens):
        soma = Decimal("0.00")
        erro = False

        for r in resultados_itens:
            ct = r.get("CT006")
            if ct:
                esp = ct.get("esperado")
                if esp is not None:
                    soma += esp

        # JSON TOTAL
        tot_json_raw = invoice.get("TOTAL_REFORMA", {}).get("VLR_TOT_BC_IBS_CBS")
        tot_json = _safe_decimal(tot_json_raw)

        if tot_json is None:
            return {"esperado": soma, "encontrado": None, "erro": True}

        erro = (soma != tot_json)

        return {
            "esperado": soma,
            "encontrado": tot_json,
            "erro": erro
        }
