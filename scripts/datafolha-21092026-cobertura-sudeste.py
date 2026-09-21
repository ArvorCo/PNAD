#!/usr/bin/env python3
"""Cobertura do Grupo Folha sobre SP, RJ, MG e ES contra a pauta da pesquisa.

O Datafolha pertence ao Grupo Folha, que tambem edita a Folha de S.Paulo e o
UOL. As pesquisas estaduais de setembro de 2026 tiveram campo de 08 a 10/09 e a
nacional, de 15 a 17/09. Este modulo registra o que os proprios veiculos do
grupo publicaram sobre os quatro estados do Sudeste entre 20/08/2026 e
21/09/2026, com data, hora, titulo exato e URL, para cruzar com o que os
questionarios de fato perguntaram.

A coleta e manual e reproduzivel. Cada item foi lido na busca do proprio
veiculo, com filtro de periodo, ou na capa de seccao do proprio veiculo. As
consultas estao declaradas em CONSULTAS com a contagem de resultados que a
busca devolveu, e qualquer leitor refaz. Nada aqui e inferencia: sao titulos
publicados com carimbo de data do veiculo.

Uso:
  python3 scripts/datafolha-21092026-cobertura-sudeste.py

Saidas:
  analysis/datafolha_21092026/cobertura_sudeste.json
  docs/assets/datafolha_21092026_cobertura_sudeste.json
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "datafolha_21092026"
ASSETS = ROOT / "docs" / "assets"

PERIODO = {"inicio": "2026-08-20", "fim": "2026-09-21"}

CAMPO = {
    "estadual": {
        "inicio": "2026-09-08",
        "fim": "2026-09-10",
        "divulgacao": "2026-09-11",
    },
    "nacional": {
        "inicio": "2026-09-15",
        "fim": "2026-09-17",
        "divulgacao": "2026-09-17",
    },
    "relatorio_completo": "2026-09-21",
}

UFS = ["SP", "RJ", "MG", "ES"]

# Lista fechada de temas. Um item so entra com um destes rotulos.
TEMAS = [
    "seguranca_publica",
    "crime_organizado",
    "transporte_mobilidade",
    "saneamento_agua",
    "clima_enchentes",
    "infraestrutura_concessoes",
    "financas_estaduais",
    "educacao",
    "habitacao_urbanismo",
    "meio_ambiente_mineracao",
    "corrupcao_investigacao",
    "justica_eleitoral",
    "campanha_eleitoral",
    "pesquisa_eleitoral",
    "judiciario_stf",
    "bets_apostas",
    "outros",
]

# Lista fechada de destinatarios do onus da pauta. "nenhum" significa que o
# titulo publicado nao imputa custo a nenhum dos atores da disputa.
PESA = [
    "governo_estadual",
    "governo_federal",
    "prefeitura_sp",
    "nenhum",
    "Tarcisio de Freitas",
    "Fernando Haddad",
    "Andre do Prado",
    "Cleitinho Azevedo",
    "Mateus Simoes",
    "Romeu Zema",
    "Patrus Ananias",
    "Aecio Neves",
    "Claudio Castro",
    "Eduardo Paes",
    "Douglas Ruas",
    "Anthony Garotinho",
    "Flavio Bolsonaro",
    "Lula",
]

DOMINIOS = ("folha.uol.com.br", "uol.com.br")

# Consultas declaradas. "resultados" e o numero que a propria busca devolveu no
# periodo; None quando a pagina nao publica contagem.
CONSULTAS = [
    {
        "id": "q_sp_tarcisio",
        "veiculo": "Folha de S.Paulo",
        "termo": "Tarcísio",
        "url": "https://search.folha.uol.com.br/?q=Tarc%C3%ADsio&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 180,
    },
    {
        "id": "q_sp_sabesp",
        "veiculo": "Folha de S.Paulo",
        "termo": "Sabesp",
        "url": "https://search.folha.uol.com.br/?q=Sabesp&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 39,
    },
    {
        "id": "q_sp_pcc",
        "veiculo": "Folha de S.Paulo",
        "termo": "PCC transporte",
        "url": "https://search.folha.uol.com.br/?q=PCC+transporte&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 38,
    },
    {
        "id": "q_sp_seg",
        "veiculo": "Folha de S.Paulo",
        "termo": "Tarcísio segurança",
        "url": "https://search.folha.uol.com.br/?q=Tarc%C3%ADsio+seguran%C3%A7a&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 44,
    },
    {
        "id": "q_sp_trem",
        "veiculo": "Folha de S.Paulo",
        "termo": "trem intercidades",
        "url": "https://search.folha.uol.com.br/?q=trem+intercidades&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 3,
    },
    {
        "id": "q_sp_pedagio",
        "veiculo": "Folha de S.Paulo",
        "termo": "pedágio São Paulo",
        "url": "https://search.folha.uol.com.br/?q=ped%C3%A1gio+S%C3%A3o+Paulo&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 15,
    },
    {
        "id": "q_sp_derrite",
        "veiculo": "Folha de S.Paulo",
        "termo": "Guilherme Derrite",
        "url": "https://search.folha.uol.com.br/?q=Guilherme+Derrite&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 31,
    },
    {
        "id": "q_mg_cleitinho",
        "veiculo": "Folha de S.Paulo",
        "termo": "Cleitinho",
        "url": "https://search.folha.uol.com.br/?q=Cleitinho&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 25,
    },
    {
        "id": "q_mg_simoes",
        "veiculo": "Folha de S.Paulo",
        "termo": "Mateus Simões",
        "url": "https://search.folha.uol.com.br/?q=Mateus+Sim%C3%B5es&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 13,
    },
    {
        "id": "q_mg_gov",
        "veiculo": "Folha de S.Paulo",
        "termo": "Minas Gerais governador",
        "url": "https://search.folha.uol.com.br/?q=Minas+Gerais+governador&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 76,
    },
    {
        "id": "q_mg_aecio",
        "veiculo": "Folha de S.Paulo",
        "termo": "Aécio Neves",
        "url": "https://search.folha.uol.com.br/?q=A%C3%A9cio+Neves&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 11,
    },
    {
        "id": "q_mg_divida",
        "veiculo": "Folha de S.Paulo",
        "termo": "dívida de Minas",
        "url": "https://search.folha.uol.com.br/?q=d%C3%ADvida+de+Minas&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 30,
    },
    {
        "id": "q_mg_patrus",
        "veiculo": "Folha de S.Paulo",
        "termo": "Patrus Ananias",
        "url": "https://search.folha.uol.com.br/?q=Patrus+Ananias&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 20,
    },
    {
        "id": "q_mg_ipva",
        "veiculo": "Folha de S.Paulo",
        "termo": "IPVA Minas",
        "url": "https://search.folha.uol.com.br/?q=IPVA+Minas&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 3,
    },
    {
        "id": "q_mg_samarco",
        "veiculo": "Folha de S.Paulo",
        "termo": "Samarco",
        "url": "https://search.folha.uol.com.br/?q=Samarco&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 5,
    },
    {
        "id": "q_mg_vale",
        "veiculo": "Folha de S.Paulo",
        "termo": "Vale mineração",
        "url": "https://search.folha.uol.com.br/?q=Vale+minera%C3%A7%C3%A3o&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 18,
    },
    {
        "id": "q_rj_castro",
        "veiculo": "Folha de S.Paulo",
        "termo": "Cláudio Castro",
        "url": "https://search.folha.uol.com.br/?q=Cl%C3%A1udio+Castro&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 47,
    },
    {
        "id": "q_rj_seg",
        "veiculo": "Folha de S.Paulo",
        "termo": "governo do Rio segurança",
        "url": "https://search.folha.uol.com.br/?q=governo+do+Rio+seguran%C3%A7a&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 109,
    },
    {
        "id": "q_rj_cv",
        "veiculo": "Folha de S.Paulo",
        "termo": "Comando Vermelho",
        "url": "https://search.folha.uol.com.br/?q=Comando+Vermelho&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 83,
    },
    {
        "id": "q_rj_paes",
        "veiculo": "Folha de S.Paulo",
        "termo": "Eduardo Paes",
        "url": "https://search.folha.uol.com.br/?q=Eduardo+Paes&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 38,
    },
    {
        "id": "q_rj_ruas",
        "veiculo": "Folha de S.Paulo",
        "termo": "Douglas Ruas",
        "url": "https://search.folha.uol.com.br/?q=Douglas+Ruas&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 33,
    },
    {
        "id": "q_rj_garotinho",
        "veiculo": "Folha de S.Paulo",
        "termo": "Garotinho",
        "url": "https://search.folha.uol.com.br/?q=Garotinho&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 24,
    },
    {
        "id": "q_rj_milicia",
        "veiculo": "Folha de S.Paulo",
        "termo": "milícia Rio",
        "url": "https://search.folha.uol.com.br/?q=mil%C3%ADcia+Rio&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 13,
    },
    {
        "id": "q_rj_cabral",
        "veiculo": "Folha de S.Paulo",
        "termo": "Sérgio Cabral",
        "url": "https://search.folha.uol.com.br/?q=S%C3%A9rgio+Cabral&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 12,
    },
    {
        "id": "q_rj_benedita",
        "veiculo": "Folha de S.Paulo",
        "termo": "Benedita da Silva",
        "url": "https://search.folha.uol.com.br/?q=Benedita+da+Silva&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 17,
    },
    {
        "id": "q_es_uf",
        "veiculo": "Folha de S.Paulo",
        "termo": "Espírito Santo",
        "url": "https://search.folha.uol.com.br/?q=Esp%C3%ADrito+Santo&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 75,
        "nota": "tres paginas lidas; nenhum item de politica estadual capixaba",
    },
    {
        "id": "q_es_ferraco",
        "veiculo": "Folha de S.Paulo",
        "termo": "Ferraço",
        "url": "https://search.folha.uol.com.br/?q=Ferra%C3%A7o&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 2,
    },
    {
        "id": "q_es_pazolini",
        "veiculo": "Folha de S.Paulo",
        "termo": "Pazolini",
        "url": "https://search.folha.uol.com.br/?q=Pazolini&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 1,
    },
    {
        "id": "q_es_casagrande",
        "veiculo": "Folha de S.Paulo",
        "termo": "Casagrande",
        "url": "https://search.folha.uol.com.br/?q=Casagrande&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 9,
    },
    {
        "id": "q_es_capixaba",
        "veiculo": "Folha de S.Paulo",
        "termo": "capixaba",
        "url": "https://search.folha.uol.com.br/?q=capixaba&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 16,
    },
    {
        "id": "q_es_gov",
        "veiculo": "Folha de S.Paulo",
        "termo": "governo do Espírito Santo",
        "url": "https://search.folha.uol.com.br/?q=governo+do+Esp%C3%ADrito+Santo&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 21,
    },
    {
        "id": "q_es_guarapari",
        "veiculo": "Folha de S.Paulo",
        "termo": "Guarapari",
        "url": "https://search.folha.uol.com.br/?q=Guarapari&periodo=personalizado&sd=20/08/2026&ed=21/09/2026&site=todos",
        "resultados": 0,
    },
    {
        "id": "q_uol_eleicoes",
        "veiculo": "UOL",
        "termo": "capa da editoria Eleições 2026",
        "url": "https://noticias.uol.com.br/eleicoes/",
        "resultados": None,
        "nota": "capa lida em 21/09/2026; a data de cada item esta no caminho da URL",
    },
    {
        "id": "q_uol_politica",
        "veiculo": "UOL",
        "termo": "capa de Política, últimas notícias",
        "url": "https://noticias.uol.com.br/politica/ultimas/",
        "resultados": None,
        "nota": "capa lida em 21/09/2026; a data de cada item esta no caminho da URL",
    },
]

FOLHA = "https://www1.folha.uol.com.br"
DATAFOLHA = "https://datafolha.folha.uol.com.br"
CLEVEL = "https://c-level.folha.uol.com.br"
F5 = "https://f5.folha.uol.com.br"
UOL = "https://noticias.uol.com.br"

# Cada item: uf, data ISO, hora do veiculo, veiculo, titulo exato, URL, tema da
# lista fechada, a quem a pauta pesa e a consulta que o devolveu.
ITENS = [
    # ------------------------------------------------------------------ SP
    {
        "uf": "SP",
        "data": "2026-08-23",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Mercado",
        "titulo": "Tarcísio encerra mandato com piora gradativa nas contas e aponta investimento maior em PPPs",
        "url": f"{FOLHA}/mercado/2026/08/tarcisio-encerra-mandato-com-piora-gradativa-nas-contas-e-aponta-investimento-maior-em-ppps.shtml",
        "tema": "financas_estaduais",
        "pesa": "governo_estadual",
        "consulta": "q_mg_divida",
    },
    {
        "uf": "SP",
        "data": "2026-08-27",
        "hora": "10h44",
        "veiculo": "Folha de S.Paulo, Painel S.A.",
        "titulo": "Consórcio Rota Mogiana assina com governo de SP concessão de rodovias com investimentos de R$ 9,4 bi",
        "url": f"{FOLHA}/colunas/painelsa/2026/08/consorcio-rota-mogiana-assina-com-governo-de-sp-concessao-de-rodovias-com-investimentos-de-r-94-bi.shtml",
        "tema": "infraestrutura_concessoes",
        "pesa": "governo_estadual",
        "consulta": "q_sp_pedagio",
    },
    {
        "uf": "SP",
        "data": "2026-09-02",
        "hora": "6h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Sistema Cantareira continua a operar na faixa de alerta em setembro",
        "url": f"{FOLHA}/cotidiano/2026/09/sistema-cantareira-continua-a-operar-na-faixa-de-alerta-em-setembro.shtml",
        "tema": "saneamento_agua",
        "pesa": "governo_estadual",
        "consulta": "q_sp_sabesp",
    },
    {
        "uf": "SP",
        "data": "2026-09-04",
        "hora": "8h00",
        "veiculo": "Folha de S.Paulo, Educação",
        "titulo": "Análise identifica resultados atípicos no Provão Paulista, que seleciona para universidades de SP",
        "url": f"{FOLHA}/educacao/2026/09/estudo-identifica-resultados-atipicos-no-provao-paulista-que-seleciona-para-universidades-de-sp.shtml",
        "tema": "educacao",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-06",
        "hora": "10h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Munições desviadas da PM de SP abastecem crimes há 14 anos; morte de advogado é caso mais recente",
        "url": f"{FOLHA}/cotidiano/2026/09/municoes-desviadas-da-pm-de-sp-abastecem-crimes-ha-14-anos-morte-de-advogado-e-caso-mais-recente.shtml",
        "tema": "seguranca_publica",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-11",
        "hora": "10h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Gangues quebra-vidros chegam a todas as regiões de SP; 'Parar em semáforo me dá desespero', diz vítima",
        "url": f"{FOLHA}/cotidiano/2026/09/gangues-quebra-vidros-chegam-a-todas-as-regioes-de-sp-parar-em-semaforo-me-da-desespero-diz-vitima.shtml",
        "tema": "seguranca_publica",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-14",
        "hora": "12h10",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "No Vale do Ribeira, interior de São Paulo, moradores deixam áreas em meio a enchentes",
        "url": f"{FOLHA}/cotidiano/2026/09/no-vale-do-ribeira-interior-de-sao-paulo-moradores-evacuam-areas-em-meio-a-enchentes.shtml",
        "tema": "clima_enchentes",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-14",
        "hora": "18h57",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Moradores enfrentam enchente há três dias no Jardim Pantanal, zona leste de São Paulo",
        "url": f"{FOLHA}/cotidiano/2026/09/moradores-enfrentam-enchente-ha-tres-dias-no-jardim-pantanal-zona-leste-de-sao-paulo.shtml",
        "tema": "clima_enchentes",
        "pesa": "governo_estadual",
        "consulta": "q_sp_sabesp",
    },
    {
        "uf": "SP",
        "data": "2026-09-15",
        "hora": "4h15",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "CPTM vai ressarcir Trivia Trens em R$ 24,4 milhões durante gestão de linhas após pane",
        "url": f"{FOLHA}/cotidiano/2026/09/cptm-vai-ressarcir-trivia-trens-em-r-244-milhoes-durante-gestao-de-linhas-apos-pane.shtml",
        "tema": "transporte_mobilidade",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-15",
        "hora": "15h44",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Último morador da favela do Moinho, no centro de São Paulo, deixa a comunidade após demolições",
        "url": f"{FOLHA}/cotidiano/2026/09/ultimo-morador-da-favela-do-moinho-no-centro-de-sao-paulo-deixa-a-comunidade-apos-demolicoes.shtml",
        "tema": "habitacao_urbanismo",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-16",
        "hora": "21h01",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Justiça Eleitoral proíbe propaganda de André do Prado que usa imagem de Tarcísio",
        "url": f"{FOLHA}/poder/2026/09/justica-eleitoral-proibe-propaganda-de-andre-do-prado-que-usa-imagem-de-tarcisio.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Andre do Prado",
        "consulta": "q_sp_derrite",
    },
    {
        "uf": "SP",
        "data": "2026-09-16",
        "hora": "22h50",
        "veiculo": "C-Level, Negócios",
        "titulo": "Sabesp encerra incorporação da Emae após rejeição de oferta aos minoritários",
        "url": f"{CLEVEL}/negocios/2026/09/sabesp-encerra-incorporacao-da-emae-apos-rejeicao-de-oferta-aos-minoritarios.shtml",
        "tema": "saneamento_agua",
        "pesa": "governo_estadual",
        "consulta": "q_sp_sabesp",
    },
    {
        "uf": "SP",
        "data": "2026-09-17",
        "hora": "13h25",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Governo Tarcísio perde recurso e terá de indenizar idoso atingido por spray de PM",
        "url": f"{FOLHA}/cotidiano/2026/09/governo-tarcisio-perde-recurso-e-tera-de-indenizar-idoso-atingido-por-spray-de-pm.shtml",
        "tema": "seguranca_publica",
        "pesa": "governo_estadual",
        "consulta": "q_sp_seg",
    },
    {
        "uf": "SP",
        "data": "2026-09-17",
        "hora": "18h13",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "'Relação institucional', diz Tarcísio sobre elo com Milton Leite, suspeito em esquema do PCC no transporte",
        "url": f"{FOLHA}/poder/2026/09/relacao-institucional-diz-tarcisio-sobre-elo-com-milton-leite-suspeito-em-esquema-do-pcc-no-transporte.shtml",
        "tema": "crime_organizado",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_sp_pcc",
        "destaque": True,
    },
    {
        "uf": "SP",
        "data": "2026-09-17",
        "hora": "19h27",
        "veiculo": "Folha de S.Paulo, Mônica Bergamo",
        "titulo": "Tarcísio aciona Justiça contra críticas de candidatos do PSOL nas redes sociais",
        "url": f"{FOLHA}/colunas/monicabergamo/2026/09/tarcisio-aciona-justica-contra-criticas-de-candidatos-do-psol-nas-redes-sociais.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_sp_sabesp",
    },
    {
        "uf": "SP",
        "data": "2026-09-18",
        "hora": "6h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Operação contra Milton Leite tem 6 suspeitos de integrar o PCC entre 16 alvos de prisão",
        "url": f"{FOLHA}/cotidiano/2026/09/operacao-contra-milton-leite-tem-6-suspeitos-de-integrar-o-pcc-entre-16-alvos-de-prisao.shtml",
        "tema": "crime_organizado",
        "pesa": "prefeitura_sp",
        "consulta": "q_sp_pcc",
    },
    {
        "uf": "SP",
        "data": "2026-09-18",
        "hora": "12h05",
        "veiculo": "Folha de S.Paulo, Mercado",
        "titulo": "Promotoria denuncia ex-diretor da Fazenda de SP por organização criminosa e corrupção",
        "url": f"{FOLHA}/mercado/2026/09/promotoria-denuncia-ex-diretor-da-fazenda-de-sp-por-organizacao-criminosa-e-corrupcao.shtml",
        "tema": "corrupcao_investigacao",
        "pesa": "governo_estadual",
        "consulta": "q_sp_tarcisio",
    },
    {
        "uf": "SP",
        "data": "2026-09-18",
        "hora": "16h36",
        "veiculo": "Folha de S.Paulo, Painel",
        "titulo": "Justiça Eleitoral tem 35 ações sobre impulsionamento negativo contra Tarcísio",
        "url": f"{FOLHA}/colunas/painel/2026/09/justica-eleitoral-tem-35-acoes-sobre-impulsionamento-negativo-contra-tarcisio.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_sp_sabesp",
    },
    {
        "uf": "SP",
        "data": "2026-09-19",
        "hora": "11h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Infiltração do PCC em empresas de ônibus de SP tem 30 anos e se tornou canal para lavagem de dinheiro",
        "url": f"{FOLHA}/cotidiano/2026/09/infiltracao-do-pcc-em-empresas-de-onibus-de-sp-tem-30-anos-e-se-tornou-canal-para-lavagem-de-dinheiro.shtml",
        "tema": "crime_organizado",
        "pesa": "prefeitura_sp",
        "consulta": "q_sp_pcc",
        "destaque": True,
    },
    {
        "uf": "SP",
        "data": "2026-09-20",
        "hora": "18h12",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Operação contra infiltração do PCC no transporte tem 11 alvos com prisões mantidas após audiências",
        "url": f"{FOLHA}/cotidiano/2026/09/operacao-contra-infiltracao-do-pcc-no-transporte-tem-11-alvos-com-prisoes-mantidas-apos-audiencias.shtml",
        "tema": "crime_organizado",
        "pesa": "prefeitura_sp",
        "consulta": "q_sp_pcc",
    },
    {
        "uf": "SP",
        "data": "2026-09-20",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Ônibus de São Paulo em horário de pico são mais lentos que galinha e patinete elétrico",
        "url": f"{FOLHA}/cotidiano/2026/09/onibus-de-sao-paulo-em-horario-de-pico-sao-mais-lentos-que-galinha-e-patinete-eletrico.shtml",
        "tema": "transporte_mobilidade",
        "pesa": "prefeitura_sp",
        "consulta": "q_sp_pcc",
    },
    {
        "uf": "SP",
        "data": "2026-09-20",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Painel",
        "titulo": "Tarcísio aproveita brecha da lei e faz 'visitas técnicas' a obras durante campanha",
        "url": f"{FOLHA}/colunas/painel/2026/09/tarcisio-aproveita-brecha-da-lei-e-faz-visitas-tecnicas-a-obras-durante-campanha.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_sp_tarcisio",
    },
    {
        "uf": "SP",
        "data": "2026-09-21",
        "hora": "14h17",
        "veiculo": "UOL, Agências",
        "titulo": "SP: Tarcísio de Freitas não vai a debate alegando que encontros viraram 'mais do mesmo'",
        "url": f"{UOL}/ultimas-noticias/agencia-estado/2026/09/21/sp-tarcisio-de-freitas-nao-vai-a-debate-alegando-que-encontros-viraram-mais-do-mesmo.htm",
        "tema": "campanha_eleitoral",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_uol_politica",
    },
    {
        "uf": "SP",
        "data": "2026-09-21",
        "hora": "14h30",
        "veiculo": "UOL, Agências",
        "titulo": "Haddad critica privatização de metrô e diz que 'Faria Lima vai ter que esperar'",
        "url": f"{UOL}/ultimas-noticias/agencia-estado/2026/09/21/haddad-critica-privatizacao-de-metro-e-diz-que-faria-lima-vai-ter-que-esperar.htm",
        "tema": "transporte_mobilidade",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_uol_politica",
    },
    {
        "uf": "SP",
        "data": "2026-09-21",
        "hora": "14h49",
        "veiculo": "UOL, Agências",
        "titulo": "Modelo de concessão de rodovias é bom, mas não pode ser feito 'a qualquer custo', diz Haddad",
        "url": f"{UOL}/ultimas-noticias/agencia-estado/2026/09/21/modelo-de-concessao-de-rodovias-e-bom-mas-nao-pode-ser-feito-a-qualquer-custo-diz-haddad.htm",
        "tema": "infraestrutura_concessoes",
        "pesa": "Tarcisio de Freitas",
        "consulta": "q_uol_politica",
    },
    {
        "uf": "MG",
        "data": "2026-08-20",
        "hora": "6h00",
        "veiculo": "Folha de S.Paulo, Painel",
        "titulo": "Promessa de Cleitinho sobre IPVA em Minas contraria entendimento do STF",
        "url": f"{FOLHA}/colunas/painel/2026/08/promessa-de-cleitinho-sobre-ipva-em-minas-contraria-entendimento-do-stf.shtml",
        "tema": "financas_estaduais",
        "pesa": "Cleitinho Azevedo",
        "consulta": "q_mg_ipva",
        "destaque": True,
    },
    {
        "uf": "MG",
        "data": "2026-08-20",
        "hora": "4h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Candidato de última hora, Patrus Ananias disse que entrou para ganhar, mas a pedido de Lula",
        "url": f"{FOLHA}/poder/2026/08/candidato-do-pt-ao-governo-de-minas-patrus-ananias-participa-de-sabatina-folhauol-nesta-quinta.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Patrus Ananias",
        "consulta": "q_mg_patrus",
    },
    {
        "uf": "MG",
        "data": "2026-08-20",
        "hora": "16h30",
        "veiculo": "Folha de S.Paulo, Esporte",
        "titulo": "Governo de MG proíbe publicidade de bets em estádios e espaços públicos do estado",
        "url": f"{FOLHA}/esporte/2026/08/governo-de-mg-proibe-publicidade-de-bets-em-estadios-e-espacos-publicos-do-estado.shtml",
        "tema": "bets_apostas",
        "pesa": "governo_estadual",
        "consulta": "q_mg_simoes",
    },
    {
        "uf": "MG",
        "data": "2026-08-21",
        "hora": "19h18",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Datafolha: Avaliação positiva do governo Mateus Simões em MG é de 23%, e a negativa, de 15%",
        "url": f"{FOLHA}/poder/2026/08/datafolha-avaliacao-positiva-do-governo-mateus-simoes-em-mg-e-de-23-e-a-negativa-de-15.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "Mateus Simoes",
        "consulta": "q_mg_cleitinho",
    },
    {
        "uf": "MG",
        "data": "2026-08-21",
        "hora": "21h46",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Em Minas, Lula diz que adversários mentem e chama Zema de 'comedor de banana com casca'",
        "url": f"{FOLHA}/poder/2026/08/em-minas-lula-diz-que-adversarios-mentem-e-chama-zema-de-comedor-de-banana-com-casca.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Romeu Zema",
        "consulta": "q_mg_divida",
    },
    {
        "uf": "MG",
        "data": "2026-08-27",
        "hora": "16h30",
        "veiculo": "Folha de S.Paulo, Painel",
        "titulo": "Aécio deve anunciar candidatura ao Senado por MG usando brecha na lei eleitoral",
        "url": f"{FOLHA}/colunas/painel/2026/08/aecio-deve-anunciar-candidatura-ao-senado-por-mg-usando-brecha-na-lei-eleitoral.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Aecio Neves",
        "consulta": "q_mg_aecio",
    },
    {
        "uf": "MG",
        "data": "2026-08-28",
        "hora": "16h10",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Aécio Neves volta atrás e confirma candidatura ao Senado por Minas Gerais",
        "url": f"{FOLHA}/poder/2026/08/aecio-neves-volta-atras-e-confirma-candidatura-ao-senado-por-minas-gerais.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Aecio Neves",
        "consulta": "q_mg_aecio",
    },
    {
        "uf": "MG",
        "data": "2026-08-29",
        "hora": "14h26",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Lula exalta Janja e fim da 6x1 em ato de mulheres em MG com protesto de petistas",
        "url": f"{FOLHA}/poder/2026/08/lula-exalta-janja-e-fim-da-6x1-em-ato-de-mulheres-em-mg-com-protesto-de-petistas.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Lula",
        "consulta": "q_mg_patrus",
    },
    {
        "uf": "MG",
        "data": "2026-08-30",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Mercado",
        "titulo": "Contas de Zema em MG têm melhora, mas caixa segue negativo e renúncias disparam",
        "url": f"{FOLHA}/mercado/2026/08/contas-de-zema-em-mg-tem-melhora-mas-caixa-segue-negativo-e-renuncias-disparam.shtml",
        "tema": "financas_estaduais",
        "pesa": "Romeu Zema",
        "consulta": "q_mg_divida",
        "destaque": True,
    },
    {
        "uf": "MG",
        "data": "2026-09-02",
        "hora": "8h00",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Comitê do caso Mariana (MG) aprova troca de escritório e abre crise com advogados britânicos",
        "url": f"{FOLHA}/cotidiano/2026/09/comite-do-caso-mariana-mg-aprova-troca-de-escritorio-e-abre-crise-com-advogados-britanicos.shtml",
        "tema": "meio_ambiente_mineracao",
        "pesa": "nenhum",
        "consulta": "q_mg_samarco",
    },
    {
        "uf": "MG",
        "data": "2026-09-04",
        "hora": "13h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Cleitinho aposta em agendas no interior e mobilização digital como estratégia de campanha em MG",
        "url": f"{FOLHA}/poder/2026/09/cleitinho-aposta-em-agendas-no-interior-e-mobilizacao-digital-como-estrategia-de-campanha-em-mg.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_mg_cleitinho",
    },
    {
        "uf": "MG",
        "data": "2026-09-04",
        "hora": "15h19",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Justiça condena Samarco e três ex-gerentes por tragédia em Mariana (MG)",
        "url": f"{FOLHA}/cotidiano/2026/09/justica-condena-samarco-e-tres-ex-gerentes-por-tragedia-em-mariana-mg.shtml",
        "tema": "meio_ambiente_mineracao",
        "pesa": "nenhum",
        "consulta": "q_mg_samarco",
        "destaque": True,
    },
    {
        "uf": "MG",
        "data": "2026-09-05",
        "hora": "21h55",
        "veiculo": "Folha de S.Paulo, Mercado",
        "titulo": "Justiça suspende licenças da Sigma e paralisa projeto no Vale do Lítio",
        "url": f"{FOLHA}/mercado/2026/09/justica-suspende-licencas-da-sigma-e-paralisa-projeto-no-vale-do-litio.shtml",
        "tema": "meio_ambiente_mineracao",
        "pesa": "governo_estadual",
        "consulta": "q_mg_vale",
    },
    {
        "uf": "MG",
        "data": "2026-09-08",
        "hora": "17h57",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Quaest: Cleitinho lidera com 32% em Minas Gerais; Patrus, Kalil e Simões disputam 2º lugar",
        "url": f"{FOLHA}/poder/2026/09/quaest-cleitinho-lidera-com-32-em-minas-gerais-patrus-kalil-e-simoes-disputam-2o-lugar.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_mg_cleitinho",
    },
    {
        "uf": "MG",
        "data": "2026-09-11",
        "hora": "17h12",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Datafolha: Cleitinho mantém liderança em MG com 37%; Patrus tem 13%, Kalil, 11%",
        "url": f"{FOLHA}/poder/2026/09/datafolha-cletinho-tem-37-e-mantem-lideranca-em-corrida-pelo-governo-de-mg.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_mg_cleitinho",
    },
    {
        "uf": "MG",
        "data": "2026-09-11",
        "hora": "17h21",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Datafolha: disputa pelo Senado em Minas tem empate triplo de Marília Campos (PT), Aécio Neves (PSDB) e Carlos Viana (PSD)",
        "url": f"{FOLHA}/poder/2026/09/datafolha-marilia-campos-tem-12-em-disputa-pelo-senado-em-mg-aecio-neves-e-carlos-viana-marcam-10.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_mg_cleitinho",
    },
    {
        "uf": "MG",
        "data": "2026-09-11",
        "hora": "17h57",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "Desconfianças em série levaram comitê a trocar escritório do caso Mariana, mudança que vai à Justiça",
        "url": f"{FOLHA}/cotidiano/2026/09/desconfiancas-em-serie-levaram-comite-a-trocar-escritorio-do-caso-mariana-mudanca-que-vai-a-justica.shtml",
        "tema": "meio_ambiente_mineracao",
        "pesa": "nenhum",
        "consulta": "q_mg_samarco",
    },
    {
        "uf": "MG",
        "data": "2026-09-14",
        "hora": "16h51",
        "veiculo": "Datafolha",
        "titulo": "Cleitinho (Republicanos) mantém a liderança com 37% das intenções de voto; Patrus (PT) e Kalil (PDT) seguem empatados no segundo lugar",
        "url": f"{DATAFOLHA}/eleicoes/2026/09/cleitinho-republicanos-mantem-a-lideranca-com-37-das-intencoes-de-voto-patrus-pt-e-kalil-pdt-seguem-empatados-no-segundo-lugar.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_mg_cleitinho",
    },
    {
        "uf": "MG",
        "data": "2026-09-16",
        "hora": "6h00",
        "veiculo": "Folha de S.Paulo, Painel",
        "titulo": "Cleitinho é carregado nos ombros em evento por deputado investigado por fraude no INSS",
        "url": f"{FOLHA}/colunas/painel/2026/09/cleitinho-e-carregado-nos-ombros-em-evento-por-deputado-investigado-por-fraude-no-inss.shtml",
        "tema": "corrupcao_investigacao",
        "pesa": "Cleitinho Azevedo",
        "consulta": "q_mg_cleitinho",
        "destaque": True,
    },
    {
        "uf": "MG",
        "data": "2026-09-17",
        "hora": "13h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Candidatos ao Governo de MG se descolam de presidenciáveis em horário eleitoral na TV",
        "url": f"{FOLHA}/poder/2026/09/candidatos-ao-governo-de-mg-se-descolam-de-presidenciaveis-em-horario-eleitoral-na-tv.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Flavio Bolsonaro",
        "consulta": "q_mg_cleitinho",
        "destaque": True,
    },
    {
        "uf": "MG",
        "data": "2026-09-21",
        "hora": None,
        "veiculo": "UOL, Eleições 2026",
        "titulo": "RealTime em MG: Cleitinho sobe e lidera; no 2º turno, empata com Patrus",
        "url": f"{UOL}/eleicoes/2026/09/21/realtime-mg-governo-e-senado.ghtm",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_uol_eleicoes",
    },
    # ------------------------------------------------------------------ RJ
    {
        "uf": "RJ",
        "data": "2026-08-20",
        "hora": "22h08",
        "veiculo": "Folha de S.Paulo, Mônica Bergamo",
        "titulo": "Garotinho acusa ex-advogado de falsificar procuração e pede investigação",
        "url": f"{FOLHA}/colunas/monicabergamo/2026/08/garotinho-acusa-ex-advogado-de-falsificar-procuracao-e-pede-investigacao.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Anthony Garotinho",
        "consulta": "q_rj_garotinho",
    },
    {
        "uf": "RJ",
        "data": "2026-08-21",
        "hora": "18h30",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Datafolha: Eduardo Paes tem 41% no Rio, contra 19% de Douglas Ruas",
        "url": f"{FOLHA}/poder/2026/08/datafolha-eduardo-paes-tem-41-no-rio-contra-19-de-douglas-ruas.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_rj_garotinho",
    },
    {
        "uf": "RJ",
        "data": "2026-08-27",
        "hora": "13h41",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "PMs do Rio são presos sob suspeita de fornecer armas a milícia e ao TCP",
        "url": f"{FOLHA}/cotidiano/2026/08/pms-do-rio-sao-presos-sob-suspeita-de-fornecer-armas-a-milicia-e-ao-tcp.shtml",
        "tema": "seguranca_publica",
        "pesa": "governo_estadual",
        "consulta": "q_rj_milicia",
    },
    {
        "uf": "RJ",
        "data": "2026-08-27",
        "hora": "19h35",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "TRE proíbe Garotinho de usar fundo eleitoral e veicular programa de TV",
        "url": f"{FOLHA}/poder/2026/08/tre-proibe-garotinho-de-usar-fundo-eleitoral-e-veicular-programa-de-tv.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Anthony Garotinho",
        "consulta": "q_rj_ruas",
    },
    {
        "uf": "RJ",
        "data": "2026-08-28",
        "hora": "4h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Vínculos com o crime superam caso Master e corrupção em ataques nas eleições do governo do RJ",
        "url": f"{FOLHA}/poder/2026/08/vinculos-com-o-crime-superam-caso-master-e-corrupcao-em-ataques-nas-eleicoes-do-governo-do-rj.shtml",
        "tema": "crime_organizado",
        "pesa": "nenhum",
        "consulta": "q_rj_ruas",
        "destaque": True,
    },
    {
        "uf": "RJ",
        "data": "2026-08-29",
        "hora": "16h17",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Em Angra, Flávio Bolsonaro defende Angra 3 e licenças para obras de resorts",
        "url": f"{FOLHA}/poder/2026/08/em-angra-flavio-bolsonaro-defende-angra-3-e-licencas-para-obras-de-resorts.shtml",
        "tema": "infraestrutura_concessoes",
        "pesa": "Flavio Bolsonaro",
        "consulta": "q_rj_ruas",
    },
    {
        "uf": "RJ",
        "data": "2026-08-31",
        "hora": "16h00",
        "veiculo": "Folha de S.Paulo, Alvaro Costa e Silva",
        "titulo": "Intervenção no Rio é aprovada pela população",
        "url": f"{FOLHA}/colunas/alvaro-costa-e-silva/2026/08/intervencao-no-rio-e-aprovada-pela-populacao.shtml",
        "tema": "seguranca_publica",
        "pesa": "nenhum",
        "consulta": "q_rj_milicia",
    },
    {
        "uf": "RJ",
        "data": "2026-09-04",
        "hora": "9h21",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Lula avalia indicar governador do RJ ao STF no lugar de Messias, e aliados defendem saída de Andrei",
        "url": f"{FOLHA}/poder/2026/09/lula-avalia-indicar-governador-do-rj-ao-stf-no-lugar-de-messias-e-aliados-defendem-saida-de-andrei.shtml",
        "tema": "judiciario_stf",
        "pesa": "nenhum",
        "consulta": "q_rj_paes",
    },
    {
        "uf": "RJ",
        "data": "2026-09-04",
        "hora": "18h07",
        "veiculo": "Folha de S.Paulo, Mercado",
        "titulo": "Rio pede à União desapropriação da refinaria de Manguinhos, da Refit",
        "url": f"{FOLHA}/mercado/2026/09/rio-pede-a-uniao-desapropriacao-da-refinaria-de-manguinhos-da-refit.shtml",
        "tema": "infraestrutura_concessoes",
        "pesa": "governo_estadual",
        "consulta": "q_rj_cabral",
    },
    {
        "uf": "RJ",
        "data": "2026-09-06",
        "hora": "12h30",
        "veiculo": "Folha de S.Paulo, Mercado",
        "titulo": "Contas do RJ perdem fôlego após impulso de receita extraordinária, e interino tenta reverter déficit",
        "url": f"{FOLHA}/mercado/2026/09/contas-do-rj-perdem-folego-apos-impulso-de-receita-extraordinaria-e-interino-tenta-reverter-deficit.shtml",
        "tema": "financas_estaduais",
        "pesa": "governo_estadual",
        "consulta": "q_mg_divida",
    },
    {
        "uf": "RJ",
        "data": "2026-09-10",
        "hora": "4h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "TRE-RJ amplia regra do TSE contra grupo paramilitar e barra candidato de 'milícia de gravata'",
        "url": f"{FOLHA}/poder/2026/09/tre-rj-amplia-regra-do-tse-contra-grupo-paramilitar-e-barra-candidato-de-milicia-de-gravata.shtml",
        "tema": "justica_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_rj_milicia",
    },
    {
        "uf": "RJ",
        "data": "2026-09-11",
        "hora": "14h51",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "TRE do Rio veta candidatura de Garotinho ao governo estadual",
        "url": f"{FOLHA}/poder/2026/09/tre-do-rio-indefere-candidatura-de-garotinho-ao-governo-estadual.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Anthony Garotinho",
        "consulta": "q_rj_paes",
    },
    {
        "uf": "RJ",
        "data": "2026-09-11",
        "hora": "17h13",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Datafolha: Eduardo Paes (PSD) lidera com 43% das intenções de voto no Rio",
        "url": f"{FOLHA}/poder/2026/09/datafolha-eduardo-paes-lidera-com-49-dos-votos-validos-no-rio.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_rj_paes",
    },
    {
        "uf": "RJ",
        "data": "2026-09-11",
        "hora": "17h27",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Datafolha: Benedita da Silva (PT) lidera com 18% disputa ao Senado no Rio",
        "url": f"{FOLHA}/poder/2026/09/datafolha-benedita-da-silva-lidera-com-18-disputa-ao-senado-no-rio.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_rj_benedita",
    },
    {
        "uf": "RJ",
        "data": "2026-09-12",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Mendonça tratou com Castro sobre prisão de Cabral; ministro diz que atuou apenas com base nos autos",
        "url": f"{FOLHA}/poder/2026/09/mendonca-tratou-com-castro-sobre-prisao-de-cabral-ministro-diz-que-atuou-apenas-com-base-nos-autos.shtml",
        "tema": "corrupcao_investigacao",
        "pesa": "Claudio Castro",
        "consulta": "q_rj_castro",
        "destaque": True,
    },
    {
        "uf": "RJ",
        "data": "2026-09-13",
        "hora": "15h00",
        "veiculo": "Folha de S.Paulo, Painel",
        "titulo": "Mendonça e Castro conversaram sobre Cabral um dia após soltura depender só do STF",
        "url": f"{FOLHA}/colunas/painel/2026/09/mendonca-e-castro-conversaram-sobre-cabral-um-dia-apos-soltura-depender-so-do-stf.shtml",
        "tema": "corrupcao_investigacao",
        "pesa": "Claudio Castro",
        "consulta": "q_rj_castro",
    },
    {
        "uf": "RJ",
        "data": "2026-09-13",
        "hora": "16h49",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Castro diz que procurou Mendonça para saber se havia ordem judicial para não soltar Cabral",
        "url": f"{FOLHA}/poder/2026/09/castro-diz-que-procurou-mendonca-para-saber-se-havia-ordem-judicial-para-nao-soltar-cabral.shtml",
        "tema": "corrupcao_investigacao",
        "pesa": "Claudio Castro",
        "consulta": "q_rj_castro",
    },
    {
        "uf": "RJ",
        "data": "2026-09-14",
        "hora": "16h44",
        "veiculo": "Datafolha",
        "titulo": "Eduardo Paes (PSD) mantém a liderança com 43% das intenções de voto; Douglas Ruas (PL) cresce e tem 25%",
        "url": f"{DATAFOLHA}/eleicoes/2026/09/eduardo-paes-psd-mantem-a-lideranca-com-43-das-intencoes-de-voto-douglas-ruas-pl-cresce-e-tem-25.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_rj_paes",
    },
    {
        "uf": "RJ",
        "data": "2026-09-14",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Paes renunciou à herança durante bloqueio de bens em 2021, e filhos ganharam R$ 13 mi de parentes",
        "url": f"{FOLHA}/poder/2026/09/paes-renunciou-a-heranca-durante-bloqueio-de-bens-em-2021-e-filhos-ganharam-r-13-mi-de-parentes.shtml",
        "tema": "corrupcao_investigacao",
        "pesa": "Eduardo Paes",
        "consulta": "q_rj_paes",
        "destaque": True,
    },
    {
        "uf": "RJ",
        "data": "2026-09-15",
        "hora": "10h23",
        "veiculo": "Folha de S.Paulo, Esporte",
        "titulo": "Concessionária Fla-Flu que gere o Maracanã é alvo de inquérito e multa por gestão",
        "url": f"{FOLHA}/esporte/2026/09/concessionaria-fla-flu-que-gere-o-maracana-e-alvo-de-inquerito-e-multa-por-gestao.shtml",
        "tema": "infraestrutura_concessoes",
        "pesa": "governo_estadual",
        "consulta": "q_rj_seg",
    },
    {
        "uf": "RJ",
        "data": "2026-09-15",
        "hora": "13h36",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "PM de folga é morto a tiros no centro de São Gonçalo (RJ)",
        "url": f"{FOLHA}/cotidiano/2026/09/pm-de-folga-e-morto-a-tiros-no-centro-de-sao-goncalo-rj.shtml",
        "tema": "seguranca_publica",
        "pesa": "governo_estadual",
        "consulta": "q_rj_cv",
    },
    {
        "uf": "RJ",
        "data": "2026-09-16",
        "hora": "4h15",
        "veiculo": "Folha de S.Paulo, Cotidiano",
        "titulo": "CV pratica extorsão em Paraty (RJ) e retalia quem se nega a pagar, relatam moradores e comerciantes",
        "url": f"{FOLHA}/cotidiano/2026/09/cv-pratica-extorsao-em-paraty-rj-e-retalia-quem-se-nega-a-pagar-relatam-moradores-e-comerciantes.shtml",
        "tema": "crime_organizado",
        "pesa": "governo_estadual",
        "consulta": "q_rj_cv",
        "destaque": True,
    },
    {
        "uf": "RJ",
        "data": "2026-09-16",
        "hora": "12h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "TRE usa 'rachadinha' para vetar ex-deputado citado no mesmo relatório de Flávio Bolsonaro",
        "url": f"{FOLHA}/poder/2026/09/tre-usa-rachadinha-para-vetar-ex-deputado-citado-no-mesmo-relatorio-de-flavio-bolsonaro.shtml",
        "tema": "justica_eleitoral",
        "pesa": "Flavio Bolsonaro",
        "consulta": "q_rj_milicia",
    },
    {
        "uf": "RJ",
        "data": "2026-09-19",
        "hora": "23h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Mulher de Ramagem faz campanha virtual com 'candidata de papelão' pelas ruas do RJ",
        "url": f"{FOLHA}/poder/2026/09/mulher-de-ramagem-faz-campanha-virtual-com-candidata-de-papelao-pelas-ruas-do-rj.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_rj_cv",
    },
    {
        "uf": "RJ",
        "data": "2026-09-21",
        "hora": "13h01",
        "veiculo": "Folha de S.Paulo, Alvaro Costa e Silva",
        "titulo": "Candidato bolsonarista finge que Cláudio Castro não existe",
        "url": f"{FOLHA}/colunas/alvaro-costa-e-silva/2026/09/candidato-bolsonarista-finge-que-claudio-castro-nao-existe.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "Douglas Ruas",
        "consulta": "q_rj_castro",
        "destaque": True,
    },
    # ------------------------------------------------------------------ ES
    {
        "uf": "ES",
        "data": "2026-08-27",
        "hora": "20h49",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Quaest mostra Ricardo Ferraço com 35% e Pazolini com 28% na disputa pelo Governo do ES",
        "url": f"{FOLHA}/poder/2026/08/quaest-mostra-ricardo-ferraco-com-35-e-pazolini-com-28-na-disputa-pelo-governo-do-es.shtml",
        "tema": "pesquisa_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_es_casagrande",
        "destaque": True,
    },
    {
        "uf": "ES",
        "data": "2026-08-29",
        "hora": "4h00",
        "veiculo": "Folha de S.Paulo, Poder",
        "titulo": "Faculdade, agronegócio, empreendimento imobiliário; veja bens de candidatos a governador",
        "url": f"{FOLHA}/poder/2026/08/faculdade-agronegocio-empreendimento-imobiliario-veja-bens-de-candidatos-a-governador.shtml",
        "tema": "campanha_eleitoral",
        "pesa": "nenhum",
        "consulta": "q_es_ferraco",
    },
    {
        "uf": "ES",
        "data": "2026-08-30",
        "hora": "9h30",
        "veiculo": "F5, Você viu?",
        "titulo": "Miss que foi destronada após revelar gravidez é internada no Espírito Santo",
        "url": f"{F5}/voceviu/2026/08/miss-que-foi-destronada-apos-revelar-gravidez-e-internada-no-espirito-santo.shtml",
        "tema": "outros",
        "pesa": "nenhum",
        "consulta": "q_es_capixaba",
    },
    {
        "uf": "ES",
        "data": "2026-09-15",
        "hora": None,
        "veiculo": "F5, De faixa a coroa",
        "titulo": "Conheça a trajetória da miss capixaba Eduarda Braum, que foi confirmada em A Fazenda 18",
        "url": f"{F5}/colunistas/de-faixa-a-coroa/2026/09/conheca-a-trajetoria-da-miss-capixaba-eduarda-braum-que-foi-confirmada-em-a-fazenda-18.shtml",
        "tema": "outros",
        "pesa": "nenhum",
        "consulta": "q_es_capixaba",
    },
    {
        "uf": "ES",
        "data": "2026-09-18",
        "hora": "4h00",
        "veiculo": "C-Level, Economia sustentável",
        "titulo": "Alemanha deve investir em usina de metanol verde no Espírito Santo, diz CEO da Atlanteo",
        "url": f"{CLEVEL}/economia-sustentavel/2026/09/alemanha-deve-investir-em-usina-de-metanol-verde-no-espirito-santo-diz-ceo-da-atlanteo.shtml",
        "tema": "infraestrutura_concessoes",
        "pesa": "nenhum",
        "consulta": "q_es_gov",
    },
]

# Pautas com valor, devedor e destinatario identificados no proprio titulo.
# "valor" fica None quando o titulo publicado nao traz cifra.
PAUTAS_MATERIAIS = {
    "SP": [
        {
            "pauta": "Concessão de rodovias ao consórcio Rota Mogiana",
            "valor": "R$ 9,4 bilhões em investimentos previstos",
            "devedor": "Consórcio Rota Mogiana",
            "destinatario": "Governo de São Paulo",
            "url": f"{FOLHA}/colunas/painelsa/2026/08/consorcio-rota-mogiana-assina-com-governo-de-sp-concessao-de-rodovias-com-investimentos-de-r-94-bi.shtml",
        },
        {
            "pauta": "Ressarcimento da CPTM à Trivia Trens após pane",
            "valor": "R$ 24,4 milhões",
            "devedor": "CPTM, empresa do governo estadual",
            "destinatario": "Trivia Trens",
            "url": f"{FOLHA}/cotidiano/2026/09/cptm-vai-ressarcir-trivia-trens-em-r-244-milhoes-durante-gestao-de-linhas-apos-pane.shtml",
        },
        {
            "pauta": "Infiltração do PCC nas concessionárias de ônibus de bairro",
            "valor": None,
            "devedor": "Concessionárias de linhas de bairro de São Paulo",
            "destinatario": "Prefeitura de São Paulo, poder concedente",
            "url": f"{FOLHA}/cotidiano/2026/09/infiltracao-do-pcc-em-empresas-de-onibus-de-sp-tem-30-anos-e-se-tornou-canal-para-lavagem-de-dinheiro.shtml",
        },
        {
            "pauta": "Sabesp encerra a incorporação da Emae",
            "valor": None,
            "devedor": "Sabesp",
            "destinatario": "Acionistas minoritários da Emae",
            "url": f"{CLEVEL}/negocios/2026/09/sabesp-encerra-incorporacao-da-emae-apos-rejeicao-de-oferta-aos-minoritarios.shtml",
        },
        {
            "pauta": "Indenização por spray de pimenta de PM contra idoso",
            "valor": "R$ 10 mil",
            "devedor": "Governo de São Paulo",
            "destinatario": "Vítima",
            "url": f"{FOLHA}/cotidiano/2026/09/governo-tarcisio-perde-recurso-e-tera-de-indenizar-idoso-atingido-por-spray-de-pm.shtml",
        },
    ],
    "MG": [
        {
            "pauta": "Condenação da Samarco e de três ex-gerentes por Mariana",
            "valor": None,
            "devedor": "Samarco",
            "destinatario": "Atingidos pela tragédia de Mariana",
            "url": f"{FOLHA}/cotidiano/2026/09/justica-condena-samarco-e-tres-ex-gerentes-por-tragedia-em-mariana-mg.shtml",
        },
        {
            "pauta": "Contas estaduais: caixa negativo e renúncias fiscais em alta",
            "valor": None,
            "devedor": "Governo de Minas Gerais",
            "destinatario": "Credores e serviços estaduais",
            "url": f"{FOLHA}/mercado/2026/08/contas-de-zema-em-mg-tem-melhora-mas-caixa-segue-negativo-e-renuncias-disparam.shtml",
        },
        {
            "pauta": "Promessa de IPVA de Cleitinho contra o entendimento do STF",
            "valor": None,
            "devedor": "Contribuintes mineiros",
            "destinatario": "Receita estadual",
            "url": f"{FOLHA}/colunas/painel/2026/08/promessa-de-cleitinho-sobre-ipva-em-minas-contraria-entendimento-do-stf.shtml",
        },
        {
            "pauta": "Suspensão de licenças no Vale do Lítio",
            "valor": None,
            "devedor": "Sigma Lithium",
            "destinatario": "Municípios do Jequitinhonha",
            "url": f"{FOLHA}/mercado/2026/09/justica-suspende-licencas-da-sigma-e-paralisa-projeto-no-vale-do-litio.shtml",
        },
        {
            "pauta": "Proibição de publicidade de bets em espaços públicos estaduais",
            "valor": None,
            "devedor": "Casas de apostas",
            "destinatario": "Governo de Minas Gerais",
            "url": f"{FOLHA}/esporte/2026/08/governo-de-mg-proibe-publicidade-de-bets-em-estadios-e-espacos-publicos-do-estado.shtml",
        },
    ],
    "RJ": [
        {
            "pauta": "Desapropriação da refinaria de Manguinhos, da Refit",
            "valor": None,
            "devedor": "Refit",
            "destinatario": "União, a pedido do governo do Rio",
            "url": f"{FOLHA}/mercado/2026/09/rio-pede-a-uniao-desapropriacao-da-refinaria-de-manguinhos-da-refit.shtml",
        },
        {
            "pauta": "Inquérito e multa à concessionária do Maracanã",
            "valor": None,
            "devedor": "Concessionária Flamengo e Fluminense",
            "destinatario": "Governo do Rio de Janeiro",
            "url": f"{FOLHA}/esporte/2026/09/concessionaria-fla-flu-que-gere-o-maracana-e-alvo-de-inquerito-e-multa-por-gestao.shtml",
        },
        {
            "pauta": "Herança e bens da família do candidato líder",
            "valor": "R$ 13 milhões recebidos pelos filhos",
            "devedor": "Parentes de Eduardo Paes",
            "destinatario": "Filhos de Eduardo Paes",
            "url": f"{FOLHA}/poder/2026/09/paes-renunciou-a-heranca-durante-bloqueio-de-bens-em-2021-e-filhos-ganharam-r-13-mi-de-parentes.shtml",
        },
        {
            "pauta": "Déficit das contas estaduais após receita extraordinária",
            "valor": None,
            "devedor": "Governo do Rio de Janeiro",
            "destinatario": "Servidores e serviços estaduais",
            "url": f"{FOLHA}/mercado/2026/09/contas-do-rj-perdem-folego-apos-impulso-de-receita-extraordinaria-e-interino-tenta-reverter-deficit.shtml",
        },
        {
            "pauta": "Extorsão do Comando Vermelho contra comerciantes em Paraty",
            "valor": None,
            "devedor": "Comerciantes e moradores de Paraty",
            "destinatario": "Comando Vermelho",
            "url": f"{FOLHA}/cotidiano/2026/09/cv-pratica-extorsao-em-paraty-rj-e-retalia-quem-se-nega-a-pagar-relatam-moradores-e-comerciantes.shtml",
        },
    ],
    "ES": [
        {
            "pauta": "Usina de metanol verde com capital alemão",
            "valor": None,
            "devedor": "Atlanteo",
            "destinatario": "Espírito Santo",
            "url": f"{CLEVEL}/economia-sustentavel/2026/09/alemanha-deve-investir-em-usina-de-metanol-verde-no-espirito-santo-diz-ceo-da-atlanteo.shtml",
        }
    ],
}

# O que os questionarios de fato perguntaram, lido nos PDFs do repositorio.
PERGUNTAS_DA_PESQUISA = {
    "nacional": {
        "fonte": "docs/fontes/datafolha_21092026_questionario.pdf",
        "blocos_tematicos": [
            "P.2 orgulho ou vergonha de ser brasileiro",
            "P.3 estado emocional diante do Brasil, seis pares",
            "P.4 confiança em oito instituições",
            "P.5 impeachment de ministros do STF e voto para senador",
            "P.6 crise entre Moraes e Mendonça e caso Banco Master",
            "P.7 quais candidatos a crise do STF prejudica",
            "P.8 espectro político dos envolvidos no caso Master",
        ],
        "perguntas_sobre_pauta_estadual": 0,
    },
    "sp": {
        "fonte": "docs/fontes/datafolha_21092026_governador_sp.pdf",
        "tabelas": 13,
        "blocos": [
            "voto para governador, espontâneo, estimulado, válidos e 2º turno",
            "rejeição, decisão e motivação do voto",
            "voto para senador, espontâneo e estimulado nas duas vagas",
            "avaliação e aprovação do trabalho de Tarcísio",
        ],
        "perguntas_sobre_pauta_estadual": 0,
    },
    "mg": {
        "fonte": "docs/fontes/datafolha_21092026_governador_mg.pdf",
        "tabelas": 13,
        "blocos": [
            "voto para governador, espontâneo, estimulado, válidos e 2º turno",
            "rejeição, decisão e motivação do voto",
            "voto para senador, espontâneo e estimulado nas duas vagas",
            "avaliação e aprovação do trabalho de Mateus Simões",
        ],
        "perguntas_sobre_pauta_estadual": 0,
    },
    "rj": {
        "fonte": "docs/fontes/datafolha_21092026_governador_rj.pdf",
        "tabelas": 13,
        "blocos": [
            "voto para governador, espontâneo, estimulado, válidos e 2º turno",
            "rejeição, decisão e motivação do voto",
            "voto para senador, espontâneo e estimulado nas duas vagas",
            "avaliação e aprovação do trabalho de Ricardo Couto",
        ],
        "registro_tse": "RJ-09217/2026 e BR-06361/2026",
        "perguntas_sobre_pauta_estadual": 0,
    },
    "es": {
        "fonte": None,
        "observacao": (
            "O Espírito Santo não aparece no relatório estadual conjunto, que "
            "cobre SP, RJ, MG, DF e PE. Não há pesquisa Datafolha capixaba no "
            "período coberto por este levantamento."
        ),
        "perguntas_sobre_pauta_estadual": 0,
    },
}

LIMITES = [
    "Isto mede o que os veículos do grupo publicaram, não o que deixaram de publicar. Resultado baixo em uma busca não prova ausência de cobertura, e este levantamento não afirma que qualquer veículo escondeu pauta.",
    "As contagens de resultados são as que a busca da Folha devolveu no período declarado. A busca é fuzzy: combina os termos e traz itens que contêm apenas parte deles, então a contagem mede alcance da consulta, não relevância.",
    "A busca do UOL (busca.uol.com.br e noticias.uol.com.br/busca) não respondeu neste ambiente: devolveu página de resultados vazia para todos os termos, inclusive matérias cuja URL já estava em mãos. Os itens do UOL vieram das capas de Eleições 2026 e de Política, lidas em 21/09/2026, e por isso concentram-se nesse dia. Isso é limitação do coletor, não do veículo.",
    "A classificação temática e o campo 'a quem pesa' são juízo editorial desta casa sobre o título publicado, não sobre o conteúdo da matéria, que não foi reproduzido.",
    "Correlação entre pauta publicada e pergunta ausente do questionário não estabelece intenção. O questionário nacional é registrado antes do campo, e a operação sobre o transporte de São Paulo só se tornou pública em 17/09, dois dias depois de o campo nacional começar e sete depois de o campo estadual fechar.",
    "A cobertura estadual capixaba tem casa própria na imprensa local, fora do alcance desta busca. O que este levantamento mostra é a presença do ES no noticiário do grupo contratante, não a cobertura total sobre o estado.",
    "As três pesquisas estaduais de governador (SP, RJ e MG) têm a mesma estrutura de 13 tabelas. O ES não tem pesquisa Datafolha no período, e o relatório estadual conjunto cobre SP, RJ, MG, DF e PE.",
]

LEITURA = (
    "Entre 20 de agosto e 21 de setembro de 2026 o grupo que contratou e "
    "publicou a pesquisa noticiou, nos quatro estados do Sudeste, pautas "
    "materiais com valor, devedor e destinatário: concessão de rodovias de "
    "R$ 9,4 bilhões e ressarcimento de R$ 24,4 milhões a uma operadora de "
    "trens em São Paulo, caixa negativo em Minas, déficit e desapropriação de "
    "refinaria no Rio. Os questionários aplicados nos mesmos dias não têm uma "
    "pergunta sobre nenhuma delas. Os três instrumentos estaduais medem voto, "
    "rejeição, decisão, motivação e aprovação do governador; o nacional mede "
    "emoção, confiança institucional, o STF e o caso Banco Master."
)


def _valida() -> None:
    urls = [item["url"] for item in ITENS]
    assert len(urls) == len(set(urls)), "URL repetida na linha do tempo"
    ids = {consulta["id"] for consulta in CONSULTAS}
    for item in ITENS:
        assert item["uf"] in UFS, item
        assert item["tema"] in TEMAS, item
        assert item["pesa"] in PESA, item
        assert item["consulta"] in ids, item
        assert PERIODO["inicio"] <= item["data"] <= PERIODO["fim"], item
        assert any(dominio in item["url"] for dominio in DOMINIOS), item


def _conta(chave: str) -> dict[str, dict[str, int]]:
    tabela: dict[str, Counter] = defaultdict(Counter)
    for item in ITENS:
        tabela[item["uf"]][item[chave]] += 1
    return {
        uf: dict(sorted(tabela[uf].items(), key=lambda par: (-par[1], par[0])))
        for uf in UFS
    }


def main() -> None:
    _valida()
    por_uf = Counter(item["uf"] for item in ITENS)
    por_veiculo = Counter(
        (
            "UOL"
            if "uol.com.br/" in item["url"] and "folha" not in item["url"]
            else "Folha"
        )
        for item in ITENS
    )
    payload = {
        "pergunta": (
            "O que o Grupo Folha publicou sobre SP, RJ, MG e ES no mês anterior "
            "à divulgação, e o que a pesquisa do próprio grupo perguntou sobre isso."
        ),
        "periodo": PERIODO,
        "campo": CAMPO,
        "metodo": (
            "Coleta manual na busca do proprio veiculo, com filtro de periodo, e "
            "nas capas de seccao do UOL. Consultas declaradas e reproduziveis. "
            "Cada item traz o titulo exato e o carimbo de data do veiculo. "
            "Nenhum trecho de materia foi reproduzido."
        ),
        "consultas": CONSULTAS,
        "temas": TEMAS,
        "pesa_opcoes": PESA,
        "itens": ITENS,
        "total_itens": len(ITENS),
        "itens_por_uf": {uf: por_uf[uf] for uf in UFS},
        "itens_por_veiculo": dict(por_veiculo),
        "por_uf_tema": _conta("tema"),
        "por_uf_pesa": _conta("pesa"),
        "pautas_materiais": PAUTAS_MATERIAIS,
        "perguntas_da_pesquisa": PERGUNTAS_DA_PESQUISA,
        "limites": LIMITES,
        "leitura": LEITURA,
    }
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(payload, ensure_ascii=False, indent=2)
    (ANALYSIS / "cobertura_sudeste.json").write_text(texto + "\n", encoding="utf-8")
    (ASSETS / "datafolha_21092026_cobertura_sudeste.json").write_text(
        texto + "\n", encoding="utf-8"
    )
    print(f"itens: {len(ITENS)}  consultas: {len(CONSULTAS)}")
    for uf in UFS:
        temas = _conta("tema")[uf]
        topo = ", ".join(f"{tema} {n}" for tema, n in list(temas.items())[:3])
        print(f"  {uf}: {por_uf[uf]:>2} itens | {topo}")


if __name__ == "__main__":
    main()
