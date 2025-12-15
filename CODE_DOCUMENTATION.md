# Code Documentation

This document provides comprehensive documentation for all classes and functions in the SQL Processor codebase.

## Architecture Overview

The SQL Processor uses a **LangGraph workflow** with a **worker-evaluator pattern**:

1. **Worker Node**: Processes requests using LLM with tools
2. **Tools Node**: Executes SQL processing operations
3. **Evaluator Node**: Validates results against success criteria
4. **Routing**: Determines next step based on tool calls and evaluation

---

## File: `sql_processor.py`

### Classes

#### `State` (TypedDict)
State dictionary for the LangGraph workflow.

**Purpose**: Defines the structure of state that flows through graph nodes, maintaining conversation history, success criteria, feedback, and workflow control flags.

**Attributes**:
- `messages`: List of conversation messages (annotated with add_messages for LangGraph)
- `success_criteria`: String describing what constitutes successful completion
- `feedback_on_work`: Optional feedback from evaluator on previous attempts
- `success_criteria_met`: Boolean flag indicating if success criteria has been achieved
- `user_input_needed`: Boolean flag indicating if user clarification is required

---

#### `EvaluatorOutput` (BaseModel)
Structured output model for the evaluator LLM.

**Purpose**: Provides structured feedback on whether the worker's response meets success criteria and if user input is needed.

**Attributes**:
- `feedback`: Detailed feedback on the assistant's response
- `success_criteria_met`: Whether the success criteria have been met
- `user_input_needed`: True if more input is needed from the user, clarifications, or if assistant is stuck

---

#### `SQLProcessor` (Class)
Main SQL Processor class implementing LangGraph workflow.

**Purpose**: Orchestrates processing of SQL files for banking data warehouses using a worker-evaluator pattern. Reads SQL files, applies banking nomenclature, validates Snowflake compliance, and generates separate DDL and DML files.

**Workflow**:
1. Worker node processes the request using LLM with tools
2. Tools execute (read files, parse SQL, generate output files)
3. Evaluator node checks if success criteria is met
4. Loop continues until criteria met or user input needed

**Attributes**:
- `worker_llm_with_tools`: LLM instance bound with SQL processing tools
- `evaluator_llm_with_output`: LLM instance with structured output for evaluation
- `tools`: List of available tools for SQL processing
- `graph`: Compiled LangGraph workflow
- `processor_id`: Unique identifier for this processor instance
- `memory`: MemorySaver for checkpointing conversation state

**Methods**:

##### `__init__(self)`
Initialize SQLProcessor instance. Creates a new processor with unique ID and memory checkpointing. Call `setup()` after initialization.

##### `async setup(self)`
Initialize and configure the SQL processor. Sets up LLM instances, loads tools, and builds the LangGraph workflow. Must be called before using the processor.

##### `worker(self, state: State) -> Dict[str, Any]`
Worker node that processes user requests using LLM and tools.

**What it does**:
- Constructs system prompts with task instructions and success criteria
- Invokes the LLM with access to SQL processing tools
- Handles feedback from previous evaluation attempts
- Returns LLM response for routing to tools or evaluator

**Instructions to worker**:
- Read SQL and nomenclature files
- Parse SQL into DDL/DML
- Apply banking nomenclature
- Ensure Snowflake compliance
- Generate separate DDL/DML files with banking controls

##### `worker_router(self, state: State) -> str`
Route worker output to either tools or evaluator. Checks if the last message contains tool calls. Returns `"tools"` if tool calls present, `"evaluator"` otherwise.

##### `format_conversation(self, messages: List[Any]) -> str`
Format conversation messages into readable text string. Converts list of message objects into formatted string showing conversation history.

##### `evaluator(self, state: State) -> State`
Evaluator node that checks if success criteria has been met.

**What it does**:
- Reviews worker's response against success criteria
- Verifies Snowflake compliance of generated SQL
- Checks if banking nomenclature was applied
- Determines if user input is needed
- Provides structured feedback

**CRITICAL**: Must verify that all SQL statements comply with Snowflake documentation.

##### `route_based_on_evaluation(self, state: State) -> str`
Route based on evaluation results. Returns `"END"` if success criteria met OR user input needed, otherwise `"worker"` to continue processing.

##### `async build_graph(self)`
Build and compile the LangGraph workflow.

**Graph Structure**:
- **Nodes**: worker, tools, evaluator
- **Flow**: START → worker → (tools or evaluator)
- **Loops**: tools → worker, evaluator → worker (if not complete)

Uses memory checkpointing to maintain conversation state.

##### `async run_superstep(self, message, success_criteria, history)`
Execute one processing step through the LangGraph workflow. Invokes the graph with user message and success criteria, formats results into conversation history.

**Returns**: Updated conversation history with user message, assistant reply, and evaluator feedback

##### `cleanup(self)`
Cleanup resources when processor is no longer needed. Placeholder for future resource cleanup.

---

## File: `sql_processor_tools.py`

### Functions

#### `read_sql_file(sql_file_path: str) -> str`
Read SQL file from relative or absolute path. Checks if file exists and returns status message with content length.

**Returns**: Success message with file path and content length, or error message

---

#### `read_banking_nomenclature(nomenclature_path: str) -> str`
Read banking nomenclature file from relative or absolute path. Checks if file exists and returns status message.

**Returns**: Success message with file path and content length, or error message

---

#### `get_sql_file_content(sql_file_path: str) -> str`
Get the actual content of SQL file for processing. Returns raw file content as string.

**Returns**: File content as string, or error message if file not found

---

#### `get_nomenclature_content(nomenclature_path: str) -> str`
Get the actual content of nomenclature file for processing. Returns raw file content as string.

**Returns**: File content as string, or error message if file not found

---

#### `parse_sql_statements(sql_content: str) -> Dict[str, List[str]]`
Parse SQL content into DDL and DML statements.

**What it does**:
- Splits SQL by semicolons
- Preserves comments (line and block)
- Classifies statements as DDL or DML based on keywords
- Handles edge cases (comments, multi-line statements)

**DDL Keywords**: CREATE, ALTER, DROP, TRUNCATE, RENAME, GRANT, REVOKE, COMMENT, INDEX, VIEW, PROCEDURE, FUNCTION, TRIGGER, SCHEMA, DATABASE, USE DATABASE, USE SCHEMA

**DML Keywords**: INSERT, UPDATE, DELETE, MERGE, UPSERT, SELECT, CALL, EXEC, EXECUTE

**Returns**: Dictionary with `'ddl'` and `'dml'` keys containing lists of statements

---

#### `validate_snowflake_syntax(sql_statement: str) -> str`
Validate SQL statement against Snowflake documentation standards.

**What it checks**:
- Unsupported features (CREATE INDEX, AUTO_INCREMENT)
- Warnings (CHECK constraints)
- Good practices (CREATE OR REPLACE, IF NOT EXISTS, Snowflake data types)

**Returns**: Validation message with compliance status, issues, warnings, and good practices detected

**Reference**: https://docs.snowflake.com/en/

---

#### `apply_banking_nomenclature(sql_statement: str, nomenclature: str) -> str`
Apply banking nomenclature rules to SQL statement.

**What it does**:
- Extracts subject areas from nomenclature (cust, acct, txn, risk)
- Validates Snowflake syntax
- Adds comprehensive comments including:
  - Banking control notes
  - Audit trail information
  - Snowflake compliance verification
  - Timestamp and source tracking

**Returns**: SQL statement with banking nomenclature comments prepended

---

#### `generate_ddl_file(sql_file_path, ddl_statements, nomenclature, output_dir=None) -> str`
Generate a DDL file with banking controls and comments.

**What it does**:
- Creates output filename: `{original_name}_DDL.sql`
- Generates comprehensive header with:
  - Banking compliance notes
  - Snowflake compliance notes
  - Execution instructions
  - Audit trail information
- Applies banking nomenclature to each statement
- Writes file to disk

**Returns**: Success message with file path, or error message

---

#### `generate_dml_file(sql_file_path, dml_statements, nomenclature, output_dir=None) -> str`
Generate a DML file with banking controls and comments.

**What it does**:
- Creates output filename: `{original_name}_DML.sql`
- Generates comprehensive header with:
  - Banking compliance notes
  - Snowflake compliance notes
  - Execution instructions
  - Transaction handling notes
- Applies banking nomenclature to each statement
- Writes file to disk

**Returns**: Success message with file path, or error message

---

#### `_process_sql_file_impl(sql_file_path, nomenclature_path, output_dir=None) -> str`
Internal implementation of complete SQL processing workflow.

**What it does**:
1. Reads SQL file content
2. Reads nomenclature file content
3. Parses SQL into DDL and DML
4. Generates separate DDL and DML files
5. Returns processing summary

**Returns**: Summary string with processing results and file paths

---

### Classes

#### `ProcessSQLFileInput` (BaseModel)
Pydantic schema for process_sql_file tool input validation.

**Purpose**: Defines required and optional parameters for the process_sql_file StructuredTool, ensuring type safety and validation.

**Attributes**:
- `sql_file_path`: Relative or absolute path to the SQL file to process (required)
- `nomenclature_path`: Relative or absolute path to the banking nomenclature file (required)
- `output_dir`: Optional output directory for generated DDL and DML files

---

#### `process_sql_file(sql_file_path, nomenclature_path, output_dir=None) -> str`
Public wrapper function for complete SQL processing.

**Purpose**: Provides clean interface for StructuredTool, delegates to `_process_sql_file_impl`.

**Returns**: Summary of processing results

---

#### `get_file_tools() -> List[Tool]`
Get file management tools from LangChain toolkit.

**Returns**: List of Tool objects for file management operations (read, write, list files, etc.)

---

#### `async sql_processor_tools() -> List[Tool]`
Get all SQL processor tools.

**Returns**: List of all available tools including:
- `read_sql_file`: Read SQL file from path
- `read_banking_nomenclature`: Read nomenclature file
- `process_sql_file`: Complete SQL processing (StructuredTool)
- `get_sql_content`: Get SQL file content
- `get_nomenclature_content`: Get nomenclature content
- `validate_snowflake_syntax`: Validate Snowflake compliance
- File management tools (read, write, list, etc.)

---

## File: `sql_processor_app.py`

### Functions

#### `async setup() -> SQLProcessor`
Initialize SQL processor for Gradio interface.

**Purpose**: Creates and sets up a new SQLProcessor instance when Gradio interface loads.

**Returns**: Initialized SQLProcessor instance

---

#### `async process_message(processor, message, success_criteria, history) -> Tuple[List[Dict], SQLProcessor]`
Process a user message through the SQL processor workflow.

**What it does**:
1. Normalizes conversation history format (converts tuples to dicts)
2. Runs the processor workflow with user message
3. Formats results for Gradio Chatbot component
4. Ensures all messages have 'role' and 'content' keys

**Returns**: Tuple of (formatted_results, processor) where formatted_results is a list of message dicts

---

#### `async reset() -> Tuple[str, str, None, SQLProcessor]`
Reset the SQL processor and clear conversation.

**Purpose**: Creates a new SQLProcessor instance and clears UI inputs when user clicks Reset.

**Returns**: Tuple of empty strings and None values to clear UI components, plus new processor

---

#### `free_resources(processor) -> None`
Cleanup function called when processor state is deleted.

**Purpose**: Ensures proper cleanup of resources when Gradio interface is closed or processor is reset. Called automatically by Gradio's State component delete_callback.

---

## Workflow Diagram

```
START
  ↓
worker (LLM with tools)
  ↓
  ├─→ Has tool calls? → tools → worker (loop)
  └─→ No tool calls? → evaluator
                        ↓
                        ├─→ Success met OR user input needed? → END
                        └─→ Not complete? → worker (loop)
```

## Key Features

1. **Banking Nomenclature**: Applies banking data warehouse naming conventions
2. **Snowflake Compliance**: Validates all SQL against Snowflake documentation
3. **DDL/DML Separation**: Automatically separates and generates separate files
4. **Audit Trail**: Comprehensive comments for compliance and auditing
5. **Error Handling**: Graceful error handling with informative messages
6. **Memory Checkpointing**: Maintains conversation state across interactions

## Usage Flow

1. User provides SQL file path and nomenclature path
2. Worker reads files and processes SQL
3. Tools parse SQL, apply nomenclature, validate Snowflake compliance
4. Tools generate DDL and DML files with banking controls
5. Evaluator verifies success criteria and Snowflake compliance
6. Process repeats until success or user input needed

