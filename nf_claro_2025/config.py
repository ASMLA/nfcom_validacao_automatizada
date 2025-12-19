import os
from dataclasses import dataclass

@dataclass
class CaminhosConfig:
    caminho_cclass: str
    caminho_tabela_ntelco: str


@dataclass
class Configuracao:
    caminhos: CaminhosConfig


def carregar_configuracao():
    """
    Carrega caminhos padrão das tabelas necessárias pelo Projeto Claro 2025.
    """

    base_path = os.path.dirname(os.path.abspath(__file__))

    # Pastas internas
    data_folder = os.path.join(base_path, "..", "data")

    # Caminhos das tabelas
    caminho_cclass = os.path.join(data_folder, "Tabela_cClass.xlsx")
    caminho_ntelco = os.path.join(data_folder, "Tabela_NTELCO.xlsx")

    return Configuracao(
        caminhos=CaminhosConfig(
            caminho_cclass=caminho_cclass,
            caminho_tabela_ntelco=caminho_ntelco
        )
    )
