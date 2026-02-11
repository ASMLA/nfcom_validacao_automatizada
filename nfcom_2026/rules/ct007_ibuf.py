from decimal import Decimal, InvalidOperation


def _safe_decimal(v):
    """Converte qualquer formato em Decimal (inclui {'$numberDecimal': '...'})."""
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


class CT007_IBSUF:
    """
    CT007 – VLR_TRIBUTO_IBSUF
    Regra oficial:
        VLR_TRIBUTO_IBSUF = VLR_BC_TRIBUTO × 0.001

    IMPORTANTE:
      - Para manter consistência entre CTs, a base usada no cálculo deve ser a MESMA do CT006.
        Portanto, usa como fonte primária o esperado do CT006.
      - Se CT006 não estiver disponível por algum motivo, cai para o VLR_BC_TRIBUTO do JSON.
    """

    ALIQUOTA_FIXA = Decimal("0.001")  # 0,10%

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {}) or {}

        # Base primária: CT006 esperado
        bc_ct006 = _safe_decimal((resultado.get("CT006") or {}).get("esperado"))
        bc_json = _safe_decimal(imposto_ref.get("VLR_BC_TRIBUTO"))
        bc = bc_ct006 if bc_ct006 is not None else bc_json

        # Valor IBSUF no JSON
        trib_ibuf = imposto_ref.get("TRIBUTO_IBSUF", {}) or {}
        ibsuf_json = _safe_decimal(trib_ibuf.get("VLR_TRIBUTO_IBSUF"))

        if bc is None or ibsuf_json is None:
            resultado["CT007"] = {
                "esperado": None,
                "encontrado": ibsuf_json,
                "erro": False,
            }
            return

        esperado = (bc * self.ALIQUOTA_FIXA).quantize(Decimal("0.01"))
        resultado["CT007"] = {
            "esperado": esperado,
            "encontrado": ibsuf_json,
            "erro": (esperado != ibsuf_json),
        }
