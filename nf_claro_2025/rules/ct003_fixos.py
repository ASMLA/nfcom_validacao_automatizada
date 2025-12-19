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
    NF Reforma entrega percentuais como:
       0.10  → representa 0,10%
       0.90  → representa 0,90%
       3.00  → representa 3,00%

    Para cálculo devemos converter para fator:
       0.10 / 100  = 0.001
       0.90 / 100  = 0.009
       3.00 / 100  = 0.03
    """
    raw = _safe_decimal(v)
    if raw is None:
        return None, None

    # Original para exibir no relatório
    original = raw

    if raw == 0:
        return original, Decimal("0")

    convertido = (raw / Decimal("100"))
    return original, convertido


class CT003_CamposFixos:
    """
    CT003 – Validação dos campos fixos:
        IBSUF, IBSMUN, CBS

    Agora:
    • Exibe JSON original (0.10)
    • Exibe JSON convertido (0.001)
    • Compara com esperado (0.001)
    """

    def validar(self, item, resultado, classificacao):
        reforma = item.get("IMPOSTO_REFORMA", {})

        # ------------------------------
        # IBSUF
        # ------------------------------
        pct_raw_ibuf = reforma.get("TRIBUTO_IBSUF", {}).get("PCT_ALIQUOTA_IBSUF")
        orig_ibuf, conv_ibuf = _normalize_pct_nf_reforma(pct_raw_ibuf)
        esperado_ibuf = Decimal("0.001")

        erro_ibuf = (conv_ibuf != esperado_ibuf)

        resultado["CT003_IBSUF"] = {
            "json_original": orig_ibuf,
            "json_convertido": conv_ibuf,
            "esperado": esperado_ibuf,
            "encontrado": conv_ibuf,
            "erro": erro_ibuf
        }

        # ------------------------------
        # IBSMUN
        # ------------------------------
        pct_raw_ibsmun = reforma.get("TRIBUTO_IBS_MUNICIPAL", {}).get("PCT_ALIQUOTA_IBSMUN")
        orig_ism, conv_ism = _normalize_pct_nf_reforma(pct_raw_ibsmun)
        esperado_ism = Decimal("0.000")

        erro_ism = (conv_ism != esperado_ism)

        resultado["CT003_IBSMUN"] = {
            "json_original": orig_ism,
            "json_convertido": conv_ism,
            "esperado": esperado_ism,
            "encontrado": conv_ism,
            "erro": erro_ism
        }

        # ------------------------------
        # CBS
        # ------------------------------
        pct_raw_cbs = reforma.get("TRIBUTO_CBS", {}).get("PCT_ALIQUOTA_CBS")
        orig_cbs, conv_cbs = _normalize_pct_nf_reforma(pct_raw_cbs)
        esperado_cbs = Decimal("0.009")

        erro_cbs = (conv_cbs != esperado_cbs)

        resultado["CT003_CBS"] = {
            "json_original": orig_cbs,
            "json_convertido": conv_cbs,
            "esperado": esperado_cbs,
            "encontrado": conv_cbs,
            "erro": erro_cbs
        }
