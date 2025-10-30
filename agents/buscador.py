import os
import sys

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from default_api import google_web_search, web_fetch, write_file

class BuscadorFiscal:
    """Agente para buscar e salvar documentos fiscais da web."""

    def __init__(self):
        self.referencias_path = os.path.join(os.path.dirname(__file__), '..\referencias')

    def buscar_e_salvar_documentos(self, query: str, file_name: str):
        """Busca um documento na web e o salva na pasta de referências."""
        print(f"Buscando por: {query}")
        try:
            # 1. Buscar na web
            search_results = google_web_search(query=query)
            
            if not search_results or not search_results.get('results'):
                print("Nenhum resultado encontrado na busca.")
                return

            # 2. Pegar a URL mais relevante
            first_result = search_results['results'][0]
            url = first_result.get('link')
            title = first_result.get('title')
            print(f"URL mais relevante encontrada: {title} ({url})")

            if not url:
                print("Não foi possível encontrar uma URL no resultado da busca.")
                return

            # 3. Buscar o conteúdo da URL
            print(f"Buscando conteúdo da URL: {url}")
            fetch_result = web_fetch(prompt=f"Extraia o conteúdo principal do seguinte URL: {url}")
            
            if not fetch_result or not fetch_result.get('content'):
                print("Não foi possível extrair o conteúdo da URL.")
                return

            content = fetch_result['content']

            # 4. Salvar o conteúdo na pasta de referências
            file_path = os.path.join(self.referencias_path, file_name)
            print(f"Salvando conteúdo em: {file_path}")
            write_file(file_path=file_path, content=content)

            print(f"Documento salvo com sucesso em {file_path}")
            return file_path

        except Exception as e:
            print(f"Ocorreu um erro durante o processo: {e}")
            return None

if __name__ == '__main__':
    buscador = BuscadorFiscal()
    # Exemplo de busca para o primeiro objetivo do usuário
    query_busca = "cálculo ICMS interestadual alíquotas e base de cálculo"
    nome_arquivo = "calculo_icms_interestadual.txt"
    print(f"--- Iniciando busca para: {query_busca} ---")
    buscador.buscar_e_salvar_documentos(query_busca, nome_arquivo)
