"""
SCRIPT LOCAL – Obter Refresh Token do YouTube (OAuth2)
Execute este script UMA VEZ no seu computador local para gerar o refresh_token.
O refresh_token não expira (exceto se você revogar), então salve-o nos Secrets do GitHub.

PRÉ-REQUISITOS:
  pip install google-auth-oauthlib google-api-python-client

COMO USAR:
  1. Acesse: https://console.cloud.google.com/
  2. Crie um projeto → Ativar YouTube Data API v3
  3. Credenciais → Criar credenciais → ID do cliente OAuth
     - Tipo: Aplicativo para desktop
  4. Baixe o JSON das credenciais como 'client_secret.json'
     e coloque na mesma pasta deste script
  5. Execute: python obter_refresh_token_youtube.py
  6. Autorize no navegador
  7. Copie o refresh_token gerado → GitHub Secrets → YOUTUBE_REFRESH_TOKEN
"""
import json
import os

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle
except ImportError:
    print("Instale as dependências: pip install google-auth-oauthlib google-api-python-client")
    raise SystemExit(1)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "youtube_token.pickle"


def main():
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERRO: Arquivo '{CLIENT_SECRET_FILE}' não encontrado.")
        print("Baixe em: console.cloud.google.com → Credenciais → OAuth → Baixar JSON")
        raise SystemExit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=8080, prompt="consent")

    # Salvar token localmente
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    print("\n" + "="*60)
    print("✅ AUTENTICAÇÃO CONCLUÍDA")
    print("="*60)
    print(f"\nRefresh Token:\n{creds.refresh_token}")
    print(f"\nClient ID:\n{creds.client_id}")
    print(f"\nClient Secret:\n{creds.client_secret}")
    print("\n" + "="*60)
    print("\nAdicione estes valores nos GitHub Secrets:")
    print("  YOUTUBE_CLIENT_ID     =", creds.client_id)
    print("  YOUTUBE_CLIENT_SECRET =", creds.client_secret)
    print("  YOUTUBE_REFRESH_TOKEN =", creds.refresh_token)
    print("="*60)

    # Salvar também em arquivo JSON para facilitar
    saida = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
    }
    with open("youtube_credentials.json", "w") as f:
        json.dump(saida, f, indent=2)
    print(f"\nCredenciais salvas em 'youtube_credentials.json'")
    print("⚠️  NÃO faça commit deste arquivo! Ele já está no .gitignore.")


if __name__ == "__main__":
    main()
