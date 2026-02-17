#!/usr/bin/env python3
"""
Visualizações de Composição de Renda - PNAD Anual 2024 (Visita 5)
Dados oficiais com pesos amostrais (V1032)
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import os

# Criar diretório de output
os.makedirs("analysis/charts", exist_ok=True)

# =============================================================================
# DADOS EXTRAÍDOS DO DASHBOARD V2.0 (COM PESOS OFICIAIS)
# =============================================================================

# Composição Nacional
composicao_nacional = {
    "Categoria": ["Trabalho", "Previdência", "Benefícios Sociais", "Capital", "Transferências Privadas", "Seguro"],
    "Percentual": [94.08, 13.50, 3.52, 2.63, 0.68, 0.35],
    "Valor_Medio": [5436.80, 780.08, 203.38, 151.88, 39.47, 20.20],
    "Cor": ["#2E8B57", "#FF8C00", "#DC143C", "#4169E1", "#9370DB", "#FFD700"]
}

# Composição por Faixa de SM
composicao_faixa = {
    "Faixa": ["0-2 SM", "2-5 SM", "5-10 SM", "10+ SM"],
    "Domicilios_Pct": [47.2, 34.6, 12.3, 5.9],
    "Trabalho": [82.8, 94.9, 96.2, 97.2],
    "Beneficios": [16.8, 2.9, 0.4, 0.1],
    "Previdencia": [22.8, 14.6, 12.8, 8.4],
    "Capital": [0.7, 1.3, 2.3, 5.1]
}

# Ranking de Dependência por UF (Top 10)
dependencia_uf = {
    "UF": ["Bahia", "Pernambuco", "Sergipe", "Paraíba", "Alagoas", 
           "Ceará", "Piauí", "Maranhão", "Rio Grande do Norte", "Acre"],
    "Dependency_Score": [27.79, 27.24, 26.77, 26.73, 26.51, 26.43, 26.37, 26.20, 24.42, 19.80],
    "Trabalho_Pct": [91.32, 92.28, 91.90, 92.22, 93.74, 92.86, 93.10, 94.58, 93.27, 95.46],
    "Beneficios_Pct": [9.79, 9.56, 9.24, 9.22, 10.06, 9.54, 8.51, 10.78, 6.91, 8.45],
    "Previdencia_Pct": [18.01, 17.68, 17.53, 17.51, 16.45, 16.89, 17.86, 15.42, 17.51, 11.35],
    "Renda_Media": [3465.78, 3525.80, 3840.40, 3960.08, 3569.90, 3542.62, 4524.90, 3279.12, 4211.90, 3832.47]
}

# Fontes detalhadas
fontes_detalhadas = {
    "Fonte": ["Aposentadoria/Pensão", "Bolsa Família", "Aluguel", "BPC-LOAS", 
              "Outros Capital", "Pensão/Doações", "Seguro-Desemprego", "Outros Prog. Sociais"],
    "Percentual": [13.50, 2.15, 1.57, 1.21, 1.06, 0.68, 0.35, 0.16],
    "Valor_Medio": [780.08, 124.53, 90.91, 69.80, 60.97, 39.47, 20.20, 9.06],
    "Recipientes_Pct": [28.61, 17.81, 4.06, 4.67, 2.32, 4.64, 1.15, 1.85]
}

# =============================================================================
# GRÁFICO 1: Composição por Faixa de SM (Stacked Bar)
# =============================================================================
print("Gerando Gráfico 1: Composição por Faixa...")

df_faixa = pd.DataFrame(composicao_faixa)

fig1 = go.Figure()

# Cores
cores = {
    "Trabalho": "#2E8B57",
    "Previdencia": "#FF8C00", 
    "Beneficios": "#DC143C",
    "Capital": "#4169E1"
}

for categoria in ["Trabalho", "Previdencia", "Beneficios", "Capital"]:
    fig1.add_trace(go.Bar(
        name=categoria.replace("_", " ").title(),
        x=df_faixa["Faixa"],
        y=df_faixa[categoria],
        marker_color=cores[categoria],
        text=[f"{v:.1f}%" for v in df_faixa[categoria]],
        textposition="inside",
        textfont=dict(size=14, color="white")
    ))

fig1.update_layout(
    title={
        "text": "📊 Composição de Renda por Faixa de Salário Mínimo<br><sup>PNAD Anual 2024 (Visita 5) - Brasil</sup>",
        "x": 0.5,
        "font": dict(size=24)
    },
    barmode="stack",
    xaxis_title="Faixa de Renda Domiciliar (em Salários Mínimos)",
    yaxis_title="% da Renda Total",
    legend_title="Fonte de Renda",
    template="plotly_white",
    height=600,
    width=1000,
    annotations=[
        dict(
            text="⚠️ Nas faixas mais pobres (0-2 SM), apenas 82.8% vem do trabalho<br>vs 97.2% nas faixas mais ricas (10+ SM)",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=12, color="gray")
        )
    ]
)

fig1.write_html("analysis/charts/01_composicao_por_faixa.html")
fig1.write_image("analysis/charts/01_composicao_por_faixa.png", scale=2)
print("✅ Gráfico 1 salvo!")

# =============================================================================
# GRÁFICO 2: Ranking de Dependência por UF
# =============================================================================
print("Gerando Gráfico 2: Ranking de Dependência...")

df_dep = pd.DataFrame(dependencia_uf)
df_dep = df_dep.sort_values("Dependency_Score", ascending=True)

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    y=df_dep["UF"],
    x=df_dep["Beneficios_Pct"],
    name="Benefícios Sociais",
    orientation="h",
    marker_color="#DC143C",
    text=[f"{v:.1f}%" for v in df_dep["Beneficios_Pct"]],
    textposition="inside"
))

fig2.add_trace(go.Bar(
    y=df_dep["UF"],
    x=df_dep["Previdencia_Pct"],
    name="Previdência",
    orientation="h",
    marker_color="#FF8C00",
    text=[f"{v:.1f}%" for v in df_dep["Previdencia_Pct"]],
    textposition="inside"
))

fig2.update_layout(
    title={
        "text": "🗺️ Ranking de Dependência por UF<br><sup>% da renda vinda de benefícios + previdência (não-trabalho)</sup>",
        "x": 0.5,
        "font": dict(size=24)
    },
    barmode="stack",
    xaxis_title="% da Renda Domiciliar",
    yaxis_title="",
    legend_title="Fonte",
    template="plotly_white",
    height=600,
    width=1000,
    annotations=[
        dict(
            text="📍 Estados do Nordeste lideram a dependência de transferências",
            xref="paper", yref="paper",
            x=0.5, y=-0.12,
            showarrow=False,
            font=dict(size=12, color="gray")
        )
    ]
)

fig2.write_html("analysis/charts/02_dependencia_por_uf.html")
fig2.write_image("analysis/charts/02_dependencia_por_uf.png", scale=2)
print("✅ Gráfico 2 salvo!")

# =============================================================================
# GRÁFICO 3: Fontes de Renda Detalhadas (Treemap)
# =============================================================================
print("Gerando Gráfico 3: Treemap de Fontes...")

df_fontes = pd.DataFrame(fontes_detalhadas)

# Adicionar categoria pai
df_fontes["Categoria"] = df_fontes["Fonte"].apply(
    lambda x: "Previdência" if "Aposentadoria" in x else 
              ("Benefícios Sociais" if x in ["Bolsa Família", "BPC-LOAS", "Outros Prog. Sociais"] else
               ("Capital" if x in ["Aluguel", "Outros Capital"] else "Outros"))
)

fig3 = px.treemap(
    df_fontes,
    path=["Categoria", "Fonte"],
    values="Percentual",
    color="Recipientes_Pct",
    color_continuous_scale="RdYlGn_r",
    title="🏠 Fontes de Renda Não-Trabalho por Categoria",
    hover_data={"Valor_Medio": ":.2f", "Recipientes_Pct": ":.1f"}
)

fig3.update_layout(
    height=600,
    width=1000,
    coloraxis_colorbar_title="% Domicílios<br>Beneficiados"
)

fig3.write_html("analysis/charts/03_treemap_fontes.html")
fig3.write_image("analysis/charts/03_treemap_fontes.png", scale=2)
print("✅ Gráfico 3 salvo!")

# =============================================================================
# GRÁFICO 4: Correlação Trabalho vs Renda (Scatter)
# =============================================================================
print("Gerando Gráfico 4: Correlação...")

# Criar dados para scatter
df_corr = pd.DataFrame({
    "Faixa": ["0-2 SM\n(47.2% dos domicílios)", "2-5 SM\n(34.6%)", "5-10 SM\n(12.3%)", "10+ SM\n(5.9%)"],
    "Pct_Trabalho": [82.8, 94.9, 96.2, 97.2],
    "Renda_Media_SM": [1.0, 3.5, 7.5, 15.0],  # Pontos médios das faixas
    "Tamanho": [47.2, 34.6, 12.3, 5.9]
})

fig4 = go.Figure()

fig4.add_trace(go.Scatter(
    x=df_corr["Pct_Trabalho"],
    y=df_corr["Renda_Media_SM"],
    mode="markers+text",
    marker=dict(
        size=df_corr["Tamanho"] * 2,
        color=df_corr["Pct_Trabalho"],
        colorscale="Greens",
        showscale=True,
        colorbar=dict(title="% Trabalho")
    ),
    text=df_corr["Faixa"],
    textposition="top center",
    textfont=dict(size=12)
))

# Linha de tendência
fig4.add_trace(go.Scatter(
    x=[82, 98],
    y=[0, 16],
    mode="lines",
    line=dict(dash="dash", color="gray"),
    name="Tendência"
))

fig4.update_layout(
    title={
        "text": "📈 Correlação: % Renda do Trabalho vs Nível de Renda<br><sup>Quanto mais trabalho, maior a renda</sup>",
        "x": 0.5,
        "font": dict(size=24)
    },
    xaxis_title="% da Renda Vinda do Trabalho",
    yaxis_title="Renda Média (em Salários Mínimos)",
    template="plotly_white",
    height=600,
    width=1000,
    showlegend=False,
    annotations=[
        dict(
            text="💡 HIPÓTESE VALIDADA: Quem depende mais de benefícios permanece nas faixas mais baixas",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=14, color="#DC143C", weight="bold")
        )
    ]
)

fig4.write_html("analysis/charts/04_correlacao_trabalho_renda.html")
fig4.write_image("analysis/charts/04_correlacao_trabalho_renda.png", scale=2)
print("✅ Gráfico 4 salvo!")

# =============================================================================
# GRÁFICO 5: Infográfico Resumo
# =============================================================================
print("Gerando Gráfico 5: Infográfico...")

fig5 = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Composição Nacional",
        "Por Faixa de SM",
        "Top 5 UFs Dependentes",
        "Hipótese Central"
    ),
    specs=[
        [{"type": "pie"}, {"type": "bar"}],
        [{"type": "bar"}, {"type": "indicator"}]
    ],
    vertical_spacing=0.15,
    horizontal_spacing=0.1
)

# 1. Pie - Composição Nacional
df_nac = pd.DataFrame(composicao_nacional)
fig5.add_trace(go.Pie(
    labels=df_nac["Categoria"],
    values=df_nac["Percentual"],
    marker_colors=df_nac["Cor"],
    textinfo="label+percent",
    hole=0.4
), row=1, col=1)

# 2. Bar - Por Faixa
fig5.add_trace(go.Bar(
    x=composicao_faixa["Faixa"],
    y=composicao_faixa["Trabalho"],
    name="Trabalho",
    marker_color="#2E8B57"
), row=1, col=2)

fig5.add_trace(go.Bar(
    x=composicao_faixa["Faixa"],
    y=composicao_faixa["Beneficios"],
    name="Benefícios",
    marker_color="#DC143C"
), row=1, col=2)

# 3. Bar horizontal - Top 5 UFs
top5 = df_dep.tail(5)
fig5.add_trace(go.Bar(
    y=top5["UF"],
    x=top5["Dependency_Score"],
    orientation="h",
    marker_color="#FF8C00",
    text=[f"{v:.1f}%" for v in top5["Dependency_Score"]],
    textposition="outside"
), row=2, col=1)

# 4. Indicator
fig5.add_trace(go.Indicator(
    mode="number+delta",
    value=82.8,
    delta={"reference": 97.2, "relative": True, "valueformat": ".1%"},
    title={"text": "% Trabalho<br>Faixa 0-2 SM vs 10+ SM"},
    number={"suffix": "%"}
), row=2, col=2)

fig5.update_layout(
    title={
        "text": "🇧🇷 PNAD ANUAL 2024 - Composição de Renda Domiciliar<br><sup>78.3 milhões de domicílios | 211.9 milhões de pessoas</sup>",
        "x": 0.5,
        "font": dict(size=20)
    },
    height=900,
    width=1200,
    showlegend=True,
    template="plotly_white"
)

fig5.write_html("analysis/charts/05_infografico_resumo.html")
fig5.write_image("analysis/charts/05_infografico_resumo.png", scale=2)
print("✅ Gráfico 5 salvo!")

print("\n" + "="*60)
print("🎉 TODOS OS GRÁFICOS GERADOS COM SUCESSO!")
print("="*60)
print("\nArquivos salvos em: analysis/charts/")
print("- 01_composicao_por_faixa.html/.png")
print("- 02_dependencia_por_uf.html/.png")
print("- 03_treemap_fontes.html/.png")
print("- 04_correlacao_trabalho_renda.html/.png")
print("- 05_infografico_resumo.html/.png")
