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


class CT006_BaseCalculo:
    """
    CT006 – VLR_BC_TRIBUTO

    Regras oficiais:

    • TELCO FUST:
        VLR_BC_TRIBUTO = VLR_BC_TRIBUTO do primeiro imposto
        onde IND_GRUPO_TIPO_IMPOSTO = 11

    • TELCO NÃO FUST:
        VLR_BC_TRIBUTO = VLR_TOT_ITEM – soma(VLR_TRIBUTO) – soma(VLR_FCP)

    • NAO TELCO:
        VLR_BC_TRIBUTO =
            (VLR_TOT_ITEM * (1 - ISS)) – soma(VLR_TRIBUTO)

        ISS:
        - Buscar AliqISS na tabela NTELCO
        - Se não encontrar ou inválido → fallback 2%

    • NAO TRIBUTADO:
        VLR_BC_TRIBUTO = None

    • INDEFINIDO:
        Mantém valor do JSON
    """

    def validar(self, item, resultado, classificacao):
        imposto_ref = item.get("IMPOSTO_REFORMA", {})
        categoria = classificacao.get("categoria")

        bc_json = _safe_decimal(imposto_ref.get("VLR_BC_TRIBUTO"))
        tot_item = _safe_decimal(item.get("VLR_TOT_ITEM"))
        impostos_item = item.get("IMPOSTO", []) or []

        esperado = None

        # ===================== TELCO FUST =====================
        if categoria == "TELCO FUST":
            for imp in impostos_item:
                if str(imp.get("IND_GRUPO_TIPO_IMPOSTO", "")).strip() == "11":
                    esperado = _safe_decimal(imp.get("VLR_BC_TRIBUTO"))
                    break

        # ================= TELCO NÃO FUST =====================
        elif categoria == "TELCO NÃO FUST":
            if tot_item is not None:
                total_trib = Decimal("0")
                total_fcp = Decimal("0")

                for imp in impostos_item:
                    trib = _safe_decimal(imp.get("VLR_TRIBUTO"))
                    if trib is not None:
                        total_trib += trib

                    fcp = _safe_decimal(imp.get("VLR_FCP"))
                    if fcp is not None:
                        total_fcp += fcp

                esperado = tot_item - total_trib - total_fcp

        # ===================== NAO TELCO ======================
        elif categoria == "NAO TELCO":
            if tot_item is not None:
                # -------- ISS --------
                aliq_iss_str = classificacao.get("aliq_iss_esperada")
                iss_aliq = None

                if aliq_iss_str:
                    s = str(aliq_iss_str).strip().replace(",", ".")
                    if s.endswith("%"):
                        s = s[:-1]
                    try:
                        iss_aliq = Decimal(s) / Decimal("100")
                    except Exception:
                        iss_aliq = None

                # fallback 2%
                if iss_aliq is None:
                    iss_aliq = Decimal("0.02")

                # -------- Tributos --------
                total_tributos = Decimal("0")

                for imp in impostos_item:
                    trib = _safe_decimal(imp.get("VLR_TRIBUTO"))
                    if trib is not None:
                        total_tributos += trib

                valor_com_iss = (tot_item * (Decimal("1") - iss_aliq)).quantize(
                    Decimal("0.01")
                )

                esperado = valor_com_iss - total_tributos

        # ================== NAO TRIBUTADO =====================
        elif categoria == "NAO TRIBUTADO":
            esperado = None

        # ==================== INDEFINIDO ======================
        else:
            esperado = bc_json

        # ===================== COMPARAÇÃO =====================
        if esperado is None and bc_json is None:
            erro = False
        elif esperado is None or bc_json is None:
            erro = True
        else:
            erro = esperado != bc_json

        resultado["CT006"] = {
            "esperado": esperado,
            "encontrado": bc_json,
            "erro": erro,
        }
