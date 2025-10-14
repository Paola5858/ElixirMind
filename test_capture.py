#!/usr/bin/env python3
"""
Simple test script for screen capture functionality.
"""

import sys
sys.path.insert(0, r'C:\Users\Usuario\AppData\Local\Programs\Python\Python310\Lib\site-packages')

import time
import cv2
import numpy as np
import mss
import pyautogui
import logging
from pathlib import Path
import platform

# Windows-specific imports
if platform.system() == 'Windows':
    try:
        import win32gui
        import win32con
        WIN32_AVAILABLE = True
        print("Win32 available")
    except ImportError:
        WIN32_AVAILABLE = False
        print("Win32 not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mss_capture():
    """Test MSS screen capture."""
    try:
        print("Testing MSS capture...")
        sct = mss.mss()
        monitor = sct.monitors[1]  # Primary monitor

        # Test basic capture
        start_time = time.time()
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        capture_time = time.time() - start_time

        print(f"MSS capture successful: {frame.shape}, time: {capture_time:.3f}s")

        # Save test image
        test_image = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        cv2.imwrite("mss_test.png", test_image)
        print("Saved mss_test.png")

        sct.close()
        return True

    except Exception as e:
        print(f"MSS capture failed: {e}")
        return False

def test_pyautogui_capture():
    """Test PyAutoGUI screenshot capture."""
    try:
        print("Testing PyAutoGUI capture...")
        start_time = time.time()
        screenshot = pyautogui.screenshot()
        capture_time = time.time() - start_time

        frame = np.array(screenshot)
        print(f"PyAutoGUI capture successful: {frame.shape}, time: {capture_time:.3f}s")

        # Save test image
        test_image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite("pyautogui_test.png", test_image)
        print("Saved pyautogui_test.png")

        return True

    except Exception as e:
        print(f"PyAutoGUI capture failed: {e}")
        return False

def test_win32_capture():
    """Test Win32 API screen capture."""
    if not WIN32_AVAILABLE:
        print("Win32 not available, skipping test")
        return False

    try:
        print("Testing Win32 capture...")

        # Find emulator window
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if 'LDPlayer' in title or 'dnplayer' in class_name or 'MEmu' in title:
                    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                    width = right - left
                    height = bottom - top
                    if 800 <= width <= 2560 and 600 <= height <= 1600:
                        windows.append((hwnd, title, class_name, left, top, width, height))

        windows = []
        win32gui.EnumWindows(callback, windows)

        if not windows:
            print("No emulator windows found")
            return False

        hwnd, title, class_name, left, top, width, height = windows[0]
        print(f"Found window: {title} ({width}x{height})")

        # Capture using Win32
        start_time = time.time()
        frame = capture_window_win32(hwnd, width, height)
        capture_time = time.time() - start_time

        if frame is not None:
            print(f"Win32 capture successful: {frame.shape}, time: {capture_time:.3f}s")
            cv2.imwrite("win32_test.png", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            print("Saved win32_test.png")
            return True
        else:
            print("Win32 capture failed")
            return False

    except Exception as e:
        print(f"Win32 capture failed: {e}")
        return False

def capture_window_win32(hwnd, width, height):
    """Capture window using Win32 API."""
    try:
        import win32ui

        # Get device context
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        # Create bitmap
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # Copy window content
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

        # Convert to numpy array
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        # Clean up
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        # Convert bitmap to numpy array
        frame = np.frombuffer(bmpstr, dtype=np.uint8)
        frame.shape = (height, width, 4)  # BGRA format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        return frame

    except Exception as e:
        print(f"Win32 capture error: {e}")
        return None

def main():
    """Main test function."""
    print("🧪 Screen Capture Test")
    print("=" * 30)

    results = {}

    # Test MSS
    results['mss'] = test_mss_capture()
    print()

    # Test PyAutoGUI
    results['pyautogui'] = test_pyautogui_capture()
    print()

    # Test Win32
    results['win32'] = test_win32_capture()
    print()

    # Summary
    successful = [m for m, r in results.items() if r]
    print("📊 Results:")
    for method, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"  {method.upper()}: {status}")

    if successful:
        print(f"\n🎯 Recommended methods: {', '.join(successful).upper()}")
    else:
        print("\n❌ No capture methods working!")

if __name__ == "__main__":
    main()
