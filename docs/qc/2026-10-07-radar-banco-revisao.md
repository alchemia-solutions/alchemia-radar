# Code Quality Gate — alchemia-radar (integração no banco da VM) — 2026-10-07

Revisora: Ada (`alchemia-quality-gate`). Só leitura; nenhum comando rodou na VM, nenhum git de escrita. Segunda tentativa do dia
(a primeira travou sem produzir nada).

**Escopo revisado (árvore com diff sem commit):**
- `pipeline/agendador.py`, `pipeline/tests/test_agendador.py`, `pipeline/tests/test_migrar_para_postgres.py`
- `deploy/README.md` (addendum) e `deploy/2026-10-07-janela-radar-banco.md` (roteiro J1 a J9, lido como código de produção)
- `docs/HISTORY.md` (Radar), e no System: `compose.yaml` (serviço `radar`) e `docs/HISTORY.md`
- Cruzado com o que o roteiro invoca: `Dockerfile`, `.dockerignore`, `pipeline/migrar_para_postgres.py`, `pipeline/armazenamento_pg.py`,
  `pipeline/run_all.py`, `alchemia-tech/infra/servers/vm-oracle/{leitura.sh,backup-system-prod.sh,restaurar-system-prod.sh,radar-pull.sh,comum.sh}`,
  `alchemia-system/packages/core/sql/papeis.sql`, `packages/core/drizzle/0024_radar.sql`, `docs/architecture/deploy-v0-8-janela.md`.

**Não coberto:** a VM em si (tudo o que depende do estado dela está em "Não verificado"); `typecheck`/`verify` do System; os 20 testes que
exigem Postgres; os diffs de `alchemia-system/AGENTS.md` e `README.md` (estão na árvore, fora da lista do pedido; só li o diff, não os revisei).

## Medições desta passada

| O quê | Resultado |
|---|---|
| Suíte do Radar sem banco (`pipeline/.venv`, Python 3.11, `unittest discover -s tests`) | `Ran 60 tests ... OK (skipped=20)`: 40 passam, 20 pulados por falta de Postgres. Bate com o que o `docs/HISTORY.md` declara para "sem o banco". Com banco não rodei. |
| `tests.test_agendador` isolado | 12 testes, OK, nenhum pulado: o tzdata existe nesta máquina, então a prova do fuso rodou de verdade. |
| `python -m pipeline.agendador --proximos 3` sobre uma cópia da árvore montada como o `.dockerignore` monta a imagem (sem `data/`, `logs/`, `tests/`) | 21:00 UTC de hoje, 09:00 e 15:00 UTC de amanhã. |
| `migrar_para_postgres --pacote ... --dry-run` sobre a mesma cópia, sem `DATABASE_URL_RADAR` | saída 0, `radar.carga.montada` emitido: o caminho do pacote não depende de nada que a imagem exclui. |
| sha256 do pacote em `alchemia-workdata/radar/` | `4b16978411ef980f27837a990cbb4d118a5cf7cedce6c830642b572cf7f64255`, 6.567.614 bytes: igual ao roteiro. |
| Conteúdo do pacote (lido com `gzip` + `json`) | 9.247 itens, todos de `dedupe_key` única; 182 execuções; 13 newsletters; catálogos 20/9/28/24; `ref` `origin/main`, `sha` `b1236f6d7d7e`; `export_do_supabase.lido = false`; `ausentes_na_carga` 0 nos dois commits de 2026-09-07. Todos os números do roteiro conferem. |
| `security_baseline.py segredos` sobre `alchemia-radar` | `segredos OK ... 335 arquivos varridos, nenhum formato de credencial` (1 exceção documentada). |

## O que sobreviveu à tentativa de refutar (sem achado)

- **Conversão de fuso.** `agendador.py` não usa `zoneinfo`: `para_utc(HORARIOS_LOCAIS, -3)` é aritmética de inteiros em módulo 24, calculada no
  import. A imagem `python:3.12-slim` não precisa de `tzdata`, e o `.dockerignore` nem leva os testes (que usam `zoneinfo`) para a imagem.
  O teste `test_o_disparo_em_utc_e_a_hora_de_parede_de_brasilia` prova o contrário do código: vê cada disparo em `America/Sao_Paulo` pelo tzdata e
  compara com `HORARIOS_LOCAIS`, e confere que o deslocamento é `FUSO_LOCAL_UTC_H`. America/Sao_Paulo sem horário de verão desde 2019: verdade.
- **Sem disparo duplo, sem horário pulado.** `proximo_horario` é estritamente `>` (`agendador.py:73`) e o laço só sai da espera com `falta <= 0`
  (`:115`); o filho só nasce depois disso, e ao terminar o próximo alvo sai de `now()`, sempre posterior. Coleta que passa de um horário pula o seguinte
  (declarado na docstring) e a trava consultiva do Postgres cobre a sobreposição. Virada de dia e de mês: `agora + timedelta(days=dia)`.
- **`${RADAR_HORARIOS_UTC:-}`.** O Compose entrega a variável vazia, `os.environ.get(...) or PADRAO_UTC` cai no padrão, e `PontoUnico` testa exatamente isso
  pela `main` real.
- **Teste de `test_5`.** A troca de data fixa por `now()` corrige um defeito real do teste (snapshots reais de 06 e 07/10 ganhavam a view por `terminada_em`);
  coerente com `0024_radar.sql:67-70` (`ORDER BY terminada_em DESC, id DESC`).
- **Papel `alchemia_radar`.** Sem `DELETE` em `radar.item`/`execucao`/`newsletter` (`papeis.sql:238-246`; só `radar.catalogo` tem): o roteiro está certo ao
  dizer que reverter a carga é restaurar o dump.
- **Idempotência da carga.** `test_3_segunda_carga_nao_muda_nada` carrega a segunda vez **pelo pacote** (`salvar_pacote` + `ler_pacote`), o caminho que a
  janela usa, e exige 0/0/0 e `depois` igual. (Rodado pelo autor contra Postgres 18.3 segundo o HISTORY; não reproduzido aqui.)
- **Nenhum segredo impresso pelos comandos do roteiro.** O `grep` do `producao.env` casa uma variável só; `sql` roda só `select count`/`select id,...`;
  `evento("radar.carga.falhou")` passa por `sem_segredo`; o script de backup só imprime o caminho.
- **Cadeia de `--no-deps`.** Confere com `compose.yaml`: `radar` depende de `papeis-final`, que depende de `migrar` (`image: alchemia-system:${APP_RELEASE:-sem-release}`,
  `pull_policy: never`). O `entrypoint` com `exit 64` vale também no `run`. `leitura.sh` tem todos os itens usados (`ready ps imagens timers estado releases coleta logs radar --linhas N`).
  O `sql()` funciona: o serviço `db` define `POSTGRES_USER` e `POSTGRES_DB`. As funções `rc`/`sql` expandem `$RADAR_SHA`/`$1` na chamada, não na definição.
- **Backup antes de qualquer escrita no banco.** J2 vem antes de J5/J6; J3 e J4 só escrevem arquivo e imagem.

## Achados

### 🔴 Bloqueante
Nenhum no código nem no roteiro. Reconciliação com o `REVIEW.md`: o 🔴 da linha do Radar (2026-08-19, `feed_collector._collect_section` descartando os feeds bons)
está corrigido desde 2026-08-31 (`common.ColetaParcial`, `docs/HISTORY.md`, addendum de 2026-08-31; o tipo é usado em `arxiv_collector.py:227`), e a linha antiga deixou de contá-lo como aberto.

### 🟡 Importante (corrigir o texto do roteiro antes de colar; nenhum muda código)

- **A1. `deploy/2026-10-07-janela-radar-banco.md:79` (J2) e `:236` (Voltar tudo) — `sudo` onde a rotina testada não usa `sudo`.** O backup roda como `ubuntu` no
  timer (`backup-system-prod.service:13-14`, `User=ubuntu`) e nas janelas anteriores (`deploy-v0-8-janela.md:33,54`: `backup-system-prod.sh --rotulo manual`); o
  restaurador usa `sudo` só por dentro, para o `systemctl` (`restaurar-system-prod.sh:197,303`) e foi ensaiado sem ele (`2026-10-03-ensaio-rollback-v7.md:59-60`).
  Evidência: o script tem `umask 077` (`backup-system-prod.sh:90`) e nenhum `--config`/`RCLONE_CONFIG` (`grep` vazio em `enviar-backup.sh`/`comum.sh`). Sob `sudo`
  o `HOME` é `/root`, então o rclone procura o remote `drive.file` em `/root/.config/rclone`, não acha, e o script, por desenho, "sai 0, avisa" quando o envio
  falha: o dump `pre-radar`, que é o rollback de tudo, pode ficar **sem a cópia para fora da VM**, com saída 0 e o `estado` mostrando `ultimo_ok` novo. Além disso o
  dump nasce `root:root` 0600, e o restaurador ensaiado roda como `ubuntu`. Cenário: o fundador cola J2, vê `dump ok`, segue; o rollback (A3) depois falha por permissão.
  Direção: J2 sem `sudo` (`vm '/usr/local/lib/alchemia/backup-system-prod.sh --rotulo pre-radar'`), e conferir no `estado` o `envio` além de `ultimo_ok`.
  (Premissa a confirmar na VM: o `HOME` sob `sudo` no Ubuntu da VM; o resto vem do disco.)
- **A2. `...janela-radar-banco.md:180` (J7 paliativo) e `:201` (J8) — `echo ... >> deploy/producao.env` sem garantir que o arquivo termina em `\n`.** Se a última linha
  do `producao.env` não terminar em quebra de linha, a linha nova **cola** na anterior (`PG_SENHA_...=xyzRADAR_FONTE=banco`). No J8 isso corrompe uma senha que o `app` lê,
  o `--wait` falha, e o "rollback imediato" (`sed -i 's/^RADAR_FONTE=.*/...'`) já não casa, porque a linha não começa mais por `RADAR_FONTE=`: o app fica fora do ar com o
  rollback escrito inoperante. O `comum.sh` lê "a última ocorrência vence", então o arquivo é de fato editado à mão. Direção: antes de cada `>>`,
  `[ -z "$(tail -c1 f)" ] || echo >> f`, e copiar `producao.env` para `producao.env.pre-radar` (modo 600) antes do primeiro `sed -i`/`>>`.
  (Não verificado: se o arquivo da VM termina em `\n`; não li o arquivo e o roteiro, corretamente, não o imprime.)
- **A3. `...janela-radar-banco.md:236` — a linha "A carga e tudo o mais" da tabela "Voltar tudo" não diz o que o rollback custa.** Restaurar `pre-radar` volta o **banco inteiro do
  System** ao instante de J2: tudo o que os colaboradores gravaram no app (jogo, CRM, papéis) entre J2 e o rollback se perde, e o roteiro só fala de "a carga". Também: (i) o
  restaurador é interativo (`restaurar-system-prod.sh` pede confirmação) e a função `vm` usa `ssh` sem `-t`; (ii) o script religa o `radar` ao fim se o banco restaurado tiver o esquema
  `radar` (`restaurar-system-prod.sh:294-300`), o dump `pre-radar` já tem (0024), então o agendador volta a coletar sobre o banco "desfeito". Direção: escrever o custo, `ssh -t`, sem
  `sudo` (A1), e `rc stop radar` depois da restauração se a intenção é desfazer a integração.
- **A4. `...janela-radar-banco.md:93-96` (J3) — a conferência do sha256 é um olho humano comparando duas linhas, não uma trava.** O hash correto aparece só como texto ("`4b169784...64255`") e a carga (J5)
  não o verifica; o pacote tem um `sha` de commit, não um hash do próprio arquivo. Um `scp` truncado ou o arquivo errado seguem para o dry-run se o fundador não comparar. Direção:
  `vm "echo '4b16978411ef980f27837a990cbb4d118a5cf7cedce6c830642b572cf7f64255  /home/ubuntu/radar-carga/radar-carga.json.gz' | sha256sum -c -"` (saída não zero = parar), com o hash do pacote refeito no lugar quando for o caso.
- **A5. `...janela-radar-banco.md:60-70` (J1) — o J1 não confirma as premissas de que J5/J7/J8 dependem.** Só olha o que o menu de leitura mostra. Faltam, por leitura que não imprime segredo:
  (i) que o `compose.yaml` do release no ar (`c602f62111ca`) **tem** o serviço `radar` com o `entrypoint` de senha (`grep -n "^  radar:" compose.yaml`); (ii) que `PG_SENHA_RADAR`
  existe no `producao.env` (`grep -c '^PG_SENHA_RADAR=.' ...`, só a contagem); (iii) o valor atual de `RADAR_FONTE`: no `compose.yaml` o padrão é **`banco`** (`:-banco`, linha 154), então se o `producao.env`
  não tiver a variável o app **já** está lendo o banco vazio ("carga pendente") e a premissa "o app ainda lê `local`, a tela não mudou" (J5, linha 134 e 144) é falsa. O J8 só descobre isso no meio.
  Direção: três greps de leitura no J1, com a regra "o que divergir, pare".

### 🟢 Sugestão

- `agendador.py:88` — `os.environ.get("RADAR_HORARIOS_UTC") or PADRAO_UTC` aceita `" "` (só espaço) como valor: é truthy, `ler_horarios` levanta "vazio", e o contêiner (`restart: unless-stopped`) entra em laço de reinício.
  Direção: `(os.environ.get(...) or "").strip() or PADRAO_UTC`, mais um caso em `PontoUnico`.
- `agendador.py:9-10` diz "mexer nessas duas constantes", mas são três (`HORARIOS_LOCAIS`, `FUSO_LOCAL`, `FUSO_LOCAL_UTC_H`), e `FUSO_LOCAL` só é lido pelo teste. A única guarda contra os dois fusos divergirem é aquele teste,
  que faz `skipTest` sem tzdata (`test_agendador.py`, `ZoneInfoNotFoundError`): numa máquina sem tzdata o elo fica sem prova, calado. Direção: pôr `tzdata` em dev-requirements, ou falhar em vez de pular.
- `test_agendador.py:69` (`test_sombra_deslocada_vinte_minutos`) — nome de um desenho que a decisão (gi) revogou; o teste continua válido (ordena `ler_horarios`), o nome engana. Renomear.
- `...janela-radar-banco.md:83` — "a última linha `dump ok`": o script imprime `dump ok` na linha 112 e depois ainda vem o envio e a retenção; é "a linha `dump ok`".
- `...janela-radar-banco.md:208` — o rollback do J8 fixa `RADAR_FONTE=local`; o valor anterior só está no que o fundador viu na tela. Com A2 (cópia `.pre-radar`) o rollback passa a ser restaurar o arquivo.
- `...janela-radar-banco.md:150` — `rc run ... radar python -m pipeline.run_all | grep` mantém a sessão `ssh` aberta por cerca de 3 minutos; se a conexão cair, o `run` pode morrer no meio (a execução órfã é fechada pela próxima, `fechar_orfas`, então é seguro, mas
  o fundador veria um `radar.execucao` em `rodando`). `ServerAliveInterval=30` ajuda; considerar `-d` com `logs`.
- `...janela-radar-banco.md:20-22` — a lista de "arquivos mudados no repositório do Radar" omite `pipeline/data/discord/README.md`, que está na árvore. Sem consequência para a janela; o commit tem de incluí-lo (ou ele fica fora do `push`).
- `...janela-radar-banco.md:242-244` — diz que a mudança do `compose.yaml` "é da Hipátia"; ela já está na árvore do System (diff de `compose.yaml`), só falta commit e release. O J7 cobre os dois casos, o texto ficará velho no commit.
- `...janela-radar-banco.md:227` — o `lerDoBanco` lê `radar.item` inteiro (9.247+ linhas) sem `LIMIT`, e o roteiro troca produção para `banco` antes de medir F6. O rollback do J8 cobre; mandar o Hopper medir em dev contra o banco carregado seria mais barato do que em produção.

## Veredito

- **Pode ir a commit?** Sim. `agendador.py`, os dois testes, o `compose.yaml` do System e os textos não têm achado bloqueante; a suíte sem banco dá 60 testes, 40 OK e 20 pulados, como declarado; a conversão de fuso não depende de tzdata na imagem; o agendador não dispara
  duas vezes nem pula horário. O commit do Radar também precisa levar `pipeline/data/discord/README.md`. O `push` e o commit são do fundador.
- **A janela pode rodar como escrita?** Sim, depois das correções de **texto** A1 a A5 no roteiro (nenhuma muda código). A1 e A2 são as que podem custar uma noite: um rollback sem cópia fora da VM e um `producao.env` corrompido com rollback inoperante. Sem elas, não cole J2 nem J8.
  Cada passo tem conferência e rollback escritos, a carga é idempotente por teste, e o `pre-radar` vem antes de qualquer escrita no banco.
- Escalonamento: nada aqui pede o fundador além do que o roteiro já pede (a decisão (gi) é dele e o roteiro cumpre a V7-6). A3 toca restauração do banco de produção: é dele ou do Gabriel.

## Não verificado

- Tudo o que depende do estado da VM: `sudo` sem senha para a chave de operação, `HOME` sob `sudo`, se o `producao.env` termina em `\n`, a versão do Compose e a auto-detecção de TTY no `run` sem `-T`, o build para aarch64 (`psycopg[binary]`), o valor de `RADAR_FONTE` hoje, o serviço `radar` no `compose.yaml` do release no ar.
- Os 20 testes que exigem Postgres (inclui `test_3` e a troca de `test_5`): rodei só o lado sem banco.
- `npm run verify`, typecheck e lint do System; o diff de `alchemia-system/AGENTS.md` e `README.md`.
- Que o 06:00/12:00/18:00 de Brasília seja o horário que o fundador quer: é decisão dele (gi), só conferi a aritmética.
