"""
Script 05 - Postar vídeo no YouTube via Data API v3
Usa OAuth2 com refresh_token armazenado nos Secrets do GitHub.
Configura licença Creative Commons (CC BY) para evitar restrições.
"""
import json
import os
import time
import requests
from pathlib import Path

OUTPUT_DIR = Path("output")

# YouTube Data API v3
YT_TOKEN_URL = "https://oauth2.googleapis.com/token"
YT_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YT_UPDATE_URL = "https://www.googleapis.com/youtube/v3/videos"
YT_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


def obter_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    resp = requests.post(YT_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    })
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError(f"Falha ao obter access_token: {resp.text}")
    print("✓ Access token obtido.")
    return token


def fazer_upload(video_path: Path, info: dict, token: str) -> str:
    """Faz upload do vídeo usando upload resumível."""
    headers_init = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(video_path.stat().st_size),
    }

    metadata = {
        "snippet": {
            "title": info["titulo_youtube"],
            "description": info["descricao_youtube"],
            "tags": info["tags"],
            "categoryId": "10",  # Music
            "defaultLanguage": "pt",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            # Creative Commons – licença CC BY
            "license": "creativeCommon",
        },
    }

    # Iniciar upload resumível
    init_resp = requests.post(
        f"{YT_UPLOAD_URL}?uploadType=resumable&part=snippet,status",
        headers=headers_init,
        json=metadata,
    )
    init_resp.raise_for_status()
    upload_url = init_resp.headers["Location"]
    print(f"✓ URL de upload obtida.")

    # Fazer upload em chunks
    CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB
    file_size = video_path.stat().st_size
    video_id = None

    with open(video_path, "rb") as f:
        offset = 0
        while offset < file_size:
            chunk = f.read(CHUNK_SIZE)
            end = offset + len(chunk) - 1
            headers_chunk = {
                "Authorization": f"Bearer {token}",
                "Content-Range": f"bytes {offset}-{end}/{file_size}",
                "Content-Type": "video/mp4",
            }
            chunk_resp = requests.put(upload_url, headers=headers_chunk, data=chunk)

            if chunk_resp.status_code in (200, 201):
                video_id = chunk_resp.json().get("id")
                print(f"✓ Upload completo! Video ID: {video_id}")
                break
            elif chunk_resp.status_code == 308:
                # Continuar
                rng = chunk_resp.headers.get("Range", "")
                if rng:
                    offset = int(rng.split("-")[1]) + 1
                else:
                    offset += len(chunk)
                pct = int(offset * 100 / file_size)
                print(f"  Enviando... {pct}%", end="\r")
            else:
                raise Exception(f"Erro no upload: {chunk_resp.status_code} {chunk_resp.text}")

    if not video_id:
        raise Exception("Upload falhou – video_id não retornado.")

    return video_id


def adicionar_thumbnail_texto(video_id: str, token: str, mes_ano: str):
    """
    Tenta adicionar uma thumbnail via API.
    Requer canal verificado. Se falhar, apenas avisa.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        img = Image.new("RGB", (1280, 720), (8, 8, 32))
        draw = ImageDraw.Draw(img)

        try:
            fonte = ImageFont.truetype(
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 90)
            fonte_sub = ImageFont.truetype(
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 50)
        except Exception:
            fonte = ImageFont.load_default()
            fonte_sub = fonte

        # Fundo gradiente
        for y in range(720):
            cor = int(8 + (48 - 8) * y / 720)
            draw.line([(0, y), (1280, y)], fill=(cor, cor // 4, cor * 2))

        # Textos
        draw.text((640, 200), "🎵 TOP 20", font=fonte, fill=(255, 200, 0),
                  anchor="mm" if hasattr(draw, "textbbox") else None)
        draw.text((640, 350), "BRASIL", font=fonte, fill=(255, 255, 255),
                  anchor="mm" if hasattr(draw, "textbbox") else None)
        draw.text((640, 480), mes_ano, font=fonte_sub, fill=(200, 200, 255),
                  anchor="mm" if hasattr(draw, "textbbox") else None)
        draw.text((640, 580), "Músicas mais tocadas", font=fonte_sub, fill=(150, 255, 150),
                  anchor="mm" if hasattr(draw, "textbbox") else None)

        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=90)
        buf.seek(0)

        resp = requests.post(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "image/jpeg",
            },
            data=buf.read(),
        )
        if resp.status_code == 200:
            print("✓ Thumbnail configurada.")
        else:
            print(f"  Thumbnail: {resp.status_code} (canal pode precisar ser verificado)")
    except Exception as e:
        print(f"  Thumbnail pulada: {e}")


def salvar_relatorio(video_id: str, info: dict):
    rel = {
        "sucesso": True,
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "titulo": info["titulo_youtube"],
        "mes_ano": info["mes_ano"],
        "licenca": "Creative Commons (CC BY)",
    }
    (OUTPUT_DIR / "relatorio.json").write_text(
        json.dumps(rel, ensure_ascii=False, indent=2)
    )
    print(f"\n✅ Vídeo publicado: https://www.youtube.com/watch?v={video_id}")


def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        print("AVISO: Credenciais do YouTube não configuradas.")
        print("Configure os Secrets: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
        # Salvar relatório de falha sem lançar exceção (permite CI não quebrar)
        rel = {"sucesso": False, "motivo": "Credenciais não configuradas"}
        (OUTPUT_DIR / "relatorio.json").write_text(json.dumps(rel, indent=2))
        return

    info_path = OUTPUT_DIR / "video_info.json"
    if not info_path.exists():
        raise SystemExit("ERRO: video_info.json não encontrado.")

    info = json.loads(info_path.read_text())
    video_path = Path(info["video_path"])

    if not video_path.exists():
        raise SystemExit(f"ERRO: Vídeo não encontrado em {video_path}")

    print("=== Postando no YouTube ===")
    print(f"Título: {info['titulo_youtube']}")
    print(f"Arquivo: {video_path} ({video_path.stat().st_size // 1024 // 1024} MB)")

    token = obter_access_token(client_id, client_secret, refresh_token)
    video_id = fazer_upload(video_path, info, token)
    adicionar_thumbnail_texto(video_id, token, info["mes_ano"])
    salvar_relatorio(video_id, info)


if __name__ == "__main__":
    main()
