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
        # Caso padrão do Mongo / JSON
        if "$numberDecimal" in v:
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
    """

    ALIQUOTA_FIXA = Decimal("0.001")  # 0,10%

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {})

        # =============================
        # BASE DE CÁLCULO
        # =============================
        bc_json_raw = imposto_ref.get("VLR_BC_TRIBUTO")
        bc_json = _safe_decimal(bc_json_raw)

        # =============================
        # VALOR DO IBSUF
        # =============================
        trib_ibuf = imposto_ref.get("TRIBUTO_IBSUF", {})
        ibsuf_raw = trib_ibuf.get("VLR_TRIBUTO_IBSUF")
        ibsuf_json = _safe_decimal(ibsuf_raw)

        # =============================
        # Verificações iniciais
        # =============================
        if bc_json is None or ibsuf_json is None:
            resultado["CT007"] = {
                "esperado": None,
                "encontrado": None,
                "erro": False
            }
            return

        # =============================
        # Cálculo esperado
        # =============================
        esperado = (bc_json * self.ALIQUOTA_FIXA).quantize(Decimal("0.01"))

        erro = (esperado != ibsuf_json)

        resultado["CT007"] = {
            "esperado": esperado,
            "encontrado": ibsuf_json,
            "erro": erro
        }
