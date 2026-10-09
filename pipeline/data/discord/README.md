# `pipeline/data/discord/` — o que o Axel publicou, verbatim

> **Diretório histórico (2026-10-07).** Os bots que publicavam no Discord, Axel e Baker, foram
> aposentados em 2026-09-28, e nada mais grava aqui: a última publicação é de 2026-09-04. Os arquivos
> ficam como registro verbatim do que a comunidade viu e não se editam. A rotina citada abaixo não existe
> mais como tarefa agendada; o que resta é o leitor, `pipeline/research_export.py`, que ainda monta
> a seção *"Publicado no Discord"* do radar de um dia que tenha arquivo aqui.

Um arquivo por publicação, nomeado `AAAA-MM-DD-HHMM.md`, contendo **cópia literal** da mensagem
que a rotina `alchemia-news-anuncio-discord` (o Axel) postou no canal `#news`. <!-- docs-vivos: ok -->
O nome da rotina é o legado, anterior ao Alchemia Radar, e fica entre crases por ser nome próprio.

**Por que este diretório existe.** O radar do dia
(`alchemia-science/research/AAAA-MM-DD-alchemia-news-radar.md`) é um arquivo **derivado**: o
`pipeline/research_export.py` o reescreve por inteiro a cada execução. Se o Axel escrevesse
direto nele, a próxima geração apagaria o registro. Escrevendo aqui, o `research_export` lê o
diretório e monta a seção *"Publicado no Discord"* do dia — o registro sobrevive a quantas
regenerações forem.

Com isso o radar fecha o ciclo inteiro do dia: **o que foi coletado** (pipeline determinístico),
**o que virou texto completo** na `alchemia-library` (só open access confirmado), e **o que a
comunidade efetivamente viu**.

Quem escrevia: só o Passo 5 da rotina do Axel, e só depois de a publicação ter retornado exit 0.
Quem lê: `pipeline/research_export.py`.

Criado em 2026-08-18, junto da integração do Radar (então `alchemia-news`) → `alchemia-science`/`alchemia-library`.
Ver `alchemia-ai/softwares/alchemia-radar/docs/specs/2026-08-18-research-library-integration.md`.
