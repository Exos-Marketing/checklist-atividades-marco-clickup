# checklist-atividades-marco-clickup

Skill do Claude Code que cria, em cada marco (milestone) de um projeto da Exos no ClickUp, o checklist nativo
**"Atividades Vinculadas"**, com um item por atividade linkada ao marco. Quem cuida do marco marca o item quando a
atividade termina e vê o progresso ali mesmo, sem abrir as listas de processo.

## Instalação

```bash
git clone https://github.com/Exos-Marketing/checklist-atividades-marco-clickup.git \
  ~/.claude/skills/checklist-atividades-marco-clickup
```

Requisitos:

- Python 3 (o script só usa a biblioteca padrão).
- O **seu** token da API do ClickUp no Keychain, no serviço `clickup-exos-api`:

  ```bash
  security add-generic-password -s clickup-exos-api -a "$USER" -w <seu-token>
  ```

- O MCP do ClickUp, para conferir o checklist depois do `--apply`.

**Nenhuma credencial mora neste repo.**

## Uso

No Claude Code, peça "cria checklist nos marcos do [DM][LB][POS][AGO][26]". Por baixo:

```bash
SCRIPT=~/.claude/skills/checklist-atividades-marco-clickup/scripts/clickup_checklist_atividades.py
CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
  python3 $SCRIPT --suffix "[DM][LB][POS][AGO][26]"            # dry-run
CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
  python3 $SCRIPT --suffix "[DM][LB][POS][AGO][26]" --apply    # escreve
```

`--perpetuo` usa as listas de fase do perpétuo. `--config <config_*.json>` lê o mapa de fases de um config da
skill `duplicar-projeto-clickup`.

## Regras

- Dry-run primeiro; `--apply` só depois do OK.
- Marco que já tem checklist, ou que não tem atividade vinculada, é pulado: dá para rodar de novo sem duplicar.
- O item leva o título da atividade sem o sufixo do projeto.

## O que tem aqui

| arquivo | o que faz |
|---|---|
| `SKILL.md` | o fluxo, as regras e as listas de fase de lançamento e perpétuo |
| `scripts/clickup_checklist_atividades.py` | lê os marcos pelas listas de fase e cria o checklist e os itens pela REST do ClickUp |

---

Interno · Exos Marketing Digital e Internacionalização Ltda.
