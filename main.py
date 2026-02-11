import argparse
import sys
from pathlib import Path

from nfcom_2026.batch_processor import BatchProcessor
from nfcom_2026.config import carregar_configuracao


def main():
    parser = argparse.ArgumentParser(description="Validador NFCom - Reforma Tributária")

    parser.add_argument("caminho", help="Arquivo JSON ou diretório")
    parser.add_argument("--multi", action="store_true", help="Processar diretório (lote)")
    parser.add_argument("--html", action="store_true", help="Gerar relatório HTML")
    parser.add_argument("--audit", action="store_true", help="Gerar auditoria TXT")
    parser.add_argument("--pdf", action="store_true", help="Gerar PDF a partir do HTML")

    args = parser.parse_args()

    config = carregar_configuracao()

    processor = BatchProcessor(
        config=config,
        gerar_html=args.html,
        gerar_audit=args.audit,
        gerar_pdf=args.pdf
    )

    caminho = Path(args.caminho)

    if args.multi:
        resumo = processor.processar_lote(caminho)
        # Falha no CI se houver qualquer divergência no lote
        if resumo.get("Status") != "OK":
            sys.exit(1)
        sys.exit(0)
    else:
        linha = processor.processar_single(caminho)
        # Falha no CI se o arquivo único for divergente
        if linha.get("Status") != "OK":
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
