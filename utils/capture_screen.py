#!/usr/bin/env python3
"""
Screen Capture Testing Utilities
Test different capture methods for emulator compatibility.
"""

import time
import cv2
import numpy as np
import os
from pathlib import Path

class CaptureTester:
    """Test different screen capture methods."""

    def __init__(self):
        self.test_results = {}
        self.screenshots_dir = Path("test_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    def run_all_tests(self):
        """Run all capture method tests."""
        print("🧪 Running Screen Capture Tests")
        print("=" * 50)

        tests = [
            ("MSS Capture", self.test_mss_capture),
            ("PyAutoGUI Capture", self.test_pyautogui_capture),
            ("Win32 Capture", self.test_win32_capture),
        ]

        for test_name, test_func in tests:
            print(f"\n🔬 Testing: {test_name}")
            try:
                result = test_func()
                self.test_results[test_name] = result
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                print(f"{status}: {result.get('message', '')}")
                if "time" in result:
                    print(".3f")
            except Exception as e:
                self.test_results[test_name] = {"success": False, "error": str(e)}
                print(f"❌ ERROR: {e}")

        self.print_summary()

    def test_mss_capture(self):
        """Test MSS screen capture."""
        try:
            import mss

            start_time = time.time()
            sct = mss.mss()

            # Capture primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Convert to numpy array
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

            capture_time = time.time() - start_time

            # Save test screenshot
            filename = self.screenshots_dir / "mss_test.png"
            cv2.imwrite(str(filename), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            return {
                "success": True,
                "message": f"Captured {frame.shape[1]}x{frame.shape[0]} frame",
                "time": capture_time,
                "shape": frame.shape,
                "filename": str(filename)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_pyautogui_capture(self):
        """Test PyAutoGUI screen capture."""
        try:
            import pyautogui

            start_time = time.time()
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            capture_time = time.time() - start_time

            # Save test screenshot
            filename = self.screenshots_dir / "pyautogui_test.png"
            cv2.imwrite(str(filename), frame)

            return {
                "success": True,
                "message": f"Captured {frame.shape[1]}x{frame.shape[0]} frame",
                "time": capture_time,
                "shape": frame.shape,
                "filename": str(filename)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_win32_capture(self):
        """Test Win32 window capture."""
        try:
            import win32gui
            import win32ui
            import win32con
            from ctypes import windll

            # Find emulator windows
            emulator_windows = self._find_emulator_windows()

            if not emulator_windows:
                return {
                    "success": False,
                    "message": "No emulator windows found"
                }

            # Use first window found
            hwnd = emulator_windows[0]['hwnd']

            start_time = time.time()

            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Create device context
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Create bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Copy window content
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

            if result == 1:
                # Convert bitmap to numpy array
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)

                frame = np.frombuffer(bmpstr, dtype=np.uint8)
                frame.shape = (height, width, 4)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

                capture_time = time.time() - start_time

                # Save test screenshot
                filename = self.screenshots_dir / "win32_test.png"
                cv2.imwrite(str(filename), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

                # Cleanup
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)

                return {
                    "success": True,
                    "message": f"Captured window {width}x{height}",
                    "time": capture_time,
                    "shape": frame.shape,
                    "filename": str(filename),
                    "window_title": emulator_windows[0]['title']
                }
            else:
                return {
                    "success": False,
                    "message": "PrintWindow failed"
                }

        except ImportError:
            return {
                "success": False,
                "error": "win32gui/win32ui not available"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _find_emulator_windows(self):
        """Find emulator windows on Windows."""
        try:
            import win32gui

            emulator_titles = {
                'ldplayer': ['LDPlayer', 'dnplayer'],
                'memu': ['MEmu', 'MEmu Player'],
                'bluestacks': ['BlueStacks', 'HD-Player']
            }

            windows = []

            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                    title = win32gui.GetWindowText(hwnd)

                    # Check for emulator titles
                    for emulator, titles in emulator_titles.items():
                        for target_title in titles:
                            if target_title.lower() in title.lower():
                                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                                width = right - left
                                height = bottom - top

                                # Filter reasonable window sizes
                                if 800 <= width <= 2560 and 600 <= height <= 1600:
                                    windows.append({
                                        'hwnd': hwnd,
                                        'title': title,
                                        'width': width,
                                        'height': height
                                    })

            win32gui.EnumWindows(callback, windows)
            return windows

        except Exception as e:
            print(f"Error finding windows: {e}")
            return []

    def print_summary(self):
        """Print test summary."""
        print("\n📊 Screen Capture Test Summary")
        print("=" * 50)

        successful_tests = 0
        total_tests = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅" if result.get("success") else "❌"
            print(f"{status} {test_name}: {result.get('message', result.get('error', 'Unknown'))}")

            if result.get("success"):
                successful_tests += 1

        print(f"\nOverall: {successful_tests}/{total_tests} tests passed")

        if successful_tests > 0:
            print("🎉 At least one capture method works!")
        else:
            print("💥 All capture methods failed - check dependencies")

def main():
    tester = CaptureTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
