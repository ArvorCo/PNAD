"""Promove a evidência do perfil publicado sem afirmar uma etapa não identificada."""

import json
from pathlib import Path

from .archive import EXPECTED_SHA

ROOT = Path(__file__).resolve().parents[3]
POLL = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-10-13.json"
NOTE = "A íntegra recebida em 15/10 publica o perfil de renda 31/42/27 na p. 147 e os votos por renda na p. 24. O perfil agora tem evidência no relatório, além das cotas registradas. A página não explicita antes/depois da ponderação; usar 31/42/27 como margem dos cruzamentos continua hipótese, com cobertura integral assumida. Bases ponderadas, não resposta à renda e pesos individuais não foram divulgados. A sensibilidade permanece 45,398 × 44,531; não é voto corrigido."


def update_poll():
    poll = json.loads(POLL.read_text())
    poll["renda"].update(
        perfil_tipo="perfil_publicado",
        nota=NOTE,
        pagina_perfil=147,
        pagina_cruzamento=24,
        etapa_ponderacao="Não explicitada no perfil publicado",
    )
    poll["perfil_economico_publicado"].update(
        tipo="perfil_amostra_publicado_etapa_nao_explicitada", nota=NOTE, pagina=147
    )
    poll["fonte"].update(
        tipo="relatorio_recebido_usuario",
        rotulo="Quaest: íntegra de 14/10 recebida do usuário, pp. 18, 24 e 147; conferida com G1 e registro TSE",
        arquivo="data/originals/quaest_102026_14/Quaest_14102026.pdf",
        sha256=EXPECTED_SHA,
        url="https://brasil.arvor.co/fontes/quaest_14102026.pdf",
        status="Íntegra de 152 páginas arquivada. Perfil 31/42/27 publicado; etapa da ponderação, bases e regra de eleitor provável não explicitadas.",
        nota=NOTE,
    )
    poll["metodo"] = (
        "presencial domiciliar; PPT em 124 municípios e setores; cotas no estágio final; pós-estratificação declarada como MrP ou rake, sem especificação operacional"
    )
    poll["cruzamentos"]["2t"][
        "nota"
    ] = "Íntegra, p. 24, conferida visualmente com os rótulos SVG do G1. Perfil de renda na p. 147; percentuais inteiros, bases não publicadas. Zero é arredondado."
    POLL.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    return poll
