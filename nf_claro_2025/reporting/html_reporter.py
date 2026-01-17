from pathlib import Path
from datetime import datetime
from typing import List, Dict
from decimal import Decimal, InvalidOperation

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
        # Geração de PDF (opcional)
        # --------------------------------------------------
        if gerar_pdf:
            try:
                from weasyprint import HTML
                caminho_pdf = caminho_html.with_suffix(".pdf")
                HTML(string=html, base_url=str(caminho_html.parent)).write_pdf(str(caminho_pdf))
            except Exception as e:
                print(f"[WARN] Falha ao gerar PDF: {e}")

        return html

    def _render_html(self, invoice: dict, summary: dict, issues: List[dict]) -> str:
        # --------------------------------------------------
        # Helper: padroniza exibição CT003_* com 3 casas decimais
        # --------------------------------------------------
        def _fmt(valor, regra_key):
            if valor is None:
                return "None"

            if isinstance(regra_key, str) and regra_key.startswith("CT003"):
                try:
                    d = valor if isinstance(valor, Decimal) else Decimal(str(valor))
                    return str(d.quantize(Decimal("0.000")))
                except (InvalidOperation, ValueError):
                    return str(valor)

            return str(valor)

        nf = summary.get("nf")
        cliente = summary.get("cliente")
        gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # --------------------------------------------------
        # Monta linhas do relatório (itens + totais)
        # --------------------------------------------------
        linhas = []

        # Itens
        for item in summary.get("itens", []):
            num_item = item.get("num_item")
            categoria = item.get("categoria")
            descricao_item = item.get("descricao")

            linhas.append(f"<h3>ITEM {str(num_item).zfill(4)} – {descricao_item}</h3>")
            linhas.append(f"<p><b>Categoria:</b> {categoria}</p>")

            linhas.append("""
<table>
<tr>
    <th>Cenário</th>
    <th>Descrição</th>
    <th>Esperado</th>
    <th>Encontrado</th>
    <th>Status</th>
</tr>
""")

            for chave, dados in item.items():
                if chave in ("num_item", "categoria", "descricao"):
                    continue

                desc = RULE_DESCRIPTIONS.get(chave, "")
                status = "erro" if dados.get("erro") else "ok"
                status_txt = "❌ ERRO" if dados.get("erro") else "✅ OK"

                linhas.append(f"""
<tr>
    <td>{chave}</td>
    <td>{desc}</td>
    <td>{_fmt(dados.get("esperado"), chave)}</td>
    <td>{_fmt(dados.get("encontrado"), chave)}</td>
    <td class="{status}">{status_txt}</td>
</tr>
""")

            linhas.append("</table>")

        # Totalizadores
        linhas_tot = []
        for chave, dados in summary.get("totais", {}).items():
            desc = RULE_DESCRIPTIONS.get(chave, "")
            status = "erro" if dados.get("erro") else "ok"
            status_txt = "❌ ERRO" if dados.get("erro") else "✅ OK"

            linhas_tot.append(f"""
<tr>
    <td>{chave}</td>
    <td>{desc}</td>
    <td>{dados.get("esperado")}</td>
    <td>{dados.get("encontrado")}</td>
    <td class="{status}">{status_txt}</td>
</tr>
""")

        linhas_tot_html = "\n".join(linhas_tot)

        # --------------------------------------------------
        # HTML Final
        # --------------------------------------------------
        linhas_html = "\n".join(linhas)

        return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8"/>
<title>Relatório NFCom – Reforma Tributária</title>
<style>
body {{
    font-family: Arial, sans-serif;
    font-size: 14px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 18px;
}}
th, td {{
    border: 1px solid #ddd;
    padding: 8px;
}}
th {{
    background: #f2f2f2;
}}
.ok {{
    color: green;
    font-weight: bold;
}}
.erro {{
    color: red;
    font-weight: bold;
}}
</style>
</head>
<body>

<h1>Relatório NFCom – Reforma Tributária</h1>

<p><b>NF:</b> {nf}</p>
<p><b>Cliente:</b> {cliente}</p>
<p><b>Gerado em:</b> {gerado_em}</p>

<h2>Itens</h2>
{linhas_html}

<h2>Totalizadores</h2>
<table>
<tr>
    <th>Cenário</th>
    <th>Descrição</th>
    <th>Esperado</th>
    <th>Encontrado</th>
    <th>Status</th>
</tr>
{linhas_tot_html}
</table>

</body>
</html>
"""

