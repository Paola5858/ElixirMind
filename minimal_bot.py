#!/usr/bin/env python3
"""
ElixirMind Minimal Bot
Versão básica funcional para testes iniciais.
"""

import cv2
import numpy as np
import pyautogui
import time
import mss
from pathlib import Path

class MinimalBot:
    def __init__(self):
        self.sct = mss.mss()
        self.running = False

        # ROIs básicos (ajustar conforme sua resolução)
        self.roi_elixir = (1700, 900, 1900, 1000)
        self.roi_cards = (0, 800, 1920, 1080)

        # Posições das cartas
        self.card_positions = [
            (240, 940), (480, 940), (720, 940), (960, 940)
        ]

    def capture_screen(self):
        """Captura tela do jogo"""
        print("📸 Tentando capturar tela...")
        try:
            monitor = self.sct.monitors[1]  # Monitor principal
            screenshot = self.sct.grab(monitor)
            frame = np.array(screenshot)
            print("✅ Tela capturada com sucesso")
            return frame
        except Exception as e:
            print(f"❌ Erro ao capturar tela: {e}")
            return None

    def detect_elixir(self, frame):
        """Detecção básica de elixir por cor"""
        try:
            print("🔍 Detectando elixir...")
            # Extrai região do elixir
            roi = frame[self.roi_elixir[1]:self.roi_elixir[3],
                       self.roi_elixir[0]:self.roi_elixir[2]]

            # Converte para HSV
            hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)

            # Máscara para cor roxa/rosa do elixir
            lower_purple = np.array([140, 50, 50])
            upper_purple = np.array([160, 255, 255])
            mask = cv2.inRange(hsv, lower_purple, upper_purple)

            # Calcula percentual preenchido
            total_pixels = mask.shape[0] * mask.shape[1]
            filled_pixels = np.sum(mask > 0)
            fill_ratio = filled_pixels / total_pixels

            # Estima elixir (0-10)
            estimated_elixir = int(fill_ratio * 10)
            elixir = max(0, min(10, estimated_elixir))
            print(f"💜 Elixir detectado: {elixir}")
            return elixir

        except Exception as e:
            print(f"❌ Erro detecção elixir: {e}")
            return 5  # Valor padrão

    def is_in_battle(self, frame):
        """Detecta se está em batalha"""
        try:
            print("🔍 Verificando se está em batalha...")
            # Verifica se há cor de elixir na tela
            roi = frame[self.roi_elixir[1]:self.roi_elixir[3],
                       self.roi_elixir[0]:self.roi_elixir[2]]

            hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
            lower_purple = np.array([140, 50, 50])
            upper_purple = np.array([160, 255, 255])
            mask = cv2.inRange(hsv, lower_purple, upper_purple)

            purple_pixels = np.sum(mask > 0)
            total_pixels = mask.shape[0] * mask.shape[1]
            ratio = purple_pixels / total_pixels

            in_battle = ratio > 0.1
            if in_battle:
                print("✅ Em batalha detectada")
            else:
                print("❌ Não está em batalha")
            return in_battle

        except Exception as e:
            print(f"❌ Erro ao detectar batalha: {e}")
            return False

    def play_random_card(self):
        """Joga carta aleatória em posição aleatória"""
        try:
            print("🎮 Preparando para jogar carta...")
            # Escolhe carta aleatória (0-3)
            import random
            card_index = random.randint(0, 3)
            card_pos = self.card_positions[card_index]

            # Posições aleatórias no campo
            target_positions = [
                (700, 500),   # Ponte esquerda
                (1220, 500),  # Ponte direita
                (960, 600),   # Centro
            ]
            target_pos = random.choice(target_positions)

            # Executa drag da carta
            pyautogui.moveTo(card_pos[0], card_pos[1])
            time.sleep(0.1)
            pyautogui.dragTo(
                target_pos[0], target_pos[1], duration=0.3, tween=pyautogui.easeOutQuad)

            print(f"✅ Decisão tomada: jogar carta {card_index} em {target_pos}")
            return True

        except Exception as e:
            print(f"❌ Erro ao jogar carta: {e}")
            return False

    async def run(self):
        """Loop principal do bot"""
        print("🤖 MinimalBot iniciado!")
        print("⚠️ Abra Clash Royale e inicie uma batalha")
        print("⚠️ Pressione Ctrl+C para parar")

        self.running = True
        last_action_time = 0

        try:
            while self.running:
                # Captura tela
                frame = self.capture_screen()

                # Verifica se está em batalha
                if self.is_in_battle(frame):
                    # Detecta elixir
                    elixir = self.detect_elixir(frame)
                    print(f"💜 Elixir: {elixir}")

                    # Joga carta se tiver elixir e tempo passou
                    current_time = time.time()
                    if (elixir >= 4 and
                        current_time - last_action_time > 3):

                        print(
                            f"🤔 Decisão tomada: jogar carta aleatória com {elixir} de elixir.")
                        if self.play_random_card():
                            last_action_time = current_time
                        else:
                            print("❌ Falha ao executar ação")

                else:
                    print("❌ Nenhum elemento de batalha detectado.")
                    print("⏳ Aguardando batalha...")

                await asyncio.sleep(1)  # Pausa 1 segundo de forma assíncrona

        except KeyboardInterrupt:
            print("\n🛑 Bot parado pelo usuário")
            self.running = False

# Execução
if __name__ == "__main__":
    import asyncio
    bot = MinimalBot()
    asyncio.run(bot.run())
