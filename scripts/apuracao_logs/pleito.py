"""Caminhos e dia de votação por pleito: 3220 (1º turno) e 3221 (2º turno) de 2026.

Os padrões do 1º turno continuam os mesmos dos módulos antigos (`coleta.DESTINO`,
`coleta.ORIGEM`, `processamento.METRICAS`, `publicacao.PUBLICO`). O 2º turno usa
bancos próprios, para nunca misturar originais nem métricas dos dois turnos.

Em 2026 a carga das urnas de setembro serviu aos dois turnos: o log do 2º turno
carrega também a preparação e o dia 04/10. O leitor retém só o dia de votação do
pleito (e o seguinte, para encerramentos após a meia-noite); o resto entra apenas
como metadado anterior (identidade, modelo, código de carga).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Pleito:
    numero: int
    dia: str  # dd/mm/aaaa, dia de votação
    dia_seguinte: str
    origem: Path  # banco de BUs por seção (somente leitura)
    raw: Path  # originais dos logs
    metricas: Path
    publico: Path
    analise: Path
    complementos: Path
    lacunas: Path

    @property
    def dias(self) -> dict[str, int]:
        return {self.dia: 0, self.dia_seguinte: 86400}

    @property
    def dia_ordem(self) -> str:
        """aaaammdd, para comparar carimbos dd/mm/aaaa."""
        return self.dia[6:10] + self.dia[3:5] + self.dia[:2]

    @property
    def base(self) -> str:
        return (
            "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/"
            f"{self.numero}/dados"
        )

    @property
    def prefixo_arquivo(self) -> str:
        return f"o{self.numero:05d}"


PLEITOS = {
    3220: Pleito(
        numero=3220,
        dia="04/10/2026",
        dia_seguinte="05/10/2026",
        origem=ROOT / "apuracao/data/secoes_2026.sqlite",
        raw=ROOT / "data/raw/tse_logs_2026/logs.sqlite",
        metricas=ROOT / "data/outputs/logs_urnas_2026.sqlite",
        publico=ROOT / "docs/assets/logs_urnas_2026",
        analise=ROOT / "analysis/apuracao_2026/logs_urnas",
        complementos=ROOT / "analysis/apuracao_2026/logs_urnas/complementos.json",
        lacunas=ROOT / "analysis/apuracao_2026/logs_urnas/lacunas.json",
    ),
    3221: Pleito(
        numero=3221,
        dia="25/10/2026",
        dia_seguinte="26/10/2026",
        origem=ROOT / "apuracao/data/secoes_2t_2026.sqlite",
        raw=ROOT / "data/raw/tse_logs_2026/logs_2t.sqlite",
        metricas=ROOT / "data/outputs/logs_urnas_2t_2026.sqlite",
        publico=ROOT / "docs/assets/logs_urnas_2t_2026",
        analise=ROOT / "analysis/apuracao_2t_2026/logs_urnas",
        complementos=ROOT / "analysis/apuracao_2t_2026/logs_urnas/complementos.json",
        lacunas=ROOT / "analysis/apuracao_2t_2026/logs_urnas/lacunas.json",
    ),
}
PRIMEIRO = PLEITOS[3220]


def obter(numero: int) -> Pleito:
    if numero not in PLEITOS:
        raise ValueError("pleito 3220 (1º turno) ou 3221 (2º turno)")
    return PLEITOS[numero]
