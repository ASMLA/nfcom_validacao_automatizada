import argparse
from pathlib import Path

from nf_claro_2025.batch_processor import BatchProcessor
from nf_claro_2025.config import carregar_configuracao


def main():
    parser = argparse.ArgumentParser(description="Validador NF Claro 2025")
    parser.add_argument("caminho", help="Arquivo JSON (single) ou pasta (lote)")
    parser.add_argument("--multi", action="store_true", help="Processar em lote")
    parser.add_argument("--html", action="store_true", help="Gerar relatório HTML")
    parser.add_argument("--audit", action="store_true", help="Gerar relatório AUDIT")

    args = parser.parse_args()

    config = carregar_configuracao()

    processor = BatchProcessor(
        config=config,
        gerar_html=args.html,
        gerar_audit=args.audit
    )

    # 📁 Pasta base de relatórios
    base_reports = Path("reports")

    if args.multi:
        # ---------------- LOTE ----------------
        pasta_saida = base_reports / "lote"
        processor.processar_lote(
            pasta_json=args.caminho,
            pasta_saida=pasta_saida
        )
    else:
        # ---------------- SINGLE ----------------
        pasta_saida = base_reports / "single"
        processor.processar_single(
            caminho_json=args.caminho,
            pasta_saida=pasta_saida
        )


if __name__ == "__main__":
    main()
