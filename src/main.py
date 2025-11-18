import argparse
import logging
import sys

from .config import ProjectConfig
from .exporter import OracleExporter
from .validator import OracleValidator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exporta dados de um Oracle 11g para 9i e valida a cópia.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    copy_parser = subparsers.add_parser("copy", help="Copiar dados do 11g para o 9i")
    copy_parser.add_argument("--schemas", help="Lista de schemas separados por vírgula", default="")
    copy_parser.add_argument("--batch-size", type=int, default=500, help="Tamanho do lote de inserção")

    validate_parser = subparsers.add_parser("validate", help="Validar dados copiados")
    validate_parser.add_argument("--schemas", help="Lista de schemas separados por vírgula", default="")

    return parser


def handle_copy(args: argparse.Namespace) -> None:
    config = ProjectConfig.load(args.schemas)
    exporter = OracleExporter(config.source, config.target, batch_size=args.batch_size)
    exporter.copy(config.schemas)


def handle_validate(args: argparse.Namespace) -> None:
    config = ProjectConfig.load(args.schemas)
    validator = OracleValidator(config.source, config.target)
    report = validator.validate(config.schemas)
    if report.all_valid():
        logging.info("Validação concluída sem divergências.")
    else:
        logging.error("Foram encontradas divergências:")
        logging.error("Tabelas: %s", report.tables.mismatches or "ok")
        logging.error("Sinônimos: %s", report.synonyms.mismatches or "ok")
        logging.error("Grants: %s", report.grants.mismatches or "ok")
        for obj_type, detail in report.objects.items():
            logging.error("%s: %s", obj_type, detail.mismatches or "ok")
        sys.exit(1)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "copy":
        handle_copy(args)
    elif args.command == "validate":
        handle_validate(args)


if __name__ == "__main__":
    main()

