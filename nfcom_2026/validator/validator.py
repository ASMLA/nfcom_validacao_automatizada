from decimal import Decimal

from nfcom_2026.classification import ClassificadorNF

from nfcom_2026.rules.ct003_fixos import CT003_CamposFixos
from nfcom_2026.rules.ct004_cst import CT004_CST
from nfcom_2026.rules.ct005_cclass import CT005_cClassTrib
from nfcom_2026.rules.ct006_bc import CT006_BaseCalculo
from nfcom_2026.rules.ct007_ibuf import CT007_IBSUF
from nfcom_2026.rules.ct008_ibs import CT008_IBS
from nfcom_2026.rules.ct009_ibsmun import CT009_IBSMUN
from nfcom_2026.rules.ct010_cbs import CT010_CBS

from nfcom_2026.rules.ct011_tot_bc import CT011_TotBC
from nfcom_2026.rules.ct012_tot_ibuf import CT012_TotIBSUF
from nfcom_2026.rules.ct013_tot_ibsmun import CT013_TotIBSMUN
from nfcom_2026.rules.ct014_tot_ibs import CT014_TotIBS
from nfcom_2026.rules.ct015_tot_cbs import CT015_TotCBS

from nfcom_2026.rules.ct016_tot_documento_fiscal import CT016_TotDocumentoFiscal


class Validator:
    """
    CT003–CT016

    - COD_FINALIDADE_NF = 4 (override global):
      * Categoria = TELCO
      * IMPOSTO_REFORMA permitido somente: COD_CST=820 e COD_CLASSIF_TRIB=820008
      * Qualquer bloco/valor extra => ERRO
      * CT003 e CT006–CT010 não devem existir (se existirem => ERRO)
      * CT011–CT015 esperados = 0.00
      * CT016 obrigatório: TOTAL_REFORMA/VLR_TOT_DOCUMENTO_FISCAL = TOTAL_NFCOM/VLR_TOT_NFCOM
      * IMPORTANTE: CT005 SEM "Extras". Sempre mostra esperado/encontrado.

    - NÃO TELCO com CST (tabela NTELCO) em 410/820:
      * Não calcula CT003/CT006–CT010
      * Se vier blocos/valores proibidos, mostrar erro + valores reais do JSON
      * CT005 SEM "Extras"
    """

    def __init__(self, config):
        self.config = config
        self.classificador = ClassificadorNF(config)

        self.ct003 = CT003_CamposFixos()
        self.ct004 = CT004_CST()
        self.ct005 = CT005_cClassTrib()
        self.ct006 = CT006_BaseCalculo()
        self.ct007 = CT007_IBSUF()
        self.ct008 = CT008_IBS()
        self.ct009 = CT009_IBSMUN()
        self.ct010 = CT010_CBS()

        self.ct011 = CT011_TotBC()
        self.ct012 = CT012_TotIBSUF()
        self.ct013 = CT013_TotIBSMUN()
        self.ct014 = CT014_TotIBS()
        self.ct015 = CT015_TotCBS()

        self.ct016 = CT016_TotDocumentoFiscal()

    def validar(self, invoice):
        cod_finalidade_nf = str(invoice.get("COD_FINALIDADE_NF", "")).strip()

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

        def _num_to_str(v):
            if v is None:
                return "Não Encontrado"
            if isinstance(v, Decimal):
                return str(v)
            if isinstance(v, dict) and "$numberDecimal" in v:
                return str(v.get("$numberDecimal"))
            return str(v)

        def _set_na(resultado_item: dict, regra: str):
            resultado_item[regra] = {"esperado": None, "encontrado": None, "erro": False}

        def _force_error(resultado_item: dict, regra: str, encontrado_txt: str):
            resultado_item[regra] = {
                "esperado": "Não Deve Existir",
                "encontrado": encontrado_txt,
                "erro": True,
            }

        def _push_issue(issues_list, item_num, regra, data):
            issues_list.append(
                {
                    "item": item_num,
                    "regra": regra,
                    "esperado": data.get("esperado"),
                    "encontrado": data.get("encontrado"),
                }
            )

        def _append_structure_details_to_ct005(resultado_item, classificacao, imposto_dict, faltando, extras):
            """
            Usar APENAS onde queremos sufixo de estrutura.
            NÃO usar em FINALIDADE 4 nem no modo CRÍTICO NTELCO 410/820.
            """
            ct005 = resultado_item.get("CT005") or {}

            esperado_cclass = str((classificacao or {}).get("cclass_esperado") or "").strip()
            encontrado_cclass = None
            if isinstance(imposto_dict, dict):
                encontrado_cclass = imposto_dict.get("COD_CLASSIF_TRIB")

            if esperado_cclass:
                ct005["esperado"] = esperado_cclass
            if encontrado_cclass is not None:
                ct005["encontrado"] = encontrado_cclass

            detalhes = []
            if faltando:
                detalhes.append(f"Faltando: {faltando}")
            if extras:
                detalhes.append(f"Extras: {extras}")

            if detalhes:
                base = str(ct005.get("encontrado")) if ct005.get("encontrado") is not None else "Não Encontrado"
                ct005["encontrado"] = base + " | " + " | ".join(detalhes)
                ct005["erro"] = True

            resultado_item["CT005"] = ct005

        def _extract_forbidden_values(imposto_ref: dict) -> dict:
            """
            Extrai valores “proibidos” para auditoria.
            """
            imposto_ref = imposto_ref or {}
            out = {}

            out["VLR_BC_TRIBUTO"] = imposto_ref.get("VLR_BC_TRIBUTO")

            trib_uf = imposto_ref.get("TRIBUTO_IBSUF") or {}
            out["PCT_ALIQUOTA_IBSUF"] = trib_uf.get("PCT_ALIQUOTA_IBSUF") if isinstance(trib_uf, dict) else None
            out["VLR_TRIBUTO_IBSUF"] = trib_uf.get("VLR_TRIBUTO_IBSUF") if isinstance(trib_uf, dict) else None

            trib_mun = imposto_ref.get("TRIBUTO_IBS_MUNICIPAL") or {}
            out["PCT_ALIQUOTA_IBSMUN"] = trib_mun.get("PCT_ALIQUOTA_IBSMUN") if isinstance(trib_mun, dict) else None
            out["VLR_TRIBUTO_IBSMUN"] = trib_mun.get("VLR_TRIBUTO_IBSMUN") if isinstance(trib_mun, dict) else None
            out["VLR_TRIBUTO_IBS (mun)"] = trib_mun.get("VLR_TRIBUTO_IBS") if isinstance(trib_mun, dict) else None

            trib_cbs = imposto_ref.get("TRIBUTO_CBS") or {}
            out["PCT_ALIQUOTA_CBS"] = trib_cbs.get("PCT_ALIQUOTA_CBS") if isinstance(trib_cbs, dict) else None
            out["VLR_TRIBUTO_CBS"] = trib_cbs.get("VLR_TRIBUTO_CBS") if isinstance(trib_cbs, dict) else None

            trib_ibs = imposto_ref.get("TRIBUTO_IBS") or {}
            out["VLR_TRIBUTO_IBS"] = trib_ibs.get("VLR_TRIBUTO_IBS") if isinstance(trib_ibs, dict) else None

            return out

        summary = {
            "itens": [],
            "totais": {},
            "nf": invoice.get("NUM_NFCOM"),
            "cliente": (invoice.get("INF_DESTINATARIO") or {}).get("DSC_NOME_CLIENTE"),
        }

        itens_json = invoice.get("ITEM", []) or []
        resultados_itens = []
        issues = []

        for item in itens_json:
            resultado_item = {}
            num_item = item.get("NUM_ITEM")

            # DEVOLUÇÃO
            ind_dev = item.get("IND_DEVOLUCAO_VLR_ITEM")
            resultado_item["_DEVOLUCAO_ITEM"] = str(ind_dev).strip() == "1"

            classificacao = self.classificador.classificar_item(item)

            # OVERRIDE: FINALIDADE 4
            if cod_finalidade_nf == "4":
                classificacao = dict(classificacao or {})
                classificacao["categoria"] = "TELCO"
                classificacao["cst_esperado"] = "820"
                classificacao["cclass_esperado"] = "820008"
                classificacao["fonte_cst_cclass"] = "FINALIDADE_4"

            categoria_base = (classificacao or {}).get("categoria")

            if cod_finalidade_nf == "4":
                categoria_final = "TELCO"
            else:
                categoria_final = categoria_base
                if categoria_base == "TELCO":
                    tem_fust = any(
                        (imp or {}).get("IND_GRUPO_TIPO_IMPOSTO") == "11"
                        for imp in (item.get("IMPOSTO") or [])
                    )
                    categoria_final = "TELCO FUST" if tem_fust else "TELCO NÃO FUST"

            item_summary = {
                "num_item": num_item,
                "categoria": categoria_final,
                "descricao": item.get("DSC_PRODUTO_SERVICO"),
            }

            # CT004/CT005 sempre rodam
            self.ct004.validar(item, resultado_item, classificacao)
            self.ct005.validar(item, resultado_item, classificacao)

            # =========================
            # FINALIDADE 4 (auditável)
            # =========================
            if cod_finalidade_nf == "4":
                imposto = item.get("IMPOSTO_REFORMA")
                allowed = {"COD_CST", "COD_CLASSIF_TRIB"}

                extras = []
                imposto_ref = imposto if isinstance(imposto, dict) else {}

                if isinstance(imposto, dict):
                    keys = set(imposto.keys())
                    extras = sorted(list(keys - allowed))
                else:
                    extras = ["IMPOSTO_REFORMA ausente ou inválido"]

                proibidas = {
                    "VLR_BC_TRIBUTO",
                    "TRIBUTO_IBSUF",
                    "TRIBUTO_IBS_MUNICIPAL",
                    "TRIBUTO_IBS",
                    "TRIBUTO_CBS",
                }
                proibidas_presentes = any(e in proibidas for e in extras)

                if proibidas_presentes:
                    vals = _extract_forbidden_values(imposto_ref)

                    # Exibir valores reais no "Encontrado"
                    pct_ibuf = _num_to_str(vals.get("PCT_ALIQUOTA_IBSUF"))
                    pct_ibsmun = _num_to_str(vals.get("PCT_ALIQUOTA_IBSMUN"))
                    pct_cbs = _num_to_str(vals.get("PCT_ALIQUOTA_CBS"))

                    bc = _num_to_str(vals.get("VLR_BC_TRIBUTO"))
                    v_ibuf = _num_to_str(vals.get("VLR_TRIBUTO_IBSUF"))
                    v_ibsmun = _num_to_str(vals.get("VLR_TRIBUTO_IBSMUN"))
                    v_cbs = _num_to_str(vals.get("VLR_TRIBUTO_CBS"))

                    v_ibs = vals.get("VLR_TRIBUTO_IBS")
                    if v_ibs is None:
                        v_ibs = vals.get("VLR_TRIBUTO_IBS (mun)")
                    v_ibs = _num_to_str(v_ibs)

                    _force_error(
                        resultado_item,
                        "CT003_IBSUF",
                        f"{pct_ibuf} | IMPOSTO_REFORMA possui blocos/valores (proibido em COD_FINALIDADE_NF=4)"
                    )
                    _force_error(
                        resultado_item,
                        "CT003_IBSMUN",
                        f"{pct_ibsmun} | IMPOSTO_REFORMA possui blocos/valores (proibido em COD_FINALIDADE_NF=4)"
                    )
                    _force_error(
                        resultado_item,
                        "CT003_CBS",
                        f"{pct_cbs} | IMPOSTO_REFORMA possui blocos/valores (proibido em COD_FINALIDADE_NF=4)"
                    )

                    _force_error(
                        resultado_item,
                        "CT006",
                        f"{bc} | VLR_BC_TRIBUTO/TRIBUTO_* presente (proibido em COD_FINALIDADE_NF=4)"
                    )
                    _force_error(
                        resultado_item,
                        "CT007",
                        f"{v_ibuf} | TRIBUTO_IBSUF presente (proibido em COD_FINALIDADE_NF=4)"
                    )
                    _force_error(
                        resultado_item,
                        "CT008",
                        f"{v_ibs} | TRIBUTO_IBS presente (proibido em COD_FINALIDADE_NF=4)"
                    )
                    _force_error(
                        resultado_item,
                        "CT009",
                        f"{v_ibsmun} | TRIBUTO_IBS_MUNICIPAL presente (proibido em COD_FINALIDADE_NF=4)"
                    )
                    _force_error(
                        resultado_item,
                        "CT010",
                        f"{v_cbs} | TRIBUTO_CBS presente (proibido em COD_FINALIDADE_NF=4)"
                    )
                else:
                    for r in ("CT003_IBSUF", "CT003_IBSMUN", "CT003_CBS", "CT006", "CT007", "CT008", "CT009", "CT010"):
                        _set_na(resultado_item, r)

                for regra, data in resultado_item.items():
                    if regra == "_DEVOLUCAO_ITEM":
                        continue
                    item_summary[regra] = data
                    if data.get("erro"):
                        _push_issue(issues, num_item, regra, data)

                summary["itens"].append(item_summary)
                resultados_itens.append(resultado_item)
                continue

            # ==========================================================
            # CRÍTICO: NÃO TELCO (NTELCO) com cst_esperado em 410/820
            # ==========================================================
            cat_upper = str(categoria_final or "").strip().upper()
            fonte = str((classificacao or {}).get("fonte_cst_cclass") or "").strip().upper()
            cst_tab = str((classificacao or {}).get("cst_esperado") or "").strip()

            is_ntelco_410_820 = (cat_upper in ("NAO TELCO", "NÃO TELCO") and fonte == "NTELCO" and cst_tab in ("410", "820"))

            if is_ntelco_410_820:
                imposto = item.get("IMPOSTO_REFORMA")
                allowed = {"COD_CST", "COD_CLASSIF_TRIB"}

                extras = []
                imposto_ref = imposto if isinstance(imposto, dict) else {}

                if isinstance(imposto, dict):
                    keys = set(imposto.keys())
                    extras = sorted(list(keys - allowed))
                else:
                    extras = ["IMPOSTO_REFORMA ausente ou inválido"]

                proibidas = {
                    "VLR_BC_TRIBUTO",
                    "TRIBUTO_IBSUF",
                    "TRIBUTO_IBS_MUNICIPAL",
                    "TRIBUTO_IBS",
                    "TRIBUTO_CBS",
                }
                proibidas_presentes = any(e in proibidas for e in extras)

                if proibidas_presentes:
                    vals = _extract_forbidden_values(imposto_ref)

                    pct_ibuf = _num_to_str(vals.get("PCT_ALIQUOTA_IBSUF"))
                    pct_ibsmun = _num_to_str(vals.get("PCT_ALIQUOTA_IBSMUN"))
                    pct_cbs = _num_to_str(vals.get("PCT_ALIQUOTA_CBS"))

                    bc = _num_to_str(vals.get("VLR_BC_TRIBUTO"))
                    v_ibuf = _num_to_str(vals.get("VLR_TRIBUTO_IBSUF"))
                    v_ibsmun = _num_to_str(vals.get("VLR_TRIBUTO_IBSMUN"))
                    v_cbs = _num_to_str(vals.get("VLR_TRIBUTO_CBS"))

                    v_ibs = vals.get("VLR_TRIBUTO_IBS")
                    if v_ibs is None:
                        v_ibs = vals.get("VLR_TRIBUTO_IBS (mun)")
                    v_ibs = _num_to_str(v_ibs)

                    _force_error(resultado_item, "CT003_IBSUF", f"{pct_ibuf} | IMPOSTO_REFORMA possui blocos/valores (proibido em CST 410/820 - NÃO TELCO)")
                    _force_error(resultado_item, "CT003_IBSMUN", f"{pct_ibsmun} | IMPOSTO_REFORMA possui blocos/valores (proibido em CST 410/820 - NÃO TELCO)")
                    _force_error(resultado_item, "CT003_CBS", f"{pct_cbs} | IMPOSTO_REFORMA possui blocos/valores (proibido em CST 410/820 - NÃO TELCO)")

                    _force_error(resultado_item, "CT006", f"{bc} | VLR_BC_TRIBUTO/TRIBUTO_* presente (proibido em CST 410/820 - NÃO TELCO)")
                    _force_error(resultado_item, "CT007", f"{v_ibuf} | TRIBUTO_IBSUF presente (proibido em CST 410/820 - NÃO TELCO)")
                    _force_error(resultado_item, "CT008", f"{v_ibs} | TRIBUTO_IBS presente (proibido em CST 410/820 - NÃO TELCO)")
                    _force_error(resultado_item, "CT009", f"{v_ibsmun} | TRIBUTO_IBS_MUNICIPAL presente (proibido em CST 410/820 - NÃO TELCO)")
                    _force_error(resultado_item, "CT010", f"{v_cbs} | TRIBUTO_CBS presente (proibido em CST 410/820 - NÃO TELCO)")
                else:
                    for r in ("CT003_IBSUF", "CT003_IBSMUN", "CT003_CBS", "CT006", "CT007", "CT008", "CT009", "CT010"):
                        _set_na(resultado_item, r)

                for regra, data in resultado_item.items():
                    if regra == "_DEVOLUCAO_ITEM":
                        continue
                    item_summary[regra] = data
                    if data.get("erro"):
                        _push_issue(issues, num_item, regra, data)

                summary["itens"].append(item_summary)
                resultados_itens.append(resultado_item)
                continue

            # =========================
            # Fluxo NORMAL
            # =========================
            self.ct003.validar(item, resultado_item, classificacao)
            self.ct006.validar(item, resultado_item, classificacao)
            self.ct007.validar(item, resultado_item, classificacao)
            self.ct009.validar(item, resultado_item, classificacao)
            self.ct008.validar(item, resultado_item, classificacao)
            self.ct010.validar(item, resultado_item, classificacao)

            # Regra REDUZIDO por item (mantida)
            cclass = str((classificacao or {}).get("cclass_esperado") or "").strip()
            cst = str((classificacao or {}).get("cst_esperado") or "").strip()
            fonte2 = str((classificacao or {}).get("fonte_cst_cclass") or "").strip().upper()
            cat2 = str(categoria_final or "").strip().upper()

            aplica_regra_reduzido = (
                (cat2 in ("NAO TELCO", "NÃO TELCO") and fonte2 == "NTELCO" and (cst in ("410", "820") or cclass in ("410008", "410999")))
                or
                (cat2 in ("NAO TRIBUTADO", "NÃO TRIBUTADO") and fonte2 == "CCLASS" and cclass == "410999")
            )

            reduzido_ok = False
            if aplica_regra_reduzido:
                imposto = item.get("IMPOSTO_REFORMA")
                allowed = {"COD_CST", "COD_CLASSIF_TRIB"}

                if isinstance(imposto, dict):
                    keys = set(imposto.keys())
                    extras = sorted(list(keys - allowed))
                    faltando = sorted(list(allowed - keys))

                    if not extras and not faltando:
                        reduzido_ok = True
                    else:
                        _append_structure_details_to_ct005(resultado_item, classificacao, imposto, faltando, extras)
                else:
                    _append_structure_details_to_ct005(
                        resultado_item,
                        classificacao,
                        {},
                        ["COD_CST", "COD_CLASSIF_TRIB"],
                        ["IMPOSTO_REFORMA ausente ou inválido"],
                    )

            if reduzido_ok:
                resultado_item["_EXCECAO_IMPOSTO_REFORMA_REDUZIDO"] = True
                for regra, data in list(resultado_item.items()):
                    if regra in ("CT004", "CT005", "_EXCECAO_IMPOSTO_REFORMA_REDUZIDO", "_DEVOLUCAO_ITEM"):
                        continue
                    data["esperado"] = None
                    data["encontrado"] = None
                    data["erro"] = False

            for regra, data in resultado_item.items():
                if regra in ("_EXCECAO_IMPOSTO_REFORMA_REDUZIDO", "_DEVOLUCAO_ITEM"):
                    continue

                data_view = data
                if reduzido_ok and regra not in ("CT004", "CT005"):
                    if data.get("esperado") is None and data.get("encontrado") is None:
                        data_view = dict(data)
                        data_view["esperado"] = "Não Encontrado"
                        data_view["encontrado"] = "Não Encontrado"
                        data_view["erro"] = False

                item_summary[regra] = data_view
                if data.get("erro"):
                    _push_issue(issues, num_item, regra, data)

            summary["itens"].append(item_summary)
            resultados_itens.append(resultado_item)

        # =========================
        # TOTALIZADORES
        # =========================
        if cod_finalidade_nf == "4":
            mapping = [
                ("CT011_TotBC", "VLR_TOT_BC_IBS_CBS"),
                ("CT012_TotIBSUF", "VLR_TOT_IBSUF"),
                ("CT013_TotIBSMUN", "VLR_TOT_IBSMUN"),
                ("CT014_TotIBS", "VLR_TOT_IBS"),
                ("CT015_TotCBS", "VLR_TOT_CBS"),
            ]
            for nome, campo in mapping:
                encontrado = _safe_decimal((invoice.get("TOTAL_REFORMA") or {}).get(campo))
                if encontrado is None:
                    encontrado = Decimal("0.00")
                res = {"esperado": Decimal("0.00"), "encontrado": encontrado, "erro": (encontrado != Decimal("0.00"))}
                summary["totais"][nome] = res
                if res.get("erro"):
                    _push_issue(issues, "TOTAL", nome, res)
        else:
            for nome, regra in [
                ("CT011_TotBC", self.ct011),
                ("CT012_TotIBSUF", self.ct012),
                ("CT013_TotIBSMUN", self.ct013),
                ("CT014_TotIBS", self.ct014),
                ("CT015_TotCBS", self.ct015),
            ]:
                res = regra.totalizar(invoice, resultados_itens)
                summary["totais"][nome] = res
                if res.get("erro"):
                    _push_issue(issues, "TOTAL", nome, res)

        res16 = self.ct016.totalizar(invoice)
        summary["totais"]["CT016_TotDocumentoFiscal"] = res16
        if res16.get("erro"):
            _push_issue(issues, "TOTAL", "CT016_TotDocumentoFiscal", res16)

        return summary, issues
