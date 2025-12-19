from decimal import Decimal
from nf_claro_2025.classification import ClassificadorNF
from nf_claro_2025.rules.ct003_fixos import CT003_CamposFixos
from nf_claro_2025.rules.ct004_cst import CT004_CST
from nf_claro_2025.rules.ct005_cclass import CT005_cClassTrib
from nf_claro_2025.rules.ct006_bc import CT006_BaseCalculo
from nf_claro_2025.rules.ct007_ibuf import CT007_IBSUF
from nf_claro_2025.rules.ct008_ibs import CT008_IBS
from nf_claro_2025.rules.ct009_ibsmun import CT009_IBSMUN
from nf_claro_2025.rules.ct010_cbs import CT010_CBS
from nf_claro_2025.rules.ct011_tot_bc import CT011_TotBC
from nf_claro_2025.rules.ct012_tot_ibuf import CT012_TotIBSUF
from nf_claro_2025.rules.ct013_tot_ibsmun import CT013_TotIBSMUN
from nf_claro_2025.rules.ct014_tot_ibs import CT014_TotIBS
from nf_claro_2025.rules.ct015_tot_cbs import CT015_TotCBS


class Validator:
    """
    Executor das regras CT003–CT015.
    Estrutura nova e oficial do summary:

    summary["itens"] = [
        {
            "num_item": "...",
            "categoria": "...",
            "descricao": "...",
            "CT003_IBSUF": {...},
            "CT004": {...},
            ...
        }
    ]
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

    # ============================================================
    # Valida a NF
    # ============================================================
    def validar(self, invoice):

        summary = {
            "itens": [],
            "totais": {},
            "nf": invoice.get("NUM_NFCOM"),
            "cliente": invoice.get("INF_DESTINATARIO", {}).get("DSC_NOME_CLIENTE")
        }

        itens_json = invoice.get("ITEM", [])
        resultados_itens = []
        issues = []

        for item in itens_json:

            resultado_item = {}
            num_item = item.get("NUM_ITEM")

            classificacao = self.classificador.classificar_item(item)

            # Estrutura NOVA do summary
            item_summary = {
                "num_item": num_item,
                "categoria": classificacao.get("categoria"),
                "descricao": item.get("DSC_PRODUTO_SERVICO")
            }

            # Regras CT003–CT010
            self.ct003.validar(item, resultado_item, classificacao)
            self.ct004.validar(item, resultado_item, classificacao)
            self.ct005.validar(item, resultado_item, classificacao)
            self.ct006.validar(item, resultado_item, classificacao)
            self.ct007.validar(item, resultado_item, classificacao)
            self.ct008.validar(item, resultado_item, classificacao)
            self.ct009.validar(item, resultado_item, classificacao)
            self.ct010.validar(item, resultado_item, classificacao)

            # Merge resultados no summary
            for regra_nome, data in resultado_item.items():
                item_summary[regra_nome] = data

                if data.get("erro"):
                    issues.append({
                        "item": num_item,
                        "regra": regra_nome,
                        "esperado": data.get("esperado"),
                        "encontrado": data.get("encontrado")
                    })

            summary["itens"].append(item_summary)
            resultados_itens.append(resultado_item)

        # Totalizadores CT011–CT015
        for totalizador, regra in [
            ("CT011_TotBC", self.ct011),
            ("CT012_TotIBSUF", self.ct012),
            ("CT013_TotIBSMUN", self.ct013),
            ("CT014_TotIBS", self.ct014),
            ("CT015_TotCBS", self.ct015),
        ]:
            res = regra.totalizar(invoice, resultados_itens)
            summary["totais"][totalizador] = res

            if res.get("erro"):
                issues.append({
                    "item": "TOTAL",
                    "regra": totalizador,
                    "esperado": res.get("esperado"),
                    "encontrado": res.get("encontrado")
                })

        return summary, issues
