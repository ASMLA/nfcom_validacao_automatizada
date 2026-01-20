from decimal import Decimal, InvalidOperation


def _safe_decimal(v):
    if isinstance(v, Decimal):
        return v
    if isinstance(v, dict) and "$numberDecimal" in v:
        try:
            return Decimal(v["$numberDecimal"])
        except InvalidOperation:
            return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _normalize_pct_nf_reforma(v):
    """
    NF Reforma traz percentuais como:
      0.10 → 0,10%
      0.90 → 0,90%
      3.00 → 3,00%
    Para cálculo precisamos do fator:
      0.10  → 0.001
      0.90  → 0.009
      3.00  → 0.03
    Portanto: sempre dividir por 100.
    """
    dec = _safe_decimal(v)
    if dec is None:
        return None
    if dec == 0:
        return Decimal("0")
    return dec / Decimal("100")


class CT010_CBS:
    """
    CT010 – VLR_TRIBUTO_CBS
    Regra oficial:
        VLR_TRIBUTO_CBS = VLR_BC_TRIBUTO × PCT_ALIQUOTA_CBS
    """

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {})

        bc = _safe_decimal(imposto_ref.get("VLR_BC_TRIBUTO"))
        pct_raw = imposto_ref.get("TRIBUTO_CBS", {}).get("PCT_ALIQUOTA_CBS")
        pct = _normalize_pct_nf_reforma(pct_raw)
        v_json = _safe_decimal(imposto_ref.get("TRIBUTO_CBS", {}).get("VLR_TRIBUTO_CBS"))

        if bc is None or pct is None or v_json is None:
            resultado["CT010"] = {
                "esperado": None,
                "encontrado": v_json,
                "erro": False,
            }
            return

        esperado = (bc * pct).quantize(Decimal("0.01"))
        erro = (esperado != v_json)

        resultado["CT010"] = {
            "esperado": esperado,
            "encontrado": v_json,
            "erro": erro,
        }
