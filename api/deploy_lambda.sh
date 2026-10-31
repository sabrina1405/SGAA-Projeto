#!/usr/bin/env bash
# Publica a API na AWS Lambda com o AWS SAM, em homologação ou produção.
#
# Uso: ./deploy_lambda.sh <homolog|prod>
#
# O SAM roda na imagem oficial, pelo Docker, sem instalar nada na máquina. As
# credenciais e o bucket dos pacotes vêm de api/.aws.env (fora do Git). As
# migrações novas são aplicadas antes, com ./aplicar_migracoes.sh.
set -euo pipefail

cd "$(dirname "$0")"

IMAGEM_SAM="public.ecr.aws/sam/build-python3.13:1.167.0-x86_64"
FONTE="build/lambda"

ambiente="${1:-}"
case "$ambiente" in
    homolog | prod) ;;
    *) echo "Uso: $0 <homolog|prod>" >&2; exit 1 ;;
esac

if [ -n "$(git status --porcelain)" ]; then
    echo "Há alterações não commitadas; o deploy sai sempre de um commit." >&2
    exit 1
fi
if [ "$ambiente" = prod ] && [ "$(git branch --show-current)" != main ]; then
    echo "Produção só é publicada a partir da main." >&2
    exit 1
fi
if [ ! -f .aws.env ]; then
    echo "Crie api/.aws.env (ver docs/deploy_aws_lambda.md)." >&2
    exit 1
fi
set -a
# shellcheck disable=SC1091
. ./.aws.env
set +a
: "${AWS_ACCESS_KEY_ID:?defina no .aws.env}"
: "${AWS_SECRET_ACCESS_KEY:?defina no .aws.env}"
: "${SGAA_DEPLOY_BUCKET:?defina no .aws.env}"
export AWS_DEFAULT_REGION=us-east-1

if ! command -v poetry >/dev/null 2>&1 && [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    . .venv/bin/activate
fi
command -v poetry >/dev/null 2>&1 || { echo "poetry não encontrado" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker não encontrado" >&2; exit 1; }

echo "Publicando $(git rev-parse --short HEAD) em $ambiente."
echo "Migração nova? Rode ./aplicar_migracoes.sh antes."

# Só o que a Lambda precisa: sem testes, scripts, .venv nem .env.
rm -rf "$FONTE"
mkdir -p "$FONTE"
cp -r src index.py lambda_handler.py lambda_tarefa.py "$FONTE"/
rm -rf "$FONTE/src/scripts"
find "$FONTE" -name __pycache__ -type d -prune -exec rm -rf {} +
poetry export -f requirements.txt --output "$FONTE/requirements.txt" \
    --without-hashes --only main

tty_flag=()
[ -t 0 ] && tty_flag=(-it)
docker run --rm "${tty_flag[@]}" \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
    -e SAM_CLI_TELEMETRY=0 \
    -v "$PWD":/api -w /api \
    "$IMAGEM_SAM" \
    bash -c 'set -e
        sam validate --lint
        sam build
        sam deploy --config-env "$1" --s3-bucket "$2"
        aws cloudformation describe-stacks --stack-name "sgaa-api-$1" \
            --query "Stacks[0].Outputs" --output table 2>/dev/null || true' \
    _ "$ambiente" "$SGAA_DEPLOY_BUCKET"

poetry run python -m src.scripts.limpar_pacotes_deploy "$SGAA_DEPLOY_BUCKET" "$ambiente"
