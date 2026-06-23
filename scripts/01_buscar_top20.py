"""
Script 01 - Buscar Top 20 músicas mais tocadas no Brasil
Fontes: Google Trends (pytrends) + scraping público do Kworb/Charts
"""
import json
import os
import re
import time
import datetime
import requests
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Fonte 1: Kworb – Spotify Brasil Top 50 (dados públicos, sem API key)
# ---------------------------------------------------------------------------
def buscar_kworb_spotify_brasil():
    url = "https://kworb.net/spotify/country/br_daily.html"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Top20Bot/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        musicas = []
        tabela = soup.find("table")
        if not tabela:
            return []
        for linha in tabela.find_all("tr")[1:21]:  # top 20
            cols = linha.find_all("td")
            if len(cols) >= 2:
                texto = cols[1].get_text(" ", strip=True)
                # formato: "Artista - Título"
                partes = texto.split(" - ", 1)
                if len(partes) == 2:
                    musicas.append({
                        "artista": partes[0].strip(),
                        "titulo": partes[1].strip(),
                        "fonte": "Spotify BR"
                    })
        return musicas
    except Exception as e:
        print(f"[Kworb] Erro: {e}")
        return []


# ---------------------------------------------------------------------------
# Fonte 2: Kworb – YouTube Brasil Music Chart
# ---------------------------------------------------------------------------
def buscar_kworb_youtube_brasil():
    url = "https://kworb.net/youtube/country/BR.html"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Top20Bot/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        musicas = []
        tabela = soup.find("table")
        if not tabela:
            return []
        for linha in tabela.find_all("tr")[1:21]:
            cols = linha.find_all("td")
            if len(cols) >= 2:
                texto = cols[1].get_text(" ", strip=True)
                partes = texto.split(" - ", 1)
                if len(partes) == 2:
                    musicas.append({
                        "artista": partes[0].strip(),
                        "titulo": partes[1].strip(),
                        "fonte": "YouTube BR"
                    })
        return musicas
    except Exception as e:
        print(f"[Kworb YT] Erro: {e}")
        return []


# ---------------------------------------------------------------------------
# Fonte 3: SerpAPI – Google Trends "músicas mais tocadas Brasil"
# (só se SERPAPI_KEY estiver configurada)
# ---------------------------------------------------------------------------
def buscar_serpapi_trends():
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        print("[SerpAPI] Chave não configurada – pulando.")
        return []
    try:
        params = {
            "engine": "google_trends",
            "q": "músicas mais tocadas",
            "geo": "BR",
            "data_type": "RELATED_QUERIES",
            "api_key": api_key,
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
        data = resp.json()
        musicas = []
        rising = data.get("related_queries", {}).get("rising", [])
        for item in rising[:20]:
            q = item.get("query", "")
            partes = q.split(" - ", 1)
            if len(partes) == 2:
                musicas.append({"artista": partes[1].strip(), "titulo": partes[0].strip(), "fonte": "Google Trends"})
        return musicas
    except Exception as e:
        print(f"[SerpAPI] Erro: {e}")
        return []


# ---------------------------------------------------------------------------
# Consolidar e deduplicar
# ---------------------------------------------------------------------------
def consolidar(fontes_listas):
    visto = set()
    resultado = []
    for lista in fontes_listas:
        for m in lista:
            chave = (m["artista"].lower(), m["titulo"].lower())
            if chave not in visto:
                visto.add(chave)
                resultado.append(m)
            if len(resultado) >= 20:
                break
        if len(resultado) >= 20:
            break
    return resultado[:20]


# ---------------------------------------------------------------------------
# Fallback hardcoded – usado se todas as fontes falharem
# (atualizar manualmente se necessário)
# ---------------------------------------------------------------------------
FALLBACK = [
    {"artista": "Mc Ryan SP", "titulo": "Solteiro Forçado", "fonte": "fallback"},
    {"artista": "Ferrugem", "titulo": "Mil Razões", "fonte": "fallback"},
    {"artista": "Gusttavo Lima", "titulo": "Pagode em Alto Mar", "fonte": "fallback"},
    {"artista": "Wesley Safadão", "titulo": "Camarote", "fonte": "fallback"},
    {"artista": "Léo Santana", "titulo": "Zona de Perigo", "fonte": "fallback"},
    {"artista": "Anitta", "titulo": "Funk Rave", "fonte": "fallback"},
    {"artista": "Matuê", "titulo": "333", "fonte": "fallback"},
    {"artista": "Zé Vaqueiro", "titulo": "Arrocha do Amor", "fonte": "fallback"},
    {"artista": "Simone Mendes", "titulo": "Erro Gostoso", "fonte": "fallback"},
    {"artista": "Dennis DJ", "titulo": "Tá OK", "fonte": "fallback"},
    {"artista": "Ludmilla", "titulo": "Nessa Vida", "fonte": "fallback"},
    {"artista": "Xamã", "titulo": "Coração", "fonte": "fallback"},
    {"artista": "Belo", "titulo": "Inevitável", "fonte": "fallback"},
    {"artista": "Vitor Fernandes", "titulo": "Leva Eu", "fonte": "fallback"},
    {"artista": "Mc Poze", "titulo": "Tá Em Paz", "fonte": "fallback"},
    {"artista": "Dilsinho", "titulo": "Sorte", "fonte": "fallback"},
    {"artista": "Péricles", "titulo": "Não Faz Assim", "fonte": "fallback"},
    {"artista": "Grupo Menos é Mais", "titulo": "Não Existe Amor em SP", "fonte": "fallback"},
    {"artista": "Thiaguinho", "titulo": "Ousadia e Alegria", "fonte": "fallback"},
    {"artista": "Henrique e Juliano", "titulo": "Fala Mal de Mim", "fonte": "fallback"},
]


def main():
    print("=== Buscando Top 20 músicas Brasil ===")

    spotify = buscar_kworb_spotify_brasil()
    print(f"Spotify BR: {len(spotify)} músicas")
    time.sleep(2)

    youtube = buscar_kworb_youtube_brasil()
    print(f"YouTube BR: {len(youtube)} músicas")
    time.sleep(2)

    trends = buscar_serpapi_trends()
    print(f"Google Trends: {len(trends)} músicas")

    top20 = consolidar([spotify, youtube, trends])

    if len(top20) < 10:
        print("Poucas músicas encontradas – usando fallback.")
        top20 = FALLBACK

    # Numerar
    for i, m in enumerate(top20, 1):
        m["posicao"] = i

    # Montar metadados do vídeo
    agora = datetime.datetime.now()
    meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    mes_ano = f"{meses[agora.month - 1]} {agora.year}"

    resultado = {
        "mes_ano": mes_ano,
        "gerado_em": agora.isoformat(),
        "musicas": top20
    }

    saida = OUTPUT_DIR / "top20.json"
    saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(f"\nTop 20 salvo em {saida}")
    for m in top20:
        print(f"  {m['posicao']:>2}. {m['artista']} – {m['titulo']}")


if __name__ == "__main__":
    main()
