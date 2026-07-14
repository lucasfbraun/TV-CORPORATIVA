"""
Rotas de gestão das integrações com login (ex.: Grafana).
"""
import os
import uuid

from flask import Blueprint, request, jsonify

from security import login_required
from grafana import (
    load_integrations, save_integrations, public_integration,
    start_worker, stop_worker, GRAFANA_AUTH_FILE,
)

bp = Blueprint("integrations", __name__)


@bp.route("/api/integrations", methods=["GET"])
@login_required
def list_integrations():
    d = load_integrations()
    return jsonify([public_integration(i, c) for i, c in d.items()])


@bp.route("/api/integrations", methods=["POST"])
@login_required
def create_integration():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    if not name or not url.startswith(("http://", "https://")):
        return jsonify({"error": "Nome e URL (http/https) são obrigatórios"}), 400
    iid = "intg-" + uuid.uuid4().hex[:8]
    d = load_integrations()
    d[iid] = {
        "type": data.get("type", "grafana"), "name": name, "url": url,
        "username": data.get("username", ""), "password": data.get("password", ""),
        "interval": int(data.get("interval") or 20), "active": True,
    }
    save_integrations(d)
    start_worker(iid)
    return jsonify(public_integration(iid, d[iid])), 201


@bp.route("/api/integrations/<iid>", methods=["PUT"])
@login_required
def update_integration(iid):
    d = load_integrations()
    c = d.get(iid)
    if not c:
        return jsonify({"error": "Integração não encontrada"}), 404
    data = request.get_json(silent=True) or {}
    keys = ("name", "username", "active", "type") if iid == "grafana" else ("name", "url", "username", "active", "type")
    for k in keys:
        if k in data:
            c[k] = data[k]
    if "interval" in data:
        c["interval"] = int(data.get("interval") or 20)
    if data.get("password"):  # só troca a senha se uma nova for enviada
        c["password"] = data["password"]
    save_integrations(d)
    if iid == "grafana":  # credenciais podem ter mudado → descarta a sessão salva
        try:
            os.remove(GRAFANA_AUTH_FILE)
        except OSError:
            pass
    start_worker(iid) if c.get("active", True) else stop_worker(iid)
    return jsonify(public_integration(iid, c))


@bp.route("/api/integrations/<iid>", methods=["DELETE"])
@login_required
def delete_integration(iid):
    d = load_integrations()
    if iid not in d:
        return jsonify({"error": "Integração não encontrada"}), 404
    del d[iid]
    save_integrations(d)
    stop_worker(iid)
    return jsonify({"status": "removed"})
