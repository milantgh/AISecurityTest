# -*- coding: utf-8 -*-
"""aisec main command."""
import argparse
import io
import sys

# Force stdout/stderr to UTF-8 to avoid Windows GBK crashes.
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

from .cmd_list import add_list_parser, handle_list
from .cmd_validate import add_validate_parser, handle_validate
from .cmd_run import add_run_parser, handle_run
from .cmd_export import add_export_parser, handle_export
from .cmd_next_id import add_next_id_parser, handle_next_id
from .cmd_categories import add_categories_parser, handle_categories
from .cmd_check_name import add_check_name_parser, handle_check_name
from .cmd_show import add_show_parser, handle_show
from .cmd_gen import add_gen_parser, handle_gen
from .cmd_compose import add_compose_parser, handle_compose
from .cmd_transform import add_transform_parser, handle_transform
from .cmd_rewrite import add_rewrite_parser, handle_rewrite
from .cmd_pipeline import add_pipeline_parser, handle_pipeline
from .cmd_multimodal import add_multimodal_parser, handle_multimodal
from .cmd_autoscan import add_autoscan_parser, handle_autoscan   # 新增
from .cmd_recon import add_recon_parser, handle_recon             # 新增
from .cmd_probes import add_probes_parser, handle_probes          # 新增
from .cmd_vuln import add_vuln_parser, handle_vuln                # 新增


def build_parser():
    p = argparse.ArgumentParser(
        prog="aisec",
        description="AISecurityTest - AI Security Test System (v1.0)")
    p.add_argument("--version", action="store_true", help="show version")
    sub = p.add_subparsers(dest="cmd")

    add_list_parser(sub)
    add_validate_parser(sub)
    add_run_parser(sub)
    add_export_parser(sub)
    add_next_id_parser(sub)
    add_categories_parser(sub)
    add_check_name_parser(sub)
    add_show_parser(sub)
    add_gen_parser(sub)
    add_compose_parser(sub)
    add_transform_parser(sub)
    add_rewrite_parser(sub)
    add_pipeline_parser(sub)
    add_multimodal_parser(sub)
    add_autoscan_parser(sub)   # 新增
    add_recon_parser(sub)      # 新增
    add_probes_parser(sub)     # 新增
    add_vuln_parser(sub)       # 新增
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        from .._version import __version__, __app_name__
        print("%s %s" % (__app_name__, __version__))
        return 0

    if not args.cmd:
        parser.print_help()
        return 0

    handlers = {
        "list": handle_list,
        "validate": handle_validate,
        "run": handle_run,
        "export": handle_export,
        "next-id": handle_next_id,
        "categories": handle_categories,
        "check-name": handle_check_name,
        "show": handle_show,
        "gen": handle_gen,
        "compose": handle_compose,
        "transform": handle_transform,
        "rewrite": handle_rewrite,
        "pipeline": handle_pipeline,
        "multimodal": handle_multimodal,
        "autoscan": handle_autoscan,   # 新增
        "recon": handle_recon,          # 新增
        "probes": handle_probes,        # 新增
        "vuln": handle_vuln,            # 新增
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())