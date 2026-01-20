from decimal import Decimal, InvalidOperation


def _safe_decimal(v):
    """
    Converte qualquer formato em Decimal:
    - {"$numberDecimal": "0.02"}
    - "0.02"
    - 0.02
    - Decimal("0.02")
    """
    if isinstance(v, Decimal):
        return v

    if isinstance(v, dict):
        if "$numberDecimal" in v:
            try:
                return Decimal(v["$numberDecimal"])
            except InvalidOperation:
                return None

    try:
        return Decimal(str(v))
    except Exception:
        return None


class CT008_IBS:
    """
    CT008 – VLR_TRIBUTO_IBS
    Regra oficial:
        VLR_TRIBUTO_IBS = VLR_TRIBUTO_IBSUF + VLR_TRIBUTO_IBSMUN
    """

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {})

        # ================
        # IBSUF
        # ================
        trib_uf = imposto_ref.get("TRIBUTO_IBSUF", {})
        ibsuf_raw = trib_uf.get("VLR_TRIBUTO_IBSUF")
        ibsuf = _safe_decimal(ibsuf_raw)

        # ================
        # IBSMUN
        # ================
        trib_mun = imposto_ref.get("TRIBUTO_IBS_MUNICIPAL", {})
        ibsmun_raw = trib_mun.get("VLR_TRIBUTO_IBSMUN")
        ibsmun = _safe_decimal(ibsmun_raw)

        # ================
        # IBS (valor do JSON)
        # ================
        ibs_json_raw = trib_mun.get("VLR_TRIBUTO_IBS")
        ibs_json = _safe_decimal(ibs_json_raw)

        if ibsuf is None or ibsmun is None or ibs_json is None:
            resultado["CT008"] = {
                "esperado": None,
                "encontrado": None,
                "erro": False
            }
            return

        # ================
        # Cálculo esperado
        # ================
        esperado = (ibsuf + ibsmun).quantize(Decimal("0.02"))

        erro = (esperado != ibs_json)

        resultado["CT008"] = {
            "esperado": esperado,
            "encontrado": ibs_json,
            "erro": erro
        }
