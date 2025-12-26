from pathlib import Path
from datetime import datetime
from typing import List, Dict

from nf_claro_2025.reporting.rule_descriptions import RULE_DESCRIPTIONS


class HTMLReporter:
    """
    Gera relatório HTML (e PDF opcional) da NF.
    NÃO altera regras.
    NÃO altera classificação.
    Apenas apresenta o summary produzido pelo Validator.
    """

    def to_html(
        self,
        *,
        invoice: dict,
        summary: dict,
        issues: List[dict],
        caminho_html: Path,
        gerar_pdf: bool = False,
    ):
        caminho_html.parent.mkdir(parents=True, exist_ok=True)

        html = self._render_html(invoice, summary, issues)

        caminho_html.write_text(html, encoding="utf-8")

        # --------------------------------------------------
        # Geração de PDF (COMPORTAMENTO ORIGINAL)
        # --------------------------------------------------
        if gerar_pdf:
            try:
                from weasyprint import HTML
                caminho_pdf = caminho_html.with_suffix(".pdf")
                HTML(str(caminho_html)).write_pdf(str(caminho_pdf))
            except Exception as e:
                print(f"[WARN] Falha ao gerar PDF: {e}")

    # ==================================================
    # Renderização HTML
    # ==================================================
    def _render_html(self, invoice: dict, summary: dict, issues: List[dict]) -> str:
        nf = summary.get("nf", "SEM_NF")
        cliente = summary.get("cliente", "N/D")
        data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        itens_html = "\n".join(self._render_item(item) for item in summary["itens"])
        totais_html = self._render_totais(summary["totais"])

        return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Relatório NF {nf}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 20px;
}}
h1, h2, h3 {{
    color: #2c3e50;
}}
.item {{
    border: 1px solid #ccc;
    padding: 12px;
    margin-bottom: 15px;
}}
.ok {{
    color: green;
    font-weight: bold;
}}
.erro {{
    color: red;
    font-weight: bold;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 8px;
}}
th, td {{
    border: 1px solid #ccc;
    padding: 6px;
    text-align: left;
}}
th {{
    background-color: #f4f4f4;
}}
</style>
</head>

<body>

<h1>Relatório NFCom – Reforma Tributária</h1>

<p><strong>NF:</strong> {nf}</p>
<p><strong>Cliente:</strong> {cliente}</p>
<p><strong>Gerado em:</strong> {data}</p>

<hr>

<h2>Itens</h2>

{itens_html}

<hr>

<h2>Totalizadores</h2>

{totais_html}

</body>
</html>
"""

    # ==================================================
    # Renderização de ITEM
    # ==================================================
    def _render_item(self, item: Dict) -> str:
        linhas = []

        for chave, dados in item.items():
            if not chave.startswith("CT"):
                continue

            desc = RULE_DESCRIPTIONS.get(chave, chave)
            status = "erro" if dados.get("erro") else "ok"
            status_txt = "❌ ERRO" if dados.get("erro") else "✅ OK"

            linhas.append(f"""
<tr>
    <td>{chave}</td>
    <td>{desc}</td>
    <td>{dados.get("esperado")}</td>
    <td>{dados.get("encontrado")}</td>
    <td class="{status}">{status_txt}</td>
</tr>
""")

        linhas_html = "\n".join(linhas)

        return f"""
<div class="item">
<h3>
ITEM {item.get("num_item")} – {item.get("descricao")}
</h3>
<p><strong>Categoria:</strong> {item.get("categoria")}</p>

<table>
<tr>
    <th>Cenário</th>
    <th>Descrição</th>
    <th>Esperado</th>
    <th>Encontrado</th>
    <th>Status</th>
</tr>

{linhas_html}

</table>
</div>
"""

    # ==================================================
    # Renderização dos TOTALIZADORES
    # ==================================================
    def _render_totais(self, totais: Dict) -> str:
        linhas = []

        for chave, dados in totais.items():
            desc = RULE_DESCRIPTIONS.get(chave, chave)
            status = "erro" if dados.get("erro") else "ok"
            status_txt = "❌ ERRO" if dados.get("erro") else "✅ OK"

            linhas.append(f"""
<tr>
    <td>{chave}</td>
    <td>{desc}</td>
    <td>{dados.get("esperado")}</td>
    <td>{dados.get("encontrado")}</td>
    <td class="{status}">{status_txt}</td>
</tr>
""")

        linhas_html = "\n".join(linhas)

        return f"""
<table>
<tr>
    <th>Cenário</th>
    <th>Descrição</th>
    <th>Esperado</th>
    <th>Encontrado</th>
    <th>Status</th>
</tr>

{linhas_html}

</table>
"""
