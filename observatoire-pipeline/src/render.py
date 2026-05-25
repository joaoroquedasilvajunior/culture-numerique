"""
Rendu du tableau de bord HTML.

Le template HTML contient un placeholder unique `__DASHBOARD_DATA__` que l'on
remplace par le JSON sérialisé des données. Cela évite tout moteur de templating
externe et garde le pipeline auto-suffisant.
"""

from __future__ import annotations
import json
from pathlib import Path


def render_dashboard(data: dict, template_path: Path, output_path: Path) -> Path:
    template_path = Path(template_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = template_path.read_text(encoding='utf-8')
    if '__DASHBOARD_DATA__' not in html:
        raise ValueError(f"Le template {template_path} ne contient pas le placeholder "
                         f"`__DASHBOARD_DATA__`.")

    payload = json.dumps(data, ensure_ascii=False)
    rendered = html.replace('__DASHBOARD_DATA__', payload)
    output_path.write_text(rendered, encoding='utf-8')
    return output_path
