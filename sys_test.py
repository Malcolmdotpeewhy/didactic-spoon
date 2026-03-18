import ctypes
from ctypes import wintypes
import time

def check_display():
    user32 = ctypes.windll.user32
    print(f"Screen width: {user32.GetSystemMetrics(0)}")
    print(f"Screen height: {user32.GetSystemMetrics(1)}")
    
    league_hwnd = user32.FindWindowW(None, "League of Legends")
    riot_hwnd = user32.FindWindowW(None, "Riot Client")
    
    print(f"League HWND: {league_hwnd}")
    print(f"Riot HWND: {riot_hwnd}")

    if league_hwnd:
        rect = wintypes.RECT()
        user32.GetWindowRect(league_hwnd, ctypes.byref(rect))
        print(f"League Rect: {rect.left}, {rect.top}, {rect.right}, {rect.bottom}")
        print(f"Calculated Pos: target_x={rect.right}, target_y={rect.top}")

check_display()
