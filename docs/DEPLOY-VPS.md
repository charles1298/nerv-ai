# Deploy do NERV AI na VPS

A VPS **ja hospeda outros projetos**. Todo este roteiro foi desenhado para nao
encostar neles: nenhuma etapa reinicia servico existente, altera configuracao
alheia ou disputa as portas 80/443.

## O que esta stack ocupa

| Recurso | Valor | Compartilhado? |
|---|---|---|
| Porta no host | `127.0.0.1:18080` (`NERV_HTTP_PORT`) | Nao — loopback, uma so |
| Rede Docker | `nerv-ai-net` | Nao |
| Volumes | `nerv-ai-pgdata`, `nerv-ai-redisdata`, `nerv-ai-uploads` | Nao |
| Containers | `nerv-ai-db`, `-redis`, `-backend`, `-frontend`, `-nginx` | Nao |
| Portas 80 / 443 | **nao tocadas** | Seguem de quem ja usa |

Postgres e Redis nao publicam porta: existem so dentro de `nerv-ai-net`.

## 1. Pre-flight (roda antes de qualquer coisa, nao altera nada)

```bash
docker --version && docker compose version   # precisa existir
docker ps --format '{{.Names}}\t{{.Ports}}'  # o que ja roda
ss -tlnp | grep -E ':(80|443|18080)\b'       # quem tem 80/443 e se 18080 esta livre
docker network ls && docker volume ls        # confirma que nao ha nome nerv-ai-*
```

Se `18080` aparecer ocupada, escolha outra livre e ajuste `NERV_HTTP_PORT` no
`.env`. **Nao** libere a porta matando o processo de outro projeto.

## 2. Codigo e configuracao

```bash
git clone https://github.com/charles1298/nerv-ai.git /opt/nerv-ai
cd /opt/nerv-ai
cp .env.production.example .env
openssl rand -hex 32          # cole em JWT_SECRET_KEY
openssl rand -hex 24          # cole em POSTGRES_PASSWORD
nano .env                     # preencha AI_API_KEY e PUBLIC_BASE_URL
```

`PUBLIC_BASE_URL` precisa ser a URL final publica. Ela entra no **build** do
frontend (o Next grava as `NEXT_PUBLIC_*` no bundle); mudar depois exige
`--build` de novo, nao basta reiniciar.

## 3. Subir

```bash
cd /opt/nerv-ai/infra
docker compose --env-file ../.env -f docker-compose.prod.yml config   # valida
docker compose --env-file ../.env -f docker-compose.prod.yml up -d --build
docker compose -p nerv-ai ps
curl -s http://127.0.0.1:18080/api/health     # {"status":"ok","env":"production"}
```

As migrations rodam sozinhas no start (`alembic upgrade head`).

Dados de demonstracao (escola, usuarios, materias), se quiser:

```bash
# PYTHONPATH=/app porque o script espera o layout do repo (scripts/ ao lado de
# backend/), e na imagem o conteudo de backend/ e' a propria raiz /app.
docker compose -p nerv-ai exec -e PYTHONPATH=/app backend python scripts/seed_dev.py
```

## 3.1 Acesso provisorio por IP (sem dominio)

Para validar antes de existir DNS, publique a porta na interface publica:

```bash
# no .env
NERV_BIND=0.0.0.0
PUBLIC_BASE_URL=http://SEU.IP.AQUI:18080
```

```bash
ufw allow 18080/tcp
docker compose --env-file ../.env -f docker-compose.prod.yml up -d --build
```

O endereco vira `http://SEU.IP.AQUI:18080`.

**Isto e' HTTP puro.** Senha de aluno e professora trafegam em texto claro, e o
Docker publica a porta escrevendo iptables por cima do ufw — ela fica exposta de
verdade. Serve para conferir que a stack funciona; nao serve para uso real com
dado de escola. Assim que houver dominio, volte `NERV_BIND=127.0.0.1`, rode
`ufw delete allow 18080/tcp` e siga para a secao 4.

## 3.2 Trocar uma variavel de ambiente

Depois de editar o `.env`, **recrie** o container. `docker compose restart` NAO
serve: ele reinicia o processo reaproveitando o container antigo, que carrega o
ambiente com que foi criado — a variavel nova simplesmente nao chega, e o app
segue reclamando que ela nao existe.

```bash
cd /opt/nerv-ai/infra
docker compose --env-file ../.env -f docker-compose.prod.yml up -d backend
docker exec nerv-ai-backend printenv AI_API_KEY   # confirma que chegou
```

Isso vale para variavel de runtime (AI_API_KEY, MEM0_API_KEY, RESEND_API_KEY...).
Ja `PUBLIC_BASE_URL` entra no bundle do frontend em build time: alem do `up -d`,
exige `--build` do servico frontend.

## 4. Publicar no dominio (proxy que ja existe na VPS)

Isto **acrescenta** um site; nao mexe nos que ja estao la. Exemplo para nginx do
host — arquivo novo em `/etc/nginx/sites-available/nerv-ai`:

```nginx
server {
    listen 80;
    server_name nerv.seudominio.com.br;

    # Sem isto o proxy corta a foto antes de chegar no NERV.
    client_max_body_size 25m;

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade           $http_upgrade;
        proxy_set_header Connection        "upgrade";

        # Streaming SSE do tutor.
        proxy_buffering    off;
        proxy_read_timeout 300s;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/nerv-ai /etc/nginx/sites-enabled/
nginx -t                 # OBRIGATORIO: se falhar, NAO recarregue
systemctl reload nginx   # reload, nao restart — nao derruba os outros sites
certbot --nginx -d nerv.seudominio.com.br
```

`nginx -t` antes do reload e' o que protege os outros tres projetos: config
invalida nao entra no ar.

## 5. Rollback

Remove so o que e' do NERV, sem tocar em mais nada:

```bash
cd /opt/nerv-ai/infra
docker compose --env-file ../.env -f docker-compose.prod.yml down          # para
docker compose --env-file ../.env -f docker-compose.prod.yml down -v       # + apaga volumes
rm /etc/nginx/sites-enabled/nerv-ai && nginx -t && systemctl reload nginx
```

## Diferencas em relacao a Vercel

| | Vercel (hoje) | VPS |
|---|---|---|
| Upload de foto | nao persiste (disco read-only) | volume `nerv-ai-uploads`, servido em `/api/uploads/` |
| Tamanho de request | teto de 4,5 MB | 25 MB (ajustavel) |
| Rate limiting | Redis externo; sem ele, desligado na pratica | Redis na propria stack |
| Pool de conexao | `NullPool`, depende de pgBouncer | pool normal do SQLAlchemy |
| Cold start | a cada instancia fria | nenhum |
