# 🚀 GerarTarefas 1.0

Sistema de automação para criação de tarefas de infraestrutura VMware usando Selenium WebDriver.

## 📋 Descrição

Este projeto automatiza o processo de criação de tarefas em sistemas de gerenciamento de chamados, integrando com ambientes VMware vSphere. O sistema é capaz de gerar tarefas aleatórias baseadas em um banco de dados CSV e preencher automaticamente formulários web.

## 🔧 Componentes do Projeto

### 📄 Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `1 - Criador de tarefas final 3.0.py` | **Script principal** - Automatiza a criação de tarefas no sistema web usando Selenium |
| `1 - Gerador de banco.py` | **Gerador de banco de dados** - Cria o arquivo CSV com tarefas aleatórias de VMware |
| `Banco_Tarefas.csv` | **Base de dados** - Contém todas as tarefas disponíveis com tempos e complexidades |
| `converter_csv.py` | **Conversor de formato** - Converte CSVs para o formato esperado pelo sistema |

### ⚙️ Arquivos de Configuração

| Arquivo | Função |
|---------|--------|
| `last_hours.txt` | Armazena a última quantidade de horas solicitada |
| `last_request.txt` | Guarda o ID do último chamado processado |
| `.gitignore` | Define quais arquivos não devem ser versionados |

### 🛠️ Dependências

| Arquivo | Descrição |
|---------|-----------|
| `msedgedriver.exe` | Driver do Microsoft Edge para automação web |
| `LICENSE.chromedriver` | Licença do ChromeDriver |
| `THIRD_PARTY_NOTICES.chromedriver` | Avisos de terceiros do ChromeDriver |

## 🎯 Funcionalidades

### ✨ Criador de Tarefas (Script Principal)
- 🔄 **Seleção inteligente**: Escolhe tarefas do CSV para totalizar exatamente as horas solicitadas
- ⚖️ **Ajuste automático**: Modifica tempos automaticamente se necessário para atingir o alvo
- 🌐 **Automação web**: Preenche formulários automaticamente usando Selenium
- 📊 **Suporte a Select2**: Manipula campos dropdown complexos
- 🎭 **Perfil persistente**: Mantém login do Edge para facilitar uso

### 🎲 Gerador de Banco
- 📝 **Tarefas VMware**: Gera atividades realistas de infraestrutura virtual
- 🏗️ **Modelos dinâmicos**: Cria variações de tarefas com hosts e storages aleatórios
- ⏱️ **Tempos variáveis**: Define tempos estimados e gastos com variação realística
- 📈 **Níveis de complexidade**: Atribui complexidade (Baixa, Média, Alta) baseada no tempo

### 🔄 Conversor CSV
- 📊 **Compatibilidade**: Converte CSVs de diferentes formatos para o padrão do sistema
- 🧹 **Limpeza de dados**: Remove aspas e ajusta delimitadores
- 🔧 **Correção automática**: Padroniza encoding para UTF-8

## 🚀 Como Usar

### 1️⃣ Preparação
```bash
# Clone o repositório
git clone https://github.com/wilscot/GerarTarefas1.0.git

# Navegue para a pasta
cd GerarTarefas1.0
```

### 2️⃣ Gerar Banco de Tarefas (Opcional)
```bash
python "1 - Gerador de banco.py"
```

### 3️⃣ Executar Automação
```bash
python "1 - Criador de tarefas final 3.0.py"
```

## 📊 Formato do CSV

O arquivo `Banco_Tarefas.csv` deve conter as seguintes colunas:

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| `titulo` | Nome da tarefa | "Verificar saúde de hosts com vCenter" |
| `descricao` | Descrição detalhada | "Checar status de CPU, rede, memória..." |
| `tempo_estimado` | Tempo previsto (horas) | "1,5" |
| `tempo_gasto` | Tempo real (horas) | "1,3" |
| `complexidade` | Nível de dificuldade | "Média" |

## ⚡ Características Técnicas

### 🔧 Tecnologias Utilizadas
- **Python 3.x**
- **Selenium WebDriver** - Automação web
- **Microsoft Edge** - Navegador padrão
- **CSV** - Armazenamento de dados

### 🎯 Funcionalidades Avançadas
- **Combinação ótima**: Algoritmo para selecionar tarefas que somem exatamente as horas desejadas
- **Ajuste inteligente**: Modifica automaticamente tempos para atingir metas
- **Persistência**: Lembra das últimas configurações utilizadas
- **Tratamento de erros**: Lida com falhas e reconexões automáticas

## 📋 Pré-requisitos

- Python 3.6+
- Microsoft Edge instalado
- Selenium WebDriver
- Acesso ao sistema web de chamados

## 🤝 Contribuição

Sinta-se à vontade para contribuir com melhorias:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Willian Alvaro Francischini**
- GitHub: [@wilscot](https://github.com/wilscot)

---
⭐ Se este projeto foi útil para você, considere dar uma estrela!
