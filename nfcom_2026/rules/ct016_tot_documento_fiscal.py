from decimal import Decimal


def _safe_decimal(v):
    if isinstance(v, Decimal):
        return v
    if isinstance(v, dict) and "$numberDecimal" in v:
        try:
            return Decimal(v["$numberDecimal"])
        except Exception:
            return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


class CT016_TotDocumentoFiscal:
    """
    CT016 – Validar VLR_TOT_DOCUMENTO_FISCAL

    Regra:
      TOTAL_REFORMA/VLR_TOT_DOCUMENTO_FISCAL DEVE existir
      e deve ser igual a TOTAL_NFCOM/VLR_TOT_NFCOM
    """

    def totalizar(self, invoice):
        # esperado vem do lugar correto no JSON
        esperado = _safe_decimal(
            (invoice.get("TOTAL_NFCOM") or {}).get("VLR_TOT_NFCOM")
        )

        # encontrado deve existir em TOTAL_REFORMA
        total_reforma = invoice.get("TOTAL_REFORMA") or {}
        existe_campo = "VLR_TOT_DOCUMENTO_FISCAL" in total_reforma
        encontrado = _safe_decimal(total_reforma.get("VLR_TOT_DOCUMENTO_FISCAL"))

        # Se não existe, é ERRO (campo obrigatório)
        if not existe_campo:
            return {
                "esperado": esperado,
                "encontrado": "Não Encontrado",
                "erro": True
            }

        # Se existe mas não é decimal válido, também é erro
        if encontrado is None:
            return {
                "esperado": esperado,
                "encontrado": "Inválido",
                "erro": True
            }

        # Se esperado não existir (caso raro), não dá para validar comparação
        if esperado is None:
            return {
                "esperado": None,
                "encontrado": encontrado,
                "erro": True  # esperado ausente é problema do JSON
            }

        return {
            "esperado": esperado,
            "encontrado": encontrado,
            "erro": (esperado != encontrado)
        }
