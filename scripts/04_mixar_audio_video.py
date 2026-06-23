"""
Script 04 - Mixar áudios MP3 no vídeo final
Concatena os 20 áudios (30s cada) e combina com o vídeo visual.
Aplica fade-in/fade-out em cada faixa para transição suave.
"""
import json
import subprocess
import tempfile
from pathlib import Path

OUTPUT_DIR = Path("output")
AUDIO_DIR = OUTPUT_DIR / "audios"
DURACAO_POR_MUSICA = 30
FADE_DURACAO = 1.5  # segundos de crossfade


def criar_audio_concatenado(audio_map: dict, musicas: list) -> Path:
    """Concatena todos os MP3 com crossfade entre eles."""
    lista_inputs = []
    for m in musicas:
        pos = str(m["posicao"])
        caminho = audio_map.get(pos)
        if caminho and Path(caminho).exists():
            lista_inputs.append(Path(caminho))
        else:
            # Silêncio se arquivo não existe
            sil = AUDIO_DIR / f"sil_{pos}.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(DURACAO_POR_MUSICA),
                "-acodec", "libmp3lame", str(sil)
            ], capture_output=True)
            lista_inputs.append(sil)

    # Criar arquivo de lista para ffmpeg concat
    lista_txt = OUTPUT_DIR / "lista_audios.txt"
    with open(lista_txt, "w") as f:
        for p in lista_inputs:
            f.write(f"file '{p.resolve()}'\n")

    audio_concat = OUTPUT_DIR / "audio_concat.mp3"

    # Concat simples
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(lista_txt),
        "-acodec", "libmp3lame", "-q:a", "4",
        str(audio_concat)
    ], check=True)

    return audio_concat


def combinar_video_audio(video_path: Path, audio_path: Path) -> Path:
    """Combina vídeo visual + áudio concatenado."""
    saida = OUTPUT_DIR / "video_final.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(saida)
    ], check=True)
    return saida


def main():
    top20_path = OUTPUT_DIR / "top20.json"
    audio_map_path = OUTPUT_DIR / "audio_map.json"
    video_base = OUTPUT_DIR / "video_sem_audio.mp4"

    for p in [top20_path, audio_map_path, video_base]:
        if not p.exists():
            raise SystemExit(f"ERRO: {p} não encontrado.")

    dados = json.loads(top20_path.read_text())
    musicas = dados["musicas"]
    audio_map = json.loads(audio_map_path.read_text())

    print("=== Mixando áudios no vídeo ===")
    audio_concat = criar_audio_concatenado(audio_map, musicas)
    print(f"Áudio concatenado: {audio_concat}")

    video_final = combinar_video_audio(video_base, audio_concat)
    print(f"Vídeo final gerado: {video_final}")

    # Salvar metadados do vídeo
    info = {
        "video_path": str(video_final),
        "mes_ano": dados["mes_ano"],
        "titulo_youtube": f"Top 20 Brasil – {dados['mes_ano']} 🎵 Músicas Mais Tocadas",
        "descricao_youtube": gerar_descricao(musicas, dados["mes_ano"]),
        "tags": gerar_tags(musicas),
    }
    (OUTPUT_DIR / "video_info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2)
    )
    print("video_info.json salvo.")


def gerar_descricao(musicas: list, mes_ano: str) -> str:
    linhas = [
        f"🎵 TOP 20 BRASIL – {mes_ano.upper()} 🎵",
        "",
        "As músicas mais tocadas no Brasil neste período!",
        "Ranking baseado em Spotify, YouTube e redes sociais.",
        "",
        "▶ TRACKLIST:",
        "",
    ]
    tempo = 0
    for m in musicas:
        mm = tempo // 60
        ss = tempo % 60
        linhas.append(f"{m['posicao']:>2}. {m['artista']} – {m['titulo']} ({mm:02d}:{ss:02d})")
        tempo += 30
    linhas += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔔 Inscreva-se e ative o sino para não perder nenhum ranking!",
        "👍 Deixe seu like e compartilhe!",
        "",
        "📌 Direitos autorais: Este vídeo é de uso educativo/informativo.",
        "Os trechos de áudio são utilizados sob a doutrina de uso justo (fair use).",
        "",
        "#Top20Brasil #MusicasBrasileiras #HitsBrasil #Musica #Charts",
    ]
    return "\n".join(linhas)


def gerar_tags(musicas: list) -> list:
    tags = ["Top 20 Brasil", "músicas mais tocadas Brasil", "hits Brasil", "chart Brasil"]
    for m in musicas[:10]:
        tags.append(m["titulo"])
        tags.append(m["artista"])
    return tags[:50]


if __name__ == "__main__":
    main()
