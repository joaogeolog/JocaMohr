import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="JocaMohr", layout="centered")

# --- INICIALIZAÇÃO DO HISTÓRICO (STRESS PATH) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'regime' not in st.session_state:
    st.session_state.regime = 'Normal'

# Título
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>JocaMohr</h1>", unsafe_allow_html=True)

# --- BARRA LATERAL (CONTROLES) ---
with st.sidebar:
    st.header("Configurações")
    
    # Botão Reset
    if st.button("RESET"):
        st.session_state.history = []
        st.rerun()

    s1 = st.slider("σ1 (MPa)", 0, 200, 120)
    s3 = st.slider("σ3 (MPa)", 0, 200, 40)
    pp = st.slider("Pporos (MPa)", 0, 100, 20)
    alpha = st.slider("Biot", 0.0, 1.0, 1.0)
    st.divider()
    coesao = st.slider("Coesão (MPa)", 0, 50, 10)
    phi_deg = st.slider("Ang.Atrito (°)", 0, 60, 30)
    st.divider()
    mergulho = st.slider("Mergulho (°)", 0, 90, 60)
    giro = st.slider("Giro View (°)", 0, 360, 45)

# --- BOTÕES DE REGIME (NORMAL / REVERSO) ---
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("NORMAL", use_container_width=True):
        st.session_state.regime = 'Normal'
with col_btn2:
    if st.button("REVERSO", use_container_width=True):
        st.session_state.regime = 'Reverso'

regime = st.session_state.regime

# --- LÓGICA DE CÁLCULO ---
s1_eff = max(s1 - (alpha * pp), 0)
s3_eff = max(s3 - (alpha * pp), 0)
if s1_eff < s3_eff: s1_eff, s3_eff = s3_eff, s1_eff # Garantir s1 > s3

centro = (s1_eff + s3_eff) / 2
raio = (s1_eff - s3_eff) / 2

# Ângulo relativo ao regime
theta_rel = mergulho if regime == 'Normal' else 90 - mergulho
theta_mohr = np.radians(2 * theta_rel)

sn = centro + raio * np.cos(theta_mohr)
tn = abs(raio * np.sin(theta_mohr))
tau_lim = coesao + sn * np.tan(np.radians(phi_deg))
tn_real = min(tn, tau_lim)

# Atualizar Stress Path
ponto_atual = (float(sn), float(tn_real))
if not st.session_state.history or np.linalg.norm(np.array(ponto_atual) - np.array(st.session_state.history[-1])) > 0.5:
    st.session_state.history.append(ponto_atual)

# --- GRÁFICO 3D ---
z = np.linspace(-1, 1, 20)
theta = np.linspace(0, 2*np.pi, 20)
theta_grid, z_grid = np.meshgrid(theta, z)
x_cil, y_cil = 0.7 * np.cos(theta_grid), 0.7 * np.sin(theta_grid)

fig3d = go.Figure()
fig3d.add_trace(go.Surface(x=x_cil, y=y_cil, z=z_grid, opacity=0.1, showscale=False, colorscale=[[0, 'grey'], [1, 'grey']]))

# Plano de Falha
xp = np.linspace(-0.7, 0.7, 15)
yp = np.linspace(-0.7, 0.7, 15)
XP, YP = np.meshgrid(xp, yp)
ZP = np.tan(np.radians(mergulho)) * XP
mask = XP**2 + YP**2 <= 0.7**2
ZP[~mask] = np.nan
fig3d.add_trace(go.Surface(x=XP, y=YP, z=ZP, colorscale='Oranges', showscale=False, opacity=0.8))

# Vetores
scale = 0.8 / 200
m_rad = np.radians(mergulho)
nx, nz = -np.sin(m_rad)*sn*scale, np.cos(m_rad)*sn*scale
tx, tz = np.cos(m_rad)*tn_real*scale, np.sin(m_rad)*tn_real*scale

fig3d.add_trace(go.Scatter3d(x=[0, nx], y=[0, 0], z=[0, nz], mode='lines', line=dict(color='black', width=8)))
fig3d.add_trace(go.Scatter3d(x=[0, tx], y=[0, 0], z=[0, tz], mode='lines', line=dict(color='blue', width=8)))

fig3d.update_layout(
    scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), 
               zaxis=dict(range=[-1.05, 1.5], visible=False), aspectmode='cube',
               camera=dict(eye=dict(x=1.5*np.cos(np.radians(giro)), y=1.5*np.sin(np.radians(giro)), z=0.8))),
    margin=dict(l=0, r=0, b=0, t=0), height=400, showlegend=False
)
st.plotly_chart(fig3d, use_container_width=True)

# --- STATUS ---
fs = tau_lim / tn if tn > 0.1 else 10.0
cor_fs = "red" if fs < 1.0 else "green"
st.markdown(f"<h3 style='text-align: center; color: {cor_fs};'>FS: {fs:.2f} | Regime: {regime}</h3>", unsafe_allow_html=True)

# --- GRÁFICO DE MOHR COM STRESS PATH ---
t_circ = np.linspace(0, np.pi, 200)
x_circ, y_circ = centro + raio * np.cos(t_circ), raio * np.sin(t_circ)
x_env = np.linspace(0, 200, 100)
y_env = coesao + x_env * np.tan(np.radians(phi_deg))

res_circ = coesao + x_circ * np.tan(np.radians(phi_deg))
y_fisico = np.where(y_circ > res_circ, res_circ, y_circ)

fig_mohr = go.Figure()

# Círculo
fig_mohr.add_trace(go.Scatter(x=x_circ, y=y_fisico, mode='lines', line=dict(color='#1f77b4', width=2)))

# Stress Path (Histórico)
if len(st.session_state.history) > 1:
    h_x, h_y = zip(*st.session_state.history)
    fig_mohr.add_trace(go.Scatter(x=h_x, y=h_y, mode='lines', line=dict(color='black', width=1, dash='dot'), opacity=0.5))

# Envoltória
fig_mohr.add_trace(go.Scatter(x=x_env, y=y_env, mode='lines', line=dict(color='red', dash='dash')))

# Ponto Atual
fig_mohr.add_trace(go.Scatter(x=[sn], y=[tn_real], mode='markers', marker=dict(color='green', size=12, line=dict(width=1, color='black'))))

fig_mohr.update_layout(
    xaxis=dict(title="σn (MPa)", range=[0, 200], dtick=20, gridcolor='lightgrey', showline=True, linecolor='black'),
    yaxis=dict(title="τ (MPa)", range=[0, 100], dtick=20, gridcolor='lightgrey', showline=True, linecolor='black'),
    plot_bgcolor='white', height=500, showlegend=False, margin=dict(l=40, r=20, t=20, b=40)
)
st.plotly_chart(fig_mohr, use_container_width=True)
