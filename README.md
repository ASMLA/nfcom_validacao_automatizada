# 📘 Projeto NF Claro 2025

## 📌 Visão Geral

O **Projeto NF Claro 2025** é um validador fiscal completo para **Notas Fiscais de Comunicação (NFCom)**, desenvolvido para validar regras da **Reforma Tributária (CBS / IBS / IBSUF / IBSMUN / ISS)** conforme especificações oficiais do projeto **NF Claro 2025**.

O sistema valida **nota individual** ou **lotes de notas**, gerando:

* 📄 Relatórios HTML detalhados
* 📝 Auditoria TXT completa (regra a regra)
* 📊 Consolidado CSV
* 📈 Consolidado XLSX

Todos os cenários fiscais estão cobertos:

* ✅ TELCO FUST
* ✅ TELCO NÃO FUST
* ✅ NÃO TELCO
* ✅ NÃO TRIBUTADO

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

* pandas
* openpyxl
* decimal

---

## 🗂️ Estrutura Atual do Projeto (CORRIGIDA)

```text
nf_claro_2025/
│
├── main.py                     # CLI principal (unitário e lote)
├── requirements.txt
├── README.md
│
├── data/                        # ENTRADAS
│   │
│   ├── 001_TELCO_FUST.json
│   ├── 002_TELCO_N_FUST.json
│   ├── 003_N_TELCO.json
│   ├── 004_N_TRIBUTADO.json
│   │
│   ├── lote/                   # 🔴 PROCESSAMENTO EM LOTE
│   │   ├── 001_TELCO_FUST.json
│   │   ├── 002_TELCO_N_FUST.json
│   │   ├── 003_N_TELCO.json
│   │   └── 004_N_TRIBUTADO.json
│   │
│   ├── Tabela_cClass.xlsx
│   └── tabela_referencia_NTELCO.xlsx
│
├── reports/                     # SAÍDA AUTOMÁTICA
│   └── YYYY-MM-DD_HH-MM-SS/
│       │
│       ├── NF_219_001_TELCO_FUST_TELCO_FUST/
│       │   ├── relatorio.html
│       │   └── auditoria.txt
│       │
│       ├── NF_3534_002_TELCO_N_FUST_TELCO_N_FUST/
│       ├── NF_4388_003_N_TELCO_NAO_TELCO/
│       │
│       ├── consolidado.csv
│       └── consolidado.xlsx
│
└── nf_claro_2025/
    ├── __init__.py
    │
    ├── config.py               # Configura caminhos e parâmetros
    ├── invoice_loader.py       # Leitura e normalização do JSON
    ├── classification.py       # Classificação fiscal (TELCO / NÃO TELCO / etc)
    │
    ├── validator/
    │   ├── __init__.py
    │   └── validator.py        # Orquestrador CT003–CT015
    │
    ├── rules/                  # Regras fiscais
    │   ├── ct003_fixos.py
    │   ├── ct004_cst.py
    │   ├── ct005_cclass.py
    │   ├── ct006_bc.py
    │   ├── ct007_ibuf.py
    │   ├── ct008_ibs.py
    │   ├── ct009_ibsmun.py
    │   ├── ct010_cbs.py
    │   ├── ct011_tot_bc.py
    │   ├── ct012_tot_ibuf.py
    │   ├── ct013_tot_ibsmun.py
    │   ├── ct014_tot_ibs.py
    │   └── ct015_tot_cbs.py
    │
    ├── reporting/
    │   ├── audit_reporter.py   # Relatório TXT (auditoria)
    │   └── html_reporter.py    # Relatório HTML
    │
    └── batch_processor.py      # 🔴 PROCESSADOR DE LOTE
```

---

## 🧠 Arquitetura e Lógica

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
python main.py data\001_TELCO_FUST.json --html --audit
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
