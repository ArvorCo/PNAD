#!/usr/bin/env python3
"""Tests for Dashboard v2.0 - Annual income composition analysis."""

import sys
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pytest
from pnad import (
    _detect_income_col,
    _detect_income_source_cols,
    _detect_pnad_mode,
    _calculate_household_income_sources,
    _aggregate_income_by_category,
    _calculate_dependency_score,
    INCOME_SOURCE_COLS,
    INCOME_CATEGORIES,
)


class TestDetectIncomeCol:
    """Tests for _detect_income_col with anual mode support."""
    
    def test_detect_vd5001_anual(self):
        """Should prefer VD5001 when present (anual mode)."""
        headers = ["dom_id", "VD5001__rend_efetivo_domiciliar", "VD4020__rendim_efetivo_qq_trabalho"]
        result = _detect_income_col(headers, None)
        assert result.startswith("VD5001")
    
    def test_detect_vd4020_trimestral(self):
        """Should use VD4020 when VD5001 not present (trimestral mode)."""
        headers = ["dom_id", "VD4020__rendim_efetivo_qq_trabalho", "VD4019"]
        result = _detect_income_col(headers, None)
        assert result.startswith("VD4020")
    
    def test_detect_vd4019_fallback(self):
        """Should fall back to VD4019 if VD4020 not present."""
        headers = ["dom_id", "VD4019__rendim_habitual"]
        result = _detect_income_col(headers, None)
        assert result.startswith("VD4019")
    
    def test_explicit_override(self):
        """Should use explicitly requested column."""
        headers = ["dom_id", "VD5001__renda", "custom_income"]
        result = _detect_income_col(headers, "custom_income")
        assert result == "custom_income"
    
    def test_raises_when_not_found(self):
        """Should raise when no income column is found."""
        headers = ["dom_id", "UF", "V2007"]
        with pytest.raises(ValueError, match="could not auto-detect income column"):
            _detect_income_col(headers, None)


class TestDetectIncomeSourceCols:
    """Tests for _detect_income_source_cols."""
    
    def test_detect_all_sources(self):
        """Should detect all V50xxA2 income source columns."""
        headers = [
            "dom_id",
            "V5001A2__rend_recebido_de_bpc_loas",
            "V5002A2__rend_recebido_de_bolsa_familia",
            "V5003A2__rend_recebido_de_outro_prog_social",
            "V5004A2__rend_recebido_de_aposentadoria_e_pensao",
            "V5005A2__rend_recebido_de_seguro_desemprego",
            "V5006A2__rend_recebido_por_pensao_alimenticia",
            "V5007A2__rend_recebido_aluguel",
            "V5008A2__rend_recebido_outros",
        ]
        result = _detect_income_source_cols(headers)
        
        assert "bpc_loas" in result
        assert "bolsa_familia" in result
        assert "outros_sociais" in result
        assert "aposentadoria_pensao" in result
        assert "seguro_desemprego" in result
        assert "pensao_doacao" in result
        assert "aluguel" in result
        assert "outros_capital" in result
        assert len(result) == 8
    
    def test_partial_detection(self):
        """Should detect only available columns."""
        headers = [
            "dom_id",
            "V5002A2__bolsa_familia",
            "V5004A2__aposentadoria",
        ]
        result = _detect_income_source_cols(headers)
        
        assert "bolsa_familia" in result
        assert "aposentadoria_pensao" in result
        assert "bpc_loas" not in result
        assert len(result) == 2
    
    def test_empty_when_no_sources(self):
        """Should return empty dict when no source columns present."""
        headers = ["dom_id", "UF", "VD5001"]
        result = _detect_income_source_cols(headers)
        assert result == {}


class TestDetectPnadMode:
    """Tests for _detect_pnad_mode."""
    
    def test_detect_anual_mode(self):
        """Should detect anual mode when VD5001 present."""
        headers = ["dom_id", "VD5001__rend_efetivo_domiciliar", "V5002A2__bolsa"]
        result = _detect_pnad_mode(headers)
        assert result == "anual"
    
    def test_detect_trimestral_mode(self):
        """Should detect trimestral mode when VD5001 not present."""
        headers = ["dom_id", "VD4020__rendim_efetivo_qq_trabalho"]
        result = _detect_pnad_mode(headers)
        assert result == "trimestral"


class TestCalculateHouseholdIncomeSources:
    """Tests for _calculate_household_income_sources."""
    
    def test_calculate_sources_with_all_data(self):
        """Should calculate income from each source including trabalho."""
        row = {
            "VD5001__total": "5000",
            "V5001A2__bpc": "500",
            "V5002A2__bf": "300",
            "V5003A2__outros": "200",
            "V5004A2__aposent": "1000",
            "V5005A2__seguro": "0",
            "V5006A2__pensao": "0",
            "V5007A2__aluguel": "0",
            "V5008A2__outros": "0",
        }
        source_cols = {
            "bpc_loas": "V5001A2__bpc",
            "bolsa_familia": "V5002A2__bf",
            "outros_sociais": "V5003A2__outros",
            "aposentadoria_pensao": "V5004A2__aposent",
            "seguro_desemprego": "V5005A2__seguro",
            "pensao_doacao": "V5006A2__pensao",
            "aluguel": "V5007A2__aluguel",
            "outros_capital": "V5008A2__outros",
        }
        
        result = _calculate_household_income_sources(row, "VD5001__total", source_cols)
        
        assert result["bpc_loas"] == 500
        assert result["bolsa_familia"] == 300
        assert result["outros_sociais"] == 200
        assert result["aposentadoria_pensao"] == 1000
        assert result["trabalho"] == 3000  # 5000 - (500+300+200+1000)
    
    def test_trabalho_never_negative(self):
        """Trabalho should never be negative even if sources exceed total."""
        row = {
            "VD5001__total": "1000",
            "V5001A2__bpc": "800",
            "V5004A2__aposent": "500",
        }
        source_cols = {
            "bpc_loas": "V5001A2__bpc",
            "aposentadoria_pensao": "V5004A2__aposent",
        }
        
        result = _calculate_household_income_sources(row, "VD5001__total", source_cols)
        
        assert result["trabalho"] == 0.0  # max(0, 1000 - 1300)
    
    def test_handles_missing_values(self):
        """Should treat missing values as zero."""
        row = {
            "VD5001__total": "1000",
            "V5001A2__bpc": "",
            "V5002A2__bf": None,
        }
        source_cols = {
            "bpc_loas": "V5001A2__bpc",
            "bolsa_familia": "V5002A2__bf",
        }
        
        result = _calculate_household_income_sources(row, "VD5001__total", source_cols)
        
        assert result["bpc_loas"] == 0.0
        assert result["bolsa_familia"] == 0.0
        assert result["trabalho"] == 1000.0


class TestAggregateIncomeByCategory:
    """Tests for _aggregate_income_by_category."""
    
    def test_aggregate_categories(self):
        """Should aggregate sources into correct categories."""
        sources = {
            "trabalho": 3000,
            "bpc_loas": 100,
            "bolsa_familia": 200,
            "outros_sociais": 50,
            "aposentadoria_pensao": 1000,
            "seguro_desemprego": 0,
            "pensao_doacao": 100,
            "aluguel": 200,
            "outros_capital": 50,
        }
        
        result = _aggregate_income_by_category(sources)
        
        assert result["trabalho"] == 3000
        assert result["beneficios_sociais"] == 350  # 100+200+50
        assert result["previdencia"] == 1000
        assert result["seguro"] == 0
        assert result["transferencias_privadas"] == 100
        assert result["capital"] == 250  # 200+50


class TestCalculateDependencyScore:
    """Tests for _calculate_dependency_score."""
    
    def test_high_dependency(self):
        """Should return high score when mostly benefits/previdencia."""
        score = _calculate_dependency_score(
            benefits_pct=30.0,
            previdencia_pct=40.0,
            work_pct=30.0,
        )
        assert score == 70.0  # 30+40
    
    def test_low_dependency(self):
        """Should return low score when mostly work income."""
        score = _calculate_dependency_score(
            benefits_pct=5.0,
            previdencia_pct=10.0,
            work_pct=85.0,
        )
        assert score == 15.0  # 5+10
    
    def test_zero_dependency(self):
        """Should return zero when all from work."""
        score = _calculate_dependency_score(
            benefits_pct=0.0,
            previdencia_pct=0.0,
            work_pct=100.0,
        )
        assert score == 0.0


class TestIncomeSourceConstants:
    """Tests for income source constants."""
    
    def test_income_source_cols_complete(self):
        """Should have all 8 income source columns defined."""
        assert len(INCOME_SOURCE_COLS) == 8
        expected_keys = [
            "bpc_loas", "bolsa_familia", "outros_sociais",
            "aposentadoria_pensao", "seguro_desemprego",
            "pensao_doacao", "aluguel", "outros_capital"
        ]
        for key in expected_keys:
            assert key in INCOME_SOURCE_COLS
    
    def test_income_categories_complete(self):
        """Should have all 6 income categories defined."""
        assert len(INCOME_CATEGORIES) == 6
        expected_cats = [
            "trabalho", "beneficios_sociais", "previdencia",
            "seguro", "transferencias_privadas", "capital"
        ]
        for cat in expected_cats:
            assert cat in INCOME_CATEGORIES
    
    def test_all_sources_in_categories(self):
        """All income sources should be mapped to a category."""
        all_sources_in_categories = set()
        for cat, sources in INCOME_CATEGORIES.items():
            if cat != "trabalho":  # trabalho is calculated, not from a column
                all_sources_in_categories.update(sources)
        
        for source in INCOME_SOURCE_COLS.keys():
            assert source in all_sources_in_categories, f"{source} not in any category"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
