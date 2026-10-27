
from pathlib import Path
import rtoml
import Sports2D as pacote
from Sports2D import Sports2D

# Localizar o video
video = Path("videos/marcha1.MTS").resolve()

# Carregar as configuracoes oficiais
config_base = (
    Path(pacote.__file__).parent
    / "Demo"
    / "Config_demo.toml"
)

config = rtoml.load(config_base)

# Selecionar o video e o intervalo
config["base"]["video_input"] = str(video)
config["base"]["time_range"] = [0, 10]

# Analisar somente uma pessoa
config["base"]["nb_persons_to_detect"] = 1
config["base"]["person_ordering_method"] = "on_click"

# Salvar o video e os angulos
config["base"]["show_realtime_results"] = False
config["base"]["save_vid"] = True
config["base"]["save_pose"] = True
config["base"]["calculate_angles"] = True
config["base"]["save_angles"] = True

# Criar uma pasta para os resultados
saida = Path("resultados_joelho").resolve()
saida.mkdir(exist_ok=True)
config["base"]["result_dir"] = str(saida)

# Selecionar somente os joelhos
config["angles"]["joint_angles"] = [
    "Right knee",
    "Left knee"
]
config["angles"]["segment_angles"] = []
config["angles"]["display_angle_values_on"] = "body"

# Nao abrir os graficos automaticamente
config["post-processing"]["show_graphs"] = False

# Executar a analise
Sports2D.process(config)

print("Analise finalizada!")
