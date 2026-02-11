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


class CT011_TotBC:
    """
    CT011 – Total VLR_TOT_BC_IBS_CBS
    Soma CT006.esperado apenas dos itens NÃO reduzidos.
    Se _DEVOLUCAO_ITEM=True => subtrai.

    Robustez:
      - Se CT006.esperado vier não numérico (ex.: "Não Deve Existir"), ignora (equivalente a 0).
      - Evita crash em execuções em lote.
    """

    def totalizar(self, invoice, resultados_itens):
        soma = Decimal("0.00")

        for r in resultados_itens:
            if r.get("_EXCECAO_IMPOSTO_REFORMA_REDUZIDO"):
                continue

            ct = r.get("CT006")
            if not ct:
                continue

            esp_raw = ct.get("esperado")
            esp = _safe_decimal(esp_raw)
            if esp is None:
                # esperado não numérico => tratar como 0 (não soma / não subtrai)
                continue

            if r.get("_DEVOLUCAO_ITEM"):
                soma -= esp
            else:
                soma += esp

        tot_json_raw = invoice.get("TOTAL_REFORMA", {}).get("VLR_TOT_BC_IBS_CBS")
        tot_json = _safe_decimal(tot_json_raw)

        if tot_json is None:
            return {"esperado": soma, "encontrado": None, "erro": True}

        return {"esperado": soma, "encontrado": tot_json, "erro": (soma != tot_json)}
