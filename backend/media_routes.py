"""
Upload, biblioteca de mídia (com pastas) e serviço dos arquivos /uploads.
"""
import io
import os
import uuid

from flask import Blueprint, request, jsonify, send_from_directory, send_file, abort
from werkzeug.utils import secure_filename

import db
from config import UPLOADS_DIR, ALLOWED_EXTENSIONS
from storage import load_content, save_content, guess_mime
from security import login_required

bp = Blueprint("media", __name__)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_rel_path(rel):
    """Sanitiza um caminho relativo dentro de uploads/ (impede '..' e traversal)."""
    rel = (rel or "").replace("\\", "/").strip().strip("/")
    parts = []
    for seg in rel.split("/"):
        seg = secure_filename(seg)
        if seg and seg not in (".", ".."):
            parts.append(seg)
    return "/".join(parts)


def _media_count_under(all_media, prefix):
    return sum(1 for m in all_media if m["path"].startswith(prefix))


def _file_kind(name):
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext in {"mp4", "webm", "ogg", "mov", "avi"}:
        return "video"
    if ext == "pdf":
        return "pdf"
    return "image"


@bp.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido"}), 400

    safe_dir = safe_rel_path(request.form.get("path", ""))
    safe_name = secure_filename(file.filename)
    unique = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    rel_url = (safe_dir + "/" + unique).strip("/")
    db.media_put(rel_url, file.read(), guess_mime(unique))
    return jsonify({"status": "ok", "url": f"/uploads/{rel_url}", "filename": unique, "path": safe_dir}), 201


@bp.route("/api/uploads", methods=["GET"])
@bp.route("/api/library", methods=["GET"])
@login_required
def list_library():
    safe = safe_rel_path(request.args.get("path", ""))
    prefix = (safe + "/") if safe else ""
    all_media = db.media_list()
    all_folders = db.folders_all()

    folder_names = set()
    files = []
    for m in all_media:
        p = m["path"]
        if not p.startswith(prefix):
            continue
        rest = p[len(prefix):]
        if "/" in rest:
            folder_names.add(rest.split("/", 1)[0])  # subpasta implícita
        else:
            size_bytes = m.get("size") or 0
            files.append({
                "filename": rest,
                "path": p,
                "url": f"/uploads/{p}",
                "type": _file_kind(rest),
                "size": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
            })
    for fp in all_folders:                      # pastas explícitas (inclusive vazias)
        if prefix and not fp.startswith(prefix):
            continue
        rest = fp[len(prefix):]
        if rest and "/" not in rest:
            folder_names.add(rest)

    folders = []
    for name in sorted(folder_names, key=str.lower):
        child_prefix = prefix + name + "/"
        folders.append({"name": name, "path": (prefix + name).strip("/"),
                        "count": _media_count_under(all_media, child_prefix)})
    files.sort(key=lambda f: f["filename"].lower())
    return jsonify({"path": safe, "folders": folders, "files": files})


@bp.route("/api/library/folder", methods=["POST"])
@login_required
def create_folder():
    data = request.get_json(silent=True) or {}
    name = secure_filename((data.get("name") or "").strip())
    if not name:
        return jsonify({"error": "Nome de pasta inválido"}), 400
    rel = (safe_rel_path(data.get("path", "")) + "/" + name).strip("/")
    if rel in set(db.folders_all()) or any(m["path"].startswith(rel + "/") for m in db.media_list()):
        return jsonify({"error": "Já existe uma pasta com esse nome"}), 409
    db.folder_add(rel)
    return jsonify({"status": "ok", "path": rel}), 201


@bp.route("/api/library/folder", methods=["DELETE"])
@login_required
def delete_folder():
    safe = safe_rel_path(request.args.get("path", ""))
    folders = set(db.folders_all())
    media = db.media_list()
    exists = (safe in folders
              or any(f.startswith(safe + "/") for f in folders)
              or any(m["path"].startswith(safe + "/") for m in media))
    if not safe or not exists:
        return jsonify({"error": "Pasta não encontrada"}), 404
    db.media_delete_prefix(safe + "/")
    db.folder_delete_prefix(safe + "/")
    db.folder_delete(safe)
    return jsonify({"status": "removed"})


@bp.route("/api/library/<path:filename>", methods=["DELETE"])
@login_required
def delete_library(filename):
    safe = safe_rel_path(filename)
    if not safe or not db.media_exists(safe):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    db.media_delete(safe)
    return jsonify({"status": "removed"})


def _replace_url_everywhere(obj, old, new):
    """Atualiza recursivamente qualquer URL antiga para a nova no conteúdo."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v == old:
                obj[k] = new
            else:
                _replace_url_everywhere(v, old, new)
    elif isinstance(obj, list):
        for item in obj:
            _replace_url_everywhere(item, old, new)


@bp.route("/api/library/move", methods=["POST"])
@login_required
def move_file():
    data = request.get_json(silent=True) or {}
    src_rel = safe_rel_path(data.get("from", ""))
    if not src_rel or not db.media_exists(src_rel):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    dst_rel = safe_rel_path(data.get("to", ""))

    name = src_rel.split("/")[-1]
    new_rel = (dst_rel + "/" + name).strip("/")
    if new_rel != src_rel and db.media_exists(new_rel):  # não sobrescreve: nome único
        base, dot, ext = name.rpartition(".")
        name = f"{base}_{uuid.uuid4().hex[:4]}.{ext}" if dot else f"{name}_{uuid.uuid4().hex[:4]}"
        new_rel = (dst_rel + "/" + name).strip("/")

    db.media_move(src_rel, new_rel)

    # Mantém os slides apontando para o novo local
    content = load_content()
    _replace_url_everywhere(content, f"/uploads/{src_rel}", f"/uploads/{new_rel}")
    save_content(content)

    return jsonify({"status": "ok", "url": f"/uploads/{new_rel}", "path": new_rel})


@bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    safe = safe_rel_path(filename)
    # Capturas do Grafana continuam em disco (transitórias, regeneradas a cada poucos segundos)
    if filename.startswith("captures/") or safe.startswith("captures/"):
        return send_from_directory(UPLOADS_DIR, safe)
    rec = db.media_get(safe)
    if rec is None:
        # compatibilidade: arquivo ainda em disco (ex.: antes da migração)
        if os.path.isfile(os.path.join(UPLOADS_DIR, safe)):
            return send_from_directory(UPLOADS_DIR, safe)
        abort(404)
    data, mime = rec
    # Usa send_file (em vez de um Response simples) para responder corretamente a
    # requisições HTTP Range (206 Partial Content). O <video> do navegador depende
    # disso para carregar/buscar o arquivo em pedaços; sem Range, o servidor sempre
    # devolve o arquivo inteiro do início, e o vídeo trava ou nem chega a iniciar em
    # boa parte dos navegadores/TVs — regressão introduzida ao migrar a mídia para o
    # Postgres (antes disso, send_from_directory servia do disco com suporte a Range
    # nativo do Flask).
    return send_file(
        io.BytesIO(data),
        mimetype=mime or "application/octet-stream",
        conditional=True,
        etag=False,
        max_age=300,
        download_name=os.path.basename(safe) or "arquivo",
    )
