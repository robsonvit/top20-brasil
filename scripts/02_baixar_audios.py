"""
Script 02 - Baixar áudios MP3 das músicas do Top 20
Usa yt-dlp para buscar no YouTube e baixar somente o áudio.
Limita a 60 segundos por faixa (para evitar copyright no vídeo final).
"""
import json
import subprocess
import time
from pathlib import Path

OUTPUT_DIR = Path("output")
AUDIO_DIR = OUTPUT_DIR / "audios"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Segundos de cada música no vídeo final
DURACAO_POR_MUSICA = 30   # 30s × 20 = 10 min de vídeo (bom para YouTube)
MAX_DURACAO_DOWNLOAD = 300  # baixa até 5 min para ter margem


def buscar_e_baixar(artista: str, titulo: str, posicao: int) -> Path | None:
    query = f"{artista} {titulo} official audio"
    nome_arquivo = f"{posicao:02d}_{artista}_{titulo}"
    # Sanitizar nome de arquivo
    nome_arquivo = "".join(c if c.isalnum() or c in " _-" else "_" for c in nome_arquivo)
    nome_arquivo = nome_arquivo[:80]
    destino = AUDIO_DIR / f"{nome_arquivo}.mp3"

    if destino.exists():
        print(f"  [{posicao:02d}] Já existe: {destino.name}")
        return destino

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",          # 128kbps aprox
        "--match-filter", f"duration <= {MAX_DURACAO_DOWNLOAD}",
        "--no-playlist",
        "--max-downloads", "1",
        "--output", str(AUDIO_DIR / f"{nome_arquivo}.%(ext)s"),
        "--quiet",
        "--no-warnings",
        f"ytsearch1:{query}",
    ]

    try:
        # yt-dlp returns 101 when using --max-downloads 1, so we don't use check=True
        result = subprocess.run(cmd, timeout=120)
        # yt-dlp pode gerar .mp3 diretamente ou .webm -> converter
        mp3 = destino
        if mp3.exists():
            # Cortar para DURACAO_POR_MUSICA segundos
            mp3_cortado = AUDIO_DIR / f"{nome_arquivo}_cut.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(mp3),
                "-t", str(DURACAO_POR_MUSICA),
                "-acodec", "libmp3lame", "-q:a", "5",
                str(mp3_cortado)
            ], check=True, capture_output=True)
            mp3.unlink()
            mp3_cortado.rename(mp3)
            print(f"  [{posicao:02d}] OK {titulo} ({DURACAO_POR_MUSICA}s)")
            return mp3
        else:
            print(f"  [{posicao:02d}] ERRO: Arquivo não gerado para: {titulo}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"  [{posicao:02d}] ERRO ao baixar '{titulo}': {e}")
        return None
    except subprocess.TimeoutExpired:
        print(f"  [{posicao:02d}] TIMEOUT: {titulo}")
        return None


def gerar_silencio(posicao: int, duracao: int) -> Path:
    """Gera arquivo de silêncio como fallback quando download falha."""
    dest = AUDIO_DIR / f"{posicao:02d}_silencio.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duracao),
        "-acodec", "libmp3lame", str(dest)
    ], capture_output=True)
    return dest


def main():
    top20_path = OUTPUT_DIR / "top20.json"
    if not top20_path.exists():
        print("ERRO: top20.json não encontrado. Rode o script 01 primeiro.")
        raise SystemExit(1)

    dados = json.loads(top20_path.read_text())
    musicas = dados["musicas"]

    print(f"=== Baixando áudios ({len(musicas)} músicas) ===")
    arquivos = []

    for m in musicas:
        pos = m["posicao"]
        artista = m["artista"]
        titulo = m["titulo"]
        caminho = buscar_e_baixar(artista, titulo, pos)
        if caminho is None:
            print(f"  [{pos:02d}] Usando silêncio como fallback")
            caminho = gerar_silencio(pos, DURACAO_POR_MUSICA)
        arquivos.append(str(caminho))
        time.sleep(3)  # pausa entre downloads

    # Salvar lista de arquivos de áudio
    mapa = {str(m["posicao"]): arquivos[i] for i, m in enumerate(musicas)}
    audio_map_path = OUTPUT_DIR / "audio_map.json"
    audio_map_path.write_text(json.dumps(mapa, ensure_ascii=False, indent=2))
    print(f"\nMapa de áudios salvo em {audio_map_path}")
    print(f"Total baixado: {len(arquivos)} arquivos")


if __name__ == "__main__":
    main()
