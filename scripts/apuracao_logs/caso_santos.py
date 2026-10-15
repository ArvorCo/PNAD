"""Exibição do caso comunicado por leitor, a partir de evidências conferidas."""

from html import escape

FONTE_INSPECAO = "https://www.justicaeleitoral.jus.br/mesario/cursos/mesarios-brasil/m3-o-que-fazer-durante-a-votacao/a6-cabina-de-votacao/index.html"


def hora(s):
    return f"{s//3600:02d}:{s//60%60:02d}:{s%60:02d}"


def painel(d):
    r = next(
        (
            r
            for r in d.get("casos_conferidos", [])
            if r["tipo"] == "inspecoes_sem_reinicio"
        ),
        None,
    )
    if not r:
        return ""
    itens = []
    for e in r["ocorrencias"]:
        if e["tipo"] == "inspecao":
            descricao = f'Inspeção · {e["fim_s"]-e["segundo"]} segundos · até {hora(e["fim_s"])}'
        else:
            descricao = "Cancelamento de habilitação"
        itens.append(
            f'<li><time>{hora(e["segundo"])}</time><span>{descricao}</span></li>'
        )
    return f"""<article class="caso-destaque" id="santos-273-214">
<p class="etiqueta">Conferência solicitada por leitor · Santos / SP</p>
<h3>Zona 273, seção 214.<br>O que o arquivo permite confirmar.</h3>
<p>O arquivo registra uma partida antes da abertura e nenhum reinício ou ERRO/FATAL durante a votação. Há sete inspeções, nove retomadas após inatividade e um cancelamento de habilitação. Os <b>275 cômputos fecham com o BU</b>, inclusive nas três categorias de identificação.</p>
<div class="medidas-caso"><div><b>73 s</b><span>mediana do processo observado</span></div><div><b>52 s</b><span>mediana após habilitação</span></div><div><b>97 s</b><span>mediana entre cômputos</span></div></div>
<details><summary>Horários das inspeções e do cancelamento</summary><ol class="linha-operacional">{"".join(itens)}</ol><p>Carimbos do log em 04/10/2026. Nenhum horário de voto individual é exibido.</p></details>
<p><b>O que ficou de fora da busca anterior:</b> inspeções, cancelamentos e retomadas da digitação eram mensagens informativas. Não apareciam no filtro de ERRO/FATAL. Agora a ficha mostra esses registros mesmo quando não ultrapassam os limiares de triagem.</p>
<p class="nota">O relato está vinculado à seção correta, mas sem horário. O log não confirma o reinício; para cruzar o episódio, falta a ata. Ausência de registro não descarta ocorrência fora do log.</p>
<p>A <a href="{FONTE_INSPECAO}">orientação oficial de 2026</a> prevê inspeções periódicas acompanhadas pelos fiscais presentes. Isso é uma explicação possível para a convocação, não a identificação do episódio relatado.</p>
<p><a href="politizesuavizinhanca.html#s=SP-273-214">Abrir a ficha completa da seção →</a> · <a href="{escape(r["url"])}">Original oficial</a></p>
<p class="arquivo-hash">SHA-256: <code>{r["sha256"]}</code></p></article>"""
