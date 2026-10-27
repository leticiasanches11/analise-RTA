from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# AJUSTE ESTES CAMINHOS
# =========================
VIDEO_ORIGINAL = Path("videos/marcha_corrigido.mp4")
PASTA_S2D = Path("marcha_corrigido_Sports2D")
PASTA_SAIDA = Path("resultados_joelho_custom")
PASTA_SAIDA.mkdir(exist_ok=True)

ARQ_MOT = PASTA_S2D / "marcha_corrigido_Sports2D_angles_person00.mot"
ARQ_TRC = PASTA_S2D / "marcha_corrigido_Sports2D_px_person00.trc"

# =========================
# FUNÇÕES AUXILIARES
# =========================
def ler_mot(caminho):
    i = 0
    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        for i, linha in enumerate(f):
            if linha.strip().lower() == "endheader":
                break
    df = pd.read_csv(caminho, sep="\t", skiprows=i + 1)
    return df

def ler_trc(caminho):
    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        linhas = f.readlines()

    marcadores = [m for m in linhas[3].strip().split("\t")[2:] if m]
    dados = pd.read_csv(caminho, sep="\t", skiprows=5, header=None)

    colunas = ["Frame", "Time"]
    for m in marcadores:
        colunas += [f"{m}_X", f"{m}_Y", f"{m}_Z"]

    dados = dados.iloc[:, :len(colunas)]
    dados.columns = colunas[:dados.shape[1]]
    return dados

def achar_coluna(df, *termos):
    for c in df.columns:
        nome = c.lower()
        if all(t.lower() in nome for t in termos):
            return c
    raise KeyError(f"Não achei coluna com termos {termos}. Colunas disponíveis: {list(df.columns)}")

def preparar_serie(s):
    return pd.Series(s).interpolate(limit_direction="both").astype(float).to_numpy()

def desenhar_segmentos(frame, p1, p2, p3, cor=(0, 255, 0)):
    if p1 is not None and p2 is not None:
        cv2.line(frame, p1, p2, cor, 2)
    if p2 is not None and p3 is not None:
        cv2.line(frame, p2, p3, cor, 2)

    if p1 is not None:
        cv2.circle(frame, p1, 5, (255, 0, 0), -1)
    if p2 is not None:
        cv2.circle(frame, p2, 6, (0, 0, 255), -1)
    if p3 is not None:
        cv2.circle(frame, p3, 5, (255, 255, 0), -1)

def ponto(x, y):
    if np.isnan(x) or np.isnan(y):
        return None
    return (int(round(x)), int(round(y)))

# =========================
# LEITURA DOS DADOS
# =========================
print("Lendo arquivos...")
mot = ler_mot(ARQ_MOT)
trc = ler_trc(ARQ_TRC)

# Colunas dos ângulos do joelho
col_joelho_dir = achar_coluna(mot, "right", "knee")
col_joelho_esq = achar_coluna(mot, "left", "knee")
col_tempo = achar_coluna(mot, "time")

tempo = preparar_serie(mot[col_tempo])
joelho_dir = preparar_serie(mot[col_joelho_dir])
joelho_esq = preparar_serie(mot[col_joelho_esq])

# Colunas dos pontos no TRC
RHip_X = preparar_serie(trc[achar_coluna(trc, "rhip", "x")])
RHip_Y = preparar_serie(trc[achar_coluna(trc, "rhip", "y")])
RKnee_X = preparar_serie(trc[achar_coluna(trc, "rknee", "x")])
RKnee_Y = preparar_serie(trc[achar_coluna(trc, "rknee", "y")])
RAnkle_X = preparar_serie(trc[achar_coluna(trc, "rank", "x")])
RAnkle_Y = preparar_serie(trc[achar_coluna(trc, "rank", "y")])

LHip_X = preparar_serie(trc[achar_coluna(trc, "lhip", "x")])
LHip_Y = preparar_serie(trc[achar_coluna(trc, "lhip", "y")])
LKnee_X = preparar_serie(trc[achar_coluna(trc, "lknee", "x")])
LKnee_Y = preparar_serie(trc[achar_coluna(trc, "lknee", "y")])
LAnkle_X = preparar_serie(trc[achar_coluna(trc, "lank", "x")])
LAnkle_Y = preparar_serie(trc[achar_coluna(trc, "lank", "y")])

# =========================
# SALVAR CSV DOS DADOS
# =========================
df_dados = pd.DataFrame({
    "tempo_s": tempo,
    "joelho_direito_graus": joelho_dir,
    "joelho_esquerdo_graus": joelho_esq
})

csv_saida = PASTA_SAIDA / "dados_joelhos.csv"
df_dados.to_csv(csv_saida, index=False)
print(f"CSV salvo em: {csv_saida}")

# =========================
# GRÁFICOS
# =========================
plt.figure(figsize=(10, 4))
plt.plot(tempo, joelho_dir)
plt.xlabel("Tempo (s)")
plt.ylabel("Ângulo (graus)")
plt.title("Ângulo do joelho direito")
plt.tight_layout()
graf_dir = PASTA_SAIDA / "joelho_direito.png"
plt.savefig(graf_dir, dpi=150)
plt.close()

plt.figure(figsize=(10, 4))
plt.plot(tempo, joelho_esq)
plt.xlabel("Tempo (s)")
plt.ylabel("Ângulo (graus)")
plt.title("Ângulo do joelho esquerdo")
plt.tight_layout()
graf_esq = PASTA_SAIDA / "joelho_esquerdo.png"
plt.savefig(graf_esq, dpi=150)
plt.close()

print(f"Gráficos salvos em: {graf_dir} e {graf_esq}")

# =========================
# CRIAR VÍDEO PERSONALIZADO
# =========================
cap = cv2.VideoCapture(str(VIDEO_ORIGINAL))
if not cap.isOpened():
    raise RuntimeError("Não consegui abrir o vídeo original.")

fps = cap.get(cv2.CAP_PROP_FPS)
largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

n = min(
    total_frames_video,
    len(tempo),
    len(joelho_dir),
    len(joelho_esq),
    len(RHip_X),
    len(RKnee_X),
    len(RAnkle_X),
    len(LHip_X),
    len(LKnee_X),
    len(LAnkle_X),
)

video_saida = PASTA_SAIDA / "video_joelhos.mp4"
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(video_saida), fourcc, fps, (largura, altura))

print("Criando vídeo...")
frame_idx = 0

while True:
    ok, frame = cap.read()
    if not ok or frame_idx >= n:
        break

    # Pontos direito
    p_rhip = ponto(RHip_X[frame_idx], RHip_Y[frame_idx])
    p_rknee = ponto(RKnee_X[frame_idx], RKnee_Y[frame_idx])
    p_rank = ponto(RAnkle_X[frame_idx], RAnkle_Y[frame_idx])

    # Pontos esquerdo
    p_lhip = ponto(LHip_X[frame_idx], LHip_Y[frame_idx])
    p_lknee = ponto(LKnee_X[frame_idx], LKnee_Y[frame_idx])
    p_lank = ponto(LAnkle_X[frame_idx], LAnkle_Y[frame_idx])

    # Desenhar segmentos
    desenhar_segmentos(frame, p_rhip, p_rknee, p_rank, cor=(0, 255, 0))
    desenhar_segmentos(frame, p_lhip, p_lknee, p_lank, cor=(255, 255, 0))

    # Texto na tela
    texto1 = f"Joelho direito: {joelho_dir[frame_idx]:.1f}°"
    texto2 = f"Joelho esquerdo: {joelho_esq[frame_idx]:.1f}°"
    texto3 = f"Tempo: {tempo[frame_idx]:.2f} s"

    cv2.putText(frame, texto1, (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, texto2, (30, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    cv2.putText(frame, texto3, (30, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Texto perto do joelho
    if p_rknee is not None:
        cv2.putText(frame, f"{joelho_dir[frame_idx]:.1f}°",
                    (p_rknee[0] + 10, p_rknee[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if p_lknee is not None:
        cv2.putText(frame, f"{joelho_esq[frame_idx]:.1f}°",
                    (p_lknee[0] + 10, p_lknee[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    writer.write(frame)
    frame_idx += 1

cap.release()
writer.release()

print(f"Vídeo salvo em: {video_saida}")
print("Processo finalizado com sucesso!")