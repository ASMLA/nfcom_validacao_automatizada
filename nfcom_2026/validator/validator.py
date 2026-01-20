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


class Validator:
    """
    Executor das regras CT003–CT015.

    Regras relevantes aqui:
    1) Itens com IND_DEVOLUCAO_VLR_ITEM = 1:
       - Marcar _DEVOLUCAO_ITEM=True para que os totalizadores subtraiam.
    2) IMPOSTO_REFORMA reduzido (por item):
       - Se NÃO TELCO (NTELCO) cclassTrib em {410008, 410999}
         OU NÃO TRIBUTADO (cClass) cclassTrib = 410999
       - IMPOSTO_REFORMA deve conter APENAS COD_CST e COD_CLASSIF_TRIB.
         Se vier extra => ERRO (no CT005).
       - Se estiver reduzido OK => marca _EXCECAO_IMPOSTO_REFORMA_REDUZIDO=True
         e torna CTs (exceto CT004/CT005) como N/A.
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

    def validar(self, invoice):

        summary = {
            "itens": [],
            "totais": {},
            "nf": invoice.get("NUM_NFCOM"),
            "cliente": invoice.get("INF_DESTINATARIO", {}).get("DSC_NOME_CLIENTE"),
        }

        itens_json = invoice.get("ITEM", [])
        resultados_itens = []
        issues = []

        for item in itens_json:
            resultado_item = {}
            num_item = item.get("NUM_ITEM")

            # ====================================================
            # NOVA REGRA: DEVOLUÇÃO DE ITEM
            # ====================================================
            ind_dev = item.get("IND_DEVOLUCAO_VLR_ITEM")
            is_devolucao = str(ind_dev).strip() == "1"
            resultado_item["_DEVOLUCAO_ITEM"] = is_devolucao
            # ====================================================

            classificacao = self.classificador.classificar_item(item)
            categoria_base = classificacao.get("categoria")

            # ====================================================
            # TELCO FUST vs TELCO NÃO FUST
            # ====================================================
            categoria_final = categoria_base

            if categoria_base == "TELCO":
                tem_fust = any(
                    imp.get("IND_GRUPO_TIPO_IMPOSTO") == "11"
                    for imp in item.get("IMPOSTO", [])
                )
                categoria_final = "TELCO FUST" if tem_fust else "TELCO NÃO FUST"

            item_summary = {
                "num_item": num_item,
                "categoria": categoria_final,
                "descricao": item.get("DSC_PRODUTO_SERVICO"),
            }

            # ====================================================
            # Regras CT003–CT010
            # ====================================================
            self.ct003.validar(item, resultado_item, classificacao)
            self.ct004.validar(item, resultado_item, classificacao)
            self.ct005.validar(item, resultado_item, classificacao)
            self.ct006.validar(item, resultado_item, classificacao)
            self.ct007.validar(item, resultado_item, classificacao)
            self.ct008.validar(item, resultado_item, classificacao)
            self.ct009.validar(item, resultado_item, classificacao)
            self.ct010.validar(item, resultado_item, classificacao)

            # ====================================================
            # REGRA: IMPOSTO_REFORMA REDUZIDO (sem CT nova)
            # ====================================================
            cclass = str(classificacao.get("cclass_esperado") or "").strip()
            fonte = str(classificacao.get("fonte_cst_cclass") or "").strip().upper()
            cat = str(categoria_final or "").strip().upper()

            aplica_regra_reduzido = (
                (cat in ("NAO TELCO", "NÃO TELCO") and fonte == "NTELCO" and cclass in ("410008", "410999"))
                or
                (cat in ("NAO TRIBUTADO", "NÃO TRIBUTADO") and fonte == "CCLASS" and cclass == "410999")
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
                        parts = []
                        if faltando:
                            parts.append(f"Faltando: {faltando}")
                        if extras:
                            parts.append(f"Extras: {extras}")
                        encontrado_msg = "; ".join(parts) if parts else str(sorted(list(keys)))

                        ct005 = resultado_item.get("CT005") or {}
                        ct005["esperado"] = "IMPOSTO_REFORMA apenas ['COD_CST', 'COD_CLASSIF_TRIB']"
                        ct005["encontrado"] = encontrado_msg
                        ct005["erro"] = True
                        resultado_item["CT005"] = ct005
                else:
                    ct005 = resultado_item.get("CT005") or {}
                    ct005["esperado"] = "IMPOSTO_REFORMA apenas ['COD_CST', 'COD_CLASSIF_TRIB']"
                    ct005["encontrado"] = "IMPOSTO_REFORMA ausente ou inválido"
                    ct005["erro"] = True
                    resultado_item["CT005"] = ct005

            if reduzido_ok:
                resultado_item["_EXCECAO_IMPOSTO_REFORMA_REDUZIDO"] = True

                for regra, data in resultado_item.items():
                    if regra in ("CT004", "CT005", "_EXCECAO_IMPOSTO_REFORMA_REDUZIDO", "_DEVOLUCAO_ITEM"):
                        continue
                    data["esperado"] = None
                    data["encontrado"] = None
                    data["erro"] = False

            # ====================================================
            # Consolidação do item (visão do relatório)
            # ====================================================
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
                    issues.append({
                        "item": num_item,
                        "regra": regra,
                        "esperado": data.get("esperado"),
                        "encontrado": data.get("encontrado"),
                    })

            summary["itens"].append(item_summary)
            resultados_itens.append(resultado_item)

        # ========================================================
        # Totalizadores CT011–CT015
        # ========================================================
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
                issues.append({
                    "item": "TOTAL",
                    "regra": nome,
                    "esperado": res.get("esperado"),
                    "encontrado": res.get("encontrado"),
                })

        return summary, issues
