import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da Página para Celular
st.set_page_config(page_title="JocaMohr", layout="centered")

# Título Principal
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>JocaMohr</h1>", unsafe_allow_html=True)

# --- BARRA LATERAL (Controles) ---
st.sidebar.header("Configurações Geomecânicas")

# Tensões e Pressão (MPa)
s1 = st.sidebar.slider("σ1 (MPa)", 0, 200, 120)
s3 = st.sidebar.slider("σ3 (MPa)", 0, 200, 40)
pp = st.sidebar.slider("Pporos (MPa)", 0, 100, 20)
alpha = st.sidebar.slider("Biot", 0.0, 1.0, 1.0)

# Resistência
coesao = st.sidebar.slider("Coesão (MPa)", 0, 50, 10)
phi_deg = st.sidebar.slider("Ang.Atrito (°)", 0, 60, 30)

# Orientação
mergulho = st.sidebar.slider("Mergulho (°)", 0, 90, 60)

# --- LÓGICA DE CÁLCULO ---
s1_eff = s1 - (alpha * pp)
s3_eff = s3 - (alpha * pp)
centro = (s1_eff + s3_eff) / 2
raio = (s1_eff - s3_eff) / 2 if s1_eff > s3_eff else 0.1

# Ponto no plano de falha
theta_mohr = np.radians(2 * mergulho)
sn = centro + raio * np.cos(theta_mohr)
tn = abs(raio * np.sin(theta_mohr))

# Resistência limite (Colapso Físico)
tau_lim = coesao + sn * np.tan(np.radians(phi_deg))
tn_real = min(tn, tau_lim)
fs = tau_lim / tn if tn > 0.1 else 10.0

# --- EXIBIÇÃO DO FATOR DE SEGURANÇA ---
cor_fs = "green" if fs > 1.0 else "red"
st.markdown(f"<h3 style='text-align: center; color: {cor_fs};'>FS: {fs:.2f}</h3>", unsafe_allow_html=True)

# --- GRÁFICO 3D ---
def criar_3d():
    z = np.linspace(-1, 1, 20)
    theta = np.linspace(0, 2*np.pi, 20)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_cil = 0.7 * np.cos(theta_grid)
    y_cil = 0.7 * np.sin(theta_grid)
    
    fig = go.Figure()
    # Cilindro
    fig.add_trace(go.Surface(x=x_cil, y=y_cil, z=z_grid, opacity=0.1, showscale=False, colorscale=[[0, 'grey'], [1, 'grey']]))
    
    # Plano de Falha
    xp = np.linspace(-0.7, 0.7, 10)
    yp = np.linspace(-0.7, 0.7, 10)
    XP, YP = np.meshgrid(xp, yp)
    ZP = np.tan(np.radians(mergulho)) * XP
    mask = XP**2 + YP**2 <= 0.7**2
    ZP[~mask] = np.nan
    fig.add_trace(go.Surface(x=XP, y=YP, z=ZP, colorscale='Oranges', showscale=False, opacity=0.8))

    # Vetores Dinâmicos (σn e τ)
    scale = 0.8 / 200
    m_rad = np.radians(mergulho)
    nx, nz = -np.sin(m_rad)*sn*scale, np.cos(m_rad)*sn*scale
    tx, tz = np.cos(m_rad)*tn_real*scale, np.sin(m_rad)*tn_real*scale

    fig.add_trace(go.Scatter3d(x=[0, nx], y=[0, 0], z=[0, nz], mode='lines', line=dict(color='black', width=8), name='σn'))
    fig.add_trace(go.Scatter3d(x=[0, tx], y=[0, 0], z=[0, tz], mode='lines', line=dict(color='blue', width=8), name='τ'))

    fig.update_layout(scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), 
                      zaxis=dict(range=[-1.05, 1.3], visible=False), aspectmode='cube'),
                      margin=dict(l=0, r=0, b=0, t=0), height=450)
    return fig

# --- GRÁFICO CÍRCULO DE MOHR ---
def criar_mohr():
    t = np.linspace(0, np.pi, 200)
    x_circ = centro + raio * np.cos(t)
    y_circ = raio * np.sin(t)
    
    x_env = np.linspace(0, 200, 100)
    y_env = coesao + x_env * np.tan(np.radians(phi_deg))
    
    resistencia_no_circ = coesao + x_circ * np.tan(np.radians(phi_deg))
    y_fisico = np.where(y_circ > resistencia_no_circ, resistencia_no_circ, y_circ)
    
    fig = go.Figure()
    # Parte estável (azul) e parte em falha (vermelha colapsada)
    fig.add_trace(go.Scatter(x=x_circ, y=y_fisico, mode='lines', line=dict(color='blue', width=2)))
    ruptura_x = x_circ[y_circ >= resistencia_no_circ]
    ruptura_y = y_fisico[y_circ >= resistencia_no_circ]
    fig.add_trace(go.Scatter(x=ruptura_x, y=ruptura_y, mode='lines', line=dict(color='red', width=4)))
    
    fig.add_trace(go.Scatter(x=x_env, y=y_env, mode='lines', line=dict(color='red', dash='dash')))
    fig.add_trace(go.Scatter(x=[sn], y=[tn_real], mode='markers', marker=dict(color='green', size=12)))

    fig.update_layout(xaxis_title="σn (MPa)", yaxis_title="τ (MPa)", 
                      xaxis=dict(range=[0, 200], dtick=20), yaxis=dict(range=[0, 100], dtick=20),
                      height=400, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
    return fig

# Exibição Final
st.plotly_chart(criar_3d(), use_container_width=True)
st.plotly_chart(criar_mohr(), use_container_width=True)