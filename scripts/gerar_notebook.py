"""Gera um notebook Jupyter executado a partir de um script com células '# %%'.

Uso: python scripts/gerar_notebook.py analise/etapa2_analise.py notebooks/etapa2_analise.ipynb
"""
import re
import sys
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

origem, destino = Path(sys.argv[1]), Path(sys.argv[2])
blocos = re.split(r"^# %%(.*)$", origem.read_text(encoding="utf-8"), flags=re.M)
celulas = []
for marcador, conteudo in zip(blocos[1::2], blocos[2::2]):
    conteudo = conteudo.strip("\n")
    if "[markdown]" in marcador:
        texto = "\n".join(re.sub(r"^# ?", "", linha) for linha in conteudo.splitlines())
        celulas.append(nbformat.v4.new_markdown_cell(texto))
    else:
        # No notebook não existe __file__; a pasta de saída é relativa à pasta do notebook.
        celulas.append(nbformat.v4.new_code_cell(conteudo))
nb = nbformat.v4.new_notebook(cells=celulas, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3",
                                                                       "language": "python"}})
destino.parent.mkdir(parents=True, exist_ok=True)
ExecutePreprocessor(timeout=900, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(destino.parent)}})
nbformat.write(nb, destino)
print(f"Notebook executado e salvo em {destino}")
