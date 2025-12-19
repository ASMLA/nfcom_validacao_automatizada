import re
from decimal import Decimal
import pandas as pd
import openpyxl


def _clean_header(h: str) -> str:
    """
    Normaliza headers vindos de planilhas:
    - remove BOM e caracteres invisíveis
    - strip
    - colapsa espaços
    - upper
    """
    if h is None:
        return ""
    s = str(h)
    # remove BOM
    s = s.replace("\ufeff", "")
    # remove invisíveis comuns
    s = re.sub(r"[\u200b\u200c\u200d\u2060]", "", s)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def _clean_cell(v) -> str:
    if v is None:
        return ""
    s = str(v)
    s = s.replace("\ufeff", "")
    s = re.sub(r"[\u200b\u200c\u200d\u2060]", "", s)
    return s.strip()


class ClassificadorNF:
    """
    Lê:
      - Tabela cClass (XLSX) → define TIPO (TELCO, NAO TELCO, NAO TRIBUTADO)
      - Tabela NTELCO (XLSX) → somente para NAO TELCO:
            COD_PS (chave)
            CST_CBS_IBS
            cClassTrib
            Municipio (opcional)
            AliqISS (opcional)
            RegraBase (opcional)

    Regras:
      - TELCO / NAO TRIBUTADO:
            usa CST e cClassTrib da cClass
      - NAO TELCO:
            usa CST_CBS_IBS e cClassTrib da NTELCO (via COD_PS = COD_PRODUTO_SERVICO)
            traz também AliqISS (ISS esperado) conforme planilha
      - Se NAO TELCO e não achar COD_PS na NTELCO:
            fallback: COD_CST="000", COD_CLASSIF_TRIB="000001", AliqISS="2%"
      - Se não achar IND_CLASSIF_PRODUTO_SERVICO na cClass:
            categoria = INDEFINIDO
    """

    def __init__(self, config):
        self.config = config
        self._cclass = None
        self._ntelco = None
        self._carregar_tabelas()

    # ============================================================
    #   Carregamento das tabelas de apoio
    # ============================================================
    def _carregar_tabelas(self):
        # ------------ cClass (openpyxl) ------------
        wb = openpyxl.load_workbook(self.config.caminhos.caminho_cclass, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise ValueError("Tabela cClass vazia.")

        headers = [_clean_cell(c) for c in rows[0]]
        df_c = pd.DataFrame([[ _clean_cell(v) for v in r ] for r in rows[1:]], columns=headers)

        # garantir nomes esperados exatamente como no arquivo (case sensitive aqui)
        # Vamos buscar colunas por "match" (sem depender de acentos/case)
        cols_map = { _clean_header(c): c for c in df_c.columns }

        def pick(*cands):
            for cand in cands:
                key = _clean_header(cand)
                if key in cols_map:
                    return cols_map[key]
            return None

        col_codigo = pick("Grupo/Código", "GRUPO/CODIGO", "GRUPO/CÓDIGO", "GRUPO CODIGO", "GRUPO CÓDIGO")
        col_cst = pick("CST", "CST_CBS_IBS")
        col_cclasstrib = pick("cClassTrib", "CCLASSTRIB", "CCLASSTRIB ", "CCLASSTRIBUTO", "COD_CLASSIF_TRIB")
        col_tipo = pick("TIPO", "CATEGORIA")

        missing = [n for n, c in [("Grupo/Código", col_codigo), ("CST", col_cst), ("cClassTrib", col_cclasstrib), ("TIPO", col_tipo)] if c is None]
        if missing:
            raise ValueError(f"cClass: colunas obrigatórias não encontradas: {missing}")

        df_c[col_codigo] = df_c[col_codigo].astype(str).map(_clean_cell)
        df_c[col_cst] = df_c[col_cst].astype(str).map(_clean_cell)
        df_c[col_cclasstrib] = df_c[col_cclasstrib].astype(str).map(_clean_cell)
        df_c[col_tipo] = df_c[col_tipo].astype(str).map(_clean_cell)

        # pad básico (sem "chapar" valor — só formatação de chave/ids)
        df_c[col_cst] = df_c[col_cst].str.zfill(3)
        df_c[col_cclasstrib] = df_c[col_cclasstrib].str.zfill(6)

        self._cclass = df_c
        self._cclass_cols = {
            "codigo": col_codigo,
            "cst": col_cst,
            "cclasstrib": col_cclasstrib,
            "tipo": col_tipo,
        }

        # ------------ NTELCO (pandas/openpyxl) ------------
        # Lê tudo como string e normaliza headers para evitar KeyError 'COD_PS'
        df_n = pd.read_excel(self.config.caminhos.caminho_tabela_ntelco, dtype=str, engine="openpyxl")
        df_n.columns = [_clean_header(c) for c in df_n.columns]

        # Normaliza valores
        for c in df_n.columns:
            df_n[c] = df_n[c].astype(str).map(_clean_cell)

        # Alguns arquivos podem ter header "COD PS" ou "COD_PS " etc — já virou "COD_PS" pelo clean_header.
        # Se mesmo assim não existir, tentamos mapear por aproximação.
        if "COD_PS" not in df_n.columns:
            # tenta encontrar algo que contenha COD e PS
            candidates = [c for c in df_n.columns if ("COD" in c and "PS" in c)]
            if candidates:
                df_n.rename(columns={candidates[0]: "COD_PS"}, inplace=True)

        # Garantir colunas-base (as outras podem ser opcionais)
        if "COD_PS" not in df_n.columns:
            # deixa carregado, mas sem COD_PS não tem como consultar — isso precisa estourar logo
            raise ValueError("NTELCO: coluna COD_PS não encontrada após normalização do header.")

        # Ajustes de pads conforme regras (sem alterar conteúdo lógico)
        if "CST_CBS_IBS" in df_n.columns:
            df_n["CST_CBS_IBS"] = df_n["CST_CBS_IBS"].str.zfill(3)
        if "CCLASSTRIB" in df_n.columns and "CCLASSTRIB" != "CCLASSTRIB":
            pass
        if "CCLASSTRIB" in df_n.columns and "CCLASSTRIB" not in df_n.columns:
            pass
        if "CCLASSTRIB" in df_n.columns:
            # alguns arquivos podem usar CCLASSTRIB ao invés de cClassTrib
            df_n.rename(columns={"CCLASSTRIB": "CCLASSTRIB"}, inplace=True)

        # Preferimos nome padrão "CCLASSTRIB"?? Não. Vamos trabalhar com "CCLASSTRIB" e "CCLASSTRIB"?
        # Melhor: usar "CCLASSTRIB" como alias do "CCLASSTRIB" (sem efeito).
        # Vamos padronizar para "CCLASSTRIB" => "CCLASSTRIB" e "CCLASSTRIB" => "CCLASSTRIB" não muda.
        # Na prática, a coluna costuma vir como "CCLASSTRIB" ou "CCLASSTRIB" só.
        # Vamos tratar "CCLASSTRIB" e "CCLASSTRIB" como candidates mais abaixo.

        self._ntelco = df_n

    # ============================================================
    #   Helpers NTELCO
    # ============================================================
    def _ntelco_get(self, row, *cands, default=""):
        """
        Busca a primeira coluna existente em row conforme lista de candidatos.
        """
        for cand in cands:
            key = _clean_header(cand)
            if key in row and row[key] != "":
                return row[key]
        return default

    def _buscar_ntelco_por_codps(self, cod_ps: str):
        cod_ps = _clean_cell(cod_ps)
        if not cod_ps:
            return None
        df = self._ntelco
        hit = df[df["COD_PS"] == cod_ps]
        if hit.empty:
            return None
        # retorna como dict com chaves normalizadas (já estão UPPER)
        return hit.iloc[0].to_dict()

    # ============================================================
    #   Classificação do item
    # ============================================================
    def classificar_item(self, item: dict) -> dict:
        ind_classif = _clean_cell(item.get("IND_CLASSIF_PRODUTO_SERVICO", ""))

        # 1) Descobrir TIPO base pela cClass
        ccols = self._cclass_cols
        hit = self._cclass[self._cclass[ccols["codigo"]] == ind_classif]

        if hit.empty:
            return {
                "categoria": "INDEFINIDO",
                "cst_esperado": None,
                "cclass_esperado": None,
                "municipio_iss": None,
                "aliq_iss_esperada": None,
                "fonte_cst_cclass": "N/A",
                "cod_ps": _clean_cell(item.get("COD_PRODUTO_SERVICO", "")),
            }

        row_c = hit.iloc[0]
        tipo_base = _clean_cell(row_c[ccols["tipo"]])

        # defaults: vindo da cClass
        cst_esp = _clean_cell(row_c[ccols["cst"]]).zfill(3)
        cclass_esp = _clean_cell(row_c[ccols["cclasstrib"]]).zfill(6)

        cod_ps = _clean_cell(item.get("COD_PRODUTO_SERVICO", ""))

        # 2) Refinamento: NAO TELCO consulta NTELCO por COD_PS
        if tipo_base.upper() == "NAO TELCO":
            nt = self._buscar_ntelco_por_codps(cod_ps)

            if nt is None:
                # fallback definido por você
                return {
                    "categoria": "NAO TELCO",
                    "cst_esperado": "000",
                    "cclass_esperado": "000001",
                    "municipio_iss": None,
                    "aliq_iss_esperada": "2%",
                    "fonte_cst_cclass": "FALLBACK_NTELCO_NAO_ENCONTRADO",
                    "cod_ps": cod_ps,
                }

            # Achou: usa o que está escrito na NTELCO (dinâmico / exato)
            cst_nt = self._ntelco_get(nt, "CST_CBS_IBS", default="").strip()
            cclass_nt = self._ntelco_get(nt, "cClassTrib", "CCLASSTRIB", default="").strip()
            municipio = self._ntelco_get(nt, "Municipio", default="").strip() or None
            aliqiss = self._ntelco_get(nt, "AliqISS", default="").strip() or None

            # pad onde faz sentido (CST 3, cClassTrib 6)
            if cst_nt != "":
                cst_nt = cst_nt.zfill(3)
            if cclass_nt != "":
                cclass_nt = cclass_nt.zfill(6)

            return {
                "categoria": "NAO TELCO",
                "cst_esperado": cst_nt if cst_nt else "000",
                "cclass_esperado": cclass_nt if cclass_nt else "000001",
                "municipio_iss": municipio,
                "aliq_iss_esperada": aliqiss,
                "fonte_cst_cclass": "NTELCO",
                "cod_ps": cod_ps,
            }

        # 3) TELCO / NAO TRIBUTADO: usa cClass
        return {
            "categoria": tipo_base,
            "cst_esperado": cst_esp,
            "cclass_esperado": cclass_esp,
            "municipio_iss": None,
            "aliq_iss_esperada": None,
            "fonte_cst_cclass": "CCLASS",
            "cod_ps": cod_ps,
        }
