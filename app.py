import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuração da página para eliminar margens escuras
st.set_page_config(page_title="JocaMohr", layout="centered")

# CSS para garantir que o fundo seja sempre branco e centralizado
st.markdown("""
    <style>
    .main { background-color: white; }
    div.block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# Título JocaMohr
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>JocaMohr</h1>", unsafe_allow_html=True)

# --- SIDEBAR COM OS CONTROLES ---
# Colocando na sidebar, o visual no celular fica mais limpo e a imagem ganha destaque
with st.sidebar:
    st.header("Parâmetros")
    s1 = st.slider(r"$\sigma_1$ (MPa)", 0, 200, 120)
    s3 = st.slider(r"$\sigma_3$ (MPa)", 0, 200, 40)
    pp = st.slider("Pporos (MPa)", 0, 100, 20)
    alpha = st.slider("Biot", 0.0, 1.0, 1.0)
    st.divider()
    coesao = st.slider("Coesão (MPa)", 0, 50, 10)
    phi = st.slider("Ang.Atrito (°)", 0, 60, 30)
    st.divider()
    mergulho = st.slider("Mergulho (°)", 0, 90, 60)
    giro = st.slider("Giro (°)", 0, 360, 45)
    regime = st.radio("Regime:", ["Normal", "Reverso"], horizontal=True)

# --- CÁLCULOS ---
s1_eff, s3_eff = s1 - (alpha * pp), s3 - (alpha * pp)
centro, raio = (s1_eff + s3_eff) / 2, (s1_eff - s3_eff) / 2
theta_rel = mergulho if regime == "Normal" else 90 - mergulho
theta_m = np.radians(2 * theta_rel)
sn = centro + raio * np.cos(theta_m)
tn = abs(raio * np.sin(theta_m))
resistencia = coesao + sn * np.tan(np.radians(phi))
tn_real = min(tn, resistencia)
fs = resistencia / tn if tn > 0.1 else 10.0

# --- GERAÇÃO DA FIGURA (IDÊNTICA À FOTO) ---
fig = plt.figure(figsize=(8, 11), facecolor='white')

# 1. Cilindro 3D
ax1 = fig.add_subplot(211, projection='3d')
ax1.set_axis_off()
ax1.view_init(elev=15, azim=giro)

u, v = np.linspace(0, 2*np.pi, 30), np.linspace(-1, 1, 30)
U, V = np.meshgrid(u, v)
XC, YC, ZC = 0.7 * np.cos(U), 0.7 * np.sin(U), V
ax1.plot_surface(XC, YC, ZC, color='lightgrey', alpha=0.1)

# Plano de Falha
xp_v = np.linspace(-0.7, 0.7, 40)
XP, YP = np.meshgrid(xp_v, xp_v)
ZP = np.tan(np.radians(mergulho)) * XP
mask = XP**2 + YP**2 <= 0.7**2
XP[~mask], YP[~mask], ZP[~mask] = np.nan, np.nan, np.nan
ax1.plot_surface(XP, YP, ZP, color='#ff7f0e', alpha=0.6, edgecolors='k', lw=0.1)

# Vetores
ax1.quiver([0, 0], [0, 0], [1.2, -1.2], [0, 0], [0, 0], [-0.3, 0.3], color='red', lw=3)
scale = 0.5 / 200
m_rad = np.radians(mergulho)
ax1.quiver(0, 0, 0, -np.sin(m_rad)*sn*scale, 0, np.cos(m_rad)*sn*scale, color='black', lw=5)
ax1.quiver(0, 0, 0, np.cos(m_rad)*tn_real*scale, 0, np.sin(m_rad)*tn_real*scale, color='blue', lw=5)

ax1.set_zlim(-1.1, 0.7)
ax1.set_box_aspect([1, 1, 1])

# 2. Círculo de Mohr
ax2 = fig.add_subplot(212)
t_c = np.linspace(0, np.pi, 200)
x_c, y_c = centro + raio * np.cos(t_c), raio * np.sin(t_c)
res_c = coesao + x_c * np.tan(np.radians(phi))
y_f = np.clip(y_c, 0, res_c)
mask_fail = y_c > res_c

ax2.plot(x_c[~mask_fail], y_f[~mask_fail], color='#1f77b4', lw=2)
ax2.plot(x_c[mask_fail], y_f[mask_fail], color='red', lw=4)
ax2.plot(np.linspace(0, 200, 100), coesao + np.linspace(0, 200, 100) * np.tan(np.radians(phi)), 'r--', lw=2)
ax2.plot(sn, tn_real, 'go', markersize=10, markeredgecolor='k')

# Texto de Status
cor_fs = 'red' if fs <= 1.0 else 'green'
ax2.text(0.05, 0.9, f"FS: {fs:.2f} | {regime}", transform=ax2.transAxes, color=cor_fs, fontsize=14, fontweight='bold')
ax2.set_xlim(0, 200); ax2.set_ylim(0, 100)
ax2.set_xticks(np.arange(0, 201, 20)); ax2.set_yticks(np.arange(0, 101, 20))
ax2.grid(True, ls=':', alpha=0.4)
ax2.set_xlabel(r"$\sigma_n$ (MPa)"); ax2.set_ylabel(r"$\tau$ (MPa)")

# Mostra no link
st.pyplot(fig)
