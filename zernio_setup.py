#!/usr/bin/env python3
"""Onboarding e diagnóstico do Zernio — habilita a publicação.

Fluxo recomendado (faça uma vez):

  1) python zernio_setup.py doctor               # checa chave, rede e conexão
  2) python zernio_setup.py create-profile --name "Minha Marca" --save
  3) python zernio_setup.py connect --platform instagram   # abra a URL no navegador
  4) python zernio_setup.py accounts --save      # salva o _id da conta de Instagram

Depois disso o post.py usa a conta salva automaticamente (.zernio.json).
"""

from __future__ import annotations

import argparse
import json
import sys

from instagram.config import load_dotenv, load_config, save_config, CONFIG_PATH
from instagram.zernio_client import ZernioClient, ZernioError

EGRESS_HINT = (
    "Parece bloqueio de rede do ambiente (egress). Adicione 'zernio.com' ao "
    "allowlist de egress do seu ambiente de execução, ou rode este comando "
    "na sua máquina local."
)


def _client() -> ZernioClient:
    return ZernioClient()


def _is_egress_error(err: Exception) -> bool:
    return "allowlist" in str(err).lower() or "egress" in str(err).lower()


def cmd_doctor(args) -> int:
    print("== Diagnóstico do Zernio ==")
    import os

    has_key = bool(os.environ.get("ZERNIO_API_KEY"))
    print(f"[{'ok' if has_key else 'x'}] ZERNIO_API_KEY {'configurada' if has_key else 'AUSENTE (defina no .env)'}")
    if not has_key:
        return 1

    cfg = load_config()
    print(f"[i] Config salva ({CONFIG_PATH.name}): {cfg or '(vazia)'}")

    try:
        profiles = _client().list_profiles()
        n = len(profiles.get("profiles", profiles)) if isinstance(profiles, (dict, list)) else 0
        print(f"[ok] API acessível. Profiles encontrados: {n}")
    except ZernioError as e:
        flag = "x"
        print(f"[{flag}] Falha ao falar com a API: {e}")
        if _is_egress_error(e):
            print(f"     -> {EGRESS_HINT}")
        return 1

    ig = None
    try:
        ig = _client().find_instagram_account()
    except ZernioError:
        pass
    if ig:
        print(f"[ok] Instagram conectado: {ig.get('username')} ({ZernioClient.account_id(ig)})")
    else:
        print("[x] Nenhuma conta de Instagram conectada. Rode: create-profile -> connect -> accounts")
    return 0


def cmd_profiles(args) -> int:
    data = _client().list_profiles()
    profiles = data.get("profiles", data) if isinstance(data, dict) else data
    for p in profiles or []:
        print(f"- {p.get('_id')}  |  {p.get('name')}")
    return 0


def cmd_create_profile(args) -> int:
    res = _client().create_profile(args.name, args.description)
    prof = res.get("profile", res) if isinstance(res, dict) else res
    pid = prof.get("_id") if isinstance(prof, dict) else None
    print(f"[ok] Profile criado: {pid}  ({args.name})")
    if args.save and pid:
        save_config(profile_id=pid)
        print(f"     salvo em {CONFIG_PATH.name}")
    return 0


def cmd_connect(args) -> int:
    profile_id = args.profile_id or load_config().get("profile_id")
    if not profile_id:
        print("[x] Informe --profile-id ou crie um profile antes (create-profile --save).", file=sys.stderr)
        return 1
    res = _client().get_connect_url(args.platform, profile_id)
    url = res.get("authUrl") or res.get("auth_url") if isinstance(res, dict) else None
    if not url:
        print(f"[x] Resposta inesperada: {res}", file=sys.stderr)
        return 1
    print("Abra esta URL no navegador para autorizar a conexão:\n")
    print(f"    {url}\n")
    print("Depois de autorizar, rode: python zernio_setup.py accounts --save")
    return 0


def cmd_accounts(args) -> int:
    data = _client().list_accounts()
    accounts = data.get("accounts", data) if isinstance(data, dict) else data
    ig_id = None
    for a in accounts or []:
        plat = a.get("platform")
        aid = ZernioClient.account_id(a)
        print(f"- {plat:10} | {a.get('username', '?'):20} | {aid}")
        if str(plat).lower() == "instagram" and ig_id is None:
            ig_id = aid
            ig_user = a.get("username")
    if args.save and ig_id:
        save_config(instagram_account_id=ig_id, instagram_username=ig_user)
        print(f"\n[ok] Conta de Instagram salva em {CONFIG_PATH.name}: {ig_user} ({ig_id})")
    elif args.save:
        print("\n[x] Nenhuma conta de Instagram encontrada para salvar.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Onboarding/diagnóstico do Zernio")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Diagnostica chave, rede e conexão")
    sub.add_parser("profiles", help="Lista profiles")

    cp = sub.add_parser("create-profile", help="Cria um profile")
    cp.add_argument("--name", required=True)
    cp.add_argument("--description")
    cp.add_argument("--save", action="store_true", help="Salva o profile_id em .zernio.json")

    cn = sub.add_parser("connect", help="Gera a URL de OAuth para conectar uma conta")
    cn.add_argument("--platform", default="instagram")
    cn.add_argument("--profile-id", help="Usa o salvo em .zernio.json se omitido")

    ac = sub.add_parser("accounts", help="Lista contas conectadas")
    ac.add_argument("--save", action="store_true", help="Salva a conta de Instagram em .zernio.json")

    args = p.parse_args()
    handlers = {
        "doctor": cmd_doctor,
        "profiles": cmd_profiles,
        "create-profile": cmd_create_profile,
        "connect": cmd_connect,
        "accounts": cmd_accounts,
    }
    try:
        return handlers[args.cmd](args)
    except ZernioError as e:
        print(f"[ERRO Zernio] {e}", file=sys.stderr)
        if _is_egress_error(e):
            print(f"     -> {EGRESS_HINT}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
