import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="JocaMohr", layout="wide")

# Título Centralizado
st.markdown("<h1 style='text-align: center; color: #2c3e50; margin-bottom: 0;'>JocaMohr</h1>", unsafe_allow_html=True)

# --- CONTROLES NA BARRA LATERAL ---
with st.sidebar:
    st.header("Configurações")
    s1 = st.slider("σ1 (MPa)", 0, 200, 120)
    s3 = st.slider("σ3 (MPa)", 0, 200, 40)
    pp = st.slider("Pporos (MPa)", 0, 100, 20)
    alpha = st.slider("Biot", 0.0, 1.0, 1.0)
    st.divider()
    coesao = st.slider("Coesão (MPa)", 0, 50, 10)
    phi_deg = st.slider("Ang.Atrito (°)", 0, 60, 30)
    st.divider()
    mergulho = st.slider("Mergulho (°)", 0, 90, 60)

# --- LÓGICA DE CÁLCULO ---
s1_eff = max(s1 - (alpha * pp), 0)
s3_eff = max(s3 - (alpha * pp), 0)
if s1_eff < s3_eff: s1_eff, s3_eff = s3_eff, s1_eff
centro = (s1_eff + s3_eff) / 2
raio = (s1_eff - s3_eff) / 2

theta_mohr = np.radians(2 * mergulho)
sn = centro + raio * np.cos(theta_mohr)
tn = abs(raio * np.sin(theta_mohr))
tau_lim = coesao + sn * np.tan(np.radians(phi_deg))
tn_real = min(tn, tau_lim)
fs = tau_lim / tn if tn > 0.1 else 10.0

# --- LAYOUT EM COLUNAS ---
col1, col2 = st.columns([1, 1])

with col1:
    # Gráfico 3D - Ajustado para ficar na base
    z = np.linspace(-1, 1, 30)
    theta = np.linspace(0, 2*np.pi, 30)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_cil, y_cil = 0.7 * np.cos(theta_grid), 0.7 * np.sin(theta_grid)
    
    fig3d = go.Figure()
    # Cilindro Transparente
    fig3d.add_trace(go.Surface(x=x_cil, y=y_cil, z=z_grid, opacity=0.1, showscale=False, colorscale=[[0, 'grey'], [1, 'grey']]))
    
    # Plano de Falha
    xp = np.linspace(-0.7, 0.7, 20)
    yp = np.linspace(-0.7, 0.7, 20)
    XP, YP = np.meshgrid(xp, yp)
    ZP = np.tan(np.radians(mergulho)) * XP
    mask = XP**2 + YP**2 <= 0.7**2
    ZP[~mask] = np.nan
    fig3d.add_trace(go.Surface(x=XP, y=YP, z=ZP, colorscale='Oranges', showscale=False, opacity=0.8))

    # Vetores de Tensão
    scale = 0.8 / 200
    m_rad = np.radians(mergulho)
    nx, nz = -np.sin(m_rad)*sn*scale, np.cos(m_rad)*sn*scale
    tx, tz = np.cos(m_rad)*tn_real*scale, np.sin(m_rad)*tn_real*scale

    fig3d.add_trace(go.Scatter3d(x=[0, nx], y=[0, 0], z=[0, nz], mode='lines', line=dict(color='black', width=10), name='σn'))
    fig3d.add_trace(go.Scatter3d(x=[0, tx], y=[0, 0], z=[0, tz], mode='lines', line=dict(color='blue', width=10), name='τ'))
    
    # Seta σ1
    fig3d.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[1.1, 1.4], mode='lines+text', line=dict(color='red', width=5), text=["", "σ1"], textposition="top center"))

    # Ajuste de câmera e limites para "sentar" o cilindro na base
    fig3d.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), 
            zaxis=dict(range=[-1.05, 1.5], visible=False),
            aspectratio=dict(x=1, y=1, z=1.2),
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.8))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=500
    )
    st.plotly_chart(fig3d, use_container_width=True)

with col2:
    # Status de Falha
    cor_fs = "green" if fs > 1.0 else "red"
    st.markdown(f"<h2 style='text-align: center; color: {cor_fs};'>FS: {fs:.2f}</h2>", unsafe_allow_html=True)
    
    # Círculo de Mohr - Ajustado para 200x100 com incremento de 20
    t = np.linspace(0, np.pi, 200)
    x_circ, y_circ = centro + raio * np.cos(t), raio * np.sin(t)
    x_env = np.linspace(0, 200, 100)
    y_env = coesao + x_env * np.tan(np.radians(phi_deg))
    
    res_circ = coesao + x_circ * np.tan(np.radians(phi_deg))
    y_fisico = np.where(y_circ > res_circ, res_circ, y_circ)
    
    fig_mohr = go.Figure()
    # Parte Estável
    fig_mohr.add_trace(go.Scatter(x=x_circ, y=y_fisico, mode='lines', line=dict(color='#1f77b4', width=3)))
    # Parte em Falha (Vermelha)
    fail_mask = y_circ > res_circ
    if any(fail_mask):
        fig_mohr.add_trace(go.Scatter(x=x_circ[fail_mask], y=y_circ[fail_mask], mode='lines', line=dict(color='red', width=5)))
    
    fig_mohr.add_trace(go.Scatter(x=x_env, y=y_env, mode='lines', line=dict(color='red', dash='dash')))
    fig_mohr.add_trace(go.Scatter(x=[sn], y=[tn_real], mode='markers', marker=dict(color='green', size=15, line=dict(width=2, color='black'))))

    fig_mohr.update_layout(
        xaxis=dict(title="σn (MPa)", range=[0, 200], tickmode='linear', tick0=0, dtick=20, gridcolor='lightgrey'),
        yaxis=dict(title="τ (MPa)", range=[0, 100], tickmode='linear', tick0=0, dtick=20, gridcolor='lightgrey'),
        height=450, plot_bgcolor='white', showlegend=False,
        margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_mohr, use_container_width=True)
