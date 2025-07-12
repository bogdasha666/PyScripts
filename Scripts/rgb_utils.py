import time
import colorsys
import os

# Флаг для включения/отключения RGB-прицела глобально
rgb_enabled = False

# Статичный цвет, если RGB отключён
static_color = (255, 0, 0)  # Красный по умолчанию

def load_rgb_settings():
    cfg_path = "rgb.cfg"
    settings = {
        'speed': 0.5,
        'saturation': 1.0,
        'brightness': 1.0,
        'steps': 0.5
    }
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        if k in settings:
                            settings[k] = float(v)
    except Exception:
        pass
    return settings

def synced_rgb():
    settings = load_rgb_settings()
    speed = settings['speed']
    saturation = settings['saturation']
    brightness = settings['brightness']
    steps = settings['steps']
    # Calculate hue with speed
    t = time.time() * speed * 50 % 360
    hue = (t % 360) / 360.0
    # Quantize hue by steps
    if steps > 0:
        quant = max(1, int(1.0 / steps))
        hue = round(hue * quant) / quant
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
    return int(r * 255), int(g * 255), int(b * 255)

def get_rgb_color():
    if rgb_enabled:
        return synced_rgb()
    else:
        return static_color
