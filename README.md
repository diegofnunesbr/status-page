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

> Atualização automática da página a cada **30 segundos**.

## Pré-requisitos

- Docker
- Linux ou WSL2

---

## Uso rápido (recomendado)

```bash
docker run -d \
  --name status-page \
  --restart unless-stopped \
  --network host \
  -e STATUS_USER=admin \
  -e STATUS_PASS=password \
  -e STATUS_SECRET=$(openssl rand -hex 32) \
  -v /etc/hostname:/host/etc/hostname:ro \
  -v /proc:/host/proc:ro \
  -v /:/host:ro \
  -v /etc/localtime:/etc/localtime:ro \
  diegofnunesbr/status-page:latest
```

## Acesse no navegador

http://192.168.1.2/

> Substitua `192.168.1.2` pelo IP do seu host.

## Observações importantes

- A Sessão expira automaticamente após **30 minutos** de inatividade.
- O container usa `--network host` para refletir corretamente o IP e recursos do host.
- Não há coleta em background (as métricas são calculadas somente quando a página é acessada).
- Consumo mínimo de recursos: CPU: ~0% | Memória: ~20–30 MB.

## Build local (opcional)

```bash
git clone https://github.com/diegofnunesbr/status-page
cd status-page
docker build -t diegofnunesbr/status-page:latest .
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

## Licença

MIT
