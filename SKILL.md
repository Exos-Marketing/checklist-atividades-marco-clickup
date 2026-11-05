---
name: checklist-atividades-marco-clickup
description: Use quando o usuário pedir para criar checklists nos marcos de um projeto Exos no ClickUp para acompanhar o progresso das atividades vinculadas, ou quando quiser "ver no marco quais atividades já foram feitas", "checklist de progresso no milestone", "rastrear atividades do marco", "criar checklist nas milestones do projeto X". Gatilhos: "cria checklist nos marcos", "adiciona checklist de atividades no marco", "quero ver o progresso das atividades no marco", "checklist de atividades vinculadas".
---

# Checklist de Atividades Vinculadas nos Marcos (ClickUp Exos)

Cria, em cada **marco (milestone)** de um projeto Exos, um checklist nativo **"Atividades Vinculadas"**
com um item por atividade linkada ao marco — apenas o título da atividade (sem sufixo de projeto).

À medida que as atividades são concluídas, o responsável marca o item no checklist e enxerga o progresso
do marco sem precisar navegar pelas listas de processo.

## Script

`~/.claude/skills/checklist-atividades-marco-clickup/scripts/clickup_checklist_atividades.py`
(dentro da skill; só usa a biblioteca padrão do Python)

Parâmetros:

| Flag | Obrigatória | Descrição |
|---|---|---|
| `--suffix "[DM][LB][POS][AGO][26]"` | **sim** | Sufixo exato do projeto (tal como aparece nos nomes das tasks) |
| `--apply` | não | Escreve de verdade; sem ela roda dry-run |
| `--perpetuo` | não | Usa as listas de fase de perpétuos em vez de lançamentos |
| `--config caminho.json` | não | Lê `phase_map` ou `phase_lists` de um `config_*.json` existente |

## Regras de negócio (hardcoded, não mude)

1. **Marco que já tem qualquer checklist → PULA.** Idempotente: após o 1º `--apply` o marco é pulado em re-runs.
2. **Marco sem atividades vinculadas → PULA.** Sem atividade não há o que rastrear.
3. **Nome do item = título limpo** (sufixo removido). Ex.: `Copy Criativos Convite para Lançamento Pós`, não `Copy Criativos Convite para Lançamento Pós [DM][LB][POS][AGO][26]`.

## Fluxo obrigatório

1. **Dry-run primeiro** — confirmar com o usuário quais marcos receberão checklist e quantos itens.
2. **Aprovação** — só rodar `--apply` depois de o usuário confirmar.
3. **Verificar** — após o apply, confirmar via MCP (`clickup_get_task` no marco) que o checklist existe com os itens certos.

## Exemplos de uso

```bash
# Lançamento — dry-run
CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
  python3 ~/.claude/skills/checklist-atividades-marco-clickup/scripts/clickup_checklist_atividades.py --suffix "[DM][LB][POS][AGO][26]"

# Lançamento — aplicar
CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
  python3 ~/.claude/skills/checklist-atividades-marco-clickup/scripts/clickup_checklist_atividades.py --suffix "[ET][RS][POS][MAI][26]" --apply

# Perpétuo — dry-run
CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
  python3 ~/.claude/skills/checklist-atividades-marco-clickup/scripts/clickup_checklist_atividades.py --suffix "[KM][PEP][AAT][26]" --perpetuo

# Config customizada (para fases não-padrão)
CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
  python3 ~/.claude/skills/checklist-atividades-marco-clickup/scripts/clickup_checklist_atividades.py --suffix "[LL][LM][POS][ABR][26]" \
    --config config_dm_lb_pos.json --apply
```

## Listas de fase padrão (embutidas no script)

**Lançamento** (`DEFAULT_PHASE_LISTS`):
Concepção `901302376636` · Setup `901302376637` · Captação `901302378944` · Aquecimento `901302378939`
· Evento `901302376639` · Lançamento `901302376640` · Pós Venda `901302376641` · Downsell `901310974062`

**Perpétuo** (`PERPETUO_PHASE_LISTS`):
Concepção `901302376636` · Setup `901302376637` · Geração de Público `901312155468`
· Vendas `901312155469` · Recuperação `901312155470` · Pós-Venda `901312155471` · Melhoria Contínua `901312155472`

## Verificação pós-apply

```python
# Via MCP — confirmar checklist no marco tratado
clickup_get_task(task_id="<id_do_marco>", include=["checklists"])
# Esperado: checklists[0].name == "Atividades Vinculadas", items com titulos sem sufixo
```

Re-run do dry-run deve mostrar todos os marcos como `SKIP — ja tem checklist` (prova de idempotência).
