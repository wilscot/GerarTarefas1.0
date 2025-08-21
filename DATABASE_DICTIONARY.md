# 📊 DICIONÁRIO DE DADOS - ServiceDesk Database

## 🎯 Informações Gerais
- **Database**: Servicedesk_2022
- **Server**: S0680.ms
- **Connection**: Windows Authentication
- **Driver**: ODBC Driver 17 for SQL Server
- **Owner ID**: 2007 (Willian Francischini)
- **Período de Análise**: Desde 26/07/2025

---

## 📋 ESTRUTURA DAS TABELAS

### 🔹 **WorkOrder** (Chamados/Solicitações)
Tabela principal que armazena os chamados do sistema.

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `WORKORDERID` | bigint | ID único do chamado | 540030 |
| `TITLE` | nvarchar | Título do chamado | "CSI EAST - Datacenter - Execução de Tarefas" |
| `REQUESTERID` | bigint | **ID do solicitante** (equiv. OWNERID) | 2007 |
| `CREATEDBYID` | bigint | ID do criador | 1 |
| `CREATEDTIME` | bigint | Timestamp de criação (milissegundos) | 1755516600362 |
| `DESCRIPTION` | ntext | Descrição detalhada do chamado | - |
| `DEPTID` | bigint | ID do departamento | 303 |
| `SITEID` | bigint | ID do site | 301 |
| `TEMPLATEID` | bigint | ID do template usado | 1 |
| `MODEID` | int | Modo do chamado | 3 |
| `SLAID` | int | ID do SLA | 1 |

**🔍 Query de Exemplo:**
```sql
SELECT WORKORDERID, TITLE, REQUESTERID, CREATEDTIME 
FROM dbo.WorkOrder 
WHERE WORKORDERID = 540030
```

---

### 🔹 **TaskDetails** (Tarefas)
Tabela que armazena as tarefas vinculadas aos chamados.

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `TASKID` | bigint | **ID único da tarefa** | 53833, 53842 |
| `TITLE` | nvarchar | Título da tarefa | "Avaliar viabilidade do OpenShift Virtualization" |
| `CREATEDDATE` | bigint | Timestamp de criação (milissegundos) | 1724248055653 |
| `ACTUALENDTIME` | bigint | Timestamp de finalização | - |

**🔍 Query de Exemplo:**
```sql
SELECT TASKID, TITLE, CREATEDDATE 
FROM dbo.TaskDetails 
WHERE TASKID = 53833
```

---

### 🔹 **WorkOrderToTaskDetails** (Relacionamento)
Tabela de relacionamento entre chamados e tarefas (N:N).

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `WORKORDERID` | bigint | ID do chamado | 540030 |
| `TASKID` | bigint | ID da tarefa | 53833 |

**🔍 Query de Relacionamento:**
```sql
SELECT w.WORKORDERID, w.TITLE AS WorkOrderTitle, 
       t.TASKID, t.TITLE AS TaskTitle
FROM dbo.WorkOrder w
JOIN dbo.WorkOrderToTaskDetails wttd ON w.WORKORDERID = wttd.WORKORDERID
JOIN dbo.TaskDetails t ON wttd.TASKID = t.TASKID
WHERE w.WORKORDERID = 540030
```

---

### 🔹 **TaskDescription** (Descrições das Tarefas)
Armazena as descrições HTML das tarefas.

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `TASKID` | bigint | ID da tarefa | 53833 |
| `DESCRIPTION` | ntext | Descrição em HTML | `<div>Analisar OpenShift...4713 --&gt;</div>` |

**🔑 Campo Crítico**: Usado para detectar EXEC_TAG discreto no formato HTML encoded.

---

### 🔹 **Task_Fields** (Campos UDF das Tarefas)
Tabela que armazena campos personalizados (User Defined Fields) das tarefas.

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `TASKID` | bigint | ID da tarefa | 53833 |
| `UDF_CHAR1` | nvarchar | **Tempo Estimado** (formato decimal com vírgula) | "2,00" |
| `UDF_CHAR2` | nvarchar | **Tempo Gasto** (formato decimal com vírgula) | "2,00" |
| `UDF_PICK1` | bigint | ID da complexidade | 9911, 9912 |

**⚙️ Conversão de Tempo:**
```sql
TRY_CONVERT(decimal(10,2), REPLACE(UDF_CHAR1, ',', '.')) AS TempoEstimado,
TRY_CONVERT(decimal(10,2), REPLACE(UDF_CHAR2, ',', '.')) AS TempoGasto
```

---

### 🔹 **UDF_PickListValues** (Valores das Listas)
Tabela que mapeia IDs para valores legíveis das listas de seleção.

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `PickListID` | bigint | ID do valor | 9911, 9912 |
| `VALUE` | nvarchar | **Label da complexidade** | "2 - Média", "3 - Alta" |
| `TABLENAME` | nvarchar | Nome da tabela origem | "Task_Fields" |
| `COLUMNNAME` | nvarchar | Nome da coluna origem | "UDF_PICK1" |

**🔍 Mapeamento de Complexidade:**
- `9910` → "1 - Baixa"
- `9911` → "2 - Média" 
- `9912` → "3 - Alta"

---

### 🔹 **WorkOrderStates** (Estados dos Chamados)
Tabela de histórico de estados e atribuições dos chamados.

| Campo | Tipo | Descrição | Valores Exemplo |
|-------|------|-----------|-----------------|
| `WORKORDERID` | bigint | ID do chamado | 540030 |
| `OWNERID` | bigint | ID do responsável atual | 2007 |
| `ASSIGNEDTIME` | bigint | Timestamp da atribuição | - |

**🔍 Query para Owner Atual:**
```sql
WITH CurrentState AS (
  SELECT WORKORDERID, OWNERID,
         ROW_NUMBER() OVER (PARTITION BY WORKORDERID ORDER BY ASSIGNEDTIME DESC) AS rn
  FROM dbo.WorkOrderStates
)
SELECT OWNERID FROM CurrentState 
WHERE WORKORDERID = 540030 AND rn = 1
```

---

## 🎯 QUERY PRINCIPAL - MÉTRICAS COMPLETAS

### 📊 Query Consolidada (WorkOrder + Tasks + Campos + Complexidade)
```sql
SELECT DISTINCT
    wo.WORKORDERID,
    wo.TITLE AS WorkOrderTitle,
    wo.REQUESTERID AS OwnerID,
    wo.CREATEDTIME AS WorkOrderCreatedTime,
    td.TASKID,
    td.TITLE AS TaskTitle,
    td.CREATEDDATE AS TaskCreatedDate,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
    plv.VALUE AS Complexidade,
    tdesc.DESCRIPTION AS TaskDescription
FROM dbo.WorkOrder wo
JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.WORKORDERID = wo.WORKORDERID
JOIN dbo.TaskDetails td ON td.TASKID = wttd.TASKID
LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
LEFT JOIN dbo.UDF_PickListValues plv ON plv.PickListID = tf.UDF_PICK1 
    AND plv.TABLENAME = 'Task_Fields' 
    AND plv.COLUMNNAME = 'UDF_PICK1'
LEFT JOIN dbo.TaskDescription tdesc ON tdesc.TASKID = td.TASKID
WHERE wo.WORKORDERID = ?
ORDER BY td.CREATEDDATE DESC
```

---

## 🤖 AUTOMAÇÃO SELENIUM - VALIDAÇÃO SQL

### 🏷️ Sistema EXEC_TAG
**Função**: Rastrear tarefas criadas automaticamente via Selenium
**Formato**: `AUTO_YYYYMMDD_HHMMSS` (ex: `AUTO_20250821_131945`)
**Localização**: Inserido na `DESCRIPTION` das tarefas criadas

### 🔍 Query de Validação de Tarefas Criadas
```sql
SELECT DISTINCT
    td.TASKID,
    td.TITLE AS TaskTitle,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
    td.CREATEDDATE,
    tdesc.DESCRIPTION
FROM dbo.TaskDetails td
JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.TASKID = td.TASKID
LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
LEFT JOIN dbo.TaskDescription tdesc ON tdesc.TASKID = td.TASKID
WHERE wttd.WORKORDERID = ?
  AND td.CREATEDDATE >= ?  -- timestamp início execução - 2min
  AND td.CREATEDDATE <= ?  -- timestamp fim execução
  AND (
    tdesc.DESCRIPTION LIKE ?  -- padrão normal: "1945 -->"
    OR tdesc.DESCRIPTION LIKE ? -- padrão HTML encoded: "1945 --&gt;"
  )
```

### 📝 Descobertas da Validação SQL

#### ✅ EXEC_TAG - Padrões Encontrados
1. **Padrão Discreto Normal**: `"1945 -->"` (últimos 4 dígitos + " -->")
2. **Padrão HTML Encoded**: `"1945 --&gt;"` (ServiceDesk converte ">" para "&gt;")
3. **Localização**: Sempre na descrição (`TaskDescription.DESCRIPTION`)
4. **Caso**: A validação SQL funciona com ambos os padrões automaticamente

#### ⏰ Timestamps
- **Formato**: Milissegundos desde Unix epoch (1970)
- **Conversão Python**: `int(datetime.timestamp() * 1000)`
- **Conversão SQL**: `datetime.fromtimestamp(value / 1000)`
- **Janela de Busca**: 2 minutos antes do início até o fim da execução

#### 🔧 Validação de Sucesso
- **Critério Principal**: Existência de pelo menos 1 tarefa com EXEC_TAG
- **Retorno**: Lista de `{"task_id": int, "title": str, "time_spent": float, "time_estimated": float}`
- **Log**: Detalhamento completo de cada tarefa encontrada

#### 📊 Estatísticas de Validação
```sql
-- Debug: Contar tasks no período sem filtro EXEC_TAG
SELECT COUNT(*), MIN(td.CREATEDDATE), MAX(td.CREATEDDATE)
FROM dbo.TaskDetails td
JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.TASKID = td.TASKID
WHERE wttd.WORKORDERID = ?
  AND td.CREATEDDATE >= ?
  AND td.CREATEDDATE <= ?
```

---

Esta é a query validada que retorna todas as informações necessárias:

```sql
DECLARE @OwnerId   bigint = 2007;
DECLARE @Cutoff    date   = '2025-07-26';
DECLARE @CutoffMs  bigint = CONVERT(bigint, DATEDIFF(SECOND, '1970-01-01', @Cutoff)) * 1000;

;WITH CurrentState AS (
  SELECT
    ws.WORKORDERID,
    ws.OWNERID,
    ROW_NUMBER() OVER (PARTITION BY ws.WORKORDERID ORDER BY ws.ASSIGNEDTIME DESC) AS rn
  FROM dbo.WorkOrderStates ws
)
SELECT
  td.TASKID,
  td.TITLE AS TaskTitle,
  w.WORKORDERID,
  w.TITLE AS WorkOrderTitle,
  TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
  TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
  tf.UDF_PICK1 AS ComplexidadeCodigo,
  upv.[VALUE] AS ComplexidadeLabel,
  CONVERT(date, DATEADD(SECOND, td.CREATEDDATE / 1000, '1970-01-01')) AS DataCriacao,
  CASE 
    WHEN td.ACTUALENDTIME IS NOT NULL AND td.ACTUALENDTIME > 0 
    THEN CONVERT(date, DATEADD(SECOND, td.ACTUALENDTIME / 1000, '1970-01-01'))
    ELSE CONVERT(date, DATEADD(SECOND, td.CREATEDDATE / 1000, '1970-01-01'))
  END AS DataFechamento
FROM dbo.WorkOrder AS w
JOIN CurrentState AS cs ON cs.WORKORDERID = w.WORKORDERID AND cs.rn = 1
LEFT JOIN dbo.WorkOrderToTaskDetails AS wttd ON wttd.WORKORDERID = w.WORKORDERID
LEFT JOIN dbo.TaskDetails AS td ON td.TASKID = wttd.TASKID
LEFT JOIN dbo.Task_Fields AS tf ON tf.TASKID = td.TASKID
INNER JOIN dbo.UDF_PickListValues AS upv
       ON upv.PickListID = tf.UDF_PICK1
      AND upv.TABLENAME = 'Task_Fields'
      AND upv.COLUMNNAME = 'UDF_PICK1'
      AND w.TITLE = 'CSI EAST - Datacenter - Execução de Tarefas'
WHERE w.CREATEDTIME >= @CutoffMs
  AND cs.OWNERID = @OwnerId
ORDER BY 
  CASE 
    WHEN td.ACTUALENDTIME IS NOT NULL AND td.ACTUALENDTIME > 0 
    THEN td.ACTUALENDTIME
    ELSE td.CREATEDDATE
  END DESC,
  w.WORKORDERID, 
  td.TASKID;
```

---

## 🔍 QUERY DE DETECÇÃO DE TAREFAS (Sistema de Automação)

Query usada pelo sistema Flask para detectar tarefas criadas pela automação:

```sql
SELECT DISTINCT
    td.TASKID,
    td.TITLE AS TaskTitle,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
    td.CREATEDDATE,
    tdesc.DESCRIPTION
FROM dbo.TaskDetails td
JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.TASKID = td.TASKID
LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
LEFT JOIN dbo.TaskDescription tdesc ON tdesc.TASKID = td.TASKID
WHERE wttd.WORKORDERID = ?
  AND td.CREATEDDATE >= ?
  AND td.CREATEDDATE <= ?
  AND tdesc.DESCRIPTION LIKE ?
```

**🔑 Parâmetros:**
- `WORKORDERID`: 540030
- `CREATEDDATE`: Timestamp de início/fim da busca
- `DESCRIPTION LIKE`: Padrão `%4713 --&gt;%` (EXEC_TAG HTML encoded)

---

## 📊 DADOS DE EXEMPLO REAIS

### Task ID: 53833
```json
{
  "TASKID": 53833,
  "TaskTitle": "Avaliar viabilidade do OpenShift Virtualization",
  "WORKORDERID": 540030,
  "WorkOrderTitle": "CSI EAST - Datacenter - Execução de Tarefas",
  "TempoEstimado": 1.30,
  "TempoGasto": 1.10,
  "ComplexidadeCodigo": 9911,
  "ComplexidadeLabel": "2 - Média",
  "DataCriacao": "2025-08-19",
  "DataFechamento": "2025-08-19"
}
```

### Task ID: 53842 (Criada pela Automação)
```json
{
  "TASKID": 53842,
  "TaskTitle": "Aplicar patch de segurança ESXi",
  "TempoEstimado": 2.00,
  "TempoGasto": 2.00,
  "EXEC_TAG": "AUTO_20250821_125935",
  "Status": "success"
}
```

---

## ⚙️ CONFIGURAÇÕES DO SISTEMA

### Aplicação Flask
- **Owner ID**: 2007 (Willian Francischini)
- **WorkOrder Title**: "CSI EAST - Datacenter - Execução de Tarefas"
- **EXEC_TAG Pattern**: `AUTO_YYYYMMDD_HHMMSS`
- **Detection Pattern**: Últimos 4 dígitos + ` -->`
- **HTML Encoded**: `4713 --&gt;`

### Timestamps
- **Formato**: Milissegundos desde Unix Epoch (1970-01-01)
- **Conversão**: `DATEADD(SECOND, timestamp / 1000, '1970-01-01')`
- **Exemplo**: 1724248055653 → 2025-08-21 12:47:35.653

### Campos Decimais
- **Formato Banco**: Vírgula como separador (`"2,00"`)
- **Formato Aplicação**: Ponto como separador (`2.00`)
- **Conversão**: `REPLACE(campo, ',', '.')`

---

## 🚀 CASOS DE USO

### 1. Buscar Tarefas por Período
```sql
SELECT * FROM dbo.TaskDetails 
WHERE CREATEDDATE >= 1724194800000  -- 2025-08-21 00:00:00
  AND CREATEDDATE <= 1724281199000  -- 2025-08-21 23:59:59
```

### 2. Buscar por EXEC_TAG
```sql
SELECT td.TASKID, td.TITLE, tdesc.DESCRIPTION
FROM dbo.TaskDetails td
JOIN dbo.TaskDescription tdesc ON td.TASKID = tdesc.TASKID
WHERE tdesc.DESCRIPTION LIKE '%5935 --&gt;%'
```

### 3. Validar WorkOrder para Automação
```sql
SELECT w.WORKORDERID, w.TITLE, w.REQUESTERID
FROM dbo.WorkOrder w
WHERE w.WORKORDERID = 540030
  AND w.REQUESTERID = 2007
  AND w.TITLE = 'CSI EAST - Datacenter - Execução de Tarefas'
```

---

## 📝 NOTAS IMPORTANTES

1. **REQUESTERID vs OWNERID**: O campo correto no WorkOrder é `REQUESTERID`, não `OWNERID`
2. **Timestamps**: Sempre em milissegundos, não segundos
3. **HTML Encoding**: Descrições são armazenadas com encoding HTML (`--&gt;` em vez de `-->`)
4. **Campos UDF**: Tempos são armazenados como strings com vírgula decimal
5. **Relacionamentos**: WorkOrder ↔ Task é N:N via `WorkOrderToTaskDetails`
6. **Detecção**: Sistema usa EXEC_TAG discreto na descrição para identificar tarefas criadas pela automação

---

*Última atualização: 21/08/2025 - Baseado em dados reais do sistema ServiceDesk*

---

## 📝 CHANGELOG & DESCOBERTAS

### 🚀 Fase 1 - Foundation & Core Logic (Finalizada)
**Data**: 21/08/2025

#### ✅ Implementações
- **API Flask**: Endpoints de status, workorders e automação
- **Conexão SQL Server**: SQLAlchemy + pyodbc validado
- **Cache TTL**: Sistema de cache com invalidação automática
- **Logs Estruturados**: Logging detalhado para debugging
- **Selenium Service**: Integração com verificação SQL real

#### 🔍 Descobertas Importantes
1. **REQUESTERID vs OWNERID**: 
   - `WorkOrder.REQUESTERID` = dono original do chamado
   - `WorkOrderStates.OWNERID` = responsável atual (pode mudar)
   - Para nosso caso: sempre usar `REQUESTERID = 2007`

2. **Timestamps**: 
   - Formato milissegundos desde Unix epoch
   - Conversão: `int(datetime.timestamp() * 1000)`

3. **HTML Encoding**: 
   - ServiceDesk converte ">" para "&gt;" nas descrições
   - EXEC_TAG deve buscar ambos padrões: `"-->"` e `"--&gt;"`

4. **Campos UDF**: 
   - `UDF_CHAR1` = Tempo Estimado
   - `UDF_CHAR2` = Tempo Gasto
   - Formato string com vírgula decimal ("4,5")
   - Conversão: `REPLACE(campo, ',', '.')`

5. **EXEC_TAG Sistema**:
   - Formato: `AUTO_YYYYMMDD_HHMMSS`
   - Padrão discreto: últimos 4 dígitos + " -->"
   - Validação SQL robusta com janela temporal

#### 🔧 Correções da Pendência
- **Endpoint `/automation/run`**: Mantido assíncrono (202) + polling
- **Endpoint `/automation/run-sync`**: Novo endpoint síncrono com timeout
- **Validação SQL**: Verificação real de criação de tarefas
- **Retornos Claros**: JSON estruturado com `success`, `tasks_created`, etc.

#### 📊 Métricas de Validação
- **Janela de Busca**: 2 minutos antes até fim da execução
- **Patterns Testados**: Normal e HTML encoded
- **Debug Queries**: Estatísticas para diagnóstico
- **Cache Invalidation**: Automática após sucesso

### 🎯 Próxima Fase 2 - Interface Web Principal
**Planejamento**:
- Página principal focada no chamado vigente
- Exibição de tarefas agrupadas por semana/dia
- Dropdown para semanas anteriores
- Aplicar ciclo mensal (26 → 25)
- Interface TailwindCSS moderna

---

## 🔗 REFERÊNCIAS E LINKS

- **Repositório**: [GerarTarefas1.0](https://github.com/wilscot/GerarTarefas1.0)
- **Servidor SQL**: S0680.ms - Servicedesk_2022
- **API Docs**: `API_AUTOMATION_GUIDE.md`
- **Logs**: `app/logs/automation.log`

**Última Atualização**: 21/08/2025 - Fase 1 Concluída ✅
