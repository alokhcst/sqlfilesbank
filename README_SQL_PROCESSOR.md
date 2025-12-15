# SQL Processor - Banking Data Warehouse Tool

A LangGraph-based tool that processes SQL files for banking data warehouses, applies banking nomenclature conventions, and generates separate DDL and DML files with comprehensive banking controls and audit comments.

## Features

- **Reads SQL files** from absolute paths
- **Applies banking nomenclature** from reference files
- **Separates SQL statements** into DDL (Data Definition Language) and DML (Data Manipulation Language)
- **Generates separate files** for DDL and DML with banking controls
- **Adds comprehensive comments** including:
  - Banking control notes
  - Audit trail information
  - Execution instructions
  - Compliance notes
- **Ready for execution and audit** - all generated files are production-ready

## Architecture

The tool follows the LangGraph framework pattern from `example_framework`:

- **sql_processor.py**: Main LangGraph application with worker-evaluator pattern
- **sql_processor_tools.py**: Tools for reading files, parsing SQL, and generating output files
- **sql_processor_app.py**: Gradio web interface for interactive use

## Installation

1. Install required dependencies:
```bash
pip install langgraph langchain langchain-openai langchain-community gradio python-dotenv
```

2. Set up environment variables:
Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Running the Application

```bash
python sql_processor_app.py
```

This will launch a Gradio web interface in your browser.

### Using the Tool

1. **Enter your request** in the message box:
   ```
   Process SQL file at C:\Users\alokh\projects\sqlfilesbank\sqlfiles\wealthmgmt_sql_ddl.txt using nomenclature at C:\Users\alokh\projects\sqlfilesbank\bankingnomenclature\naming_conventions.txt
   ```

2. **Optional**: Specify success criteria if you have specific requirements

3. **Click "Process SQL"** or press Enter

4. The tool will:
   - Read the SQL file
   - Read the banking nomenclature file
   - Parse SQL statements into DDL and DML
   - Apply banking nomenclature conventions
   - Generate separate DDL and DML files with banking controls

### Generated Files

The tool generates two files in the same directory as the input SQL file (or in a specified output directory):

- **`{original_filename}_DDL.sql`**: All Data Definition Language statements
  - CREATE, ALTER, DROP statements
  - Schema and database definitions
  - Views, procedures, functions
  - Grants and permissions

- **`{original_filename}_DML.sql`**: All Data Manipulation Language statements
  - INSERT, UPDATE, DELETE statements
  - SELECT queries
  - Stored procedure calls

Both files include:
- Comprehensive header comments
- Banking control notes
- Audit trail information
- Execution instructions
- Compliance notes

## Banking Controls

The generated files include banking-specific controls:

- **Nomenclature Compliance**: All names follow banking data warehouse conventions
- **Audit Trail**: Timestamp and source file tracking
- **Execution Safety**: Clear instructions for safe execution
- **Compliance Notes**: Regulatory and audit requirements documented

## Example

### Input
SQL file at: `C:\Users\alokh\projects\sqlfilesbank\sqlfiles\wealthmgmt_sql_ddl.txt`
Nomenclature at: `C:\Users\alokh\projects\sqlfilesbank\bankingnomenclature\naming_conventions.txt`

### Output
- `wealthmgmt_sql_ddl_DDL.sql` - All DDL statements with banking controls
- `wealthmgmt_sql_ddl_DML.sql` - All DML statements with banking controls

## File Structure

```
sqlfilesbank/
├── sqlfiles/                    # Input SQL files
│   └── wealthmgmt_sql_ddl.txt
├── bankingnomenclature/         # Banking nomenclature reference
│   └── naming_conventions.txt
├── example_framework/           # Reference LangGraph framework
│   ├── app.py
│   ├── sidekick.py
│   └── sidekick_tools.py
├── sql_processor.py            # Main LangGraph application
├── sql_processor_tools.py      # SQL processing tools
└── sql_processor_app.py        # Gradio interface
```

## How It Works

1. **Worker Node**: Uses LLM with tools to process the request
2. **Tool Execution**: Reads files, parses SQL, applies nomenclature, generates files
3. **Evaluator Node**: Checks if success criteria are met
4. **Iteration**: Continues until criteria are met or user input is needed

## Banking Nomenclature

The tool applies banking nomenclature conventions including:

- **Layer Prefixes**: `stg_`, `dim_`, `fct_`, `dw_`, `dm_`, `src_`
- **Subject Areas**: Customer (`cust`), Accounts (`acct`), Transactions (`txn`), Risk (`risk`)
- **Naming Patterns**: Consistent table, column, and schema naming
- **Standards**: Follows banking data warehouse best practices

## Requirements

- Python 3.8+
- OpenAI API key
- Access to SQL files and nomenclature files at absolute paths

## Notes

- The tool preserves all original comments from SQL files
- Generated files are ready for immediate execution
- All changes are documented in audit trail comments
- Files follow banking regulatory compliance standards

