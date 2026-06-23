"""
Script 03 - Criar vídeo animado 16:9 com visual dinâmico (sem loop aparente)
Gera frames PNG com Pillow e compila com FFmpeg.
Efeitos: pulsação de texto, fundo com partículas, gradiente animado, barra de progresso.
"""
import json
import math
import random
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = Path("output")
FRAMES_DIR = OUTPUT_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Configurações de vídeo
WIDTH, HEIGHT = 1920, 1080
FPS = 24
DURACAO_POR_MUSICA = 30      # segundos por música
TOTAL_MUSICAS = 20
DURACAO_TOTAL = DURACAO_POR_MUSICA * TOTAL_MUSICAS  # 600s = 10min
TOTAL_FRAMES = FPS * DURACAO_TOTAL

# Paleta de cores
COR_FUNDO_1 = (8, 8, 32)        # azul muito escuro
COR_FUNDO_2 = (32, 8, 48)       # roxo escuro
COR_DESTAQUE = (255, 200, 0)     # amarelo dourado
COR_TITULO = (255, 255, 255)
COR_ARTISTA = (200, 200, 255)
COR_NUMERO = (255, 160, 0)
COR_BARRA = (0, 220, 160)        # verde-água

PARTICULAS_N = 80


def carregar_fontes():
    """Tenta carregar fontes do sistema, fallback para default."""
    candidatos_bold = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    candidatos_regular = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]

    def achar(lista, tamanho):
        for p in lista:
            if Path(p).exists():
                try:
                    return ImageFont.truetype(p, tamanho)
                except Exception:
                    continue
        return ImageFont.load_default()

    return {
        "titulo_grande": achar(candidatos_bold, 80),
        "titulo_medio": achar(candidatos_bold, 56),
        "numero": achar(candidatos_bold, 72),
        "musica": achar(candidatos_bold, 48),
        "artista": achar(candidatos_regular, 36),
        "pequeno": achar(candidatos_regular, 28),
    }


def gerar_particulas(seed=42):
    """Gera posição/velocidade inicial de partículas."""
    rng = random.Random(seed)
    return [
        {
            "x": rng.uniform(0, WIDTH),
            "y": rng.uniform(0, HEIGHT),
            "vx": rng.uniform(-0.3, 0.3),
            "vy": rng.uniform(-0.2, -0.5),
            "r": rng.randint(2, 6),
            "brilho": rng.randint(100, 255),
            "fase": rng.uniform(0, math.tau),
        }
        for _ in range(PARTICULAS_N)
    ]


def cor_fundo_gradiente(t_global: float) -> tuple:
    """Gradiente de fundo que muda lentamente (ciclo ~120s)."""
    ciclo = (math.sin(t_global / 120 * math.tau) + 1) / 2
    r = int(COR_FUNDO_1[0] + (COR_FUNDO_2[0] - COR_FUNDO_1[0]) * ciclo)
    g = int(COR_FUNDO_1[1] + (COR_FUNDO_2[1] - COR_FUNDO_1[1]) * ciclo)
    b = int(COR_FUNDO_1[2] + (COR_FUNDO_2[2] - COR_FUNDO_1[2]) * ciclo)
    return (r, g, b)


def desenhar_fundo_gradiente(draw: ImageDraw, cor_base: tuple):
    """Fundo com gradiente vertical suave."""
    for y in range(HEIGHT):
        fator = y / HEIGHT
        r2 = max(0, min(255, int(cor_base[0] * (1 - fator * 0.4))))
        g2 = max(0, min(255, int(cor_base[1] * (1 - fator * 0.2))))
        b2 = max(0, min(255, int(cor_base[2] + (60 * fator))))
        draw.line([(0, y), (WIDTH, y)], fill=(r2, g2, b2))


def desenhar_particulas(draw: ImageDraw, particulas: list, frame: int):
    for p in particulas:
        t = frame / FPS
        px = (p["x"] + p["vx"] * t * 60) % WIDTH
        py = (p["y"] + p["vy"] * t * 60) % HEIGHT
        brilho = int(p["brilho"] * (0.6 + 0.4 * math.sin(t * 2 + p["fase"])))
        r_circ = p["r"]
        cor = (brilho, brilho, min(255, brilho + 60))
        draw.ellipse([
            (px - r_circ, py - r_circ),
            (px + r_circ, py + r_circ)
        ], fill=cor)


def pulso(t: float, freq: float = 1.0, amplitude: float = 0.08) -> float:
    """Fator de escala pulsante entre (1-amplitude) e (1+amplitude)."""
    return 1.0 + amplitude * math.sin(t * freq * math.tau)


def alfa_piscar(t: float, freq: float = 0.5) -> int:
    """Opacidade oscilante para efeito 'breathing'."""
    return int(200 + 55 * math.sin(t * freq * math.tau))


def texto_centrado(draw, texto, fonte, cx, cy, cor, sombra=True):
    bbox = draw.textbbox((0, 0), texto, font=fonte)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = cx - w // 2
    y = cy - h // 2
    if sombra:
        draw.text((x + 3, y + 3), texto, font=fonte, fill=(0, 0, 0, 150))
    draw.text((x, y), texto, font=fonte, fill=cor)


def desenhar_barra_progresso(draw, posicao_atual: int, t_musica: float):
    """Barra de progresso da música atual."""
    bw = WIDTH - 200
    bh = 8
    bx = 100
    by = HEIGHT - 60
    # fundo
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4, fill=(50, 50, 80))
    # progresso
    frac = t_musica / DURACAO_POR_MUSICA
    draw.rounded_rectangle([bx, by, bx + int(bw * frac), by + bh], radius=4, fill=COR_BARRA)
    # texto
    draw.text((bx, by - 22), f"Faixa {posicao_atual} de {TOTAL_MUSICAS}", fill=(180, 180, 200))


def desenhar_ondas_decorativas(draw, t: float):
    """Ondas horizontais decorativas no topo e base."""
    for i in range(3):
        desl = math.sin(t * 0.7 + i * 1.2) * 20
        y_top = 20 + i * 6 + desl
        draw.line([(0, y_top), (WIDTH, y_top)], fill=(255, 200, 0, 40 + i * 20), width=2)
        y_bot = HEIGHT - 80 - i * 6 + desl
        draw.line([(0, y_bot), (WIDTH, y_bot)], fill=(0, 180, 255, 40 + i * 20), width=2)


def gerar_frame(
    frame_idx: int,
    musicas: list,
    mes_ano: str,
    particulas: list,
    fontes: dict,
) -> Image.Image:
    t_global = frame_idx / FPS
    musica_idx = int(t_global / DURACAO_POR_MUSICA) % TOTAL_MUSICAS
    t_musica = t_global - musica_idx * DURACAO_POR_MUSICA

    musica = musicas[musica_idx]
    pos = musica["posicao"]
    titulo_musica = musica["titulo"].upper()
    nome_artista = musica["artista"]

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # --- Fundo ---
    cor_base = cor_fundo_gradiente(t_global)
    desenhar_fundo_gradiente(draw, cor_base)

    # --- Partículas ---
    desenhar_particulas(draw, particulas, frame_idx)

    # --- Ondas decorativas ---
    desenhar_ondas_decorativas(draw, t_global)

    # --- Título do vídeo (topo) ---
    titulo_video = f"♪ TOP 20 BRASIL – {mes_ano.upper()} ♪"
    alpha_titulo = alfa_piscar(t_global, freq=0.3)
    cor_titulo_atual = (
        min(255, COR_DESTAQUE[0]),
        min(255, COR_DESTAQUE[1]),
        int(100 + 155 * (math.sin(t_global * 0.5) * 0.5 + 0.5)),
    )
    texto_centrado(draw, titulo_video, fontes["titulo_medio"], WIDTH // 2, 80, cor_titulo_atual)

    # --- Linha separadora superior ---
    sep_y = 130
    for xi in range(0, WIDTH, 4):
        intensidade = int(200 * abs(math.sin(xi / WIDTH * math.pi + t_global * 2)))
        draw.point((xi, sep_y), fill=(intensidade, intensidade // 2, 0))

    # --- Número da posição (grande, pulsante) ---
    fator_pulso = pulso(t_musica, freq=0.8, amplitude=0.06)
    tam_num = int(200 * fator_pulso)
    try:
        fonte_num_grande = ImageFont.truetype(
            list(fontes["numero"].path if hasattr(fontes["numero"], 'path') else [
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ])[0] if False else "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            tam_num
        )
    except Exception:
        fonte_num_grande = fontes["numero"]

    num_texto = f"#{pos}"
    bbox_num = draw.textbbox((0, 0), num_texto, font=fonte_num_grande)
    wn = bbox_num[2] - bbox_num[0]
    hn = bbox_num[3] - bbox_num[1]
    xn = WIDTH // 4 - wn // 2
    yn = HEIGHT // 2 - hn // 2 - 30

    brilho_num = alfa_piscar(t_musica, freq=1.2)
    cor_num = (min(255, COR_NUMERO[0]), min(255, int(COR_NUMERO[1] * brilho_num / 255)), 0)
    # Sombra do número
    draw.text((xn + 5, yn + 5), num_texto, font=fonte_num_grande, fill=(0, 0, 0))
    draw.text((xn, yn), num_texto, font=fonte_num_grande, fill=cor_num)

    # --- Painel central da música ---
    painel_x = WIDTH // 2 - 20
    painel_w = WIDTH // 2 + 10
    painel_cy = HEIGHT // 2

    # Retângulo de fundo semi-transparente (simulado com sobreposição escura)
    painel_rect = [painel_x, painel_cy - 180, painel_x + painel_w, painel_cy + 160]
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    alpha_painel = int(120 + 30 * math.sin(t_musica * 0.5))
    ov_draw.rounded_rectangle(painel_rect, radius=20, fill=(20, 10, 50, alpha_painel))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Nome da música
    cx_painel = painel_x + painel_w // 2
    escala_titulo = pulso(t_musica, freq=0.6, amplitude=0.03)
    # Quebra de linha se título for longo
    palavras = titulo_musica.split()
    linha1, linha2 = titulo_musica, ""
    if len(titulo_musica) > 22:
        meio = len(palavras) // 2
        linha1 = " ".join(palavras[:meio])
        linha2 = " ".join(palavras[meio:])

    cor_musica_atual = (
        255,
        int(220 + 35 * math.sin(t_musica * 1.5)),
        int(50 + 100 * abs(math.sin(t_global * 0.4))),
    )
    if linha2:
        texto_centrado(draw, linha1, fontes["titulo_medio"], cx_painel, painel_cy - 100, cor_musica_atual)
        texto_centrado(draw, linha2, fontes["titulo_medio"], cx_painel, painel_cy - 40, cor_musica_atual)
    else:
        texto_centrado(draw, linha1, fontes["titulo_grande"], cx_painel, painel_cy - 70, cor_musica_atual)

    # Separador decorativo
    sep_mx = cx_painel - 120
    sep_mw = 240
    sep_my = painel_cy + 20
    draw.line([(sep_mx, sep_my), (sep_mx + sep_mw, sep_my)], fill=COR_DESTAQUE, width=3)

    # Nome do artista
    cor_artista_atual = (
        int(180 + 75 * abs(math.sin(t_global * 0.3))),
        int(180 + 75 * abs(math.sin(t_global * 0.3 + 1))),
        255,
    )
    texto_centrado(draw, nome_artista, fontes["artista"], cx_painel, painel_cy + 70, cor_artista_atual)

    # --- Lista lateral (miniatura das outras músicas) ---
    lista_x = 40
    lista_y_inicio = 160
    linha_h = 42
    for i, m in enumerate(musicas):
        p = m["posicao"]
        is_atual = (p == pos)
        cor_item = COR_DESTAQUE if is_atual else (120, 120, 160)
        if is_atual:
            cor_item = (
                255,
                int(200 * abs(math.sin(t_musica * 2))),
                0
            )
        y_item = lista_y_inicio + i * linha_h
        label = f"{p:>2}. {m['titulo'][:18]}"
        if is_atual:
            draw.rectangle([lista_x - 5, y_item - 5, lista_x + 320, y_item + 30],
                           fill=(60, 30, 0))
        draw.text((lista_x, y_item), label,
                  font=fontes["pequeno"], fill=cor_item)

    # --- Barra de progresso ---
    bw = WIDTH - 200
    bh = 10
    bx = 100
    by = HEIGHT - 55
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=5, fill=(40, 40, 70))
    frac = min(1.0, t_musica / DURACAO_POR_MUSICA)
    cor_barra = (
        int(COR_BARRA[0] * (0.7 + 0.3 * math.sin(t_global * 3))),
        COR_BARRA[1],
        COR_BARRA[2],
    )
    draw.rounded_rectangle([bx, by, bx + int(bw * frac), by + bh], radius=5, fill=cor_barra)
    draw.text((bx, by - 24), f"Tocando agora • Faixa {pos}/{TOTAL_MUSICAS}",
              font=fontes["pequeno"], fill=(150, 150, 200))

    return img


def main():
    top20_path = OUTPUT_DIR / "top20.json"
    if not top20_path.exists():
        raise SystemExit("ERRO: top20.json não encontrado.")

    dados = json.loads(top20_path.read_text())
    musicas = dados["musicas"]
    mes_ano = dados["mes_ano"]

    print(f"=== Gerando video animado: Top 20 - {mes_ano} ===")
    print(f"Duração total: {DURACAO_TOTAL}s | Frames: {TOTAL_FRAMES} | FPS: {FPS}")

    fontes = carregar_fontes()
    particulas = gerar_particulas()

    print("Iniciando geração de frames e compressão direta via FFmpeg...")

    video_sem_audio = OUTPUT_DIR / "video_sem_audio.mp4"
    
    comando_ffmpeg = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "26",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(video_sem_audio)
    ]
    
    processo = subprocess.Popen(comando_ffmpeg, stdin=subprocess.PIPE)

    LOG_INTERVALO = FPS * 10  # log a cada 10s
    for fi in range(TOTAL_FRAMES):
        if fi % LOG_INTERVALO == 0:
            print(f"  Frame {fi}/{TOTAL_FRAMES} ({fi*100//TOTAL_FRAMES}%)")

        frame = gerar_frame(fi, musicas, mes_ano, particulas, fontes)
        processo.stdin.write(frame.tobytes())

    processo.stdin.close()
    processo.wait()
    
    if processo.returncode != 0:
        raise RuntimeError("Erro ao executar FFmpeg.")

    print(f"Vídeo base criado: {video_sem_audio}")


if __name__ == "__main__":
    main()
