# Fixtures para Testes Visuais

Este diretório contém imagens estáticas usadas para testar os componentes de visão computacional do detector.

## Estrutura

- `images/`: Imagens de teste para diferentes cenários do jogo
  - `battle_screen.png`: Tela de batalha ativa com elixir, cartas e torres visíveis
  - `main_menu.png`: Menu principal do jogo
  - `loading_screen.png`: Tela de carregamento

## Como Adicionar Novas Imagens de Teste

1. Capture screenshots do jogo em diferentes estados
2. Salve as imagens em `images/` com nomes descritivos
3. Atualize os testes em `test_vision_detector.py` para incluir os novos casos

## Notas

- As imagens devem estar no formato PNG
- Use resoluções consistentes (recomendado: 1920x1080)
- Certifique-se de que as imagens representam estados reais do jogo
