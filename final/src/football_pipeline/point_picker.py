"""Responsive image point selection using Streamlit's inline component API."""

import base64
import math
from copy import deepcopy

import cv2
import streamlit as st

from .calibration_input import point_label
from .contracts import PipelineError


def apply_point_click(points, event, *, context, selected, width, height):
    """Validate a browser event before changing original-image coordinates."""
    if not isinstance(event, dict) or event.get("context") != context:
        raise PipelineError("Dit klikpunt hoort bij een ouder beeld. Klik opnieuw.")
    index = event.get("index")
    if type(index) is not int or index != selected or not 0 <= index < len(points):
        raise PipelineError("Kies eerst een geldig veldpunt.")
    coordinates = [event.get("x"), event.get("y")]
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in coordinates):
        raise PipelineError("Het klikpunt bevat ongeldige coördinaten.")
    x, y = coordinates
    if not (0 <= x <= width - 1 and 0 <= y <= height - 1):
        raise PipelineError("Klik binnen het videobeeld.")
    updated = deepcopy(points)
    updated[index].update(x=round(x, 2), y=round(y, 2))
    return updated


def picker_view(event):
    """Optional view state never changes a clicked point's original-image coordinates."""
    values = [event.get(key) for key in ("zoom", "scroll_x", "scroll_y")]
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        return None
    zoom, x, y = values
    # Scroll uses screen pixels, not video pixels; the browser clamps the viewport.
    if not 1 <= zoom <= 4 or x < 0 or y < 0:
        return None
    return {"zoom": zoom, "scroll_x": x, "scroll_y": y}


PICKER_JS = """
export default function(component) {
  const {data, parentElement, setTriggerValue} = component;
  const canvas = parentElement.querySelector('canvas');
  const zoom = parentElement.querySelector('input');
  const output = parentElement.querySelector('output');
  const status = parentElement.querySelector('[role="status"]');
  const viewport = parentElement.querySelector('.viewport');
  const ctx = canvas.getContext('2d');
  let disposed = false;
  let pressed = null;
  let sent = false;
  canvas.width = data.width;
  canvas.height = data.height;
  canvas.setAttribute('aria-label', 'Klik de positie van ' + data.pointLabel);
  zoom.value = data.view?.zoom ?? 1;
  const resize = () => {
    canvas.style.width = (Number(zoom.value) * 100) + '%';
    output.textContent = zoom.value + '×';
  };
  resize();
  zoom.oninput = resize;
  const picture = new Image();
  picture.onload = () => {
    if (disposed) return;
    ctx.drawImage(picture, 0, 0, data.width, data.height);
    const radius = Math.max(5, data.width / 250);
    ctx.font = 'bold ' + Math.max(14, data.width / 110) + 'px sans-serif';
    data.points.forEach((point, i) => {
      if (point.x === null || point.y === null || !Number.isFinite(point.x) || !Number.isFinite(point.y)) return;
      ctx.beginPath();
      ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = point.role === 'fit' ? '#00d5ff' : '#ffce32';
      ctx.fill();
      ctx.lineWidth = i === data.selected ? radius / 2 : radius / 4;
      ctx.strokeStyle = i === data.selected ? '#ffffff' : '#111111';
      ctx.stroke();
      ctx.lineWidth = Math.max(3, data.width / 700);
      ctx.strokeStyle = '#111111';
      const labelX = Math.min(point.x + radius * 1.3, data.width - radius * 4);
      const labelY = Math.max(radius * 2, point.y - radius);
      ctx.strokeText(String(i + 1), labelX, labelY);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(String(i + 1), labelX, labelY);
    });
    (data.diagnostics || []).forEach((check, i) => {
      const [x, y] = check.predicted;
      if (!Number.isFinite(x) || !Number.isFinite(y)) return;
      ctx.strokeStyle = '#ff5252';
      ctx.lineWidth = Math.max(3, radius / 3);
      ctx.beginPath();
      ctx.moveTo(check.clicked[0], check.clicked[1]);
      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.strokeStyle = '#ff9900';
      ctx.beginPath();
      ctx.moveTo(x - radius, y - radius);
      ctx.lineTo(x + radius, y + radius);
      ctx.moveTo(x - radius, y + radius);
      ctx.lineTo(x + radius, y - radius);
      ctx.stroke();
    });
    viewport.scrollLeft = data.view?.scroll_x ?? 0;
    viewport.scrollTop = data.view?.scroll_y ?? 0;
    status.textContent = 'Klik op het beeld voor: ' + data.pointLabel;
  };
  picture.onerror = () => { status.textContent = 'Het referentiebeeld kon niet laden.'; };
  picture.src = data.image;
  canvas.onpointerdown = event => {
    if (event.button === 0) pressed = [event.clientX, event.clientY];
  };
  canvas.onpointercancel = () => { pressed = null; };
  canvas.onpointerup = event => {
    if (!pressed || sent || !picture.complete || !picture.naturalWidth) return;
    const distance = Math.hypot(event.clientX - pressed[0], event.clientY - pressed[1]);
    pressed = null;
    if (distance > 6) return; // Panning/scrolling is not point selection.
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const rx = (event.clientX - rect.left) / rect.width;
    const ry = (event.clientY - rect.top) / rect.height;
    if (rx < 0 || rx > 1 || ry < 0 || ry > 1) return;
    const x = Math.min(data.width - 1, rx * data.width);
    const y = Math.min(data.height - 1, ry * data.height);
    sent = true;
    status.textContent = 'Punt bewaren…';
    setTriggerValue('clicked', {x, y, index: data.selected, context: data.context,
      zoom: Number(zoom.value), scroll_x: viewport.scrollLeft, scroll_y: viewport.scrollTop});
  };
  return () => {
    disposed = true;
    picture.onload = null;
    picture.onerror = null;
    canvas.onpointerdown = null;
    canvas.onpointerup = null;
    canvas.onpointercancel = null;
    zoom.oninput = null;
  };
}
"""


def _register_picker():
    # Registration is idempotent, including after a runtime restart or hot reload.
    return st.components.v2.component(
        "football_field_point_picker",
        html="""
        <label>Zoom <input type="range" min="1" max="4" step="0.25" value="1"
          aria-label="Zoom op het referentiebeeld" /><output>1×</output></label>
        <div class="viewport"><canvas role="img"></canvas></div>
        <p role="status" aria-live="polite">Referentiebeeld laden…</p>
        """,
        css="""
        label {display:flex; align-items:center; gap:0.75rem; margin-bottom:0.5rem;}
        input {max-width:16rem; flex:1; accent-color:var(--st-primary-color);}
        .viewport {width:100%; max-height:550px; overflow:auto; background:#111;}
        canvas {display:block; height:auto; cursor:crosshair; touch-action:pan-x pan-y;}
        p {font-size:0.9rem; margin:0.5rem 0; color:var(--st-text-color);}
        """,
        js=PICKER_JS,
    )


def point_picker(frame, points, selected, *, context, key, on_clicked_change, diagnostics=None):
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise PipelineError("Referentiebeeld kon niet worden voorbereid.")
    return _register_picker()(
        key=key,
        data={
            "image": "data:image/jpeg;base64," + base64.b64encode(encoded).decode("ascii"),
            "width": frame.shape[1],
            "height": frame.shape[0],
            "points": points,
            "selected": selected,
            "pointLabel": f"{selected + 1}. {point_label(points[selected])}",
            "context": context,
            "diagnostics": diagnostics or [],
            "view": st.session_state.get(key + "_view"),
        },
        on_clicked_change=on_clicked_change,
    )
