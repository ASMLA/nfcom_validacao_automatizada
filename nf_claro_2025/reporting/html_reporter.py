import html
from datetime import datetime

from nf_claro_2025.reporting.rule_descriptions import RULE_DESCRIPTIONS


class HTMLReporter:
    """
    Gera relatório HTML da NF com:
    - Separação por ITEM (comportamento validado)
    - Nome amigável dos cenários (CTxxx)
    - Totalizadores
    """

    def to_html(self, summary, invoice, issues, caminho_html):
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Relatório NF Claro 2025</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 25px;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 6px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .ok {{
                    color: green;
                    font-weight: bold;
                }}
                .erro {{
                    color: red;
                    font-weight: bold;
                }}
                .item-header {{
                    background-color: #e9e9e9;
                    padding: 8px;
                    margin-top: 30px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>

        <h1>Relatório de Validação - NF Claro 2025</h1>

        <p><b>Número da NF:</b> {html.escape(str(summary.get("nf", "")))}</p>
        <p><b>Cliente:</b> {html.escape(str(summary.get("cliente", "")))}</p>
        <p><b>Data de geração:</b> {data_geracao}</p>
        """

        # ==================================================
        # VALIDAÇÕES POR ITEM (SEM REGRESSÃO)
        # ==================================================
        html_content += "<h2>Validações por Item</h2>"

        for item in summary.get("itens", []):
            num_item = item.get("num_item")
            descricao = item.get("descricao", "")

            # Cabeçalho do item
            html_content += f"""
            <div class="item-header">
                ITEM {html.escape(str(num_item))} – {html.escape(str(descricao))}
            </div>

            <table>
                <tr>
                    <th>Cenário</th>
                    <th>Esperado</th>
                    <th>Encontrado</th>
                    <th>Status</th>
                </tr>
            """

            for regra, res in item.items():
                if regra in ("num_item", "categoria", "descricao"):
                    continue

                status_ok = not res.get("erro")
                status_txt = "✅ OK" if status_ok else "❌ ERRO"
                status_class = "ok" if status_ok else "erro"

                nome_regra = RULE_DESCRIPTIONS.get(regra, regra)

                html_content += f"""
                <tr>
                    <td>{html.escape(nome_regra)}</td>
                    <td>{html.escape(str(res.get("esperado")))} </td>
                    <td>{html.escape(str(res.get("encontrado")))} </td>
                    <td class="{status_class}">{status_txt}</td>
                </tr>
                """

            html_content += "</table>"

        # ==================================================
        # TOTALIZADORES (mantidos)
        # ==================================================
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

        for regra, res in summary.get("totais", {}).items():
            status_ok = not res.get("erro")
            status_txt = "✅ OK" if status_ok else "❌ ERRO"
            status_class = "ok" if status_ok else "erro"

            nome_regra = RULE_DESCRIPTIONS.get(regra, regra)

            html_content += f"""
            <tr>
                <td>{html.escape(nome_regra)}</td>
                <td>{html.escape(str(res.get("esperado")))} </td>
                <td>{html.escape(str(res.get("encontrado")))} </td>
                <td class="{status_class}">{status_txt}</td>
            </tr>
            """

        html_content += "</table>"

        # ==================================================
        # RESUMO
        # ==================================================
        html_content += f"""
        <h2>Resumo</h2>
        <p><b>Total de divergências:</b> {len(issues)}</p>
        </body>
        </html>
        """

        with open(caminho_html, "w", encoding="utf-8") as f:
            f.write(html_content)
