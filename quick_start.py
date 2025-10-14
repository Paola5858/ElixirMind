#!/usr/bin/env python3
"""
ElixirMind Quick Start Validator
Verifica se o sistema está pronto para uso.
"""

import asyncio
import sys
from pathlib import Path

class SystemValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []

    async def validate_dependencies(self):
        """Valida dependências Python"""
        print("🔍 Verificando dependências...")

        required_modules = [
            ('cv2', 'opencv-python'),
            ('numpy', 'numpy'),
            ('PIL', 'Pillow'),
            ('mss', 'mss'),
            ('pyautogui', 'pyautogui'),
        ]

        for module_name, package_name in required_modules:
            try:
                __import__(module_name)
                print(f"   ✅ {module_name}")
            except ImportError:
                self.issues.append(f"❌ {module_name} não encontrado (instale: pip install {package_name})")

        # Optional dependencies
        optional_modules = [
            ('torch', 'torch'),
            ('streamlit', 'streamlit'),
        ]

        for module_name, package_name in optional_modules:
            try:
                __import__(module_name)
                print(f"   ✅ {module_name} (opcional)")
            except ImportError:
                self.warnings.append(f"⚠️ {module_name} não encontrado (opcional: pip install {package_name})")

    async def validate_emulator(self):
        """Valida conexão com emulador"""
        print("🔍 Verificando emulador...")

        import subprocess
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            if 'device' in result.stdout and 'emulator' in result.stdout.lower():
                print("   ✅ Emulador conectado via ADB")
            elif 'device' in result.stdout:
                print("   ✅ Dispositivo ADB conectado")
            else:
                self.warnings.append("⚠️ Nenhum dispositivo ADB detectado")
        except FileNotFoundError:
            self.warnings.append("⚠️ ADB não encontrado no PATH")
        except subprocess.TimeoutExpired:
            self.warnings.append("⚠️ ADB não respondeu (timeout)")

    async def validate_models(self):
        """Valida modelos de IA"""
        print("🔍 Verificando modelos...")

        models_dir = Path("models")
        if not models_dir.exists():
            self.warnings.append("⚠️ Diretório models/ não encontrado")
            return

        yolo_models = list(models_dir.glob("*.pt"))
        if yolo_models:
            print(f"   ✅ {len(yolo_models)} modelo(s) YOLOv5 encontrado(s)")
            for model in yolo_models:
                size_mb = model.stat().st_size / (1024 * 1024)
                print(".1f"        else:
            self.warnings.append("⚠️ Nenhum modelo YOLOv5 encontrado")

    async def validate_config(self):
        """Valida configuração"""
        print("🔍 Verificando configuração...")

        config_files = [
            Path("config.py"),
            Path("config.json"),
            Path("config.yaml"),
        ]

        config_found = False
        for config_file in config_files:
            if config_file.exists():
                print(f"   ✅ {config_file.name} encontrado")
                config_found = True
                break

        if not config_found:
            self.warnings.append("⚠️ Arquivo de configuração não encontrado")

    async def validate_directories(self):
        """Valida estrutura de diretórios"""
        print("🔍 Verificando estrutura...")

        required_dirs = [
            "vision",
            "actions",
            "strategy",
            "core",
            "models",
            "data",
        ]

        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists() and dir_path.is_dir():
                print(f"   ✅ {dir_name}/")
            else:
                self.warnings.append(f"⚠️ {dir_name}/ não encontrado")

    async def run_validation(self):
        """Executa todas as validações"""
        print("🚀 Validando sistema ElixirMind...\n")

        await self.validate_dependencies()
        await self.validate_emulator()
        await self.validate_models()
        await self.validate_config()
        await self.validate_directories()

        print("
📊 RESULTADOS DA VALIDAÇÃO:"        print(f"❌ Problemas críticos: {len(self.issues)}")
        print(f"⚠️ Avisos: {len(self.warnings)}")

        if self.issues:
            print("
🚨 PROBLEMAS CRÍTICOS:"            for issue in self.issues:
                print(f"  {issue}")
            print("
❌ Sistema NÃO está pronto para uso!"            return False

        if self.warnings:
            print("
⚠️ AVISOS:"            for warning in self.warnings:
                print(f"  {warning}")

        print("
✅ Sistema básico funcional!"        return True

async def main():
    print("🤖 ElixirMind - Quick Start Validator")
    print("=" * 50)

    validator = SystemValidator()
    is_ready = await validator.run_validation()

    if is_ready:
        print("
🚀 PRÓXIMOS PASSOS:"        print("1. pip install -r requirements.txt  # Instalar dependências")
        print("2. python setup_wizard.py          # Executar configuração")
        print("3. python minimal_bot.py           # Testar bot básico")
        print("4. streamlit run dashboard/app.py  # Abrir dashboard")
        print("
💡 Para desenvolvimento:"        print("   python main.py --mode development")
    else:
        print("
🔧 CORREÇÕES NECESSÁRIAS:"        print("Execute os comandos indicados acima para resolver os problemas críticos!")

if __name__ == "__main__":
    asyncio.run(main())
