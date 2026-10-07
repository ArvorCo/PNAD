from senado_2027.pagina import fixo

FUNCOES = [
    fixo.aula_estagios,
    fixo.aula_rito,
    fixo.o_que_nao_e,
    fixo.como_ler_ficha,
    fixo.checklist_leitor,
]
TERMOS = [
    "Lei 1.079",
    "dois terços",
    "três quintos",
    "admissibilidade",
    "inquérito",
    "réu",
]


def test_sem_travessao_sem_placeholder_e_tamanho_minimo():
    for fn in FUNCOES:
        html = fn()
        assert isinstance(html, str)
        assert "—" not in html, fn.__name__
        assert "{{" not in html, fn.__name__
        assert "<h3>" in html and "<p>" in html, fn.__name__
        assert len(html) >= 600, fn.__name__


def test_termos_chave_presentes():
    tudo = " ".join(fn() for fn in FUNCOES)
    for termo in TERMOS:
        assert termo in tudo, termo


def test_cada_aula_tem_analogia():
    for fn in FUNCOES:
        assert "analogy" in fn(), fn.__name__
