
# 📘 Projeto NFCOM - NOVA REFORMA TRIBUTÁRIA

## 📌 Visão Geral

O **Projeto NFCOM Reforma Tributária** é um validador fiscal completo para **Notas Fiscais de Comunicação (NFCom)**, desenvolvido para validar regras da **Reforma Tributária (CBS / IBS / IBSUF / IBSMUN / ISS)** conforme especificações oficiais do projeto **[NFCOM](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-consumo/orientacoes-2026)**.

O sistema valida **nota individual** ou **lotes de notas**, gerando:

- 📄 **Relatórios HTML detalhados**
- 📝 **Auditoria TXT completa (regra a regra)**
- 📊 **Consolidado CSV**
- 📈 **Consolidado XLSX**

Todos os cenários fiscais estão cobertos:

- ✅ TELCO FUST
- ✅ TELCO NÃO FUST
- ✅ NÃO TELCO
- ✅ NÃO TRIBUTADO

---

## 🧱 Pré‑requisitos

### 1️⃣ Python

* Python **3.10 ou superior**

Verificação:

```bash
python --version
```

### 2️⃣ Bibliotecas Python

Instale todas as dependências com:

```bash
pip install -r requirements.txt
```

Dependências principais:

- pandas
- openpyxl
- decimal

---

## 🗂️ Estrutura Atual do Projeto

```text
nf_claro_2025/
│
├── main.py
│
├── reports/
│   ├── single/
│   │   └── (saídas de execução individual)
│   │
│   └── lote/
│       └── (saídas de execução em lote + consolidados)
│
├── data/
│   ├── 001_TELCO_FUST.json
│   ├── lote/
│   │   ├── 001_TELCO_FUST.json
│   │   ├── 002_TELCO_NAO_FUST.json
│   │   └── ...
│   │
│   ├── Tabela_cClass.xlsx
│   └── Tabela_NTELCO.xlsx
│
├── nf_claro_2025/
│   │
│   ├── batch_processor.py
│   ├── invoice_loader.py
│   ├── classification.py
│   │
│   ├── config.py
│   │
│   ├── validator/
│   │   ├── __init__.py
│   │   └── validator.py
│   │
│   ├── rules/
│   │   ├── ct003_fixos.py
│   │   ├── ct004_cst.py
│   │   ├── ct005_cclass.py
│   │   ├── ct006_bc.py
│   │   ├── ct007_ibuf.py
│   │   ├── ct008_ibs.py
│   │   ├── ct009_ibsmun.py
│   │   ├── ct010_cbs.py
│   │   ├── ct011_tot_bc.py
│   │   ├── ct012_tot_ibuf.py
│   │   ├── ct013_tot_ibsmun.py
│   │   ├── ct014_tot_ibs.py
│   │   └── ct015_tot_cbs.py
│   │
│   ├── reporting/
│   │   ├── html_reporter.py
│   │   ├── audit_reporter.py
│   │   ├── rule_descriptions.py
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── .gitignore
├── README.md
└── requirements.txt

📂 ESTRUTURA DE SAÍDA (REPORTS)
▶ Execução SINGLE
reports/
└── single/
    └── NF_<NUMERO>_<ARQUIVO>_<CATEGORIA>/
        ├── relatorio.html
        └── auditoria.txt

▶ Execução LOTE
reports/
└── lote/
    ├── NF_<NUMERO>_<ARQUIVO>_<CATEGORIA>/
    │   ├── relatorio.html
    │   └── auditoria.txt
    │
    ├── NF_<NUMERO>_<ARQUIVO>_<CATEGORIA>/
    │   ├── relatorio.html
    │   └── auditoria.txt
    │
    ├── consolidado.csv
    └── consolidado.xlsx        
```

---

## 🧠 Arquitetura e Lógica

### ✅ Responsabilidades bem separadas

#### `main.py`
- Interface de linha de comando (CLI)
- Decide o modo de execução:
  - **Single** (arquivo único)
  - **Lote** (diretório com múltiplos arquivos)
- Define as **pastas de saída** dos relatórios (`reports/single` e `reports/lote`)

---

#### `BatchProcessor`
- Orquestra a execução do processamento
- Coordena fluxo **single** e **lote**
- Gera relatórios (HTML e auditoria)
- Mantém **feedback imediato no console** (OK / DIVERGENTE)

---

#### `Validator`
- Executa as regras fiscais **CT003 a CT015**
- Centraliza a lógica de validação
- Gera:
  - `summary` (resultado estruturado)
  - `issues` (lista de divergências)

---

#### `HTMLReporter`
- Responsável exclusivamente pelo **layout do relatório**
- Mantém:
  - Separação por **ITEM**
  - Nomes amigáveis dos cenários (CT)
  - Destaque visual de **OK / ERRO**
- Aplica cores e organização visual sem impactar regras ou cálculos

### 🔹 Classificação Fiscal

* Baseada em **IND_CLASSIF_PRODUTO_SERVICO**
* Usa:

  * **Tabela cClass** → define categoria base
  * **Tabela NTELCO** → define CST, cClassTrib e ISS (dinâmico)

### 🔹 Regras Implementadas

* CT003 → Campos Fixos
* CT004 → COD_CST
* CT005 → COD_CLASSIF_TRIB
* CT006 → Base de Cálculo
* CT007 → IBSUF
* CT008 → IBS
* CT009 → IBSMUN
* CT010 → CBS
* CT011–CT015 → Totalizadores

---

## ▶️ Execução

### 🔹 Nota Única

```bash
python main.py data_TELCO_FUST.json --html --audit
```

### 🔹 Lote de Notas

```bash
python main.py data\lote --multi --html --audit
```

---

## 📄 Saídas Geradas

### ✔ Por Nota

* relatorio.html
* auditoria.txt

### ✔ Por Lote

* consolidado.csv
* consolidado.xlsx

---

## 🏁 Status do Projeto

* ✔ Projeto funcional
* ✔ Todos os cenários validados
* ✔ Arquitetura estável
* ✔ Pronto para versionamento, CI/CD e entrega

---

## 👤 Autor

Projeto desenvolvido e validado por **André Leite**.

---

## 📌 Observação Final

Este README reflete **exatamente** o estado atual do código e da estrutura do projeto.

---

### ✅ Links de Navegação (em formato de índice)

- [Visão Geral](#-visão-geral)
- [Pré‑requisitos](#-pré‑requisitos)
- [Estrutura Atual do Projeto](#️-estrutura-atual-do-projeto)
- [Arquitetura e Lógica](#️-arquitetura-e-lógica)
- [Execução](#️-execução)
- [Saídas Geradas](#📄-saídas-geradas)
- [Status do Projeto](#🏁-status-do-projeto)
- [Autor](#👤-autor)
- [Observação Final](#📌-observação-final)
