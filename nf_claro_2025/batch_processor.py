from pathlib import Path
import csv
from openpyxl import Workbook

from nf_claro_2025.invoice_loader import carregar_invoice
from nf_claro_2025.validator.validator import Validator
from nf_claro_2025.reporting.html_reporter import HTMLReporter
from nf_claro_2025.reporting.audit_reporter import AuditReporter


class BatchProcessor:
    """
    Orquestra execução SINGLE e LOTE.
    Organiza saída e mantém feedback no console.
    """

    def __init__(self, config, gerar_html=False, gerar_audit=False, gerar_pdf=False):
        self.config = config
        self.gerar_html = gerar_html
        self.gerar_audit = gerar_audit
        self.gerar_pdf = gerar_pdf

        self.validator = Validator(config)

        self.html_reporter = HTMLReporter() if gerar_html else None
        self.audit_reporter = AuditReporter() if gerar_audit else None

    # ==================================================
    def processar_single(self, arquivo_json: Path):
        pasta_saida = Path("reports/single")
        pasta_saida.mkdir(parents=True, exist_ok=True)

        self._processar_arquivo(arquivo_json, pasta_saida)

    # ==================================================
    def processar_lote(self, pasta_json: Path):
        pasta_saida = Path("reports/lote")
        pasta_saida.mkdir(parents=True, exist_ok=True)

        linhas_consolidadas = []

        for arquivo in pasta_json.glob("*.json"):
            linha = self._processar_arquivo(arquivo, pasta_saida)
            if linha:
                linhas_consolidadas.append(linha)

        if linhas_consolidadas:
            self._salvar_csv(linhas_consolidadas, pasta_saida / "consolidado.csv")
            self._salvar_xlsx(linhas_consolidadas, pasta_saida / "consolidado.xlsx")

    # ==================================================
    def _processar_arquivo(self, arquivo_json: Path, pasta_saida: Path):

        invoice = carregar_invoice(arquivo_json)
        summary, issues = self.validator.validar(invoice)

        # 📂 Pasta = nome do JSON
        pasta_nf = pasta_saida / arquivo_json.name
        pasta_nf.mkdir(parents=True, exist_ok=True)

        if self.html_reporter:
            self.html_reporter.to_html(
                summary=summary,
                invoice=invoice,
                issues=issues,
                caminho_html=pasta_nf / "relatorio.html",
                gerar_pdf=self.gerar_pdf
            )

        if self.audit_reporter:
            texto = self.audit_reporter.to_text(invoice, summary, self.config)
            (pasta_nf / "auditoria.txt").write_text(texto, encoding="utf-8")

        num_nf = summary.get("nf", "SEM_NF")
        status = "OK" if not issues else "DIVERGENTE"
        print(f"[{status}] NF {num_nf} - {arquivo_json.name}")

        return {
            "Arquivo": arquivo_json.name,
            "NF": num_nf,
            "Qtd_Issues": len(issues),
            "Status": status
        }

    # ==================================================
    def _salvar_csv(self, linhas, caminho):
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=linhas[0].keys())
            writer.writeheader()
            writer.writerows(linhas)

    # ==================================================
    def _salvar_xlsx(self, linhas, caminho):
        wb = Workbook()
        ws = wb.active
        ws.append(list(linhas[0].keys()))

        for linha in linhas:
            ws.append(list(linha.values()))

        wb.save(caminho)
