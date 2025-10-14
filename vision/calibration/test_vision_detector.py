"""
Testes visuais para o Detector usando imagens estáticas.

Este script carrega imagens de fixtures e valida se a detecção de batalha
funciona como esperado para diferentes cenários do jogo, incluindo detecção
de elixir, cartas, torres e templates.
"""

import pytest
import cv2
from pathlib import Path

# Adiciona o diretório raiz ao path para permitir importações diretas
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vision.detector import Detector

# Config class defined inline to avoid import issues
class Config:
    def __init__(self):
        self.ROI_ELIXIR = (1700, 900, 1900, 1000)
        self.ROI_HAND = (0, 800, 1920, 1080)
        self.ROI_BATTLEFIELD = (0, 0, 1920, 800)
        self.ROI_ENEMY_TOWERS = (0, 0, 1920, 400)
        self.ROI_MY_TOWERS = (0, 400, 1920, 800)

# --- Configuração dos Testes ---

# Diretório onde as imagens de teste estão localizadas
FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"

# Diretório para salvar os resultados visuais da depuração
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Fixtures do Pytest ---

@pytest.fixture(scope="module")
def detector():
    """
    Fixture do Pytest que inicializa o Detector uma vez para todos os testes.
    """
    print("Inicializando o Detector para os testes visuais...")
    config = Config()
    # Garante que o detector seja inicializado para carregar modelos, etc.
    # Pode ser necessário mockar caminhos de modelos se eles não estiverem presentes
    # config.YOLO_MODEL_PATH = "path/to/fake_model.pt"
    d = Detector(config)
    d.initialize()
    yield d
    print("\nFinalizando o Detector.")
    d.shutdown()

# --- Casos de Teste ---

@pytest.mark.parametrize(
    "image_filename, expected_battle_state, description",
    [
        ("battle_screen.png", True, "Tela de batalha ativa"),
        ("main_menu.png", False, "Menu principal do jogo"),
        ("loading_screen.png", False, "Tela de carregamento"),
        # Adicione mais casos de teste aqui
    ],
)
def test_battle_detection_on_static_images(
    detector: Detector, image_filename: str, expected_battle_state: bool, description: str
):
    """
    Testa a função `detect_battle` com diferentes imagens estáticas.
    """
    image_path = IMAGES_DIR / image_filename
    if not image_path.exists():
        pytest.skip(f"Arquivo de imagem de teste não encontrado: {image_path}")

    print(f"\nTestando: {description} ({image_filename})")
    image_path_str = str(image_path).replace('\\', '/')
    print(f"Loading image from: {image_path_str}")
    image = cv2.imread(image_path_str)
    assert image is not None, f"Não foi possível carregar a imagem: {image_path}"

    # Executa a detecção com o modo de depuração ativado
    is_battle, debug_image = detector.detect_battle(image, debug_mode=True)

    # Salva a imagem de depuração para análise visual
    output_path = OUTPUT_DIR / f"debug_{image_filename}"
    cv2.imwrite(str(output_path), debug_image)
    print(f"Imagem de depuração salva em: {output_path}")

    # Valida o resultado
    assert is_battle == expected_battle_state


@pytest.mark.parametrize(
    "image_filename, expected_elixir_present, description",
    [
        ("battle_screen.png", True, "Tela de batalha com elixir visível"),
        ("main_menu.png", False, "Menu principal sem elixir"),
        ("loading_screen.png", False, "Tela de carregamento sem elixir"),
    ],
)
def test_elixir_detection_on_static_images(
    detector: Detector, image_filename: str, expected_elixir_present: bool, description: str
):
    """
    Testa a detecção de elixir com imagens estáticas.
    """
    image_path = IMAGES_DIR / image_filename
    if not image_path.exists():
        pytest.skip(f"Arquivo de imagem de teste não encontrado: {image_path}")

    print(f"\nTestando elixir: {description} ({image_filename})")
    image = cv2.imread(str(image_path).replace('\\', '/'))
    assert image is not None, f"Não foi possível carregar a imagem: {image_path}"

    # Executa a detecção de elixir
    elixir_present = detector._detect_elixir_presence(image)

    # Valida o resultado
    assert elixir_present == expected_elixir_present


@pytest.mark.parametrize(
    "image_filename, expected_cards_present, description",
    [
        ("battle_screen.png", True, "Tela de batalha com cartas na mão"),
        ("main_menu.png", False, "Menu principal sem cartas"),
        ("loading_screen.png", False, "Tela de carregamento sem cartas"),
    ],
)
def test_card_hand_detection_on_static_images(
    detector: Detector, image_filename: str, expected_cards_present: bool, description: str
):
    """
    Testa a detecção de cartas na mão com imagens estáticas.
    """
    image_path = IMAGES_DIR / image_filename
    if not image_path.exists():
        pytest.skip(f"Arquivo de imagem de teste não encontrado: {image_path}")

    print(f"\nTestando cartas: {description} ({image_filename})")
    image = cv2.imread(str(image_path).replace('\\', '/'))
    assert image is not None, f"Não foi possível carregar a imagem: {image_path}"

    # Executa a detecção de cartas
    cards_present = detector._detect_card_hand(image)

    # Valida o resultado
    assert cards_present == expected_cards_present


@pytest.mark.parametrize(
    "image_filename, expected_towers_present, description",
    [
        ("battle_screen.png", True, "Tela de batalha com torres visíveis"),
        ("main_menu.png", False, "Menu principal sem torres"),
        ("loading_screen.png", False, "Tela de carregamento sem torres"),
    ],
)
def test_tower_detection_on_static_images(
    detector: Detector, image_filename: str, expected_towers_present: bool, description: str
):
    """
    Testa a detecção de torres com imagens estáticas.
    """
    image_path = IMAGES_DIR / image_filename
    if not image_path.exists():
        pytest.skip(f"Arquivo de imagem de teste não encontrado: {image_path}")

    print(f"\nTestando torres: {description} ({image_filename})")
    image = cv2.imread(str(image_path).replace('\\', '/'))
    assert image is not None, f"Não foi possível carregar a imagem: {image_path}"

    # Executa a detecção de torres
    towers_present = detector._detect_towers(image)

    # Valida o resultado
    assert towers_present == expected_towers_present


@pytest.mark.parametrize(
    "image_filename, expected_template_match, description",
    [
        ("battle_screen.png", True, "Tela de batalha com template correspondente"),
        ("main_menu.png", False, "Menu principal sem template"),
        ("loading_screen.png", False, "Tela de carregamento sem template"),
    ],
)
def test_template_matching_on_static_images(
    detector: Detector, image_filename: str, expected_template_match: bool, description: str
):
    """
    Testa o matching de templates com imagens estáticas.
    """
    image_path = IMAGES_DIR / image_filename
    if not image_path.exists():
        pytest.skip(f"Arquivo de imagem de teste não encontrado: {image_path}")

    print(f"\nTestando template: {description} ({image_filename})")
    image = cv2.imread(str(image_path).replace('\\', '/'))
    assert image is not None, f"Não foi possível carregar a imagem: {image_path}"

    # Executa o matching de templates
    template_match = detector._detect_battle_template(image)

    # Valida o resultado
    assert template_match == expected_template_match
