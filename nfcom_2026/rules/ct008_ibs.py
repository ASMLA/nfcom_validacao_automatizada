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


class CT008_IBS:
    """
    CT008 – VLR_TRIBUTO_IBS
    Regra oficial:
        VLR_TRIBUTO_IBS = VLR_TRIBUTO_IBSUF + VLR_TRIBUTO_IBSMUN

    Regras de validação:
      - Esperado vem de CT007 + CT009 (primário).
      - Encontrado vem de TRIBUTO_IBS/VLR_TRIBUTO_IBS (preferencial)
        ou TRIBUTO_IBS_MUNICIPAL/VLR_TRIBUTO_IBS (fallback legado).
      - Se IBS total não existir no JSON (cenário normal), é ERRO.
    """

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {}) or {}

        # Fonte primária: CT007 e CT009 (esperados calculados)
        ibsuf = _safe_decimal((resultado.get("CT007") or {}).get("esperado"))
        ibsmun = _safe_decimal((resultado.get("CT009") or {}).get("esperado"))

        # Fallback (só se CT007/CT009 não estiverem disponíveis)
        if ibsuf is None:
            trib_uf = imposto_ref.get("TRIBUTO_IBSUF", {}) or {}
            ibsuf = _safe_decimal(trib_uf.get("VLR_TRIBUTO_IBSUF"))

        if ibsmun is None:
            trib_mun = imposto_ref.get("TRIBUTO_IBS_MUNICIPAL", {}) or {}
            ibsmun = _safe_decimal(trib_mun.get("VLR_TRIBUTO_IBSMUN"))

        # Encontrado: IBS total deve estar em TRIBUTO_IBS/VLR_TRIBUTO_IBS
        trib_ibs = imposto_ref.get("TRIBUTO_IBS", {}) or {}
        ibs_json = _safe_decimal(trib_ibs.get("VLR_TRIBUTO_IBS"))

        # Fallback para JSON legado (IBS total dentro do municipal)
        if ibs_json is None:
            trib_mun = imposto_ref.get("TRIBUTO_IBS_MUNICIPAL", {}) or {}
            ibs_json = _safe_decimal(trib_mun.get("VLR_TRIBUTO_IBS"))

        if ibsuf is None or ibsmun is None:
            resultado["CT008"] = {"esperado": None, "encontrado": ibs_json, "erro": False}
            return

        esperado = (ibsuf + ibsmun).quantize(Decimal("0.01"))

        if ibs_json is None:
            resultado["CT008"] = {"esperado": esperado, "encontrado": None, "erro": True}
            return

        resultado["CT008"] = {"esperado": esperado, "encontrado": ibs_json, "erro": (esperado != ibs_json)}
