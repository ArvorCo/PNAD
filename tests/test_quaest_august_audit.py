"""Guard rails for the August 2026 Genial/Quaest dossier.

The report's charts are images without a text layer, so every number in the
public pages comes from a manual transcription. These tests keep the three
artifacts in agreement: the transcription in the audit script, the derived
numbers in the JSON, and the figures printed in the HTML.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/assets/quaest_082026_data.json"
DOSSIER = ROOT / "docs/quaest_082026.html"
THREAD = ROOT / "docs/quaest_082026_thread.html"


@pytest.fixture(scope="module")
def payload() -> dict:
    if not DATA.exists():
        pytest.skip("run scripts/quaest-august-audit.py first")
    return json.loads(DATA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pages() -> dict[str, str]:
    return {
        "dossiê": DOSSIER.read_text(encoding="utf-8"),
        "thread": THREAD.read_text(encoding="utf-8"),
    }


def brl(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def test_bloc_shares_close_the_electorate(payload: dict) -> None:
    assert sum(payload["report"]["bloc_shares"].values()) == 100


def test_first_round_columns_are_faithful_to_the_report(payload: dict) -> None:
    """Each positioning column must land within rounding distance of 100."""
    for bloc, votes in payload["report"]["first_round_by_bloc"].items():
        total = sum(votes.values())
        assert 98 <= total <= 101, f"{bloc} soma {total}"


def test_runoff_columns_are_faithful_to_the_report(payload: dict) -> None:
    for bloc, votes in payload["report"]["runoff_by_bloc"].items():
        assert sum(votes.values()) == 100, bloc


def test_reconstruction_reproduces_the_published_topline(payload: dict) -> None:
    """The transcription is only usable if it rebuilds the published score."""
    for scope in ("first_round", "runoff"):
        for row in payload["strategy"]["reconstruction"][scope]:
            assert 0 <= row["residual"] <= 1.2, (scope, row)


def test_income_bands_are_a_closed_partition(payload: dict) -> None:
    assert sum(payload["report"]["income_shares"].values()) == 100


def test_addressable_gap_beats_the_runoff_distance(payload: dict) -> None:
    partition = payload["strategy"]["conversion"]["income_partition"]
    assert partition["national_unconverted"] > partition["runoff_gap"]


def test_flavio_is_the_shortest_distance_of_the_four_scenarios(payload: dict) -> None:
    scenarios = payload["strategy"]["substitution"]["scenarios"]
    best = min(scenarios, key=lambda row: row["gap"])
    assert best["challenger"] == "Flávio Bolsonaro"
    assert [row["gap"] for row in scenarios] == [5, 8, 10, 12]


def test_lula_barely_moves_across_scenarios(payload: dict) -> None:
    low, high = payload["strategy"]["substitution"]["lula_range"]
    assert high - low <= 2


def test_third_way_split_adds_up(payload: dict) -> None:
    useful = payload["strategy"]["useful_vote"]
    total = sum(row["third_way_national"] for row in useful["rows"])
    assert round(total, 2) == useful["third_way_total"]


def test_program_reach_is_the_product_of_the_two_published_rates(payload: dict) -> None:
    for row in payload["strategy"]["programs"]["rows"]:
        expected = round(row["reached_pct"] * row["felt_a_lot_pct_of_reached"] / 100, 2)
        assert row["felt_a_lot_national"] == expected


@pytest.mark.parametrize(
    "path",
    [
        ("strategy", "conversion", "income_partition", "national_unconverted"),
        ("strategy", "useful_vote", "third_way_total"),
        ("strategy", "useful_vote", "third_way_inside_right"),
        ("strategy", "useful_vote", "parked_total"),
        ("strategy", "useful_vote", "slack_inside_right"),
    ],
)
def test_headline_numbers_are_printed_in_the_dossier(
    payload: dict, pages: dict[str, str], path: tuple[str, ...]
) -> None:
    node: object = payload
    for key in path:
        node = node[key]  # type: ignore[index]
    assert isinstance(node, (int, float))
    assert brl(float(node)) in pages["dossiê"], f"{path} = {brl(float(node))}"


def test_no_em_dash_in_public_pages(pages: dict[str, str]) -> None:
    for name, html in pages.items():
        assert "—" not in html, f"travessão encontrado em {name}"


def test_thread_posts_are_long_form(pages: dict[str, str]) -> None:
    """The X long-form target for this series is 1000 to 2000 characters."""
    blocks = re.findall(
        r'<div class="copy"><span class="cc">(\d+) chars</span>(.*?)</div>',
        pages["thread"],
        re.S,
    )
    assert len(blocks) == 22
    for declared, body in blocks:
        text = re.sub(r"<[^>]+>", "", body)
        assert int(declared) == len(text)
        assert 1000 <= len(text) <= 2000


def test_svg_labels_stay_inside_their_viewbox(pages: dict[str, str]) -> None:
    """Catches truncated captions after any type-size change."""
    for name, html in pages.items():
        for overflow in _svg_overflows(html):
            pytest.fail(f"{name}: texto fora da caixa {overflow}")


def _svg_overflows(html: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for svg in re.finditer(
        r'<svg[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"(.*?)</svg>', html, re.S
    ):
        view_width, body = float(svg.group(1)), svg.group(3)
        stack: list[str] = []
        for token in re.finditer(
            r"<g([^>]*)>|</g>|<text([^>]*)>(.*?)</text>", body, re.S
        ):
            raw = token.group(0)
            if raw.startswith("</g"):
                if stack:
                    stack.pop()
                continue
            if raw.startswith("<g"):
                stack.append(token.group(1))
                continue
            attrs = token.group(2)
            text = re.sub(r"<[^>]+>", "", token.group(3))

            def attribute(name: str, default: str, scope: str = attrs) -> str:
                direct = re.search(rf'{name}="([^"]+)"', scope)
                if direct:
                    return direct.group(1)
                for group in reversed(stack):
                    inherited = re.search(rf'{name}="([^"]+)"', group)
                    if inherited:
                        return inherited.group(1)
                return default

            x = float(attribute("x", "0"))
            size = float(attribute("font-size", "13"))
            family = attribute("font-family", "")
            anchor = attribute("text-anchor", "start")
            per_char = (
                0.60 if "Mono" in family else 0.50 if "Archivo" in family else 0.47
            )
            width = len(text) * size * per_char
            left = (
                x - width
                if anchor == "end"
                else x - width / 2 if anchor == "middle" else x
            )
            if left < -3 or left + width > view_width + 3:
                found.append((int(view_width), text[:60]))
    return found


def test_substitution_scoreboard_matches_the_published_text(
    payload: dict, pages: dict[str, str]
) -> None:
    """The 12/1/6 count is quoted in both pages and must follow the data."""
    segments = payload["strategy"]["substitution"]["segments"]
    wins = sum(1 for row in segments if row["gap_to_best"] > 0)
    ties = sum(1 for row in segments if row["gap_to_best"] == 0)
    losses = sum(1 for row in segments if row["gap_to_best"] < 0)
    assert (wins, ties, losses) == (12, 1, 6)
    for name, html in pages.items():
        assert f"{wins} dos {len(segments)} recortes" in html, name


def test_caiado_beats_flavio_in_five_segments(payload: dict) -> None:
    segments = payload["strategy"]["substitution"]["segments"]
    better = [
        row["segment"]
        for row in segments
        if row["all"]["Ronaldo Caiado"] > row["flavio"]
    ]
    assert len(better) == 5
    assert "5+ SM" in better and "Superior" in better


def test_questionnaire_blocks_cover_the_109_items(payload: dict) -> None:
    balance = payload["strategy"]["questionnaire_balance"]
    assert balance["totals"]["items"] == 109
    assert balance["totals"]["opposition_policy_items"] == 0


def test_bolsonaro_block_is_mostly_episode(payload: dict) -> None:
    """14 of the 15 items about Flávio are episodes, and the pages say so."""
    blocks = payload["strategy"]["questionnaire_balance"]["blocks"]
    flavio = [row for row in blocks if row["onus"] == "Flávio"]
    episodes = [row for row in flavio if row["tipo"] == "episódio"]
    assert sum(row["items"] for row in flavio) == 15
    assert sum(row["items"] for row in episodes) == 14


def test_press_ledger_only_lists_recovered_pieces(payload: dict) -> None:
    press = payload["strategy"]["press"]
    assert len(press["pieces"]) == 15
    assert len(press["outlets"]) == 12
    assert press["economy_block_pieces"] == 0
    assert press["recovery_check"], "o zero precisa vir com a trilha de auditoria"
    assert sum(press["frames"].values()) == len(press["pieces"])
    for piece in press["pieces"]:
        assert piece["url"].startswith("https://")


def test_public_pages_never_compare_across_waves(pages: dict[str, str]) -> None:
    """Cobertura de outras ondas fica no JSON, nunca no texto público."""
    for name, html in pages.items():
        for wave in press_other_wave_markers():
            assert wave not in html, f"{name} cita cobertura de outra onda: {wave}"


def press_other_wave_markers() -> list[str]:
    return [
        "Itatiaia",
        "13 de maio",
        "15 de abril",
        "Preços pesam no bolso do eleitor",
        "Eleitor de Lula sente mais a perda",
    ]


def test_press_limit_is_stated_in_the_dossier(pages: dict[str, str]) -> None:
    """Never claim absence of coverage, only absence of recovery."""
    assert "não recuperamos a peça, não que ela não exista" in pages["dossiê"]
    assert "não recuperamos a peça, não que ela não exista" in pages["thread"]
