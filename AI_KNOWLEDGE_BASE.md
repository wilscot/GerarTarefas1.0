# AI_KNOWLEDGE_BASE - ServiceDesk Automation System

## SYSTEM_OVERVIEW
Purpose: Flask automation system for ServiceDesk task creation and productivity tracking
Environment: Windows PowerShell SQL_Server Python_3.13.3
Stack: Flask + SQL_Server + Selenium + Cache_TTL + HTML_JavaScript
Owner_ID: 2007
Owner_Name: Willian Francischini

## AI_DIRECTIVES
1. BACKUP_POLICY: Always save previous version before component removal or recreation
2. COMMUNICATION_POLICY: Never assume intentions. Ask explicit questions when uncertain
3. EXECUTION_PHASES: Divide tasks into small sequential phases
4. AUTHORIZATION_REQUIRED: Do not edit create or alter without explicit permission
5. DATABASE_REFERENCE: Always consult DATABASE_DICTIONARY.md before data interactions
6. HISTORY_MAINTENANCE: Update this knowledge base with completed tasks and pending items
7. SCOPE_CONTROL: Never add extra functionality without request
8. TECHNICAL_CLARITY: Always specify which files were altered and describe effects
9. SECURITY: Never expose credentials. Use environment variables
10. EXECUTION_LIMITS: Never execute multiple parallel actions without authorization

## CORE_BUSINESS_RULES
WorkOrder_Management:
- Owner_ID: 2007 (FIXED - never change)
- Title_Pattern: "CSI EAST - Datacenter - Execução de Tarefas"
- Policy: One active WorkOrder per owner at a time
- Work_Cycle: Day 26 previous month to Day 25 current month

Task_System:
- Source: Banco_Tarefas.csv (VMware infrastructure tasks)
- Selection_Algorithm: Intelligent selection to meet exact hour targets
- Critical_Fields: UDF_CHAR1 (estimated_time) UDF_CHAR2 (spent_time) UDF_PICK1 (complexity)
- EXEC_TAG_Format: AUTO_YYYYMMDD_HHMMSS
- EXEC_TAG_Detection: Last 4 digits + " -->" or " --&gt;" (HTML encoded)

Selenium_Automation:
- Modes: Asynchronous (recommended) Synchronous
- Timeout: 5 minutes per operation
- Detection_Method: Search for EXEC_TAG in HTML encoded format
- Profile_Persistence: Maintains Edge login between executions

Cache_System:
- Default_TTL: 15 minutes
- Persistence: JSON files in data/cache/
- Types: Calendar_Cache (999min disabled) User_Tasks_Cache (2min) Execution_Cache (15min)

Productivity_Calendar:
- Period: Day 26 previous month to Day 25 current month
- Date_Logic: ACTUALENDTIME if exists and > 0 else CREATEDDATE
- Exclusions: Holidays and absences via exclusions.json
- Refresh_Method: Manual button only (auto-refresh disabled due to corruption)

## DATABASE_SCHEMA
Server: S0680.ms
Database: Servicedesk_2022
Connection: Windows Authentication
Driver: ODBC Driver 17 for SQL Server

Table_WorkOrder:
- WORKORDERID bigint (primary key)
- TITLE nvarchar ("CSI EAST - Datacenter - Execução de Tarefas")
- REQUESTERID bigint (2007 - use this not OWNERID)
- CREATEDBYID bigint
- CREATEDTIME bigint (milliseconds timestamp)
- DESCRIPTION ntext
- DEPTID bigint
- SITEID bigint
- TEMPLATEID bigint
- MODEID int
- SLAID int

Table_TaskDetails:
- TASKID bigint (primary key)
- TITLE nvarchar
- CREATEDDATE bigint (milliseconds timestamp)
- ACTUALENDTIME bigint (priority for productivity calculation)

Table_Task_Fields:
- TASKID bigint (foreign key)
- UDF_CHAR1 nvarchar (estimated_time format "X,XX")
- UDF_CHAR2 nvarchar (spent_time format "X,XX")
- UDF_PICK1 bigint (complexity_id)

Table_UDF_PickListValues:
- PickListID bigint
- VALUE nvarchar (complexity label)
- TABLENAME nvarchar ("Task_Fields")
- COLUMNNAME nvarchar ("UDF_PICK1")

Complexity_Mapping:
- 9910: "1 - Baixa"
- 9911: "2 - Média"
- 9912: "3 - Alta"

Table_TaskDescription:
- TASKID bigint (foreign key)
- DESCRIPTION ntext (HTML with EXEC_TAG)

Table_WorkOrderToTaskDetails:
- WORKORDERID bigint (foreign key)
- TASKID bigint (foreign key)

Table_WorkOrderStates:
- WORKORDERID bigint (foreign key)
- OWNERID bigint (current responsible)
- ASSIGNEDTIME bigint (assignment timestamp)

## CRITICAL_DATABASE_DISCOVERIES
REQUESTERID_vs_OWNERID:
- WorkOrder.REQUESTERID: Original ticket owner
- WorkOrderStates.OWNERID: Current responsible (can change)
- Rule: Always use REQUESTERID = 2007

Timestamp_Format:
- Format: Milliseconds since Unix epoch (1970-01-01)
- Conversion_Python: int(datetime.timestamp() * 1000)
- Conversion_SQL: DATEADD(SECOND, timestamp / 1000, '1970-01-01')

HTML_Encoding:
- Issue: ServiceDesk converts ">" to "&gt;" in descriptions
- EXEC_TAG_Search: Must search both "-->" and "--&gt;" patterns

UDF_Fields:
- UDF_CHAR1: Estimated time
- UDF_CHAR2: Spent time
- Format: String with comma decimal ("4,5")
- Conversion: REPLACE(field, ',', '.')

## FLASK_APPLICATION_STRUCTURE
app/
├── app.py (main Flask application)
├── models/
│   ├── database.py (SQL Server connection with fallback)
│   ├── workorder.py (WorkOrder model)
│   └── cache.py (TTL cache system)
├── services/
│   ├── selenium_service.py (web automation)
│   ├── calendar_service.py (calendar data)
│   ├── workorder_service.py (WorkOrder operations)
│   └── *_cache_service.py (cache services)
├── routes/
│   ├── automation.py (automation API)
│   ├── calendar.py (calendar API)
│   ├── workorders.py (WorkOrder API)
│   └── status.py (monitoring)
└── templates/
    └── index.html (main dashboard)

## FLASK_CONFIGURATION
WORKORDER_TITLE: "CSI EAST - Datacenter - Execução de Tarefas"
OWNER_ID: 2007
CACHE_TTL_MINUTES: 15
SELENIUM_TIMEOUT_MINUTES: 5
TIMEZONE: "America/Campo_Grande"

Cache_TTL_by_Service:
- Calendar: 999 minutes (disabled)
- User_Tasks: 2 minutes
- Execution: 15 minutes (default)

## API_ENDPOINTS
Automation:
- POST /automation/run (asynchronous mode)
- POST /automation/run-sync (synchronous mode)
- GET /automation/result/{id} (polling result)

Calendar:
- GET /calendar/data (current period data)
- POST /calendar/refresh (manual refresh with force=true)

WorkOrders:
- GET /workorders/current (active WorkOrder)
- POST /workorders/create (create new WorkOrder)

Status:
- GET /status/sql (SQL connection status)
- GET /status/cache (cache status)

## KEY_SQL_QUERIES
Consolidated_Query:
```sql
SELECT DISTINCT
    wo.WORKORDERID, wo.TITLE AS WorkOrderTitle, wo.REQUESTERID AS OwnerID,
    wo.CREATEDTIME AS WorkOrderCreatedTime, td.TASKID, td.TITLE AS TaskTitle,
    td.CREATEDDATE AS TaskCreatedDate, td.ACTUALENDTIME,
    CASE 
        WHEN td.ACTUALENDTIME IS NOT NULL AND td.ACTUALENDTIME > 0 
        THEN td.ACTUALENDTIME 
        ELSE td.CREATEDDATE 
    END AS DataFinalCalculada,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
    plv.VALUE AS Complexidade, tdesc.DESCRIPTION AS TaskDescription
FROM dbo.WorkOrder wo
JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.WORKORDERID = wo.WORKORDERID
JOIN dbo.TaskDetails td ON td.TASKID = wttd.TASKID
LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
LEFT JOIN dbo.UDF_PickListValues plv ON plv.PickListID = tf.UDF_PICK1 
    AND plv.TABLENAME = 'Task_Fields' AND plv.COLUMNNAME = 'UDF_PICK1'
LEFT JOIN dbo.TaskDescription tdesc ON tdesc.TASKID = td.TASKID
WHERE wo.WORKORDERID = ?
ORDER BY DataFinalCalculada DESC
```

Productivity_by_Period:
```sql
WITH PeriodTasks AS (
    SELECT td.TASKID, td.TITLE,
        TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
        CONVERT(date, DATEADD(SECOND, 
            CASE 
                WHEN td.ACTUALENDTIME IS NOT NULL AND td.ACTUALENDTIME > 0 
                THEN td.ACTUALENDTIME 
                ELSE td.CREATEDDATE 
            END / 1000, '1970-01-01')) AS DataTarefa
    FROM dbo.TaskDetails td
    JOIN dbo.WorkOrderToTaskDetails wttd ON td.TASKID = wttd.TASKID
    JOIN dbo.WorkOrder wo ON wo.WORKORDERID = wttd.WORKORDERID
    LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
    WHERE wo.REQUESTERID = 2007 
      AND wo.TITLE = 'CSI EAST - Datacenter - Execução de Tarefas'
      AND CONVERT(date, DATEADD(SECOND, 
          CASE 
              WHEN td.ACTUALENDTIME IS NOT NULL AND td.ACTUALENDTIME > 0 
              THEN td.ACTUALENDTIME 
              ELSE td.CREATEDDATE 
          END / 1000, '1970-01-01')) BETWEEN ? AND ?
)
SELECT DataTarefa, SUM(ISNULL(TempoGasto, 0)) AS TotalHoras, COUNT(*) AS TotalTarefas,
       STRING_AGG(CONCAT(TASKID, ': ', LEFT(TITLE, 50)), '; ') AS TarefasResumo
FROM PeriodTasks
GROUP BY DataTarefa
ORDER BY DataTarefa DESC
```

EXEC_TAG_Validation:
```sql
SELECT DISTINCT
    td.TASKID, td.TITLE AS TaskTitle,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
    TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
    td.CREATEDDATE, tdesc.DESCRIPTION
FROM dbo.TaskDetails td
JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.TASKID = td.TASKID
LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
LEFT JOIN dbo.TaskDescription tdesc ON tdesc.TASKID = td.TASKID
WHERE wttd.WORKORDERID = ?
  AND td.CREATEDDATE >= ?
  AND td.CREATEDDATE <= ?
  AND (tdesc.DESCRIPTION LIKE ? OR tdesc.DESCRIPTION LIKE ?)
```

## TASK_SELECTION_ALGORITHM
1. Read CSV of available tasks
2. Apply complexity filters
3. Use dynamic programming for optimal combination
4. Automatically adjust times if necessary
5. Generate unique EXEC_TAG based on timestamp

## TASK_DETECTION_ALGORITHM
1. Generate EXEC_TAG: AUTO_YYYYMMDD_HHMMSS
2. Extract discrete pattern: last 4 digits + " -->"
3. Search both normal and HTML encoded patterns
4. Query within 2-minute window before execution start to execution end
5. Validate success: existence of at least 1 task with EXEC_TAG

## PRODUCTIVITY_CALCULATION
Date_Logic: ACTUALENDTIME if exists and > 0 else CREATEDDATE
Conversion: timestamp / 1000 to get seconds since Unix epoch
Period: Day 26 previous month to Day 25 current month
Exclusions: Apply holidays and absences from exclusions.json

## KNOWN_ISSUES_RESOLVED
Cache_Corruption:
- Problem: Calendar cache cleared by UserTasksCacheService
- Solution: Removed clear_all() from UserTasksCacheService init
- Status: Fixed

Auto_Refresh_Corruption:
- Problem: Auto-refresh overwrote valid data with empty results
- Solution: TTL changed from 3 to 999 minutes + manual button
- Status: Fixed

HTML_Encoding_EXEC_TAG:
- Problem: EXEC_TAG stored as "--&gt;" in database
- Solution: Dual detection (normal + HTML encoded)
- Status: Fixed

File_Redundancy:
- Problem: run.py and start_app.py duplicated
- Solution: run.py deleted
- Status: Fixed

## DEVELOPMENT_COMMANDS
Start_Application:
```powershell
python start_app.py
```

API_Testing:
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/automation/run" -Method Post -ContentType "application/json" -Body '{"hours_target": 8.0}'
Invoke-RestMethod -Uri "http://127.0.0.1:5000/automation/result/$($response.execution_id)"
Invoke-RestMethod -Uri "http://127.0.0.1:5000/calendar/refresh" -Method Post -ContentType "application/json" -Body '{"force_refresh": true}'
```

Database_Debug:
```powershell
python debug_task_detection.py
python examine_task_tables.py
```

## CODING_STANDARDS
Logging: Always use logger = logging.getLogger(__name__)
Timestamps: Convert milliseconds to datetime properly
Cache: Validate TTL before expensive operations
SQL: Use prepared statements for security
Error_Handling: Capture and log specific exceptions

## DEBUGGING_GUIDELINES
Cache_Files: data/cache/ are readable JSON
Logs: logs/app.log shows complete flow
EXEC_TAG: Always ends with " -->" or " --&gt;"
SQL_Queries: Can be tested in SSMS
Terminal_Output: Shows automation progress

## DEVELOPMENT_PHASES
Phase_1_Complete: Foundation and core logic
- SQL Server connection with fallback
- TTL cache system with persistence
- Asynchronous/synchronous Selenium automation
- Interactive productivity calendar
- Modern web interface with manual refresh
- Code redundancy elimination

Phase_2_Planned: Advanced productivity reports
Phase_3_Planned: Microsoft Teams integration
Phase_4_Planned: Real-time metrics dashboard
Phase_5_Planned: Automatic configuration backup

## CRITICAL_CONSTANTS
OWNER_ID: 2007 (never change)
EXEC_TAG_PATTERN: AUTO_YYYYMMDD_HHMMSS
WORKORDER_TITLE: "CSI EAST - Datacenter - Execução de Tarefas"
PERIOD_START_DAY: 26
PERIOD_END_DAY: 25
CACHE_MANUAL_ONLY: true (auto-refresh disabled)
WINDOWS_AUTH_REQUIRED: true

## FILE_REFERENCES
Essential_Files:
- app/app.py (main configurations and routes)
- app/models/database.py (SQL connection with fallback)
- app/services/selenium_service.py (core automation)
- DATABASE_DICTIONARY.md (complete database structure)
- API_AUTOMATION_GUIDE.md (API usage guide)

Mandatory_Tests_Before_Deploy:
1. Verify SQL Server connection
2. Test automation with 1 task
3. Validate manual calendar cache
4. Confirm EXEC_TAG detection
5. Test APIs via PowerShell/Postman

Last_Updated: 2025-08-25
Version: 1.2_AI_Optimized
Status: Complete_Phase_1_with_AI_Directives
