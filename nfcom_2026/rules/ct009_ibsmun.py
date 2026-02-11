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
    """Normaliza percentual do JSON de Reforma (ex.: 0.90 -> 0.009)."""
    dec = _safe_decimal(v)
    if dec is None:
        return None
    if dec == 0:
        return Decimal("0")
    return dec / Decimal("100")


class CT009_IBSMUN:
    """
    CT009 – VLR_TRIBUTO_IBSMUN
    Regra oficial:
        VLR_TRIBUTO_IBSMUN = VLR_BC_TRIBUTO × PCT_ALIQUOTA_IBSMUN

    IMPORTANTE:
      - Para consistência, usa como base primária o esperado do CT006.
      - PCT_ALIQUOTA_IBSMUN vem no padrão da Reforma (divide por 100).
    """

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {}) or {}

        # Base primária: CT006 esperado
        bc_ct006 = _safe_decimal((resultado.get("CT006") or {}).get("esperado"))
        bc_json = _safe_decimal(imposto_ref.get("VLR_BC_TRIBUTO"))
        bc = bc_ct006 if bc_ct006 is not None else bc_json

        pct_raw = (imposto_ref.get("TRIBUTO_IBS_MUNICIPAL") or {}).get("PCT_ALIQUOTA_IBSMUN")
        pct = _normalize_pct_nf_reforma(pct_raw)

        v_json_raw = (imposto_ref.get("TRIBUTO_IBS_MUNICIPAL") or {}).get("VLR_TRIBUTO_IBSMUN")
        v_json = _safe_decimal(v_json_raw)

        if bc is None or pct is None or v_json is None:
            resultado["CT009"] = {
                "esperado": None,
                "encontrado": v_json,
                "erro": False,
            }
            return

        esperado = (bc * pct).quantize(Decimal("0.01"))
        resultado["CT009"] = {
            "esperado": esperado,
            "encontrado": v_json,
            "erro": (esperado != v_json),
        }
