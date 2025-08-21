# 🚀 API de Automação - ServiceDesk Tarefas

## 📌 Visão Geral

A API oferece **dois modos** de execução da automação Selenium:

1. **Assíncrono** (`/automation/run`) - Retorna imediatamente com `execution_id` para polling
2. **Síncrono** (`/automation/run-sync`) - Aguarda conclusão e retorna resultado final

---

## 🔄 Modo Assíncrono (Recomendado)

### 1. Iniciar Automação
```http
POST /automation/run
Content-Type: application/json

{
    "hours_target": 8.0,
    "workorder_id": 540030  // opcional - usa chamado vigente se omitido
}
```

**Resposta (202 Accepted):**
```json
{
    "execution_id": "a1b2c3d4-e5f6-...",
    "workorder_id": 540030,
    "hours_target": 8.0,
    "exec_tag": "AUTO_20250821_131945",
    "status": "started",
    "started_at": "2025-08-21T13:19:45.123456",
    "message": "Automação iniciada. Use GET /automation/result/{execution_id} para verificar se tarefas foram criadas.",
    "polling_url": "/automation/result/a1b2c3d4-e5f6-..."
}
```

### 2. Verificar Resultado (Polling)
```http
GET /automation/result/{execution_id}
```

**Resposta durante execução (202 Accepted):**
```json
{
    "execution_id": "a1b2c3d4-e5f6-...",
    "status": "running",
    "summary": {
        "success": null,
        "tasks_created": null,
        "total_hours_logged": null,
        "message": "Automação em andamento... (status: running)"
    }
}
```

**Resposta de sucesso (200 OK):**
```json
{
    "execution_id": "a1b2c3d4-e5f6-...",
    "workorder_id": 540030,
    "hours_target": 8.0,
    "exec_tag": "AUTO_20250821_131945",
    "status": "success",
    "started_at": "2025-08-21T13:19:45.123456",
    "finished_at": "2025-08-21T13:22:03.789012",
    "created_task_ids": [
        {
            "task_id": 12345,
            "title": "Análise de Sistema",
            "time_spent": 2.5,
            "time_estimated": 3.0
        },
        {
            "task_id": 12346,
            "title": "Desenvolvimento Backend",
            "time_spent": 4.0,
            "time_estimated": 4.0
        }
    ],
    "summary": {
        "success": true,
        "tasks_created": 2,
        "total_hours_logged": 6.5,
        "message": "Automação concluída com sucesso! 2 tarefas criadas, 6.50h registradas."
    }
}
```

**Resposta de falha (206 Partial Content ou 500 Error):**
```json
{
    "execution_id": "a1b2c3d4-e5f6-...",
    "status": "no_tasks_detected",
    "error": null,
    "created_task_ids": [],
    "summary": {
        "success": false,
        "tasks_created": 0,
        "total_hours_logged": 0,
        "message": "Automação executada mas nenhuma tarefa foi criada. Verifique os logs para mais detalhes."
    }
}
```

---

## ⚡ Modo Síncrono (Simplicidade)

### Execução Completa
```http
POST /automation/run-sync
Content-Type: application/json

{
    "hours_target": 8.0,
    "workorder_id": 540030,  // opcional
    "timeout": 300           // opcional, padrão 300s (5min)
}
```

**Resposta de sucesso (200 OK):**
```json
{
    "success": true,
    "execution_id": "a1b2c3d4-e5f6-...",
    "workorder_id": 540030,
    "hours_target": 8.0,
    "tasks_created": 2,
    "total_hours_logged": 6.5,
    "created_task_ids": [
        {
            "task_id": 12345,
            "title": "Análise de Sistema",
            "time_spent": 2.5,
            "time_estimated": 3.0
        }
    ],
    "message": "Automação concluída com sucesso! 2 tarefas criadas, 6.50h registradas.",
    "execution_time": 138.45
}
```

**Resposta de falha (400 Bad Request):**
```json
{
    "success": false,
    "execution_id": "a1b2c3d4-e5f6-...",
    "workorder_id": 540030,
    "hours_target": 8.0,
    "tasks_created": 0,
    "total_hours_logged": 0,
    "status": "no_tasks_detected",
    "message": "Automação executada mas falhou ou não criou tarefas. Verifique os logs.",
    "execution_time": 95.23
}
```

**Resposta de timeout (408 Request Timeout):**
```json
{
    "success": false,
    "execution_id": "a1b2c3d4-e5f6-...",
    "error": "Timeout de 300s atingido",
    "status": "timeout",
    "message": "Automação não completou dentro de 300s. Use GET /automation/result/{execution_id} para verificar posteriormente.",
    "execution_time": 300
}
```

---

## 🎯 Validação Real de Sucesso

### ✅ Critérios de Sucesso
A API **só retorna sucesso** quando:

1. ✅ Script Selenium executou sem erro (exit code 0)
2. ✅ Tarefas foram **realmente criadas** no SQL Server
3. ✅ EXEC_TAG foi encontrado nas descrições das tarefas
4. ✅ Retorna os `task_id`s das tarefas criadas

### ❌ Critérios de Falha
A API retorna falha quando:

- ❌ Script Selenium falhou (exit code != 0)
- ❌ Nenhuma tarefa foi criada no banco de dados
- ❌ EXEC_TAG não foi encontrado nas descrições
- ❌ Erro de validação nos parâmetros
- ❌ Chamado não existe ou não é válido para automação

---

## 🔍 Status Possíveis

| Status | Descrição | HTTP Code |
|--------|-----------|-----------|
| `started` | Automação iniciada | 202 |
| `running` | Executando script Selenium | 202 |
| `success` | ✅ Tarefas criadas com sucesso | 200 |
| `no_tasks_detected` | ❌ Executou mas não criou tarefas | 206 |
| `error` | ❌ Erro durante execução | 500 |
| `timeout` | ❌ Timeout atingido (só sync) | 408 |
| `not_found` | ❌ Execution ID inválido | 404 |

---

## 📋 Exemplo de Uso Completo

```javascript
// 1. Iniciar automação (async)
const response = await fetch('/automation/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hours_target: 8.0 })
});

const { execution_id } = await response.json();

// 2. Polling para resultado
let result;
do {
    await new Promise(resolve => setTimeout(resolve, 2000)); // 2s
    const pollResponse = await fetch(`/automation/result/${execution_id}`);
    result = await pollResponse.json();
} while (result.status === 'started' || result.status === 'running');

// 3. Verificar sucesso
if (result.summary.success) {
    console.log(`✅ ${result.summary.tasks_created} tarefas criadas!`);
    console.log(`⏰ Total: ${result.summary.total_hours_logged}h registradas`);
} else {
    console.log(`❌ Falha: ${result.summary.message}`);
}
```

---

## 🚨 Importante

- **Use sempre os endpoints para verificação real** - não confie apenas no exit code do Selenium
- **O modo assíncrono é recomendado** para interfaces que podem fazer polling
- **O modo síncrono é ideal** para scripts ou integrações simples
- **Sempre verifique os logs** em caso de falha para diagnóstico detalhado
- **Cache é invalidado automaticamente** após criação bem-sucedida de tarefas
