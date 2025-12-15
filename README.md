# SQL Files Bank - LangGraph-Based SQL Processor for Banking Data Warehouses

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-green.svg)](https://github.com/langchain-ai/langgraph)

A sophisticated **multi-agent AI system** built with LangGraph that automatically processes SQL files for banking data warehouses. The tool applies banking nomenclature conventions, validates Snowflake compliance, and generates production-ready DDL and DML files with comprehensive banking controls and audit comments.

## 🎯 Value Proposition

### For Banking Data Teams
- **Compliance First**: Ensures all SQL statements comply with Snowflake documentation standards
- **Audit Ready**: Generates files with comprehensive audit trails and banking controls
- **Time Savings**: Automates manual SQL file processing and separation
- **Consistency**: Applies standardized banking nomenclature across all SQL files
- **Risk Reduction**: Validates syntax and compliance before execution

### For Data Engineers
- **Automated Processing**: Intelligent parsing and separation of DDL/DML statements
- **Snowflake Optimized**: Built specifically for Snowflake data warehouse platform
- **Production Ready**: Generated files are immediately executable with proper documentation
- **Extensible**: Modular architecture allows easy customization and extension

### For Compliance Teams
- **Regulatory Compliance**: Banking-specific controls and documentation
- **Traceability**: Complete audit trail with timestamps and source tracking
- **Standards Enforcement**: Automatic application of banking nomenclature conventions
- **Documentation**: Comprehensive comments for regulatory reviews

## ✨ Key Features

### 🔄 Multi-Agent Architecture
- **Worker-Evaluator Pattern**: Self-correcting workflow that iterates until success criteria is met
- **Tool Integration**: Seamless integration with file operations and SQL processing tools
- **Memory Checkpointing**: Maintains conversation state across interactions

### 🏦 Banking-Specific Features
- **Nomenclature Application**: Automatically applies banking data warehouse naming conventions
- **Layer Prefixes**: Supports `stg_`, `dim_`, `fct_`, `dw_`, `dm_`, `src_` prefixes
- **Subject Areas**: Handles customer, account, transaction, and risk domains
- **Compliance Controls**: Banking-specific audit and compliance documentation

### ❄️ Snowflake Compliance
- **Syntax Validation**: Validates all SQL against [Snowflake documentation](https://docs.snowflake.com/en/)
- **Data Type Checking**: Ensures Snowflake-specific data types (VARCHAR, NUMBER, TIMESTAMP_NTZ, etc.)
- **Feature Detection**: Identifies unsupported features and suggests alternatives
- **Best Practices**: Enforces Snowflake-specific patterns (CREATE OR REPLACE, IF NOT EXISTS, etc.)

### 📊 SQL Processing
- **Intelligent Parsing**: Separates SQL into DDL and DML statements while preserving comments
- **File Generation**: Creates separate, well-documented DDL and DML files
- **Comment Preservation**: Maintains all original SQL comments
- **Error Handling**: Graceful error handling with informative messages

### 🖥️ User Interface
- **Gradio Web Interface**: Interactive web-based UI for easy access
- **Real-time Processing**: See results as they're generated
- **Conversation History**: Maintains context across multiple requests
- **Success Criteria**: Customizable success criteria for different use cases

## 🏗️ Architecture

The system uses a **LangGraph workflow** with three main components:

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   Worker    │────▶│    Tools    │
│   (LLM)     │◀────│  (Execute)  │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ Evaluator   │
│  (Validate) │
└──────┬──────┘
       │
       ├─ Success? ──▶ END
       │
       └─ Continue ──▶ Worker (loop)
```

### Components

1. **Worker Node**: Processes requests using LLM with access to SQL processing tools
2. **Tools Node**: Executes file operations, SQL parsing, and file generation
3. **Evaluator Node**: Validates results against success criteria and Snowflake compliance

## 📁 Project Structure

```
sqlfilesbank/
│
├── 📄 Core Application Files
│   ├── sql_processor.py           # Main LangGraph processor class
│   ├── sql_processor_tools.py     # SQL processing tools and utilities
│   └── sql_processor_app.py       # Gradio web interface
│
├── 📚 Documentation
│   ├── README.md                  # This file - project overview
│   ├── README_SQL_PROCESSOR.md    # Detailed usage guide
│   ├── CODE_DOCUMENTATION.md      # Comprehensive code documentation
│   ├── SNOWFLAKE_COMPLIANCE.md    # Snowflake compliance details
│   └── activate_instructions.md   # Virtual environment setup
│
├── 📂 Data Directories
│   ├── sqlfiles/                  # Input SQL files directory
│   │   ├── wealthmgmt_sql_ddl.txt
│   │   ├── wealthmgmt_sql_ddl_DDL.sql    # Generated DDL
│   │   └── wealthmgmt_sql_ddl_DML.sql    # Generated DML
│   │
│   └── bankingnomenclature/       # Banking nomenclature reference
│       └── naming_conventions.txt
│
├── 🔧 Configuration & Setup
│   ├── requirements.txt           # Python dependencies
│   ├── setup_venv.bat            # Windows virtual environment setup
│   ├── .gitignore                # Git ignore rules
│   └── .env                       # Environment variables (create this)
│
└── 🐍 Virtual Environment
    └── venv/                      # Python virtual environment (gitignored)
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **OpenAI API Key** (for LLM functionality)
- **Git** (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alokhcst/sqlfilesbank.git
   cd sqlfilesbank
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Application

```bash
python sql_processor_app.py
```

This will launch the Gradio web interface at `http://127.0.0.1:7860`

## 💻 Usage

### Basic Usage

1. **Start the application** (see Quick Start above)

2. **Enter your request** in the message box:
   ```
   Process SQL file at C:\Users\alokh\projects\sqlfilesbank\sqlfiles\wealthmgmt_sql_ddl.txt 
   using nomenclature at C:\Users\alokh\projects\sqlfilesbank\bankingnomenclature\naming_conventions.txt
   ```

3. **Optional**: Specify custom success criteria

4. **Click "Process SQL"** or press Enter

5. **Review results**: The tool will generate separate DDL and DML files with banking controls

### Generated Output

The tool generates two files:

- **`{filename}_DDL.sql`**: All Data Definition Language statements
  - CREATE, ALTER, DROP statements
  - Schema and database definitions
  - Views, procedures, functions
  - Grants and permissions

- **`{filename}_DML.sql`**: All Data Manipulation Language statements
  - INSERT, UPDATE, DELETE statements
  - SELECT queries
  - Stored procedure calls

Both files include:
- ✅ Comprehensive header comments
- ✅ Banking control notes
- ✅ Snowflake compliance verification
- ✅ Audit trail information
- ✅ Execution instructions
- ✅ Compliance documentation

## 🔍 Example Workflow

### Input
```
SQL File: sqlfiles/wealthmgmt_sql_ddl.txt
Nomenclature: bankingnomenclature/naming_conventions.txt
```

### Processing Steps
1. **Read Files**: Loads SQL and nomenclature files
2. **Parse SQL**: Separates statements into DDL and DML
3. **Apply Nomenclature**: Applies banking naming conventions
4. **Validate Snowflake**: Checks compliance with Snowflake standards
5. **Generate Files**: Creates separate DDL and DML files with comments

### Output
```
✅ wealthmgmt_sql_ddl_DDL.sql (with banking controls)
✅ wealthmgmt_sql_ddl_DML.sql (with banking controls)
```

## 🎓 Key Concepts

### Banking Nomenclature
The tool applies standard banking data warehouse naming conventions:
- **Layer Prefixes**: `stg_` (staging), `dim_` (dimension), `fct_` (fact), `dw_` (data warehouse)
- **Subject Areas**: Customer (`cust`), Accounts (`acct`), Transactions (`txn`), Risk (`risk`)
- **Naming Patterns**: Consistent table, column, and schema naming

### Snowflake Compliance
All generated SQL is validated against [Snowflake documentation](https://docs.snowflake.com/en/):
- ✅ Uses Snowflake-specific data types
- ✅ Follows Snowflake DDL/DML patterns
- ✅ Avoids unsupported features
- ✅ Implements Snowflake best practices

### Worker-Evaluator Pattern
The system uses an iterative approach:
1. **Worker** attempts to complete the task
2. **Evaluator** checks if success criteria is met
3. **Feedback Loop** continues until success or user input needed

## 📊 Use Cases

### 1. SQL File Migration
Migrate SQL files from other databases to Snowflake with automatic compliance checking

### 2. Banking Data Warehouse Setup
Process existing SQL files and apply banking nomenclature standards

### 3. Compliance Documentation
Generate audit-ready SQL files with comprehensive documentation

### 4. Code Review Preparation
Separate DDL and DML statements for easier code review and deployment

### 5. Standardization
Apply consistent naming conventions across multiple SQL files

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:
```env
OPENAI_API_KEY=your_api_key_here
```

### Customization

- **Success Criteria**: Define custom success criteria for different use cases
- **Output Directory**: Specify custom output directories for generated files
- **Nomenclature Rules**: Modify `bankingnomenclature/naming_conventions.txt` for custom rules

## 📖 Documentation

- **[README_SQL_PROCESSOR.md](README_SQL_PROCESSOR.md)**: Detailed usage guide
- **[CODE_DOCUMENTATION.md](CODE_DOCUMENTATION.md)**: Comprehensive code documentation
- **[SNOWFLAKE_COMPLIANCE.md](SNOWFLAKE_COMPLIANCE.md)**: Snowflake compliance details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Uses [LangChain](https://github.com/langchain-ai/langchain) for LLM integration
- [Gradio](https://gradio.app/) for the web interface
- Snowflake documentation: https://docs.snowflake.com/en/

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🗺️ Roadmap

- [ ] Support for additional database platforms
- [ ] Batch processing of multiple SQL files
- [ ] Custom nomenclature rule engine
- [ ] Integration with CI/CD pipelines
- [ ] Advanced Snowflake optimization suggestions
- [ ] Support for stored procedures and functions parsing

---

**Made with ❤️ for banking data teams**

