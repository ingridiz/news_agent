"""Cliente para a API do Zernio (publicação em redes sociais).

Docs:  https://docs.zernio.com
Base:  https://zernio.com/api
Auth:  header  Authorization: Bearer sk_...

NOTA sobre nomes de campos: os SDKs oficiais do Zernio divergem em alguns
nomes (ex.: ``content`` vs ``caption``, ``scheduledFor`` vs ``scheduleDate``).
Por isso os nomes ficam centralizados nas constantes ``FIELDS`` abaixo — basta
ajustar aqui depois da primeira chamada real (use ``create_post(..., dry_run=True)``
para inspecionar o payload exato antes de publicar).
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path

import requests

BASE_URL = os.environ.get("ZERNIO_BASE_URL", "https://zernio.com/api")

# Nomes de campos do payload — ajuste aqui se a API real divergir.
FIELDS = {
    "caption": "content",        # texto do post
    "media": "mediaUrls",        # lista de URLs públicas de mídia
    "schedule": "scheduledFor",  # ISO 8601 para agendamento
    "publish_now": "publishNow",
}


class ZernioError(RuntimeError):
    """Erro retornado pela API do Zernio ou de configuração do cliente."""


class ZernioClient:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL, timeout: int = 60):
        self.api_key = api_key or os.environ.get("ZERNIO_API_KEY")
        if not self.api_key:
            raise ZernioError(
                "ZERNIO_API_KEY não configurada. Defina no .env ou como variável de ambiente."
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        )

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if resp.status_code >= 400:
            raise ZernioError(f"{method} {path} -> HTTP {resp.status_code}: {resp.text[:500]}")
        if not resp.text:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text

    # --- Contas -----------------------------------------------------------
    def list_accounts(self):
        """Lista as contas sociais conectadas (GET /v1/accounts)."""
        return self._request("GET", "/v1/accounts")

    def find_instagram_account(self, username: str | None = None):
        """Devolve a primeira conta de Instagram conectada (ou a do ``username``)."""
        data = self.list_accounts()
        accounts = data.get("accounts", data) if isinstance(data, dict) else data
        for acc in accounts or []:
            if str(acc.get("platform", "")).lower() != "instagram":
                continue
            if username and acc.get("username") != username:
                continue
            return acc
        return None

    @staticmethod
    def account_id(acc: dict) -> str | None:
        """Extrai o identificador da conta (o Zernio usa ``_id``)."""
        return acc.get("_id") or acc.get("accountId") or acc.get("id")

    # --- Mídia ------------------------------------------------------------
    def upload_media(self, file_path: str | Path) -> str:
        """Upload em 2 passos (presign -> PUT) e devolve a ``publicUrl``."""
        path = Path(file_path)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        presign = self._request(
            "POST", "/v1/media/presign",
            json={"filename": path.name, "contentType": content_type},
        )
        upload_url = presign.get("uploadUrl") or presign.get("url")
        public_url = presign.get("publicUrl") or presign.get("publicURL")
        if not upload_url or not public_url:
            raise ZernioError(f"Resposta de presign inesperada: {presign}")
        with open(path, "rb") as fh:
            put = requests.put(
                upload_url, data=fh,
                headers={"Content-Type": content_type}, timeout=self.timeout,
            )
        if put.status_code >= 400:
            raise ZernioError(f"Upload PUT falhou: HTTP {put.status_code}: {put.text[:300]}")
        return public_url

    # --- Posts ------------------------------------------------------------
    def create_post(
        self,
        *,
        account_id: str,
        caption: str,
        media_urls: list[str],
        ig_type: str = "feed",          # feed | carousel | reel | story
        publish_now: bool = False,
        scheduled_for: str | None = None,  # ISO 8601 (ex.: 2026-06-16T09:00:00)
        timezone: str | None = None,       # ex.: America/Sao_Paulo
        cover_image_url: str | None = None,
        dry_run: bool = False,
    ):
        platform_entry = {"platform": "instagram", "accountId": account_id}
        platform_data: dict = {}
        if ig_type and ig_type != "feed":
            platform_data["type"] = ig_type
        if cover_image_url:
            platform_data["coverImageUrl"] = cover_image_url
        if platform_data:
            platform_entry["platformSpecificData"] = platform_data

        payload = {
            FIELDS["caption"]: caption,
            "platforms": [platform_entry],
            FIELDS["media"]: media_urls,
        }
        if publish_now:
            payload[FIELDS["publish_now"]] = True
        elif scheduled_for:
            payload[FIELDS["schedule"]] = scheduled_for
            if timezone:
                payload["timezone"] = timezone
        # (omitir publishNow e scheduledFor cria um rascunho nativo no Zernio)

        if dry_run:
            return {"dry_run": True, "endpoint": "POST /v1/posts", "payload": payload}
        return self._request("POST", "/v1/posts", json=payload)
