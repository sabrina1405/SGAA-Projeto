#!/usr/bin/env bash
# Aplica as migrações do Alembic em um banco remoto 
# (produção ou homologação no Supabase).
#
# Uso: ./aplicar_migracoes.sh
#
# Pede a URL do Session pooler (porta 5432) sem exibi-la nem gravá-la no
# histórico do shell, mostra o estado do banco e só aplica após confirmação.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v poetry >/dev/null 2>&1 && [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    . .venv/bin/activate
fi
command -v poetry >/dev/null 2>&1 || { echo "poetry não encontrado" >&2; exit 1; }

read -rsp "URL do Session pooler (porta 5432): " url
echo
[ -n "$url" ] || { echo "URL vazia; nada foi feito" >&2; exit 1; }

# O Supabase entrega postgresql:// (ou postgres://); o projeto usa o driver psycopg.
case "$url" in
    postgresql+psycopg://*) ;;
    postgresql://*) url="postgresql+psycopg://${url#postgresql://}" ;;
    postgres://*) url="postgresql+psycopg://${url#postgres://}" ;;
    *) echo "URL não começa com postgresql://" >&2; exit 1 ;;
esac

case "$url" in
    *:6543/*)
        echo "Essa é a URL do Transaction pooler (6543), que é a da API." >&2
        echo "Para migrações use a do Session pooler (5432)." >&2
        exit 1
        ;;
esac

export DATABASE_URL="$url"
# O Alembic não usa a chave, mas a configuração da API exige que ela exista.
export SECRET_KEY="${SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')}"

# Destino sem usuário e senha.
destino="${url##*@}"
echo "Destino: $destino"
echo
echo "Revisão atual do banco:"
poetry run alembic current
echo
echo "Revisão mais recente do código:"
poetry run alembic heads
echo

read -rp "Aplicar as migrações em $destino? Digite 'sim' para confirmar: " resposta
[ "$resposta" = "sim" ] || { echo "Cancelado; nada foi aplicado."; exit 1; }

poetry run alembic upgrade head
echo
echo "Revisão do banco depois da migração:"
poetry run alembic current
