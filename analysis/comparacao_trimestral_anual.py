#!/usr/bin/env python3
"""
Comparação PNAD Trimestral vs Anual
Mostra a diferença quando se considera TODAS as fontes de renda
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

os.makedirs("analysis/charts", exist_ok=True)

# =============================================================================
# DADOS EXTRAÍDOS DOS DASHBOARDS
# =============================================================================

# PNAD TRIMESTRAL (só renda do trabalho - VD4020)
trimestral = {
    "nome": "Trimestral (só trabalho)",
    "renda_col": "VD4020",
    "domicilios": 79_744_596,
    "pessoas": 212_929_807,
    "media_sm": 2.789,
    "mediana_sm": 1.557,
    "gini": 0.628,
    "faixa_0_2": 58.81,
    "faixa_2_5": 27.08,
    "faixa_5_10": 9.57,
    "faixa_10_plus": 4.55,
    # Top/Bottom UFs
    "top_uf": "Distrito Federal",
    "top_uf_sm": 5.444,
    "bottom_uf": "Maranhão",
    "bottom_uf_sm": 1.574,
}

# PNAD ANUAL (todas as fontes - VD5001)
anual = {
    "nome": "Anual (todas as fontes)",
    "renda_col": "VD5001",
    "domicilios": 78_276_741,
    "pessoas": 211_852_978,
    "media_sm": 3.565,
    "mediana_sm": 2.156,
    "gini": 0.520,
    "faixa_0_2": 47.19,
    "faixa_2_5": 34.65,
    "faixa_5_10": 12.27,
    "faixa_10_plus": 5.89,
    # Top/Bottom UFs
    "top_uf": "Distrito Federal",
    "top_uf_sm": 6.514,
    "bottom_uf": "Maranhão",
    "bottom_uf_sm": 2.023,
}

# Calcular diferenças
diff = {
    "media_sm": ((anual["media_sm"] - trimestral["media_sm"]) / trimestral["media_sm"]) * 100,
    "mediana_sm": ((anual["mediana_sm"] - trimestral["mediana_sm"]) / trimestral["mediana_sm"]) * 100,
    "gini": ((anual["gini"] - trimestral["gini"]) / trimestral["gini"]) * 100,
    "faixa_0_2": anual["faixa_0_2"] - trimestral["faixa_0_2"],
    "faixa_10_plus": anual["faixa_10_plus"] - trimestral["faixa_10_plus"],
}

print("="*60)
print("COMPARAÇÃO PNAD TRIMESTRAL vs ANUAL")
print("="*60)
print(f"\n{'Métrica':<25} {'Trimestral':>15} {'Anual':>15} {'Diferença':>15}")
print("-"*70)
print(f"{'Média (SM)':<25} {trimestral['media_sm']:>15.3f} {anual['media_sm']:>15.3f} {diff['media_sm']:>+14.1f}%")
print(f"{'Mediana (SM)':<25} {trimestral['mediana_sm']:>15.3f} {anual['mediana_sm']:>15.3f} {diff['mediana_sm']:>+14.1f}%")
print(f"{'Gini':<25} {trimestral['gini']:>15.3f} {anual['gini']:>15.3f} {diff['gini']:>+14.1f}%")
print(f"{'Faixa 0-2 SM (%)':<25} {trimestral['faixa_0_2']:>15.2f} {anual['faixa_0_2']:>15.2f} {diff['faixa_0_2']:>+14.1f}pp")
print(f"{'Faixa 10+ SM (%)':<25} {trimestral['faixa_10_plus']:>15.2f} {anual['faixa_10_plus']:>15.2f} {diff['faixa_10_plus']:>+14.1f}pp")

# =============================================================================
# GRÁFICO 1: Comparação de Métricas Principais
# =============================================================================
print("\nGerando gráficos...")

fig1 = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Média de Renda (SM)",
        "Mediana de Renda (SM)",
        "Coeficiente de Gini",
        "Distribuição por Faixa de SM"
    ),
    specs=[
        [{"type": "bar"}, {"type": "bar"}],
        [{"type": "bar"}, {"type": "bar"}]
    ],
    vertical_spacing=0.15,
    horizontal_spacing=0.1
)

cores = ["#DC143C", "#2E8B57"]  # Vermelho=Trimestral, Verde=Anual

# 1. Média
fig1.add_trace(go.Bar(
    x=["Trimestral", "Anual"],
    y=[trimestral["media_sm"], anual["media_sm"]],
    marker_color=cores,
    text=[f"{trimestral['media_sm']:.2f}", f"{anual['media_sm']:.2f}"],
    textposition="outside",
    name="Média SM"
), row=1, col=1)

# Anotação de diferença
fig1.add_annotation(
    x=0.5, y=anual["media_sm"] + 0.3,
    text=f"+{diff['media_sm']:.1f}%",
    showarrow=False,
    font=dict(size=14, color="green"),
    xref="x", yref="y"
)

# 2. Mediana
fig1.add_trace(go.Bar(
    x=["Trimestral", "Anual"],
    y=[trimestral["mediana_sm"], anual["mediana_sm"]],
    marker_color=cores,
    text=[f"{trimestral['mediana_sm']:.2f}", f"{anual['mediana_sm']:.2f}"],
    textposition="outside",
    name="Mediana SM"
), row=1, col=2)

fig1.add_annotation(
    x=0.5, y=anual["mediana_sm"] + 0.2,
    text=f"+{diff['mediana_sm']:.1f}%",
    showarrow=False,
    font=dict(size=14, color="green"),
    xref="x2", yref="y2"
)

# 3. Gini
fig1.add_trace(go.Bar(
    x=["Trimestral", "Anual"],
    y=[trimestral["gini"], anual["gini"]],
    marker_color=cores,
    text=[f"{trimestral['gini']:.3f}", f"{anual['gini']:.3f}"],
    textposition="outside",
    name="Gini"
), row=2, col=1)

fig1.add_annotation(
    x=0.5, y=anual["gini"] + 0.03,
    text=f"{diff['gini']:.1f}%",
    showarrow=False,
    font=dict(size=14, color="green"),
    xref="x3", yref="y3"
)

# 4. Distribuição por Faixa
faixas = ["0-2 SM", "2-5 SM", "5-10 SM", "10+ SM"]
tri_faixas = [trimestral["faixa_0_2"], trimestral["faixa_2_5"], trimestral["faixa_5_10"], trimestral["faixa_10_plus"]]
anu_faixas = [anual["faixa_0_2"], anual["faixa_2_5"], anual["faixa_5_10"], anual["faixa_10_plus"]]

fig1.add_trace(go.Bar(
    x=faixas,
    y=tri_faixas,
    name="Trimestral",
    marker_color="#DC143C",
    text=[f"{v:.1f}%" for v in tri_faixas],
    textposition="outside"
), row=2, col=2)

fig1.add_trace(go.Bar(
    x=faixas,
    y=anu_faixas,
    name="Anual",
    marker_color="#2E8B57",
    text=[f"{v:.1f}%" for v in anu_faixas],
    textposition="outside"
), row=2, col=2)

fig1.update_layout(
    title={
        "text": "🔄 Comparação PNAD: Trimestral (só trabalho) vs Anual (todas as fontes)<br><sup>Impacto de considerar benefícios, previdência, aluguéis e capital na renda domiciliar</sup>",
        "x": 0.5,
        "font": dict(size=20)
    },
    height=800,
    width=1200,
    showlegend=True,
    template="plotly_white",
    barmode="group"
)

fig1.write_html("analysis/charts/06_comparacao_trimestral_anual.html")
fig1.write_image("analysis/charts/06_comparacao_trimestral_anual.png", scale=2)
print("✅ Gráfico 1 salvo!")

# =============================================================================
# GRÁFICO 2: Waterfall - De onde vem a diferença
# =============================================================================

# A diferença na média (3.565 - 2.789 = 0.776 SM) vem de:
# - Previdência: 13.5% da renda anual = ~0.48 SM
# - Benefícios: 3.5% = ~0.13 SM
# - Capital: 2.6% = ~0.09 SM
# - Outros: ~0.06 SM

renda_tri = trimestral["media_sm"] * 1621  # Em R$
renda_anu = anual["media_sm"] * 1621

# Componentes da diferença (estimados da composição)
previdencia_contrib = 0.135 * renda_anu
beneficios_contrib = 0.035 * renda_anu
capital_contrib = 0.026 * renda_anu
outros_contrib = 0.007 * renda_anu  # transferências + seguro

fig2 = go.Figure(go.Waterfall(
    name="Composição",
    orientation="v",
    measure=["relative", "relative", "relative", "relative", "total"],
    x=["Renda do<br>Trabalho", "Previdência<br>(+13.5%)", "Benefícios<br>Sociais (+3.5%)", "Capital e<br>Outros (+3.3%)", "Renda Total<br>Anual"],
    y=[renda_tri, previdencia_contrib, beneficios_contrib, capital_contrib + outros_contrib, 0],
    text=[f"R$ {renda_tri:,.0f}", f"+R$ {previdencia_contrib:,.0f}", f"+R$ {beneficios_contrib:,.0f}", 
          f"+R$ {capital_contrib + outros_contrib:,.0f}", f"R$ {renda_anu:,.0f}"],
    textposition="outside",
    connector={"line": {"color": "rgb(63, 63, 63)"}},
    decreasing={"marker": {"color": "#DC143C"}},
    increasing={"marker": {"color": "#2E8B57"}},
    totals={"marker": {"color": "#4169E1"}}
))

fig2.update_layout(
    title={
        "text": "💰 De Onde Vem a Diferença na Renda?<br><sup>Decomposição: Trimestral (trabalho) → Anual (todas fontes)</sup>",
        "x": 0.5,
        "font": dict(size=22)
    },
    yaxis_title="Renda Média Domiciliar (R$)",
    height=600,
    width=1000,
    template="plotly_white",
    annotations=[
        dict(
            text="⚠️ A PNAD Trimestral SUBESTIMA a renda em ~28% ao ignorar previdência, benefícios e capital",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=14, color="#DC143C")
        )
    ]
)

fig2.write_html("analysis/charts/07_waterfall_diferenca.html")
fig2.write_image("analysis/charts/07_waterfall_diferenca.png", scale=2)
print("✅ Gráfico 2 salvo!")

# =============================================================================
# GRÁFICO 3: Mudança na Distribuição por Faixa
# =============================================================================

fig3 = go.Figure()

# Trimestral
fig3.add_trace(go.Bar(
    name="Trimestral (só trabalho)",
    x=faixas,
    y=tri_faixas,
    marker_color="rgba(220, 20, 60, 0.7)",
    text=[f"{v:.1f}%" for v in tri_faixas],
    textposition="inside",
    textfont=dict(color="white", size=14)
))

# Anual
fig3.add_trace(go.Bar(
    name="Anual (todas as fontes)",
    x=faixas,
    y=anu_faixas,
    marker_color="rgba(46, 139, 87, 0.7)",
    text=[f"{v:.1f}%" for v in anu_faixas],
    textposition="inside",
    textfont=dict(color="white", size=14)
))

# Setas indicando a mudança
for i, (t, a) in enumerate(zip(tri_faixas, anu_faixas)):
    diff_pp = a - t
    color = "green" if diff_pp < 0 else "red" if i == 0 else "green"
    fig3.add_annotation(
        x=i, y=max(t, a) + 3,
        text=f"{'↓' if diff_pp < 0 else '↑'} {abs(diff_pp):.1f}pp",
        showarrow=False,
        font=dict(size=14, color=color, weight="bold")
    )

fig3.update_layout(
    title={
        "text": "📊 Mudança na Distribuição por Faixa de Renda<br><sup>Quando se considera TODAS as fontes de renda (não só trabalho)</sup>",
        "x": 0.5,
        "font": dict(size=22)
    },
    xaxis_title="Faixa de Salário Mínimo",
    yaxis_title="% dos Domicílios",
    barmode="group",
    height=600,
    width=1000,
    template="plotly_white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    annotations=[
        dict(
            text="💡 11.6pp MENOS domicílios na faixa mais pobre quando se considera todas as rendas!",
            xref="paper", yref="paper",
            x=0.5, y=-0.18,
            showarrow=False,
            font=dict(size=14, color="#2E8B57", weight="bold")
        )
    ]
)

fig3.write_html("analysis/charts/08_mudanca_distribuicao.html")
fig3.write_image("analysis/charts/08_mudanca_distribuicao.png", scale=2)
print("✅ Gráfico 3 salvo!")

# =============================================================================
# RESUMO FINAL
# =============================================================================

print("\n" + "="*70)
print("📊 RESUMO DA COMPARAÇÃO")
print("="*70)
print("""
PNAD TRIMESTRAL (só renda do trabalho - VD4020):
  • Média: 2.789 SM (R$ 4.521)
  • Mediana: 1.557 SM (R$ 2.524)
  • Gini: 0.628 (mais desigual)
  • 58.8% dos domicílios na faixa 0-2 SM

PNAD ANUAL (todas as fontes - VD5001):
  • Média: 3.565 SM (R$ 5.779) → +27.8% maior!
  • Mediana: 2.156 SM (R$ 3.495) → +38.5% maior!
  • Gini: 0.520 (menos desigual) → -17.2%!
  • 47.2% dos domicílios na faixa 0-2 SM → -11.6pp!

🔥 CONCLUSÃO:
   A PNAD Trimestral SUBESTIMA a renda domiciliar em quase 28%
   ao considerar apenas renda do trabalho.
   
   Quando incluímos previdência, benefícios e capital:
   • A renda média SOBE
   • A desigualdade (Gini) CAI
   • Menos domicílios "aparecem" na faixa mais pobre
   
   ⚠️ Centros de pesquisa que usam só a Trimestral podem estar
      EXAGERANDO a pobreza ao ignorar outras fontes de renda.
""")
print("="*70)
