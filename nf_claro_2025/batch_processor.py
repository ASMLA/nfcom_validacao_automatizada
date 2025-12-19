import csv
from pathlib import Path
from openpyxl import Workbook

from nf_claro_2025.invoice_loader import carregar_invoice
from nf_claro_2025.validator.validator import Validator
from nf_claro_2025.reporting.html_reporter import HTMLReporter
from nf_claro_2025.reporting.audit_reporter import AuditReporter


class BatchProcessor:
    """
    Processa NF Claro 2025 (single ou lote)

    - Mantém feedback no console
    - Gera HTML individual
    - Gera auditoria TXT
    - Gera CSV/XLSX consolidado (lote)
    """

    def __init__(self, config, gerar_html=False, gerar_audit=False):
        self.config = config
        self.gerar_html = gerar_html
        self.gerar_audit = gerar_audit
        self.validator = Validator(config)

    # ==================================================
    # SINGLE
    # ==================================================
    def processar_single(self, caminho_json, pasta_saida):
        pasta_saida = Path(pasta_saida)
        pasta_saida.mkdir(parents=True, exist_ok=True)

        arquivo = Path(caminho_json)
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

        self._processar_arquivo(arquivo, pasta_saida)

    # ==================================================
    # LOTE
    # ==================================================
    def processar_lote(self, pasta_json, pasta_saida):
        pasta_saida = Path(pasta_saida)
        pasta_saida.mkdir(parents=True, exist_ok=True)

        pasta_json = Path(pasta_json)
        arquivos = list(pasta_json.glob("*.json"))

        if not arquivos:
            raise RuntimeError("Nenhum arquivo JSON encontrado para processamento em lote.")

        linhas_consolidadas = []

        for arquivo in arquivos:
            linha = self._processar_arquivo(arquivo, pasta_saida)
            if linha:
                linhas_consolidadas.append(linha)

        self._salvar_csv(linhas_consolidadas, pasta_saida / "consolidado.csv")
        self._salvar_xlsx(linhas_consolidadas, pasta_saida / "consolidado.xlsx")

    # ==================================================
    # CORE ÚNICO (SINGLE + LOTE)
    # ==================================================
    def _processar_arquivo(self, arquivo, pasta_saida):
        invoice = carregar_invoice(arquivo)
        summary, issues = self.validator.validar(invoice)

        # ------------------------------
        # FEEDBACK NO CONSOLE (RESTAURADO)
        # ------------------------------
        nf = summary.get("nf")

        if not issues:
            print(f"NF {nf} | STATUS: OK")
        else:
            print(f"NF {nf} | STATUS: DIVERGENTE")
            for issue in issues:
                print(
                    f"  - {issue.get('regra')}: "
                    f"esperado={issue.get('esperado')} "
                    f"encontrado={issue.get('encontrado')}"
                )

        # ------------------------------
        # PASTA DA NF
        # ------------------------------
        categoria = summary["itens"][0]["categoria"] if summary["itens"] else "SEM_ITEM"
        pasta_nf = pasta_saida / f"NF_{nf}_{arquivo.stem}_{categoria}"
        pasta_nf.mkdir(parents=True, exist_ok=True)

        # ------------------------------
        # HTML
        # ------------------------------
        if self.gerar_html:
            html = HTMLReporter()
            html.to_html(
                summary=summary,
                invoice=invoice,
                issues=issues,
                caminho_html=pasta_nf / "relatorio.html"
            )

        # ------------------------------
        # AUDIT
        # ------------------------------
        if self.gerar_audit:
            texto = AuditReporter.to_text(invoice, summary, self.config)
            with open(pasta_nf / "auditoria.txt", "w", encoding="utf-8") as f:
                f.write(texto)

        return self._linha_consolidada(arquivo.name, summary, issues)

    # ==================================================
    # CONSOLIDAÇÃO
    # ==================================================
    def _linha_consolidada(self, arquivo, summary, issues):
        tot = summary["totais"]

        return {
            "Arquivo": arquivo,
            "NF": summary.get("nf"),
            "Cliente": summary.get("cliente"),
            "Categoria": summary["itens"][0]["categoria"] if summary["itens"] else None,
            "Qtd_Issues": len(issues),
            "Status": "OK" if not issues else "DIVERGENTE",

            "CT011_TotBC_Esperado": tot["CT011_TotBC"]["esperado"],
            "CT011_TotBC_Encontrado": tot["CT011_TotBC"]["encontrado"],
            "CT012_TotIBSUF_Esperado": tot["CT012_TotIBSUF"]["esperado"],
            "CT012_TotIBSUF_Encontrado": tot["CT012_TotIBSUF"]["encontrado"],
            "CT013_TotIBSMUN_Esperado": tot["CT013_TotIBSMUN"]["esperado"],
            "CT013_TotIBSMUN_Encontrado": tot["CT013_TotIBSMUN"]["encontrado"],
            "CT014_TotIBS_Esperado": tot["CT014_TotIBS"]["esperado"],
            "CT014_TotIBS_Encontrado": tot["CT014_TotIBS"]["encontrado"],
            "CT015_TotCBS_Esperado": tot["CT015_TotCBS"]["esperado"],
            "CT015_TotCBS_Encontrado": tot["CT015_TotCBS"]["encontrado"],
        }

    # ==================================================
    # SAÍDAS
    # ==================================================
    def _salvar_csv(self, linhas, caminho):
        if not linhas:
            return

        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=linhas[0].keys())
            writer.writeheader()
            writer.writerows(linhas)

    def _salvar_xlsx(self, linhas, caminho):
        if not linhas:
            return

        wb = Workbook()
        ws = wb.active
        ws.append(list(linhas[0].keys()))

        for linha in linhas:
            ws.append(list(linha.values()))

        wb.save(caminho)
