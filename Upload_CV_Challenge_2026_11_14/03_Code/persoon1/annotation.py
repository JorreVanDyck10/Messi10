"""Lokale bounding-boxeditor voor labelcorrecties met afzonderlijke voorstellen en reviewstatus."""

import json
import math
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote

from .core import dataset_path, load_manifest, now, read_labels, write_json


HTML = r'''<!doctype html><html lang="nl"><meta charset="utf-8">
<title>Persoon 1 · Annotatie en review</title>
<style>body{font:16px system-ui;background:#111827;color:#f9fafb;margin:24px}button,input,select{font:inherit;padding:8px;margin:4px}canvas{width:100%;max-width:none;height:auto;display:block;cursor:crosshair}#viewport{overflow:auto;max-height:75vh;border:1px solid #6b7280}aside{padding:12px;background:#1f2937}#message{white-space:pre-wrap}label{display:inline-block}button{cursor:pointer}h1{font-size:24px}</style>
<h1>Annoteren en onafhankelijk reviewen</h1>
<p>Automatische voorstellen zijn startpunten. Controleer ook objecten zonder voorstel. Teken een box door te slepen; klik op een box om hem te selecteren.</p>
<aside><button id="prev">Vorige</button><select id="frames"></select><button id="next">Volgende</button>
<select id="classes"></select><button id="remove">Verwijder geselecteerde box</button><button id="proposals">Laad automatische voorstellen</button><button id="clear">Wis alle boxen</button><br>
<label>Annotator <input id="author" placeholder="Eigen naam"></label>
<label>Reviewer <input id="reviewer" placeholder="Naam andere persoon"></label><br>
<label><input id="negative" type="checkbox"> Alle klassen gecontroleerd: werkelijk negatief frame</label>
<button id="save">Bewaar annotatie</button><button id="approve">Keur bewaarde annotatie goed</button><br>
<label>Zoom voor kleine objecten <input id="zoom" type="range" min="100" max="800" step="25" value="100"></label><output id="zoomValue">100%</output></aside>
<p id="status"></p><div id="viewport"><canvas id="canvas"></canvas></div><p id="message" role="status"></p>
<script>
const TOKEN='__TOKEN__';let state,frame,boxes=[],selected=-1,start=null,dirty=false;
const el=id=>document.getElementById(id),canvas=el('canvas'),ctx=canvas.getContext('2d'),image=new Image();
async function api(path,body){const r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':TOKEN},body:JSON.stringify(body)}:{});const j=await r.json();if(!r.ok)throw Error(j.error||r.status);return j;}
function message(t){el('message').textContent=t;}
function draw(){ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0);boxes.forEach((b,i)=>{const [c,x,y,w,h]=b;ctx.strokeStyle=i===selected?'#fbbf24':'#22c55e';ctx.lineWidth=3;ctx.strokeRect((x-w/2)*canvas.width,(y-h/2)*canvas.height,w*canvas.width,h*canvas.height);ctx.fillStyle=ctx.strokeStyle;ctx.font='18px sans-serif';ctx.fillText(`${i+1} ${state.names[c]}`,(x-w/2)*canvas.width,Math.max(20,(y-h/2)*canvas.height));});}
async function load(){frame=state.frames[Number(el('frames').value)];boxes=frame.boxes.map(b=>[...b]);selected=-1;dirty=false;el('negative').checked=frame.label_status==='negative';el('author').value=frame.annotator||'';el('status').textContent=`${frame.frame_id} · ${frame.split} · ${frame.review_status} · ${frame.width}×${frame.height}`;image.onload=()=>{canvas.width=image.width;canvas.height=image.height;draw();};image.src='/image/'+encodeURIComponent(frame.frame_id);}
function point(e){const r=canvas.getBoundingClientRect();return [Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))];}
canvas.onpointerdown=e=>{canvas.setPointerCapture(e.pointerId);start=point(e);};
canvas.onpointerup=e=>{if(!start)return;const end=point(e),w=Math.abs(end[0]-start[0]),h=Math.abs(end[1]-start[1]);if(w*canvas.width>2&&h*canvas.height>2){boxes.push([Number(el('classes').value),(end[0]+start[0])/2,(end[1]+start[1])/2,w,h]);selected=boxes.length-1;dirty=true;el('negative').checked=false;}else{selected=boxes.findLastIndex(b=>Math.abs(end[0]-b[1])<=b[3]/2&&Math.abs(end[1]-b[2])<=b[4]/2);}start=null;draw();};
el('remove').onclick=()=>{if(selected>=0){boxes.splice(selected,1);selected=-1;dirty=true;draw();}};
el('classes').onchange=()=>{if(selected>=0){boxes[selected][0]=Number(el('classes').value);dirty=true;draw();}};
el('zoom').oninput=()=>{canvas.style.width=el('zoom').value+'%';el('zoomValue').textContent=el('zoom').value+'%';};
el('negative').onchange=()=>{dirty=true;};
el('clear').onclick=()=>{if(confirm('Alle boxen wissen?')){boxes=[];selected=-1;dirty=true;draw();}};
el('proposals').onclick=()=>{if(dirty&&!confirm('Onbewaarde aanpassingen vervangen?'))return;boxes=frame.proposals.map(b=>[...b]);selected=-1;dirty=true;el('negative').checked=false;draw();message('Voorstellen geladen; nog niet bewaard of gereviewd.');};
async function save(action){try{if(action==='approve'&&dirty)throw Error('Bewaar wijzigingen eerst; review is een afzonderlijke handeling.');const j=await api('/api/save',{frame_id:frame.frame_id,action,boxes,negative:el('negative').checked,annotator:el('author').value.trim(),reviewer:el('reviewer').value.trim()});message(j.message);await init(Number(el('frames').value));}catch(e){message(e.message);}}
el('save').onclick=()=>save('save');el('approve').onclick=()=>save('approve');
function move(delta){if(dirty&&!confirm('Onbewaarde aanpassingen weggooien?'))return;el('frames').value=Math.max(0,Math.min(state.frames.length-1,Number(el('frames').value)+delta));load();}
el('prev').onclick=()=>move(-1);el('next').onclick=()=>move(1);el('frames').onchange=()=>{if(dirty&&!confirm('Onbewaarde aanpassingen weggooien?')){el('frames').value=state.frames.indexOf(frame);return;}load();};
async function init(index=0){state=await api('/api/state');el('frames').replaceChildren();state.frames.forEach((f,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1}/${state.frames.length} ${f.frame_id}`;el('frames').append(o);});el('classes').replaceChildren();state.names.forEach((n,i)=>{const o=document.createElement('option');o.value=i;o.textContent=n;el('classes').append(o);});if(!state.frames.length){message('Geen frames in deze subset.');return;}el('frames').value=index;await load();}
window.onbeforeunload=e=>{if(dirty){e.preventDefault();e.returnValue='';}};init().catch(e=>message(e.message));
</script></html>'''


def save_annotation(manifest, payload):
    """Approval records human assertions; this is not identity authentication."""
    data, root = load_manifest(manifest)
    frame = next((f for f in data["frames"] if f["frame_id"] == payload.get("frame_id")), None)
    if frame is None:
        raise ValueError("Unknown frame")
    label_path = dataset_path(root, frame["label"])
    action = payload.get("action")
    before = dict(frame)
    old_labels = label_path.read_text(encoding="utf-8") if label_path.exists() else None
    if action == "approve":
        reviewer = payload.get("reviewer", "").strip()
        author = frame.get("annotator", "").strip()
        if not author or not reviewer or reviewer.casefold() == author.casefold():
            raise ValueError("Independent review needs a different actual team member")
        labels = read_labels(label_path, len(data["names"]))
        if (not labels and frame.get("label_status") != "negative") or (labels and frame.get("label_status") != "positive"):
            raise ValueError("Annotation status does not match saved labels")
        frame.update(reviewer=reviewer, review_status="approved", reviewed_at=now())
    elif action == "save":
        author = payload.get("annotator", "").strip()
        if not author:
            raise ValueError("Enter the actual annotator name")
        boxes = payload.get("boxes")
        if not isinstance(boxes, list) or len(boxes) > 1000:
            raise ValueError("Invalid box list")
        if not boxes and payload.get("negative") is not True:
            raise ValueError("Confirm a genuine negative frame or leave it unlabelled")
        lines = []
        for box in boxes:
            if not isinstance(box, list) or len(box) != 5:
                raise ValueError("Each box requires class xc yc w h")
            cls, x, y, w, h = box
            if type(cls) is not int or not 0 <= cls < len(data["names"]) or not all(type(v) in (int, float) and math.isfinite(v) for v in (x, y, w, h)):
                raise ValueError("Invalid class or numeric coordinates")
            if not (0 < w <= 1 and 0 < h <= 1 and x - w / 2 >= -1e-6 and y - h / 2 >= -1e-6 and x + w / 2 <= 1 + 1e-6 and y + h / 2 <= 1 + 1e-6):
                raise ValueError("Box lies outside image or has no area")
            lines.append(f"{cls} {x:.8f} {y:.8f} {w:.8f} {h:.8f}")
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        frame.update(annotator=author, reviewer="", review_status="open",
                     label_status="positive" if boxes else "negative", annotated_at=now())
        frame.pop("reviewed_at", None)
    else:
        raise ValueError("Unknown annotation action")
    history = root / "review-history.jsonl"
    with history.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"recorded_at": now(), "action": action, "before": before,
                                 "previous_labels": old_labels, "after": frame}, ensure_ascii=False) + "\n")
    write_json(manifest, data)
    return frame


def serve(manifest, proposals, split, port):
    """Start de bounding-boxeditor uitsluitend op localhost en houd automatische voorstellen en
    opgeslagen reviewbeslissingen gescheiden.
    """
    manifest = Path(manifest).resolve()
    proposals = Path(proposals).resolve() if proposals else None
    token = secrets.token_urlsafe(24)
    html = HTML.replace("__TOKEN__", token).encode()

    class Handler(BaseHTTPRequestHandler):
        def respond(self, body, content="application/json", status=200):
            """Serialiseer de response, schrijf HTTP-status en contentheaders en stuur de inhoud naar de
            lokale browserclient.
            """
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            """Lever de editorpagina, geselecteerde framemetadata of bronbeelden voor de toegestane
            lokale GET-routes.
            """
            try:
                data, root = load_manifest(manifest)
                selected = [f for f in data["frames"] if split == "all" or f["split"] == split]
                if self.path == "/":
                    return self.respond(html, "text/html; charset=utf-8")
                if self.path == "/api/state":
                    records = []
                    for frame in selected:
                        label = dataset_path(root, frame["label"])
                        suggestion = proposals / f"{frame['frame_id']}.txt" if proposals else None
                        boxes = read_labels(label, len(data["names"])) if label.is_file() else []
                        suggested = read_labels(suggestion, len(data["names"])) if suggestion and suggestion.is_file() else []
                        records.append({**frame, "boxes": [[b["class_id"], *b["xywh"]] for b in boxes],
                                        "proposals": [[b["class_id"], *b["xywh"]] for b in suggested]})
                    return self.respond({"names": data["names"], "frames": records})
                if self.path.startswith("/image/"):
                    fid = unquote(self.path[len("/image/"):])
                    frame = next(f for f in selected if f["frame_id"] == fid)
                    path = dataset_path(root, frame["image"])
                    import mimetypes
                    return self.respond(path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")
                self.respond({"error": "Not found"}, status=404)
            except (ValueError, OSError, KeyError, StopIteration) as exc:
                self.respond({"error": str(exc)}, status=400)

        def do_POST(self):
            """Controleer route en reviewtoken, lees de ingediende annotatie en sla alleen een geldige
            labelcorrectie op.
            """
            try:
                if self.path != "/api/save" or self.headers.get("X-Review-Token") != token:
                    return self.respond({"error": "Invalid request"}, status=403)
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1_000_000:
                    raise ValueError("Invalid request size")
                payload = json.loads(self.rfile.read(length))
                data, _ = load_manifest(manifest)
                if not any(f["frame_id"] == payload.get("frame_id") and (split == "all" or f["split"] == split) for f in data["frames"]):
                    raise ValueError("Frame outside active subset")
                save_annotation(manifest, payload)
                self.respond({"message": "Bewaard. Een gewijzigde annotatie moet opnieuw onafhankelijk worden gereviewd."})
            except (ValueError, OSError, KeyError) as exc:
                self.respond({"error": str(exc)}, status=400)

    print(f"Annotation and review: http://127.0.0.1:{port} (subset: {split})", flush=True)
    print("Names record actual human work; this tool cannot substitute for the second team member.", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
