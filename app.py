
import streamlit as st
from pathlib import Path
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape
import subprocess
import sys
import shutil
import time

import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm


# ======================================
# 1. CONFIGURACOES
# ======================================

st.set_page_config(
    page_title="Analise Cinematica da Marcha",
    page_icon="🏃",
    layout="wide"
)

BASE = Path(__file__).resolve().parent

VIDEO = BASE / "videos" / "marcha_corrigido.mp4"
PASTA_DADOS = BASE / "marcha_corrigido_Sports2D"
PASTA_RESULTADOS = BASE / "resultados_joelho_custom"

MOT = PASTA_DADOS / "marcha_corrigido_Sports2D_angles_person00.mot"
TRC = PASTA_DADOS / "marcha_corrigido_Sports2D_px_person00.trc"

VIDEO_FINAL = PASTA_RESULTADOS / "video_joelhos.mp4"
CSV = PASTA_RESULTADOS / "dados_joelhos.csv"
GRAF_DIR = PASTA_RESULTADOS / "joelho_direito.png"
GRAF_ESQ = PASTA_RESULTADOS / "joelho_esquerdo.png"


# ======================================
# 2. FUNCAO PARA GERAR O PDF
# ======================================

def gerar_pdf(identificacao, movimento, condicao,
              observacoes, nome_video, data_analise):

    dados = pd.read_csv(CSV)

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name="TituloProjeto",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=22,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=15
    ))

    estilos.add(ParagraphStyle(
        name="SubtituloProjeto",
        parent=estilos["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=12,
        spaceAfter=8
    ))

    estilos.add(ParagraphStyle(
        name="TextoProjeto",
        parent=estilos["Normal"],
        fontSize=9,
        leading=14,
        spaceAfter=8
    ))

    elementos = []

    def texto(valor):
        return escape(str(valor))

    def paragrafo(conteudo):
        return Paragraph(conteudo, estilos["TextoProjeto"])

    # ----------------------------------
    # PAGINA 1 - IDENTIFICACAO
    # ----------------------------------

    elementos.append(Paragraph(
        "RELATORIO DE ANALISE CINEMATICA",
        estilos["TituloProjeto"]
    ))

    elementos.append(paragrafo(
        "Analise bidimensional dos angulos articulares "
        "dos joelhos durante o movimento."
    ))

    elementos.append(Paragraph(
        "1. Identificacao da analise",
        estilos["SubtituloProjeto"]
    ))

    informacoes = [
        ["Campo", "Informacao"],
        ["Identificacao", texto(identificacao)],
        ["Data", data_analise],
        ["Movimento", texto(movimento)],
        ["Condicao", texto(condicao)],
        ["Articulacoes", "Joelhos direito e esquerdo"],
        ["Video original", texto(nome_video)]
    ]

    tabela = Table(
        [
            [paragrafo(celula) for celula in linha]
            for linha in informacoes
        ],
        colWidths=[5 * cm, 12 * cm],
        hAlign="LEFT"
    )

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#DCE6F1")),
        ("GRID", (0, 0), (-1, -1),
         0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    elementos.append(tabela)

    # ----------------------------------
    # METODOLOGIA
    # ----------------------------------

    elementos.append(Paragraph(
        "2. Metodologia",
        estilos["SubtituloProjeto"]
    ))

    elementos.append(paragrafo(
        "O video foi processado utilizando o Sports2D, "
        "uma ferramenta de estimativa de pose humana "
        "bidimensional. Foram obtidas as coordenadas "
        "anatomicas e os angulos articulares dos joelhos. "
        "Os dados foram posteriormente utilizados para "
        "gerar os graficos e o video com marcacoes."
    ))

    # ----------------------------------
    # RESULTADOS
    # ----------------------------------

    elementos.append(Paragraph(
        "3. Resultados angulares",
        estilos["SubtituloProjeto"]
    ))

    resultados = [
        ["Articulacao", "Minimo", "Maximo", "Media"]
    ]

    for coluna, nome in [
        ("joelho_direito_graus", "Joelho direito"),
        ("joelho_esquerdo_graus", "Joelho esquerdo")
    ]:
        serie = pd.to_numeric(
            dados[coluna], errors="coerce"
        ).dropna()

        if serie.empty:
            resultados.append([
                nome, "N/D", "N/D", "N/D"
            ])
        else:
            resultados.append([
                nome,
                f"{serie.min():.1f} graus",
                f"{serie.max():.1f} graus",
                f"{serie.mean():.1f} graus"
            ])

    tabela_resultados = Table(
        resultados,
        colWidths=[5 * cm, 4 * cm, 4 * cm, 4 * cm]
    )

    tabela_resultados.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#DCE6F1")),
        ("GRID", (0, 0), (-1, -1),
         0.4, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9)
    ]))

    elementos.append(tabela_resultados)
    elementos.append(Spacer(1, 0.3 * cm))

    elementos.append(paragrafo(
        "Os valores apresentados correspondem aos dados "
        "disponiveis no arquivo processado. Os extremos "
        "e a media nao representam, isoladamente, uma "
        "avaliacao clinica ou uma medida de simetria."
    ))

    # ----------------------------------
    # PAGINA 2 - GRAFICOS
    # ----------------------------------

    elementos.append(PageBreak())

    elementos.append(Paragraph(
        "4. Graficos dos angulos articulares",
        estilos["SubtituloProjeto"]
    ))

    elementos.append(paragrafo(
        "Os graficos apresentam a variacao dos angulos "
        "dos joelhos ao longo do tempo. "
        "A interpretacao depende da convencao angular "
        "e da qualidade das marcacoes anatomicas."
    ))

    for titulo, caminho in [
        ("Joelho direito", GRAF_DIR),
        ("Joelho esquerdo", GRAF_ESQ)
    ]:
        bloco = [
            paragrafo(f"<b>{titulo}</b>"),
            Image(
                str(caminho),
                width=16 * cm,
                height=6.2 * cm,
                kind="proportional"
            ),
            Spacer(1, 0.3 * cm)
        ]
        elementos.append(KeepTogether(bloco))

    # ----------------------------------
    # OBSERVACOES
    # ----------------------------------

    elementos.append(Paragraph(
        "5. Observacoes",
        estilos["SubtituloProjeto"]
    ))

    if observacoes.strip():
        elementos.append(paragrafo(
            texto(observacoes)
        ))
    else:
        elementos.append(paragrafo(
            "Nenhuma observacao adicional registrada."
        ))

    elementos.append(Paragraph(
        "6. Limitacoes da analise",
        estilos["SubtituloProjeto"]
    ))

    elementos.append(paragrafo(
        "Os resultados sao estimativas obtidas a partir "
        "de video bidimensional. A precisao depende do "
        "posicionamento da camera, da visibilidade das "
        "articulacoes e da qualidade do rastreamento. "
        "A confiabilidade dos resultados ainda deve ser "
        "validada por comparacao com medidas de referencia. "
        "O sistema nao constitui instrumento de diagnostico."
    ))

    # ----------------------------------
    # NUMERACAO DE PAGINAS
    # ----------------------------------

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            A4[0] / 2,
            1 * cm,
            f"Pagina {doc.page}"
        )
        canvas.restoreState()

    documento.build(
        elementos,
        onFirstPage=rodape,
        onLaterPages=rodape
    )

    return buffer.getvalue()


# ======================================
# 3. INTERFACE
# ======================================

st.title("Sistema de Analise Cinematica da Marcha")

st.write(
    "Plataforma para analise automatica dos angulos "
    "dos joelhos a partir de videos."
)

st.divider()

st.subheader("1. Identificacao da analise")

identificacao = st.text_input(
    "Codigo ou identificacao do participante",
    placeholder="Exemplo: Participante 001"
)

col1, col2 = st.columns(2)

with col1:
    movimento = st.selectbox(
        "Tipo de movimento",
        ["Corrida", "Caminhada"]
    )

with col2:
    condicao = st.selectbox(
        "Condicao da gravacao",
        ["Esteira", "Solo"]
    )

observacoes = st.text_area(
    "Observacoes (opcional)",
    placeholder="Descreva alguma condicao relevante..."
)

st.divider()

st.subheader("2. Enviar video")

arquivo = st.file_uploader(
    "Selecione o video do participante",
    type=["mp4"]
)

st.caption(
    "Utilize preferencialmente um video lateral, "
    "com apenas uma pessoa e o corpo inteiro visivel."
)

# Limpar resultados anteriores quando mudar o arquivo
identidade_atual = (
    arquivo.file_id if arquivo is not None else None
)

if st.session_state.get("arquivo_anterior") != identidade_atual:
    st.session_state.pop("resultado", None)
    st.session_state["arquivo_anterior"] = identidade_atual

if arquivo is not None:

    st.video(arquivo)

    if st.button(
        "Iniciar analise automatica",
        type="primary"
    ):

        st.session_state.pop("resultado", None)

        if not identificacao.strip():
            st.warning(
                "Informe a identificacao do participante."
            )

        else:
            try:

                VIDEO.parent.mkdir(
                    parents=True, exist_ok=True
                )

                PASTA_RESULTADOS.mkdir(
                    parents=True, exist_ok=True
                )

                caminho_script = BASE / "video_joelhos.py"

                if not caminho_script.exists():
                    raise FileNotFoundError(
                        "Arquivo video_joelhos.py nao encontrado."
                    )

                # Salvar video enviado
                with open(VIDEO, "wb") as destino:
                    arquivo.seek(0)
                    shutil.copyfileobj(arquivo, destino)

                inicio = time.time()

                # Executar Sports2D
                with st.spinner(
                    "Identificando pontos anatomicos..."
                ):

                    executavel = (
                        BASE / ".venv" / "Scripts"
                        / "sports2d.exe"
                    )

                    comando = [
                        str(executavel),
                        "--video_input",
                        "videos/marcha_corrigido.mp4",
                        "--nb_persons_to_detect", "1",
                        "--save_vid", "false",
                        "--save_pose", "true",
                        "--calculate_angles", "true",
                        "--save_angles", "true",
                        "--show_graphs", "false",
                        "--show_realtime_results", "false"
                    ]

                    resultado_s2d = subprocess.run(
                        comando,
                        cwd=BASE,
                        capture_output=True,
                        text=True,
                        errors="replace"
                    )

                # Conferir novos dados
                for caminho in [MOT, TRC]:
                    if (
                        not caminho.exists()
                        or caminho.stat().st_size == 0
                        or caminho.stat().st_mtime < inicio - 2
                    ):
                        st.code(
                            (resultado_s2d.stdout + "\n" +
                             resultado_s2d.stderr)[-4000:]
                        )
                        raise RuntimeError(
                            "Sports2D nao gerou os dados esperados."
                        )

                # Criar video personalizado
                with st.spinner(
                    "Gerando video e graficos dos joelhos..."
                ):

                    resultado_video = subprocess.run(
                        [
                            sys.executable,
                            str(caminho_script)
                        ],
                        cwd=BASE,
                        capture_output=True,
                        text=True,
                        errors="replace"
                    )

                if resultado_video.returncode != 0:
                    st.code(resultado_video.stderr[-4000:])
                    raise RuntimeError(
                        "Erro ao gerar o video dos joelhos."
                    )

                arquivos_saida = [
                    VIDEO_FINAL,
                    CSV,
                    GRAF_DIR,
                    GRAF_ESQ
                ]

                if not all(
                    p.exists()
                    and p.stat().st_size > 0
                    and p.stat().st_mtime >= inicio - 2
                    for p in arquivos_saida
                ):
                    raise RuntimeError(
                        "Os resultados nao foram gerados corretamente."
                    )

                data_analise = datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                )

                pdf = gerar_pdf(
                    identificacao,
                    movimento,
                    condicao,
                    observacoes,
                    arquivo.name,
                    data_analise
                )

                st.session_state["resultado"] = {
                    "video": VIDEO_FINAL.read_bytes(),
                    "pdf": pdf,
                    "grafico_direito": GRAF_DIR.read_bytes(),
                    "grafico_esquerdo": GRAF_ESQ.read_bytes(),
                    "identificacao": identificacao,
                    "data": data_analise
                }

                st.success(
                    "Analise concluida com sucesso!"
                )

            except Exception as erro:
                st.error(
                    f"Nao foi possivel concluir a analise: {erro}"
                )


# ======================================
# 4. RESULTADOS E DOWNLOADS
# ======================================

if "resultado" in st.session_state:

    r = st.session_state["resultado"]

    st.divider()

    st.subheader("3. Resultados da analise")

    st.write(
        f"**Participante:** {r['identificacao']}"
    )

    st.write(
        f"**Data da analise:** {r['data']}"
    )

    st.write("### Graficos dos joelhos")

    c1, c2 = st.columns(2)

    with c1:
        st.image(
            r["grafico_direito"],
            caption="Joelho direito"
        )

    with c2:
        st.image(
            r["grafico_esquerdo"],
            caption="Joelho esquerdo"
        )

    st.write("### Arquivos disponiveis")

    st.download_button(
        "Baixar video com angulos dos joelhos",
        data=r["video"],
        file_name="video_joelhos.mp4",
        mime="video/mp4"
    )

    st.download_button(
        "Baixar relatorio completo em PDF",
        data=r["pdf"],
        file_name="relatorio_cinematico.pdf",
        mime="application/pdf"
    )
