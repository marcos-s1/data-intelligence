import os
from pathlib import Path

def estruturar_pasta_testes():
    raiz = Path(__file__).parent.resolve()
    pasta_tests = raiz / "tests"
    
    # 1. Cria a pasta tests se não existir
    pasta_tests.mkdir(exist_ok=True)
    print("📁 Diretório 'tests/' criado ou verificado.")
    
    # 2. Arquivos de teste a serem criados em branco (serão preenchidos nos passos seguintes)
    arquivos = [
        "__init__.py",
        "test_extraction.py",
        "test_transformation.py",
        "test_utils.py"
    ]
    
    for arquivo in arquivos:
        caminho_arq = pasta_tests / arquivo
        if not caminho_arq.exists():
            caminho_arq.touch()
            print(f"📄 Arquivo criado: tests/{arquivo}")
            
    # 3. Atualização automática do requirements.txt
    req_path = raiz / "requirements.txt"
    dependencias_teste = ["pytest\n", "pytest-mock\n"]
    
    if req_path.exists():
        conteudo_atual = req_path.read_text(encoding='utf-8')
        novas_deps = [dep for dep in dependencias_teste if dep not in conteudo_atual]
        
        if novas_deps:
            with open(req_path, "a", encoding="utf-8") as f:
                f.writelines(novas_deps)
            print("✅ 'requirements.txt' atualizado com as bibliotecas de teste!")
        else:
            print("⚠️ 'requirements.txt' já continha as bibliotecas de teste.")
            
if __name__ == "__main__":
    estruturar_pasta_testes()