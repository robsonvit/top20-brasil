"""
Script 02 - Baixar áudios MP3 das músicas do Top 20
Usa yt-dlp (como biblioteca) para buscar no SoundCloud e baixar somente o áudio.
Limita a 60 segundos por faixa (para evitar copyright no vídeo final).
"""
import json
import subprocess
import time
from pathlib import Path
import yt_dlp

OUTPUT_DIR = Path("output")
AUDIO_DIR = OUTPUT_DIR / "audios"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

DURACAO_POR_MUSICA = 30   # 30s × 20 = 10 min de vídeo

def buscar_e_baixar(artista: str, titulo: str, posicao: int) -> Path | None:
    query = f"scsearch1:{artista} {titulo}"
    nome_arquivo = f"{posicao:02d}_{artista}_{titulo}"
    # Sanitizar nome de arquivo
    nome_arquivo = "".join(c if c.isalnum() or c in " _-" else "_" for c in nome_arquivo)
    nome_arquivo = nome_arquivo[:80]
    destino = AUDIO_DIR / f"{nome_arquivo}.mp3"

    if destino.exists():
        print(f"  [{posicao:02d}] Já existe: {destino.name}")
        return destino

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(AUDIO_DIR / f"{nome_arquivo}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        print(f"  [{posicao:02d}] Buscando via SoundCloud...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
            
        if destino.exists():
            # Cortar para DURACAO_POR_MUSICA segundos usando FFmpeg
            mp3_cortado = AUDIO_DIR / f"{nome_arquivo}_cut.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(destino),
                "-t", str(DURACAO_POR_MUSICA),
                "-acodec", "libmp3lame", "-q:a", "5",
                str(mp3_cortado)
            ], check=True, capture_output=True)
            destino.unlink()
            mp3_cortado.rename(destino)
            print(f"  [{posicao:02d}] OK {titulo} ({DURACAO_POR_MUSICA}s)")
            return destino
        else:
            print(f"  [{posicao:02d}] ERRO: Arquivo não gerado pelo yt-dlp.")
            return None
    except Exception as e:
        print(f"  [{posicao:02d}] ERRO ao baixar '{titulo}': {e}")
        return None


def gerar_silencio(posicao: int, duracao: int) -> Path:
    """Gera arquivo de silêncio como fallback quando download falha."""
    dest = AUDIO_DIR / f"{posicao:02d}_silencio.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
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
        time.sleep(2)

    mapa = {str(m["posicao"]): arquivos[i] for i, m in enumerate(musicas)}
    audio_map_path = OUTPUT_DIR / "audio_map.json"
    audio_map_path.write_text(json.dumps(mapa, ensure_ascii=False, indent=2))
    print(f"\nMapa de áudios salvo em {audio_map_path}")
    print(f"Total baixado: {len(arquivos)} arquivos")


if __name__ == "__main__":
    main()
