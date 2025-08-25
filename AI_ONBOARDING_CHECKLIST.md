# AI_ONBOARDING_CHECKLIST - ServiceDesk Automation System

## MANDATORY_READING_PHASE
- [ ] Read AI_KNOWLEDGE_BASE.md completely (required)
- [ ] Read DATABASE_DICTIONARY.md for database structure (pure database schema only)
- [ ] Read API_AUTOMATION_GUIDE.md for endpoint documentation
- [ ] Memorize all 10 AI_DIRECTIVES from knowledge base
- [ ] Identify critical constants: OWNER_ID=2007, EXEC_TAG_FORMAT, WORKORDER_TITLE

## ENVIRONMENT_RECONNAISSANCE
- [ ] Explore app/ directory structure
- [ ] Verify data/cache/ directory exists
- [ ] Check logs/app.log accessibility
- [ ] Locate start_app.py startup file
- [ ] Confirm Banco_Tarefas.csv presence (task source)

## TECHNICAL_VALIDATION
- [ ] Test SQL Server connectivity to S0680.ms
- [ ] Validate database Servicedesk_2022 accessibility
- [ ] Check core table structure: WorkOrder, TaskDetails, Task_Fields
- [ ] Verify REQUESTERID=2007 in WorkOrder queries
- [ ] Understand EXEC_TAG format: AUTO_YYYYMMDD_HHMMSS

## SYSTEM_CONSTANTS_VERIFICATION
- [ ] OWNER_ID: 2007 (never change)
- [ ] WORKORDER_TITLE: "CSI EAST - Datacenter - Execução de Tarefas"
- [ ] PERIOD_CYCLE: 26th previous month to 25th current month
- [ ] CACHE_TTL: Calendar=999min(disabled), UserTasks=2min, Execution=15min
- [ ] SELENIUM_TIMEOUT: 5 minutes

## DATABASE_CRITICAL_DISCOVERIES
- [ ] Use REQUESTERID not OWNERID in WorkOrder queries
- [ ] Timestamps are milliseconds since Unix epoch
- [ ] HTML encoding converts ">" to "&gt;" in descriptions
- [ ] UDF fields use comma decimal format ("4,5" not "4.5")
- [ ] EXEC_TAG detection requires both "-->" and "--&gt;" patterns

## COMMUNICATION_PROTOCOL
- [ ] Never assume intentions - ask explicit questions
- [ ] Confirm task understanding before execution
- [ ] Alert immediately about any inconsistencies
- [ ] Request authorization before any file modifications
- [ ] Provide specific file paths when reporting changes

## PRE_EXECUTION_REQUIREMENTS
- [ ] Backup existing files before modifications
- [ ] Consult DATABASE_DICTIONARY.md before data operations
- [ ] Update BASE_DE_CONHECIMENTO.md with completed tasks
- [ ] Verify SQL connection before database operations
- [ ] Check cache status before expensive operations

## TESTING_VALIDATION
- [ ] SQL Server connection test
- [ ] Single task automation test
- [ ] Manual calendar cache refresh test
- [ ] EXEC_TAG detection verification
- [ ] API endpoints test via PowerShell

## DEVELOPMENT_ENVIRONMENT
- [ ] Windows PowerShell environment confirmed
- [ ] Python 3.13.3 confirmed
- [ ] Flask application structure understood
- [ ] Selenium WebDriver configuration verified
- [ ] Windows Authentication for SQL Server confirmed

## SECURITY_COMPLIANCE
- [ ] No credentials exposure in code
- [ ] Environment variables usage confirmed
- [ ] Prepared statements for SQL queries
- [ ] Proper error handling implementation
- [ ] Logging configuration verified

## TASK_EXECUTION_PROTOCOL
- [ ] Divide complex tasks into sequential phases
- [ ] Execute only authorized phases
- [ ] Wait for validation between phases
- [ ] Document changes in knowledge base
- [ ] Specify affected files clearly

## EMERGENCY_PROTOCOLS
- [ ] Stop execution on contradictory instructions
- [ ] Alert user about impossible operations
- [ ] Never execute parallel actions without authorization
- [ ] Maintain data integrity at all costs
- [ ] Report system inconsistencies immediately

## SUCCESS_CRITERIA
All checkboxes completed = AI ready for task execution
Any failed checkbox = Request user assistance before proceeding
Critical constants memorized = Safe to begin development work
Communication protocol understood = Ready for user interaction

## FINAL_CONFIRMATION_REQUIRED
Before any task execution, AI must explicitly state:
"I have completed the onboarding checklist. I understand the system architecture, critical constants, database structure, and communication protocols. I am ready to execute [specific task] following the established directives. Please confirm authorization to proceed."
