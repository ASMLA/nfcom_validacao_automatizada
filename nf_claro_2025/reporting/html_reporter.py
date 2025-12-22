import html
from datetime import datetime
from nf_claro_2025.reporting.rule_descriptions import RULE_DESCRIPTIONS


class HTMLReporter:
    """
    Gera relatório HTML.
    Cada ITEM exibe explicitamente sua categoria fiscal.
    """

    def to_html(self, summary, invoice, issues, caminho_html, gerar_pdf=False):
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Relatório NFCom</title>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 14px; }}
                h1, h2 {{ margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 25px; }}
                th, td {{ border: 1px solid #ccc; padding: 6px; }}
                th {{ background-color: #f1f1f1; }}
                .ok {{ background-color: #d4edda; font-weight: bold; text-align: center; }}
                .erro {{ background-color: #f8d7da; font-weight: bold; text-align: center; }}
                .item-header {{ margin-top: 25px; padding: 8px; background-color: #e9ecef; font-weight: bold; }}
                .categoria {{ font-style: italic; color: #555; }}
            </style>
        </head>
        <body>

        <h1>Relatório de Validação – NFCom</h1>
        <p><b>NF:</b> {summary.get("nf")}</p>
        <p><b>Cliente:</b> {html.escape(str(summary.get("cliente", "")))}</p>
        <p><b>Data de geração:</b> {data_geracao}</p>

        <h2>Validações por Item</h2>
        """

        # ===================== ITENS =====================
        for item in summary.get("itens", []):
            categoria_item = item.get("categoria", "NÃO IDENTIFICADO")

            html_content += f"""
            <div class="item-header">
                ITEM {item["num_item"]} – {html.escape(str(item.get("descricao", "")))}<br>
                <span class="categoria">Categoria: {categoria_item}</span>
            </div>

            <table>
                <tr>
                    <th>Cenário</th>
                    <th>Esperado</th>
                    <th>Encontrado</th>
                    <th>Status</th>
                </tr>
            """

            for regra, resultado in item.items():
                if regra in ("num_item", "categoria", "descricao"):
                    continue

                status_ok = not resultado.get("erro")
                status_txt = "OK" if status_ok else "ERRO"
                status_class = "ok" if status_ok else "erro"

                nome_regra = RULE_DESCRIPTIONS.get(regra, regra)

                html_content += f"""
                <tr>
                    <td>{html.escape(nome_regra)}</td>
                    <td>{resultado.get("esperado")}</td>
                    <td>{resultado.get("encontrado")}</td>
                    <td class="{status_class}">{status_txt}</td>
                </tr>
                """

            html_content += "</table>"

        # ===================== TOTALIZADORES =====================
        html_content += """
        <h2>Totalizadores</h2>
        <table>
            <tr>
                <th>Cenário</th>
                <th>Esperado</th>
                <th>Encontrado</th>
                <th>Status</th>
            </tr>
        """

        for regra, resultado in summary.get("totais", {}).items():
            status_ok = not resultado.get("erro")
            status_txt = "OK" if status_ok else "ERRO"
            status_class = "ok" if status_ok else "erro"

            nome_regra = RULE_DESCRIPTIONS.get(regra, regra)

            html_content += f"""
            <tr>
                <td>{html.escape(nome_regra)}</td>
                <td>{resultado.get("esperado")}</td>
                <td>{resultado.get("encontrado")}</td>
                <td class="{status_class}">{status_txt}</td>
            </tr>
            """

        html_content += """
        </table>
        </body>
        </html>
        """

        with open(caminho_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        if gerar_pdf:
            self._gerar_pdf(caminho_html)

    # ==================================================
    def _gerar_pdf(self, caminho_html):
        from weasyprint import HTML
        import os

        caminho_pdf = str(caminho_html).replace(".html", ".pdf")

        if os.path.exists(caminho_pdf):
            try:
                os.remove(caminho_pdf)
            except PermissionError:
                raise PermissionError(
                    f"O arquivo PDF está aberto ou bloqueado:\n{caminho_pdf}\n"
                    "Feche o arquivo antes de continuar."
                )

        HTML(caminho_html).write_pdf(caminho_pdf)
