import win32gui
import win32con
import win32api
import win32process
import psutil
import time
import keyboard
from PIL import ImageGrab
import pyautogui
import os

FLAG_FILE = "autoreport.flag"

COLOR_MAP = {
    "Purple": ["be2d97", "711759", "be195f", "710a36"],
    "Green":  ["009f81", "005e4b", "006551", "003a2d"],
    "Orange": ["e6812b", "8a4b16", "e65118", "8a2d0a"],
    "Blue":   ["89cef5", "507b94", "89849e", "504d5d"],
    "Yellow": ["f1e442", "918924", "f19327", "915613"],
}

def get_flag_data():
    team = color = bind = None
    with open(FLAG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("team:"):
                team = line.split(":", 1)[1].strip()
            elif line.startswith("color:"):
                color = line.split(":", 1)[1].strip()
            elif line.startswith("bind:"):
                bind = line.split(":", 1)[1].strip()
    return team, color, bind

def find_cs2_window():
    def enum_windows_callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                if proc.name().lower() == "cs2.exe":
                    result.append(hwnd)
            except Exception:
                pass
    result = []
    win32gui.EnumWindows(enum_windows_callback, result)
    return result[0] if result else None

def send_esc_to_window(hwnd):
    # ESC key virtual code is 0x1B
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)

def hex_to_rgb(hex_str):
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def search_and_click_color(target_colors, team, img):
    width, height = img.size

    # Игнорировать верхнюю и нижнюю четверти
    y_start = height // 4
    y_end = height * 3 // 4

    # Для CT — только верхняя половина (без верхней четверти)
    # Для T — только нижняя половина (без нижней четверти)
    if team == "CT":
        y_end = height // 2
    elif team == "T":
        y_start = height // 2

    rgb_targets = [hex_to_rgb(c) for c in target_colors]

    for y in range(y_start, y_end):
        for x in range(width):
            pixel = img.getpixel((x, y))
            if pixel[:3] in rgb_targets:
                # Кликнуть по найденной точке
                pyautogui.click(x, y)
                print(f"Клик по цвету {pixel[:3]} в точке ({x},{y})")
                return True
    print("Цвет не найден.")
    return False

def click_report_if_found():
    report_path = os.path.join(os.path.dirname(__file__), "report.png")
    try:
        location = pyautogui.locateOnScreen(report_path, confidence=0.85)
        if location:
            center = pyautogui.center(location)
            time.sleep(0.05)  # Задержка перед кликами
            pyautogui.click(center)
            time.sleep(0.005)
            pyautogui.click(center)
            time.sleep(0.005)
            pyautogui.click(center)
            print(f'4 быстрых клика по report.png в точке {center}')
            # Клик на 40 пикселей выше центра экрана (2 раза)
            screen_width, screen_height = pyautogui.size()
            center_screen = (screen_width // 2, screen_height // 2)
            above_center = (center_screen[0], center_screen[1] - 40)
            pyautogui.click(above_center)
            time.sleep(0.01)
            pyautogui.click(above_center)
            print(f'2 клика выше центра экрана: {above_center}')
            # Клик на 180 вправо и 155 вниз от центра экрана (2 раза)
            offset_point = (center_screen[0] + 180, center_screen[1] + 155)
            time.sleep(0.002)
            pyautogui.click(offset_point)
            time.sleep(0.01)
            print(f'2 клика вправо и вниз от центра экрана: {offset_point}')
            return True
        else:
            print('report.png не найден на экране.')
            return False
    except Exception as e:
        print(f'Ошибка поиска report.png: {e}')
        return False

def main():
    print("Ожидание нажатия клавиши (бинд будет перечитываться каждый раз из флага)...")
    while True:
        _, _, bind_key = get_flag_data()
        keyboard.wait(bind_key)
        team, color, bind_key = get_flag_data()
        if not (team and color and bind_key):
            print("Не удалось найти все параметры во флаге.")
            time.sleep(0.5)
            continue

        if color not in COLOR_MAP:
            print(f"Неизвестный цвет: {color}")
            time.sleep(0.5)
            continue

        hwnd = find_cs2_window()
        if hwnd:
            print("Окно CS2 найдено, отправляю ESC...")
            send_esc_to_window(hwnd)
            time.sleep(0.2)
            print(f"Ищу цвет {color} для команды {team}...")
            img = ImageGrab.grab()
            found = search_and_click_color(COLOR_MAP[color], team, img)
            if not found:
                print("Цвет не найден на экране.")
            else:
                # После клика по цвету ищем report.png
                time.sleep(0.2)
                click_report_if_found()
        else:
            print("Окно CS2 не найдено.")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
