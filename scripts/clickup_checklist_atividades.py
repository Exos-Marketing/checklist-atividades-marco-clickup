#!/usr/bin/env python3
"""
Cria, em cada MARCO (milestone) de um projeto Exos no ClickUp, um checklist nativo
"Atividades Vinculadas" com 1 item por atividade vinculada (apenas o titulo, sem sufixo).

Regras:
  - Marco que JA tem qualquer checklist  -> PULA (nao duplica, nao mexe nos existentes).
  - Marco SEM atividades vinculadas       -> PULA (nada a rastrear).
  - Demais marcos                         -> cria "Atividades Vinculadas" com os titulos limpos.

Idempotente: apos o 1o --apply o marco passa a ter checklist e e pulado em re-runs.

Uso:
  CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \\
    python3 clickup_checklist_atividades.py --suffix "[DM][LB][POS][AGO][26]"
  CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \\
    python3 clickup_checklist_atividades.py --suffix "[ET][RS][POS][MAI][26]" --apply
  # Com config customizada de fases (ex.: perpetuo):
  CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \\
    python3 clickup_checklist_atividades.py --suffix "[KM][PEP][AAT][26]" \\
      --config config_km_aat.json --apply
"""
import os, sys, time, json, argparse, urllib.request, urllib.error

TOKEN = os.environ.get("CLICKUP_TOKEN", "")
if not TOKEN:
    print("ERRO: defina CLICKUP_TOKEN (security find-generic-password -s clickup-exos-api -w)")
    sys.exit(1)

CHECKLIST_NAME = "Atividades Vinculadas"

# Listas de fase padrao para LANCAMENTOS (phase_map[*].dst nos configs de lançamento)
DEFAULT_PHASE_LISTS = {
    "Concepção":   "901302376636",
    "Setup":       "901302376637",
    "Captação":    "901302378944",
    "Aquecimento": "901302378939",
    "Evento":      "901302376639",
    "Lançamento":  "901302376640",
    "Pós Venda":   "901302376641",
    "Downsell":    "901310974062",
}

# Listas de fase padrao para PERPETUOS
PERPETUO_PHASE_LISTS = {
    "Concepção":          "901302376636",
    "Setup":              "901302376637",
    "Geração de Público": "901312155468",
    "Vendas":             "901312155469",
    "Recuperação":        "901312155470",
    "Pós-Venda":          "901312155471",
    "Melhoria Contínua":  "901312155472",
}


def parse_args():
    p = argparse.ArgumentParser(description="Cria checklist de atividades nos marcos de um projeto Exos.")
    p.add_argument("--suffix", required=True,
                   help='Sufixo do projeto, ex.: "[DM][LB][POS][AGO][26]"')
    p.add_argument("--apply", action="store_true",
                   help="Escreve de verdade (sem esta flag roda dry-run)")
    p.add_argument("--config",
                   help="Caminho para um config_*.json com phase_lists customizadas (opcional)")
    p.add_argument("--perpetuo", action="store_true",
                   help="Usa as listas de fase de perpetuos em vez das de lancamento")
    return p.parse_args()


def load_phase_lists(args):
    if args.config:
        with open(args.config) as f:
            cfg = json.load(f)
        # Aceita tanto phase_map (config do engine) quanto phase_lists direto
        if "phase_map" in cfg:
            return {ph: pm["dst"] for ph, pm in cfg["phase_map"].items() if isinstance(pm, dict) and pm.get("dst")}
        if "phase_lists" in cfg:
            return cfg["phase_lists"]
    if args.perpetuo:
        return PERPETUO_PHASE_LISTS
    return DEFAULT_PHASE_LISTS


def _safe(s):
    try: return json.loads(s)
    except Exception: return s


def api(method, path, body=None, tries=5):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(tries):
        req = urllib.request.Request("https://api.clickup.com" + path, data=data, method=method)
        req.add_header("Authorization", TOKEN); req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t.strip() else {})
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(3*(a+1)); continue
            return e.code, _safe(e.read().decode())
        except Exception:
            time.sleep(2); continue
    return 0, "retry"


def list_tasks(list_id):
    out, page = [], 0
    while True:
        c, b = api("GET", f"/api/v2/list/{list_id}/task?archived=false&include_closed=true&subtasks=false&page={page}")
        if c != 200 or not isinstance(b, dict): break
        out += b.get("tasks", [])
        if b.get("last_page", True) or page > 25: break
        page += 1
    return out


def clean_title(name, suffix):
    """Remove o sufixo do projeto do nome da atividade, deixando so o titulo."""
    return name.replace(suffix, "").strip()


def linked_activities(marco, suffix):
    """Resolve atividades vinculadas ao marco; retorna lista de titulos limpos (sem sufixo)."""
    acts, seen = [], set()
    mid = marco["id"]
    for ln in marco.get("linked_tasks", []) or []:
        aid = ln.get("link_id") or ln.get("task_id")
        if not aid or aid == mid: aid = ln.get("task_id")
        if not aid or aid == mid or aid in seen: continue
        seen.add(aid)
        ca, act = api("GET", f"/api/v2/task/{aid}")
        if ca != 200 or not isinstance(act, dict): continue
        if act.get("custom_item_id") == 1: continue   # outro marco, pular
        acts.append(clean_title(act["name"], suffix))
    return acts


def create_checklist(marco_id, items):
    c, r = api("POST", f"/api/v2/task/{marco_id}/checklist", {"name": CHECKLIST_NAME})
    cid = (r or {}).get("checklist", {}).get("id") if isinstance(r, dict) else None
    if not cid:
        print(f"      ! falha ao criar checklist (status {c}): {r}")
        return False
    for it in items:
        api("POST", f"/api/v2/checklist/{cid}/checklist_item", {"name": it})
        time.sleep(0.45)
    return True


def main():
    args = parse_args()
    suffix = args.suffix
    phase_lists = load_phase_lists(args)
    mode = "APPLY (escrevendo)" if args.apply else "DRY-RUN (nao escreve nada)"
    print(f"== Checklists de atividades em marcos de {suffix} — {mode} ==\n")
    created = skipped_cl = skipped_noact = 0

    for phase, list_id in phase_lists.items():
        for t in list_tasks(list_id):
            if suffix not in t.get("name", ""): continue
            if t.get("custom_item_id") != 1: continue   # so marcos
            c, m = api("GET", f"/api/v2/task/{t['id']}")
            if c != 200 or not isinstance(m, dict): continue
            name = m.get("name", t["id"])

            if (m.get("checklists") or []):
                skipped_cl += 1
                print(f"[{phase}] {name}\n   SKIP — ja tem checklist\n")
                continue

            acts = linked_activities(m, suffix)
            if not acts:
                skipped_noact += 1
                print(f"[{phase}] {name}\n   SKIP — sem atividades vinculadas\n")
                continue

            print(f"[{phase}] {name}\n   CREATE — '{CHECKLIST_NAME}' com {len(acts)} itens:")
            for a in acts:
                print(f"      - {a}")
            if args.apply:
                ok = create_checklist(m["id"], acts)
                print("      => criado" if ok else "      => ERRO")
            else:
                print("      (dry-run: nada escrito)")
            print()
            created += 1

    print("==== RESUMO ====")
    print(f"  marcos com checklist criado: {created}")
    print(f"  pulados (ja tinham checklist): {skipped_cl}")
    print(f"  pulados (sem atividade vinculada): {skipped_noact}")
    if not args.apply:
        print("\n  DRY-RUN — rode com --apply para escrever.")


if __name__ == "__main__":
    main()
