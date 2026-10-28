"""Contrast checks for the configured light theme, not a complete WCAG audit."""
from pathlib import Path
import tomllib


def contrast(a, b):
    def luminance(hex_color):
        channels = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                  for v in channels]
        return sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + .05) / (low + .05)


def test_body_links_and_white_button_labels_meet_normal_text_contrast():
    config = Path(__file__).resolve().parents[1] / '.streamlit/config.toml'
    theme = tomllib.loads(config.read_text())['theme']
    assert theme['base'] == 'light'
    for background in ('backgroundColor', 'secondaryBackgroundColor'):
        assert contrast(theme['textColor'], theme[background]) >= 4.5
        assert contrast(theme['primaryColor'], theme[background]) >= 4.5
    assert contrast('#ffffff', theme['primaryColor']) >= 4.5
