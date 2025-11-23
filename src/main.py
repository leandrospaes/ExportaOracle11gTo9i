import argparse
import logging
import sys

from .config import ProjectConfig
from .db_utils import test_connection
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

    test_parser = subparsers.add_parser("test", help="Testar conexões com os bancos")
    test_parser.add_argument("--source", action="store_true", help="Testar apenas conexão com banco 11g (origem)")
    test_parser.add_argument("--target", action="store_true", help="Testar apenas conexão com banco 9i (destino)")

    return parser


def handle_copy(args: argparse.Namespace) -> None:
    logger = logging.getLogger(__name__)
    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 20 + "COMANDO: COPY" + " " * 34 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    try:
        config = ProjectConfig.load(args.schemas)
        exporter = OracleExporter(config.source, config.target, batch_size=args.batch_size)
        exporter.copy(config.schemas)
        logger.info("")
        logger.info("✓ Operação de cópia finalizada com sucesso!")
    except Exception as e:
        logger.error("")
        logger.error("✗ Erro durante a operação de cópia: %s", e)
        raise


def handle_validate(args: argparse.Namespace) -> None:
    logger = logging.getLogger(__name__)
    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 15 + "COMANDO: VALIDATE" + " " * 33 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    try:
        config = ProjectConfig.load(args.schemas)
        validator = OracleValidator(config.source, config.target)
        report = validator.validate(config.schemas)
        
        logger.info("=" * 70)
        logger.info("RESUMO DA VALIDAÇÃO")
        logger.info("=" * 70)
        
        if report.all_valid():
            logger.info("")
            logger.info("✓✓✓ VALIDAÇÃO CONCLUÍDA SEM DIVERGÊNCIAS ✓✓✓")
            logger.info("")
            logger.info("Todos os objetos foram copiados corretamente:")
            logger.info("  • Tabelas: OK")
            logger.info("  • Sinônimos: OK")
            logger.info("  • Grants: OK")
            for obj_type in report.objects.keys():
                logger.info("  • %s: OK", obj_type.capitalize())
            logger.info("")
        else:
            logger.error("")
            logger.error("✗✗✗ FORAM ENCONTRADAS DIVERGÊNCIAS ✗✗✗")
            logger.error("")
            logger.error("Detalhes das divergências:")
            logger.error("")
            
            if report.tables.mismatches:
                logger.error("  TABELAS:")
                for mismatch in report.tables.mismatches:
                    logger.error("    • %s", mismatch)
            else:
                logger.info("  TABELAS: OK")
            
            if report.synonyms.mismatches:
                logger.error("  SINÔNIMOS:")
                for mismatch in report.synonyms.mismatches:
                    logger.error("    • %s", mismatch)
            else:
                logger.info("  SINÔNIMOS: OK")
            
            if report.grants.mismatches:
                logger.error("  GRANTS:")
                for mismatch in report.grants.mismatches:
                    logger.error("    • %s", mismatch)
            else:
                logger.info("  GRANTS: OK")
            
            for obj_type, detail in report.objects.items():
                if detail.mismatches:
                    logger.error("  %s:", obj_type.upper())
                    for mismatch in detail.mismatches:
                        logger.error("    • %s", mismatch)
                else:
                    logger.info("  %s: OK", obj_type.upper())
            
            logger.error("")
            logger.error("=" * 70)
            sys.exit(1)
    except Exception as e:
        logger.error("")
        logger.error("✗ Erro durante a operação de validação: %s", e)
        raise


def handle_test(args: argparse.Namespace) -> None:
    logger = logging.getLogger(__name__)
    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 18 + "COMANDO: TEST CONNECTION" + " " * 27 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    try:
        config = ProjectConfig.load("")
        
        test_source = not args.target or args.source
        test_target = not args.source or args.target
        
        results = []
        
        if test_source:
            logger.info("=" * 70)
            logger.info("TESTE DE CONEXÃO - BANCO ORIGEM (11g)")
            logger.info("=" * 70)
            logger.info("")
            result_source = test_connection(config.source, "Banco Origem (11g)")
            results.append(result_source)
            logger.info("")
        
        if test_target:
            logger.info("=" * 70)
            logger.info("TESTE DE CONEXÃO - BANCO DESTINO (9i)")
            logger.info("=" * 70)
            logger.info("")
            result_target = test_connection(config.target, "Banco Destino (9i)")
            results.append(result_target)
            logger.info("")
        
        # Resumo final
        logger.info("=" * 70)
        logger.info("RESUMO DOS TESTES")
        logger.info("=" * 70)
        logger.info("")
        
        all_success = True
        for result in results:
            status = "✓ SUCESSO" if result["success"] else "✗ FALHOU"
            logger.info("%s - %s", status, result["label"])
            logger.info("  DSN: %s", result["dsn"])
            logger.info("  Usuário: %s", result["user"])
            
            if result["success"]:
                db_info = result["database_info"]
                logger.info("  Versão: %s", db_info.get("version", "N/A"))
                logger.info("  Banco: %s", db_info.get("database_name", "N/A"))
            else:
                error = result["error"]
                logger.error("  Erro: %s (código: %s)", error.get("message", "Desconhecido"), error.get("code", "N/A"))
                all_success = False
            logger.info("")
        
        if all_success:
            logger.info("✓✓✓ TODAS AS CONEXÕES TESTADAS COM SUCESSO ✓✓✓")
            logger.info("")
        else:
            logger.error("✗✗✗ ALGUMAS CONEXÕES FALHARAM ✗✗✗")
            logger.error("")
            sys.exit(1)
            
    except Exception as e:
        logger.error("")
        logger.error("✗ Erro durante o teste de conexão: %s", e)
        raise


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "copy":
        handle_copy(args)
    elif args.command == "validate":
        handle_validate(args)
    elif args.command == "test":
        handle_test(args)


if __name__ == "__main__":
    main()

