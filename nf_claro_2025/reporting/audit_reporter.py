from datetime import datetime
from decimal import Decimal


class AuditReporter:
    """
    Gera relatório em texto puro (auditoria.txt),
    com todos os detalhes das regras CT003–CT015.
    """

    @staticmethod
    def to_text(invoice, summary, config):
        linhas = []

        num_nf = summary.get("nf", "N/D")
        cliente = summary.get("cliente", "N/D")

        linhas.append("============================================")
        linhas.append(f"NF: {num_nf}")
        linhas.append(f"Cliente: {cliente}")
        linhas.append("============================================\n")

        # ============================================================
        # ITENS CT003–CT010
        # ============================================================
        for item in summary["itens"]:
            num_item = item.get("num_item")
            categoria = item.get("categoria")
            descricao = item.get("descricao", "")

            linhas.append(f"ITEM {num_item:>4} – Categoria: {categoria}")
            linhas.append(f"Descrição: {descricao}\n")

            # Percorrer regras CT003–CT010
            for regra, dados in item.items():
                if regra in ["num_item", "categoria", "descricao"]:
                    continue

                esperado = dados.get("esperado")
                encontrado = dados.get("encontrado")
                erro = dados.get("erro", False)
                json_original = dados.get("json_original")
                json_convertido = dados.get("json_convertido")

                linhas.append(f"📌 {regra}")

                # JSON original (quando existir)
                if json_original is not None:
                    linhas.append(f"JSON original = {json_original}")

                # JSON convertido (quando existir)
                if json_convertido is not None:
                    linhas.append(f"JSON convertido = {json_convertido}")

                # Esperado × encontrado
                linhas.append(f"Esperado = {esperado}")
                linhas.append(f"Encontrado = {encontrado}")

                # Status
                linhas.append(f"Status = {'❗ Divergência' if erro else 'OK'}")
                linhas.append("--------------------------------------------")

            linhas.append("")  # Linha em branco entre itens

        # ============================================================
        # TOTALIZADORES CT011–CT015
        # ============================================================
        linhas.append("TOTALIZADORES")

        for nome, dados in summary["totais"].items():
            esperado = dados.get("esperado")
            encontrado = dados.get("encontrado")
            erro = dados.get("erro", False)
            linhas.append(
                f"{nome}: esperado={esperado}, json={encontrado}, status={'❗ Divergência' if erro else 'OK'}"
            )

        linhas.append("\nFIM DO RELATÓRIO\n")

        return "\n".join(linhas)
