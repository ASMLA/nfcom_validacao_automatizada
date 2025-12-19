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


class CT009_IBSMUN:
    """
    CT009 – VLR_TRIBUTO_IBSMUN
    """

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {})

        bc_raw = imposto_ref.get("VLR_BC_TRIBUTO")
        bc = _safe_decimal(bc_raw)

        pct_raw = imposto_ref.get("TRIBUTO_IBS_MUNICIPAL", {}).get("PCT_ALIQUOTA_IBSMUN")
        pct = _safe_decimal(pct_raw)

        v_json_raw = imposto_ref.get("TRIBUTO_IBS_MUNICIPAL", {}).get("VLR_TRIBUTO_IBSMUN")
        v_json = _safe_decimal(v_json_raw)

        if bc is None or pct is None or v_json is None:
            resultado["CT009"] = {
                "esperado": None,
                "encontrado": None,
                "erro": False
            }
            return

        esperado = (bc * pct).quantize(Decimal("0.01"))
        erro = (esperado != v_json)

        resultado["CT009"] = {
            "esperado": esperado,
            "encontrado": v_json,
            "erro": erro
        }
