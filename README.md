# status-page

O **status-page** é uma aplicação HTTP ultra-leve para exibir o status básico do host Linux (ou WSL) em tempo real.

É ideal para servidores caseiros e ambientes de laboratório, oferecendo uma visão rápida do estado da máquina diretamente no navegador.

## O que é exibido

- Hostname
- Sistema Operacional
- Endereço IP
- Uptime
- Uso de CPU (%)
- Memória (usado / total + %)
- Disco (usado / total + %)
- Timestamp da última atualização

A página é atualizada automaticamente a cada **30 segundos**.

## Pré-requisitos

- Docker
- Linux ou WSL2

---

## Configuração (obrigatória)

A aplicação utiliza autenticação simples (login por página).

As credenciais devem ser definidas em um arquivo `.env`.

### Criar o arquivo `.env`

```bash
cat <<EOF > "$HOME/.env"
STATUS_USER=admin
STATUS_PASS=password
STATUS_SECRET=chave_randomica
EOF
```

## Uso rápido (recomendado)

```bash
docker run -d \
  --name status-page \
  --restart unless-stopped \
  --network host \
  --env-file "$HOME/.env" \
  -v /etc/hostname:/host/etc/hostname:ro \
  -v /proc:/host/proc:ro \
  -v /:/host:ro \
  -v /etc/localtime:/etc/localtime:ro \
  diegofnunesbr/status-page:latest
```

## Acesse no navegador

http://<IP_DO_HOST>/

## Observações importantes

- Não utilize `-p 80:80`.
- O container usa `--network host` para refletir corretamente o IP e recursos do host.
- Não há coleta em background.
- As métricas são calculadas somente quando a página é acessada.
- Sessão expira automaticamente após 30 minutos de inatividade.
- Consumo mínimo de recursos: CPU: ~0% | Memória: ~20–30 MB.

## Build local (opcional)

```bash
git clone https://github.com/diegofnunesbr/status-page
docker build -t diegofnunesbr/status-page:latest status-page
```

## Publicação no Docker Hub

```bash
docker login
docker push diegofnunesbr/status-page:latest
```

## Remoção

### Remover o container

```bash
docker rm -f status-page
```

### Remover a imagem

```bash
docker rmi diegofnunesbr/status-page:latest
```

### Remover o arquivo `.env`

```bash
rm -f "$HOME/.env"
```

## Licença

MIT
