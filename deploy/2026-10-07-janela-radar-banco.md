# Janela: o Radar coletando no banco da VM

> **Executada em 2026-10-07, resultado:** J1 a J9 feitos pelo fundador entre 20:51 e 21:05 UTC; a VM carregou o acervo (9.247 itens, 182 execuções) e coletou à mão a execução 183 (113 itens novos, estado `parcial`: `newsletters` e `biorxiv` com erro), o `radar` está no ar com o agendador em 09:00, 15:00 e 21:00 UTC (próximo: 2026-10-08T09:00Z) e o app lê `banco`; a sombra de 7 dias começou. Pendente: tela `/science/radar` conferida pelo fundador, primeira coleta agendada, o `biorxiv`, o paliativo de horário no `producao.env` e a virada (R6). Números e pendências: addendum de 2026-10-07 (noite) do `docs/HISTORY.md`. O texto abaixo é o roteiro como foi escrito.

Roteiro para o fundador colar, passo a passo. Decisão: `decisions-log` (gi), 2026-10-07 (a VM coleta, o agendador mora no
contêiner, 06:00, 12:00 e 18:00 de Brasília). Cumpre a V7-6 da spec v7 e a spec
`alchemia-tech/docs/specs/2026-10-02-bancos-radar-e-vault-na-vm.md` (Portão (ee)). O porquê de cada peça está em
[`README.md`](README.md) (R0 a R6) e na spec [`../docs/specs/2026-10-02-radar-na-vm-postgres.md`](../docs/specs/2026-10-02-radar-na-vm-postgres.md).

Legenda: **L** = só leitura (nada muda na VM). **M** = muda a VM, pela chave `alchemia-vm-operacao`. Nenhum agente roda
nenhum passo M. Os comandos saem do WSL do fundador. O estado de 2026-10-07 (menu de leitura, ~17h50 UTC): app e banco no
ar, 36 migrações aplicadas de 36, **sem contêiner nem imagem do Radar**, o esquema `radar` existe e, pelo registro da Tech,
nunca recebeu carga (0 execuções; o menu não consulta o banco, então isto não foi medido por mim).

O que esta janela **não** faz: não desliga o Actions, o Supabase nem o `radar-pull.timer` (R6, do fundador); não mexe em
`agendamentos-autorizados.json`. O Actions segue gravando o git em 06:40, 12:40 e 18:40 de Brasília; a VM grava o banco
40 minutos antes.

## Antes da janela (estação)

1. **Empurrar o Radar (fundador).** A imagem é construída pelo clone que o `radar-pull` puxa do GitHub, então o código novo
   do agendador (06:00, 12:00, 18:00 de Brasília) precisa estar no remoto antes do passo J4. Arquivos a commitar no repositório
   do Radar: `pipeline/agendador.py`, `pipeline/tests/test_agendador.py`, `pipeline/tests/test_migrar_para_postgres.py`,
   `pipeline/data/discord/README.md`, `deploy/README.md`, este arquivo, `docs/HISTORY.md` e `docs/qc/2026-10-07-radar-banco-revisao.md`.
   Nenhum agente dá `commit` nem `push`.
2. **O pacote do acervo.** Já montado em 2026-10-07 (18h24 UTC), a partir de `origin/main` = `b1236f6d7d7e`, fora do Drive:

   | | |
   |---|---|
   | Caminho | `C:\Users\AryelBezerra\alchemia-workdata\radar\radar-carga.json.gz` (no WSL: `/mnt/c/Users/AryelBezerra/alchemia-workdata/radar/radar-carga.json.gz`) |
   | Tamanho | 6.567.614 bytes |
   | sha256 | `4b16978411ef980f27837a990cbb4d118a5cf7cedce6c830642b572cf7f64255` |
   | Itens (chaves únicas) | 9.247 (o JSON do `origin/main` tem 5.783; o histórico do git soma mais 3.464) |
   | Execuções importadas | 182 |
   | Newsletters | 13 |
   | Catálogos | companies 20, resources 9, funding_channels 28, corporate_programs 24 (81 linhas) |
   | Sem export do Supabase | `export_do_supabase.lido = false`; a carga é só git |

   Se a janela ficar para outro dia, refaça o pacote para o buraco entre o acervo e a primeira coleta da VM ser o menor
   possível (o dado novo do Actions não está neste pacote). Na raiz do repositório do Radar, no Git Bash:

   ```bash
   git fetch origin
   pipeline/.venv/Scripts/python.exe -m pipeline.migrar_para_postgres --salvar-pacote C:/Users/AryelBezerra/alchemia-workdata/radar/radar-carga.json.gz
   sha256sum /c/Users/AryelBezerra/alchemia-workdata/radar/radar-carga.json.gz
   ```

   O evento `radar.carga.pacote` e o `sha256sum` têm de dar o mesmo hash; o `.sha256` do passo seguinte é regerado sobre o
   pacote novo.
3. **O arquivo `.sha256` do pacote** (para o J3 conferir com `sha256sum -c`, uma trava e não um olho). Na pasta do pacote, no WSL:

   ```bash
   cd /mnt/c/Users/AryelBezerra/alchemia-workdata/radar && sha256sum radar-carga.json.gz | tee radar-carga.json.gz.sha256
   ```

   Esperado: a linha começa por `4b16978411ef980f27837a990cbb4d118a5cf7cedce6c830642b572cf7f64255` (ou pelo hash do pacote refeito).
4. **Sessão do WSL.** Cole uma vez (a chave de operação no `ssh-agent`, como no checklist da Tech):

   ```bash
   vm()  { ssh -o ServerAliveInterval=30 alchemia-vm-operacao "$@"; }
   vmt() { ssh -t -o ServerAliveInterval=30 alchemia-vm-operacao "$@"; }   # com terminal: só o restaurador, que pergunta s/N
   ENV=/home/ubuntu/alchemia-system/deploy/producao.env
   rc()  { vm "cd /home/ubuntu/alchemia-system && RADAR_RELEASE=$RADAR_SHA docker compose --env-file deploy/producao.env --profile radar $*"; }
   sql() { vm "cd /home/ubuntu/alchemia-system && docker compose --env-file deploy/producao.env exec -T db sh -c 'psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"$1\"'"; }
   ```

   `rc` roda o `docker compose` do serviço `radar` (sempre com o perfil e o `--env-file`; cada chamada leva `--no-deps` no
   comando, porque sem ele o Compose sobe `papeis -> migrar -> papeis-final` e o `migrar` falha sem `APP_RELEASE`).
   `sql` só aceita SQL sem aspas.

## A sequência

### J1. L, o estado de antes

```bash
ssh alchemia-vm-leitura ready; ssh alchemia-vm-leitura ps; ssh alchemia-vm-leitura imagens; ssh alchemia-vm-leitura timers
```

- **Esperado:** `ready` 200 e `pronto`, migrações 36 de 36 e 0 pendentes; anote a `versao` (hoje `c602f62111ca`): é o
  `APP_SHA`. `ps` só com `app` e `db`; `imagens` sem `alchemia-radar:*`; `timers` com `radar-pull.timer` e sem timer novo.

As três premissas de que J5, J7 e J8 dependem, por leitura que **não imprime valor de segredo** (só nome e contagem). Vão pela
chave de operação porque o menu de leitura não lê o `producao.env` nem o `compose.yaml`; nada muda na VM:

```bash
vm 'grep -n "^  radar:" /home/ubuntu/alchemia-system/compose.yaml; grep -n "RADAR_HORARIOS_UTC:\|RADAR_FONTE:" /home/ubuntu/alchemia-system/compose.yaml'
vm "grep -c '^PG_SENHA_RADAR=.' $ENV"
vm "grep -c '^RADAR_FONTE=' $ENV; tail -c1 $ENV | od -An -c"
```

- **1ª linha, esperado:** `<n>:  radar:` (o checkout da VM tem o serviço `radar`, com o `entrypoint` que exige a senha) e as
  linhas de `RADAR_HORARIOS_UTC` e `RADAR_FONTE` do compose. Horário: `${RADAR_HORARIOS_UTC:-}` (vazio, cai no padrão do código)
  ou `:-09:40,15:40,21:40` (o J7 cobre os dois). Leitura do app: `${RADAR_FONTE:-banco}` é o padrão do compose.
- **2ª linha, esperado:** `1`. Zero quer dizer que não há senha do papel do Radar: o serviço sai 64 e a carga não conecta.
- **3ª linha:** a contagem de `RADAR_FONTE=` no `producao.env` e o último byte do arquivo (só o byte, nunca o arquivo): `\n`
  quer dizer que termina em quebra de linha; qualquer outra coisa quer dizer que não, e é por isso que o J7 e o J8 garantem a
  quebra antes de acrescentar. **Qual leitura o app usa hoje** decide o texto do J5 e do J8:
  - contagem `1`: vale o valor do arquivo, que o J8 mostra antes de trocar; se for `local`, o app lê a pasta do `radar-pull` e a
    tela não muda até o J8.
  - contagem `0`: vale o padrão do compose, **`banco`**. O app **já** lê o banco, ainda vazio, e a tela de Radar mostra "carga
    pendente". Então "o app ainda lê `local`" é falso: a tela passa a mostrar dado já no J5/J6 (o cache se renova pela última
    execução terminada, então o J6 basta), e o J8 deixa de ser uma troca (veja lá).
- **Se divergir** (sem `radar:` no compose do checkout, senha ausente, versão de app ou migração diferente da esperada,
  contêiner `radar` já de pé): pare e chame a Hipátia ou o Gabriel.
- **Rollback:** nada a desfazer.

```bash
APP_SHA=<a versao que o ready devolveu>
```

### J2. M, o backup de antes (rótulo `pre-radar`)

Sem `sudo`: o backup roda como `ubuntu`, como no timer (`User=ubuntu`) e nas janelas anteriores. Sob `sudo` o `HOME` seria
`/root`, o rclone não acharia a configuração do `ubuntu`, o envio falharia calado (o script sai 0 e avisa) e o dump nasceria
`root:root`, que o restaurador (também `ubuntu`) não leria.

```bash
vm '/usr/local/lib/alchemia/backup-system-prod.sh --rotulo pre-radar'
ssh alchemia-vm-leitura estado
vm "ls -l /home/ubuntu/backups/system-prod/ | grep pre-radar"
vm "install -m 600 $ENV /home/ubuntu/backups/system-prod/producao.env.pre-radar && ls -l /home/ubuntu/backups/system-prod/producao.env.pre-radar"
```

- **Esperado:** a linha `dump ok: ... sha256 em system-prod-<carimbo>-pre-radar.dump.sha256` (não é a última: depois dela ainda
  vêm o envio e a retenção); no `estado`, o `backup-system-prod.json` com `ultimo_ok` novo, `rotulo: pre-radar` e o **`envio`**:
  `desligado` em 2026-10-07 (medido), e então o dump **só existe na VM**; se vier `gdrive`, o envio tem de estar ok, não um
  aviso. O `ls` mostra o `.dump` e o `.sha256` com dono `ubuntu`. A cópia do `producao.env` (modo 600, fora do repositório e do
  vault) é o que o rollback dos J7 e J8 restaura.
- **Rollback:** nada a desfazer; este dump é o rollback de todos os passos abaixo (ver "Voltar tudo", no fim).

### J3. M, levar o pacote e conferir o sha256

```bash
vm 'mkdir -p /home/ubuntu/radar-carga && chmod 755 /home/ubuntu/radar-carga'
scp /mnt/c/Users/AryelBezerra/alchemia-workdata/radar/radar-carga.json.gz /mnt/c/Users/AryelBezerra/alchemia-workdata/radar/radar-carga.json.gz.sha256 alchemia-vm-operacao:/home/ubuntu/radar-carga/
vm 'cd /home/ubuntu/radar-carga && chmod 644 radar-carga.json.gz radar-carga.json.gz.sha256 && sha256sum -c radar-carga.json.gz.sha256'
```

- **Esperado:** `radar-carga.json.gz: OK` (saída 0). O 755/644 é de propósito: o contêiner roda com o usuário 10001 e lê a
  pasta montada só para leitura.
- **Se divergir:** `FAILED` ou saída diferente de 0: não siga. Copie de novo; falhou de novo, refaça o pacote e o `.sha256`.
- **Rollback:** `vm 'rm -r /home/ubuntu/radar-carga'` (só uma cópia do pacote; o banco não foi tocado).

### J4. M, atualizar o clone e construir a imagem

```bash
vm 'sudo systemctl start radar-pull.service; git -C /home/ubuntu/alchemia-radar log -1 --format="%h %cI %s"; grep -c "^HORARIOS_LOCAIS" /home/ubuntu/alchemia-radar/pipeline/agendador.py'
vm 'R=$(git -C /home/ubuntu/alchemia-radar rev-parse --short=12 HEAD) && echo RADAR_SHA=$R && docker build -t alchemia-radar:$R --build-arg RADAR_VERSAO=$R /home/ubuntu/alchemia-radar && docker run --rm alchemia-radar:$R python -m pipeline.agendador --proximos 3'
```

- **Esperado:** o `grep -c` devolve `1` (o clone já tem o agendador novo; se vier `0`, o `push` do passo 1 ainda não chegou:
  pare). O `build` termina sem erro (confirma a roda `psycopg[binary]` para aarch64). O `--proximos 3` imprime três
  horários em UTC terminados em `09:00`, `15:00` e `21:00` (06:00, 12:00 e 18:00 de Brasília).
- **Anote** o `RADAR_SHA=...` impresso e cole no WSL: `RADAR_SHA=<o sha impresso>`.
- **Rollback:** `vm 'docker rmi alchemia-radar:<sha>'`. Nada mais mudou.

### J5. M, a carga: `--dry-run`, a real, e a segunda 0/0

```bash
rc run --rm --no-deps -v /home/ubuntu/radar-carga:/carga:ro radar python -m pipeline.migrar_para_postgres --pacote /carga/radar-carga.json.gz --dry-run; echo saida=$?
```

- **Esperado:** `saida=0`. `radar.carga.montada` com `uniao` 9247 (do pacote), `execucoes` 182, `newsletters` 13, e depois
  `radar.carga.dry_run` com as contagens de "antes" do banco, todas em 0.
- **Se divergir:** `radar.carga.falhou` com `password authentication failed` quer dizer que a senha do papel
  `alchemia_radar` não foi aplicada no banco (o passo `papeis` do deploy): pare e chame o Gabriel ou a Hipátia. `saida=64`
  quer dizer `PG_SENHA_RADAR` ausente no `producao.env`. `radar.carga.falhou` com outro erro: pare e leve a linha inteira
  (a URL do banco nunca aparece no log).

```bash
rc run --rm --no-deps -v /home/ubuntu/radar-carga:/carga:ro radar python -m pipeline.migrar_para_postgres --pacote /carga/radar-carga.json.gz; echo saida=$?
```

- **Esperado:** `saida=0` e o evento `radar.carga.fim` com `chaves_da_carga_no_banco` igual ao total do pacote (9247),
  `empresa_sem_slug` 0 e `recuperadas` com as duas conferências de 2026-09-07 (`6800a38`, `9bdfbd8`) sem ausentes. Qualquer
  `radar.carga.divergente` (saída 1) reprova o passo.
- **Se divergir:** não siga. Se o J1 mostrou que o app lê `local`, a tela não mudou; se mostrou `banco` (padrão do compose), a
  tela já lê este banco e pode estar com a carga pela metade. Guarde a saída inteira.

```bash
rc run --rm --no-deps -v /home/ubuntu/radar-carga:/carga:ro radar python -m pipeline.migrar_para_postgres --pacote /carga/radar-carga.json.gz; echo saida=$?
sql "select count(*) as itens from radar.item"
```

- **Esperado:** `saida=0`, o `radar.carga.fim` da segunda carga com **0 inserções e 0 atualizações** de itens e
  `execucoes_novas` 0; `itens` = 9247.
- **Rollback de toda a carga:** o papel `alchemia_radar` não tem `DELETE` em `radar.item`, e esvaziar com superusuário é
  destrutivo (decisão do fundador). O caminho é restaurar o dump `pre-radar` (ver "Voltar tudo", que custa as escritas do
  System desde o J2). Se o J1 mostrou o app em `local`, nada na tela depende desta carga até o J8; se mostrou `banco`, a tela
  já a mostra.

### J6. M, uma coleta à mão (a primeira execução do banco)

```bash
rc run --rm --no-deps radar python -m pipeline.run_all --destino postgres --origem manual | grep -E 'radar.coletor|radar.execucao'; echo saida=${PIPESTATUS[0]}
```

- **Esperado:** cerca de 3 minutos (na estação, 169,3 s). `saida=0`; um `radar.coletor` por fonte (`count`, `segundos`,
  `erro`); termina em `radar.execucao.fim` ou `radar.execucao.parcial` (o coletor `newsletters` já falha assim no Actions).
  `radar.execucao.ocupado` quer dizer que outra coleta segura a trava: espere e repita. `radar.execucao.falhou` reprova.
- Conferir (a primeira coleta conta como `atualizados` os itens que reencontra, porque o acervo importado tem `coletores`
  vazio; da segunda em diante só muda campo):

```bash
sql "select id, origem, estado, iniciada_em, terminada_em from radar.execucao order by id desc limit 3"
sql "select count(*) as itens from radar.item"
```

- `itens` >= 9247; a execução nova com `origem` = manual e `estado` = ok ou parcial.
- A sessão `ssh` fica aberta uns 3 minutos. Se a conexão cair, o `run` pode morrer no meio: a execução fica `rodando` e a
  próxima coleta a fecha como órfã (`fechar_orfas`); é seguro, só repita o comando.
- **Rollback:** a execução fica registrada (não se apaga). Nada a desfazer.

### J7. M, subir o serviço (o agendador do contêiner)

Primeiro, de onde vêm os horários. O `compose.yaml` do System é quem passa `RADAR_HORARIOS_UTC` ao contêiner. A mudança para o
padrão vazio já está na árvore do System (conferido em 2026-10-07), mas a VM só a tem depois do deploy de um release que a
leve. A linha que o J1 mostrou do `compose.yaml` da VM decide:

- `${RADAR_HORARIOS_UTC:-}` (padrão vazio): o contêiner usa o padrão do código (09:00, 15:00 e 21:00 UTC). Siga.
- `:-09:40,15:40,21:40`: o compose sobrepõe o código. **Paliativo até o release novo chegar:** acrescentar ao `producao.env` só
  esta linha (um segundo lugar para os horários, a remover depois). O comando garante a quebra de linha antes, sem imprimir o
  arquivo:

  ```bash
  vm 'f=/home/ubuntu/alchemia-system/deploy/producao.env; [ -z "$(tail -c1 "$f")" ] || echo >> "$f"; echo "RADAR_HORARIOS_UTC=09:00,15:00,21:00" >> "$f"; grep -c "^RADAR_HORARIOS_UTC=" "$f"'
  ```

  Esperado: `1`. Rollback do arquivo: restaurar a cópia do J2 (abaixo, J8 e "Voltar tudo"), que desfaz esta linha e a do J8.

```bash
rc up -d --no-build --no-deps radar
sleep 5; ssh alchemia-vm-leitura ps; ssh alchemia-vm-leitura logs radar --linhas 50
```

- **Esperado:** `ps` mostra `alchemia-system-radar-1` Up. O log traz `radar.agendador.inicio` com `horarios_utc`
  `["09:00","15:00","21:00"]` e `radar.agendador.espera` com o `proximo` em `09:00`, `15:00` ou `21:00` UTC, o primeiro
  depois de agora. Nenhum `radar.execucao.falhou`.
- **Se divergir:** contêiner reiniciando em laço (código 64 = senha ausente; outra saída: `logs radar`): pare o serviço
  (abaixo) e chame a Hipátia.
- **Rollback:** `rc stop radar`; se o paliativo foi usado, restaurar também a cópia do `producao.env` (J8, rollback). O
  contêiner fica parado, o banco e o app não mudam. Para voltar uma imagem: `RADAR_SHA=<sha anterior>` e repetir o `up`.

### J8. M, trocar a leitura do app para `banco` e recriar o app

Só o nome da variável e o valor; o arquivo tem as senhas e **não se imprime**. A cópia do J2
(`/home/ubuntu/backups/system-prod/producao.env.pre-radar`) é o rollback exato.

**Se o J1 mostrou `RADAR_FONTE=` ausente do `producao.env`** (contagem 0), o app já lê `banco` pelo padrão do compose: não há o
que trocar. Pule o segundo comando abaixo, rode só a conferência de valor (primeiro) e, se a tela não refletir a carga, recrie
o app (terceiro). Em qualquer caso, o texto "o app ainda lê `local`" não vale para esta janela.

```bash
vm 'grep -n "^RADAR_FONTE=" /home/ubuntu/alchemia-system/deploy/producao.env || echo ausente'
vm 'f=/home/ubuntu/alchemia-system/deploy/producao.env; if grep -q "^RADAR_FONTE=" "$f"; then sed -i "s/^RADAR_FONTE=.*/RADAR_FONTE=banco/" "$f"; else { [ -z "$(tail -c1 "$f")" ] || echo >> "$f"; echo "RADAR_FONTE=banco" >> "$f"; }; fi; grep -n "^RADAR_FONTE=" "$f"'
vm "cd /home/ubuntu/alchemia-system && APP_RELEASE=$APP_SHA docker compose --env-file deploy/producao.env up -d --no-build --no-deps --wait app"
```

- **Esperado:** o primeiro comando mostra a linha atual (`<n>:RADAR_FONTE=local`) ou `ausente`; o segundo, `<n>:RADAR_FONTE=banco`
  (uma linha só: se vier mais de uma, pare, o arquivo tem a variável repetida); o terceiro recria só o `app` e espera ele ficar `healthy`.
- **Se divergir:** o `--wait` estourar ou o `app` não ficar `healthy`: faça o rollback abaixo na hora.
- **Rollback imediato** (a cópia do J2 restaura o arquivo inteiro e desfaz também o paliativo do J7):

  ```bash
  vm 'install -m 600 /home/ubuntu/backups/system-prod/producao.env.pre-radar /home/ubuntu/alchemia-system/deploy/producao.env'
  vm "cd /home/ubuntu/alchemia-system && APP_RELEASE=$APP_SHA docker compose --env-file deploy/producao.env up -d --no-build --no-deps --wait app"
  ```

  O `radar-pull.timer` mantém a pasta local em dia, e é isso que torna a volta para `local` segura. O modo original do
  `producao.env` não foi medido; a cópia e a restauração usam 600, o de segredo.

### J9. L, as conferências pelo menu de leitura

```bash
ssh alchemia-vm-leitura ready; ssh alchemia-vm-leitura ps; ssh alchemia-vm-leitura logs app --linhas 100
ssh alchemia-vm-leitura logs radar --linhas 50; ssh alchemia-vm-leitura releases; ssh alchemia-vm-leitura timers; ssh alchemia-vm-leitura coleta
```

- **Esperado:** `ready` 200, `versao` = `APP_SHA`, 36 de 36; `ps` com `app` `healthy`, `db` e `radar` Up; o log do `app` sem
  `radar.banco.erro`; `releases` sem deploy novo; `timers` sem nenhuma unidade nova (o agendador é interno ao contêiner e
  não aparece nos timers); `coleta` sem alerta de agendamento fora da lista.
- **Na tela (logado):** `/science/radar`, cartão "Última coleta" com a fonte `postgres:<banco>/radar.meta`, a data da
  coleta do J6 e **sem** o aviso "carga pendente"; Analytics > Dashboards e Science > Projects > Fomento (catálogos) sem
  aviso; Tech > DevOps > Sincronização com a linha do Radar `ok`.
- **A primeira coleta agendada** (o próximo 06:00, 12:00 ou 18:00 de Brasília, 09, 15 ou 21 UTC): uns 4 minutos depois,
  `ssh alchemia-vm-leitura logs radar --linhas 100` mostra `radar.execucao.inicio`, `radar.coletor` e `radar.execucao.fim`
  (ou `.parcial`) e `radar.agendador.coleta` com `saida` 0; e `sql "select id, origem, estado from radar.execucao order by id desc limit 3"`
  traz uma linha `agendada`. Mande o Hopper medir a rota (F6, <= 1,0 s morno; `lerDoBanco` lê `radar.item` inteiro, sem `LIMIT`).
- **Se divergir** (aviso de carga pendente com o banco carregado, `radar.banco.erro`): rollback do J8.

## Voltar tudo

| O que voltar | Como |
|---|---|
| Só a leitura do app | O rollback do J8 (restaurar a cópia do `producao.env` e recriar o app). Não perde dado |
| Só o serviço | `rc stop radar`. Não perde dado |
| A carga e tudo o mais | Restaurar o dump do J2, abaixo. **Perde dado.** |

> **Restaurar o `pre-radar` volta o banco INTEIRO do System ao instante do J2, não só o esquema `radar`.** Tudo o que os
> colaboradores gravaram no app (jogo, CRM, papéis, tarefas) entre o J2 e a restauração se perde: o script renomeia o banco de
> agora para `<PG_BANCO>_antes_<carimbo>` e não o apaga, então o dado fica no servidor, mas fora do ar. É decisão do fundador ou do
> Gabriel, e só quando a carga ou o serviço não dão para desfazer pelas duas linhas de cima. Quanto antes depois do J2, menos custa.

O restaurador é **interativo** (pede `s/N` no terminal, lido de `/dev/tty`): por isso o `ssh -t` (`vmt`), e ele roda como
`ubuntu`, sem `sudo` (o `sudo` está por dentro, só nos `systemctl`). Na ordem:

```bash
vm 'install -m 600 /home/ubuntu/backups/system-prod/producao.env.pre-radar /home/ubuntu/alchemia-system/deploy/producao.env'
vmt '/usr/local/lib/alchemia/restaurar-system-prod.sh --dump /home/ubuntu/backups/system-prod/system-prod-<carimbo>-pre-radar.dump --release <APP_SHA> --dry-run'
vmt '/usr/local/lib/alchemia/restaurar-system-prod.sh --dump /home/ubuntu/backups/system-prod/system-prod-<carimbo>-pre-radar.dump --release <APP_SHA>'
rc stop radar
ssh alchemia-vm-leitura ready; ssh alchemia-vm-leitura ps
```

- O primeiro comando devolve o `producao.env` ao de antes da janela **antes** da restauração (o script recria o app com o arquivo
  que encontrar). O segundo só mostra os passos. O terceiro pergunta a cada passo.
- **O restaurador religa o `radar` ao fim** quando o banco restaurado tem o esquema `radar` (o dump `pre-radar` tem, é a 0024), e o
  agendador voltaria a coletar sobre o banco "desfeito". O `rc stop radar` logo depois, se a intenção é desfazer a integração
  (sem ele, o `radar` segue de pé e na próxima hora marcada grava de novo, depois do dump). Esperado depois: `ready` 200, `ps` sem
  `radar` de pé.

## Fora desta janela

R6 (desligar o `coleta.yml` e o `research-export.yml`, congelar `pipeline/data/`, o Supabase, o destino do `radar-pull.timer`
e da lista de agendamentos) segue com o fundador, depois da sombra. A mudança do `compose.yaml` do System (padrão vazio para
`RADAR_HORARIOS_UTC`) já está na árvore do System, falta commit e release; não bloqueia esta janela, porque o J7 decide pelo
`compose.yaml` que a VM tem de fato e traz o paliativo. Depois do deploy desse release, a linha `RADAR_HORARIOS_UTC` que o
paliativo pôs no `producao.env` deve sair.
