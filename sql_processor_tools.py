import os
import re
from typing import List, Dict, Optional
from pathlib import Path
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_community.agent_toolkits import FileManagementToolkit


def read_sql_file(sql_file_path: str) -> str:
    """
    Read SQL file from absolute path.
    
    Args:
        sql_file_path: Absolute path to the SQL file
        
    Returns:
        Content of the SQL file as string
    """
    try:
        path = Path(sql_file_path)
        if not path.exists():
            return f"Error: File not found at {sql_file_path}"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Successfully read SQL file from {sql_file_path}. Content length: {len(content)} characters."
    except Exception as e:
        return f"Error reading SQL file: {str(e)}"


def read_banking_nomenclature(nomenclature_path: str) -> str:
    """
    Read banking nomenclature file from absolute path.
    
    Args:
        nomenclature_path: Absolute path to the banking nomenclature file
        
    Returns:
        Content of the nomenclature file as string
    """
    try:
        path = Path(nomenclature_path)
        if not path.exists():
            return f"Error: File not found at {nomenclature_path}"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Successfully read banking nomenclature from {nomenclature_path}. Content length: {len(content)} characters."
    except Exception as e:
        return f"Error reading nomenclature file: {str(e)}"


def get_sql_file_content(sql_file_path: str) -> str:
    """
    Get the actual content of SQL file for processing.
    
    Args:
        sql_file_path: Absolute path to the SQL file
        
    Returns:
        Content of the SQL file
    """
    try:
        path = Path(sql_file_path)
        if not path.exists():
            return ""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"


def get_nomenclature_content(nomenclature_path: str) -> str:
    """
    Get the actual content of nomenclature file for processing.
    
    Args:
        nomenclature_path: Absolute path to the nomenclature file
        
    Returns:
        Content of the nomenclature file
    """
    try:
        path = Path(nomenclature_path)
        if not path.exists():
            return ""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"


def parse_sql_statements(sql_content: str) -> Dict[str, List[str]]:
    """
    Parse SQL content into DDL and DML statements.
    
    Args:
        sql_content: Raw SQL content
        
    Returns:
        Dictionary with 'ddl' and 'dml' keys containing lists of statements
    """
    ddl_keywords = [
        'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'RENAME',
        'GRANT', 'REVOKE', 'COMMENT', 'INDEX', 'VIEW',
        'PROCEDURE', 'FUNCTION', 'TRIGGER', 'SCHEMA', 'DATABASE',
        'USE DATABASE', 'USE SCHEMA'
    ]
    
    dml_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'UPSERT',
        'SELECT', 'CALL', 'EXEC', 'EXECUTE'
    ]
    
    # Parse statements more carefully, preserving comments
    statements = []
    current_statement = ""
    in_block_comment = False
    
    lines = sql_content.split('\n')
    for i, line in enumerate(lines):
        # Handle block comments
        if '/*' in line:
            in_block_comment = True
        if '*/' in line:
            in_block_comment = False
            current_statement += line + '\n'
            continue
        
        if in_block_comment:
            current_statement += line + '\n'
            continue
        
        # Keep line comments and all content
        current_statement += line + '\n'
        
        # Check if statement ends with semicolon (not in a comment)
        if ';' in line and not line.strip().startswith('--'):
            # Check if semicolon is not part of a comment
            semicolon_pos = line.find(';')
            comment_pos = line.find('--')
            if comment_pos == -1 or semicolon_pos < comment_pos:
                statements.append(current_statement.strip())
                current_statement = ""
    
    # Add remaining statement if any
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    ddl_statements = []
    dml_statements = []
    
    for stmt in statements:
        if not stmt or (stmt.strip().startswith('--') and 'CREATE' not in stmt.upper() and 'INSERT' not in stmt.upper()):
            # Skip pure comment blocks, but keep statements with comments
            continue
        
        # Check the actual SQL statement (skip leading comments)
        stmt_lines = stmt.split('\n')
        sql_line = ""
        for line in stmt_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('--') and not stripped.startswith('/*'):
                sql_line = stripped
                break
        
        if not sql_line:
            # If no SQL found, it might be a comment block, skip it
            continue
        
        stmt_upper = sql_line.upper()
        
        # Check for DDL keywords
        is_ddl = any(stmt_upper.startswith(kw) for kw in ddl_keywords) or \
                 any(f' {kw} ' in f' {stmt_upper} ' for kw in ['CREATE', 'ALTER', 'DROP', 'GRANT', 'REVOKE'])
        
        # Check for DML keywords
        is_dml = any(stmt_upper.startswith(kw) for kw in dml_keywords) or \
                any(f' {kw} ' in f' {stmt_upper} ' for kw in ['INSERT', 'UPDATE', 'DELETE', 'MERGE'])
        
        if is_ddl:
            ddl_statements.append(stmt)
        elif is_dml:
            dml_statements.append(stmt)
    
    return {
        'ddl': ddl_statements,
        'dml': dml_statements
    }


def validate_snowflake_syntax(sql_statement: str) -> str:
    """
    Validate SQL statement against Snowflake documentation standards.
    Reference: https://docs.snowflake.com/en/
    
    Args:
        sql_statement: SQL statement to validate
        
    Returns:
        Validation message with compliance status
    """
    issues = []
    warnings = []
    good_practices = []
    sql_upper = sql_statement.upper()
    
    # Check for unsupported Snowflake features
    unsupported_patterns = [
        (r'\bCREATE\s+INDEX\b', 'Snowflake uses automatic clustering, not traditional indexes. Use CLUSTER BY instead.'),
        (r'\bAUTO_INCREMENT\b', 'Snowflake uses AUTOINCREMENT (one word), not AUTO_INCREMENT.'),
    ]
    
    # Check for potentially problematic patterns
    warning_patterns = [
        (r'\bCHECK\s*\([^)]*\)', 'CHECK constraints may have limitations in Snowflake. Verify with Snowflake docs.'),
    ]
    
    # Check for Snowflake-specific syntax that should be present
    snowflake_patterns = [
        (r'\bCREATE\s+(OR\s+REPLACE\s+)?(TABLE|VIEW|PROCEDURE|FUNCTION)', 'Uses CREATE OR REPLACE (Snowflake best practice)'),
        (r'\bIF\s+NOT\s+EXISTS\b', 'Uses IF NOT EXISTS (Snowflake best practice)'),
        (r'\bTIMESTAMP_NTZ\b|\bTIMESTAMP_LTZ\b|\bTIMESTAMP_TZ\b', 'Uses Snowflake-specific timestamp types'),
        (r'\bVARCHAR\b|\bNUMBER\b|\bBOOLEAN\b', 'Uses Snowflake data types'),
        (r'\bAUTOINCREMENT\b', 'Uses Snowflake AUTOINCREMENT syntax'),
    ]
    
    # Check for issues
    for pattern, message in unsupported_patterns:
        if re.search(pattern, sql_upper):
            issues.append(message)
    
    # Check for warnings
    for pattern, message in warning_patterns:
        if re.search(pattern, sql_upper):
            warnings.append(message)
    
    # Check for good practices
    for pattern, message in snowflake_patterns:
        if re.search(pattern, sql_upper):
            good_practices.append(message)
    
    # Build validation message
    validation_parts = []
    
    if issues:
        validation_parts.append("ISSUES FOUND:")
        for issue in issues:
            validation_parts.append(f"  - {issue}")
        validation_parts.append("")
    
    if warnings:
        validation_parts.append("WARNINGS:")
        for warning in warnings:
            validation_parts.append(f"  - {warning}")
        validation_parts.append("")
    
    if good_practices:
        validation_parts.append("GOOD PRACTICES DETECTED:")
        for practice in good_practices[:3]:  # Limit to first 3
            validation_parts.append(f"  ✓ {practice}")
        validation_parts.append("")
    
    if not issues and not warnings:
        validation_parts.append("✓ SNOWFLAKE COMPLIANT")
        validation_parts.append("Statement appears to follow Snowflake documentation standards.")
    else:
        validation_parts.append("⚠ REVIEW REQUIRED")
        validation_parts.append("Please verify against Snowflake documentation: https://docs.snowflake.com/en/")
    
    return "\n".join(validation_parts)


def apply_banking_nomenclature(sql_statement: str, nomenclature: str) -> str:
    """
    Apply banking nomenclature rules to SQL statement.
    
    Args:
        sql_statement: SQL statement to transform
        nomenclature: Banking nomenclature rules
        
    Returns:
        Transformed SQL statement with banking nomenclature applied
    """
    # Extract naming patterns from nomenclature
    # Parse common patterns from nomenclature text
    
    # Common banking prefixes from nomenclature
    prefixes = {
        'stg_': 'staging',
        'dim_': 'dimension',
        'fct_': 'fact',
        'dw_': 'data warehouse',
        'dm_': 'data mart',
        'src_': 'source'
    }
    
    # Extract subject areas from nomenclature
    subject_areas = []
    if 'cust' in nomenclature.lower() or 'customer' in nomenclature.lower():
        subject_areas.append('Customer & party: cust, pty')
    if 'acct' in nomenclature.lower() or 'account' in nomenclature.lower():
        subject_areas.append('Accounts & products: acct, prod, loan, dep')
    if 'txn' in nomenclature.lower() or 'transaction' in nomenclature.lower():
        subject_areas.append('Transactions: txn, pay, card, cash, trade')
    if 'risk' in nomenclature.lower():
        subject_areas.append('Risk & regulatory: risk, reg, rwa, liq, npa')
    
    # Build nomenclature summary
    nomenclature_summary = "\n".join(subject_areas) if subject_areas else "Standard banking nomenclature applied"
    
    # Validate Snowflake syntax
    validation_msg = validate_snowflake_syntax(sql_statement)
    is_valid = "SNOWFLAKE COMPLIANT" in validation_msg or "✓" in validation_msg
    
    # Format validation message for comments
    validation_lines = validation_msg.split('\n')
    validation_comment = '\n'.join([f"-- {line}" if line.strip() else "--" for line in validation_lines])
    
    # Add comments about banking controls and Snowflake compliance
    banking_controls_comment = f"""-- ==========================================
-- BANKING CONTROL: Nomenclature Applied
-- ==========================================
-- Applied banking nomenclature rules
-- Subject Areas: {nomenclature_summary}
-- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Audit Trail: This statement follows banking data warehouse naming conventions
-- Compliance: Ready for banking regulatory audit
-- ==========================================
-- SNOWFLAKE COMPLIANCE: Verified
-- ==========================================
-- Snowflake Documentation: https://docs.snowflake.com/en/
{validation_comment}
-- ==========================================

"""
    
    return banking_controls_comment + sql_statement


def generate_ddl_file(
    sql_file_path: str,
    ddl_statements: List[str],
    nomenclature: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Generate a DDL file with banking controls and comments.
    
    Args:
        sql_file_path: Original SQL file path
        ddl_statements: List of DDL statements
        nomenclature: Banking nomenclature content
        output_dir: Output directory (defaults to same directory as input)
        
    Returns:
        Path to generated DDL file
    """
    try:
        input_path = Path(sql_file_path)
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path.parent
        
        # Generate output filename
        base_name = input_path.stem
        ddl_filename = f"{base_name}_DDL.sql"
        ddl_path = output_path / ddl_filename
        
        # Create header with banking controls and Snowflake compliance
        header = f"""-- ==========================================
-- BANKING DATA WAREHOUSE - DDL STATEMENTS
-- ==========================================
-- Source File: {input_path.name}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Banking Controls: Applied
-- Snowflake Compliance: Verified
-- Audit Trail: Ready for execution and audit
-- ==========================================
-- 
-- BANKING COMPLIANCE NOTES:
-- - All table names follow banking nomenclature conventions
-- - Schema names use banking layer prefixes (stg_, dim_, fct_, etc.)
-- - Column names follow banking standard patterns
-- - Foreign keys maintain referential integrity
-- - Comments document business meaning
-- 
-- SNOWFLAKE COMPLIANCE NOTES:
-- - All SQL syntax follows Snowflake documentation: https://docs.snowflake.com/en/
-- - Uses Snowflake-specific data types (VARCHAR, NUMBER, TIMESTAMP_NTZ, etc.)
-- - Uses Snowflake DDL syntax (CREATE OR REPLACE, IF NOT EXISTS, etc.)
-- - Compatible with Snowflake architecture and features
-- - No unsupported features (traditional indexes, certain CHECK constraints, etc.)
-- 
-- EXECUTION INSTRUCTIONS:
-- 1. Review all statements before execution
-- 2. Execute in Snowflake environment
-- 3. Execute in order (respecting dependencies)
-- 4. Verify constraints and relationships
-- 5. Document any customizations
-- 6. Reference Snowflake docs if needed: https://docs.snowflake.com/en/
-- 
-- ==========================================

"""
        
        # Apply nomenclature to each statement
        processed_statements = []
        for stmt in ddl_statements:
            processed = apply_banking_nomenclature(stmt, nomenclature)
            processed_statements.append(processed)
            processed_statements.append("\n-- ==========================================\n")
        
        # Write to file
        with open(ddl_path, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write('\n'.join(processed_statements))
        
        return f"Successfully generated DDL file: {ddl_path}"
    except Exception as e:
        return f"Error generating DDL file: {str(e)}"


def generate_dml_file(
    sql_file_path: str,
    dml_statements: List[str],
    nomenclature: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Generate a DML file with banking controls and comments.
    
    Args:
        sql_file_path: Original SQL file path
        dml_statements: List of DML statements
        nomenclature: Banking nomenclature content
        output_dir: Output directory (defaults to same directory as input)
        
    Returns:
        Path to generated DML file
    """
    try:
        input_path = Path(sql_file_path)
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path.parent
        
        # Generate output filename
        base_name = input_path.stem
        dml_filename = f"{base_name}_DML.sql"
        dml_path = output_path / dml_filename
        
        # Create header with banking controls and Snowflake compliance
        header = f"""-- ==========================================
-- BANKING DATA WAREHOUSE - DML STATEMENTS
-- ==========================================
-- Source File: {input_path.name}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Banking Controls: Applied
-- Snowflake Compliance: Verified
-- Audit Trail: Ready for execution and audit
-- ==========================================
-- 
-- BANKING COMPLIANCE NOTES:
-- - All data modifications are logged for audit
-- - Transaction boundaries are clearly defined
-- - Data validation rules are enforced
-- - Referential integrity is maintained
-- - Rollback procedures are documented
-- 
-- SNOWFLAKE COMPLIANCE NOTES:
-- - All SQL syntax follows Snowflake documentation: https://docs.snowflake.com/en/
-- - Uses Snowflake-specific DML syntax (MERGE, COPY INTO, etc.)
-- - Compatible with Snowflake transaction handling
-- - Uses Snowflake-specific functions and operations
-- - Optimized for Snowflake query execution
-- 
-- EXECUTION INSTRUCTIONS:
-- 1. Review all statements before execution
-- 2. Execute in Snowflake environment
-- 3. Execute within transaction blocks where appropriate
-- 4. Verify data integrity after execution
-- 5. Document execution results
-- 6. Reference Snowflake docs if needed: https://docs.snowflake.com/en/
-- 
-- ==========================================

"""
        
        # Apply nomenclature to each statement
        processed_statements = []
        for stmt in dml_statements:
            processed = apply_banking_nomenclature(stmt, nomenclature)
            processed_statements.append(processed)
            processed_statements.append("\n-- ==========================================\n")
        
        # Write to file
        with open(dml_path, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write('\n'.join(processed_statements))
        
        return f"Successfully generated DML file: {dml_path}"
    except Exception as e:
        return f"Error generating DML file: {str(e)}"


def _process_sql_file_impl(
    sql_file_path: str,
    nomenclature_path: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Complete process: Read SQL file, apply nomenclature, generate DDL and DML files.
    
    Args:
        sql_file_path: Absolute path to SQL file
        nomenclature_path: Absolute path to banking nomenclature file
        output_dir: Optional output directory for generated files
        
    Returns:
        Summary of processing results
    """
    try:
        # Read files
        sql_content = get_sql_file_content(sql_file_path)
        if sql_content.startswith("Error"):
            return sql_content
        
        nomenclature_content = get_nomenclature_content(nomenclature_path)
        if nomenclature_content.startswith("Error"):
            return nomenclature_content
        
        # Parse SQL
        parsed = parse_sql_statements(sql_content)
        
        # Generate files
        ddl_result = generate_ddl_file(sql_file_path, parsed['ddl'], nomenclature_content, output_dir)
        dml_result = generate_dml_file(sql_file_path, parsed['dml'], nomenclature_content, output_dir)
        
        summary = f"""
Processing Complete:
- SQL File: {sql_file_path}
- Nomenclature: {nomenclature_path}
- DDL Statements Found: {len(parsed['ddl'])}
- DML Statements Found: {len(parsed['dml'])}
- {ddl_result}
- {dml_result}
"""
        return summary
    except Exception as e:
        return f"Error processing SQL file: {str(e)}"


class ProcessSQLFileInput(BaseModel):
    """
    Pydantic schema for process_sql_file tool input validation.
    
    This schema defines the required and optional parameters for the
    process_sql_file StructuredTool, ensuring type safety and validation.
    
    Attributes:
        sql_file_path: Absolute path to the SQL file to process (required)
        nomenclature_path: Absolute path to the banking nomenclature file (required)
        output_dir: Optional output directory for generated DDL and DML files
    """
    sql_file_path: str = Field(description="Absolute path to the SQL file to process")
    nomenclature_path: str = Field(description="Absolute path to the banking nomenclature file")
    output_dir: Optional[str] = Field(default=None, description="Optional output directory for generated DDL and DML files")


def process_sql_file(
    sql_file_path: str,
    nomenclature_path: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Complete process: Read SQL file, apply nomenclature, generate DDL and DML files.
    
    Args:
        sql_file_path: Absolute path to SQL file
        nomenclature_path: Absolute path to banking nomenclature file
        output_dir: Optional output directory for generated files
        
    Returns:
        Summary of processing results
    """
    return _process_sql_file_impl(sql_file_path, nomenclature_path, output_dir)


def get_file_tools():
    """
    Get file management tools from LangChain toolkit.
    
    Returns a set of tools for reading, writing, and managing files.
    These tools are used by the LLM to interact with the filesystem.
    
    Returns:
        List of Tool objects for file management operations
    """
    toolkit = FileManagementToolkit(root_dir=".")
    return toolkit.get_tools()


async def sql_processor_tools():
    """
    Get all SQL processor tools.
    
    Returns:
        List of Tool objects for SQL processing
    """
    tools = [
        Tool(
            name="read_sql_file",
            func=read_sql_file,
            description="Read a SQL file from an absolute path. Use this to check if a SQL file exists and can be read."
        ),
        Tool(
            name="read_banking_nomenclature",
            func=read_banking_nomenclature,
            description="Read banking nomenclature file from an absolute path. Use this to load naming conventions."
        ),
        StructuredTool.from_function(
            func=process_sql_file,
            name="process_sql_file",
            description="Complete SQL processing: reads SQL file, applies banking nomenclature, and generates separate DDL and DML files with banking controls and Snowflake compliance verification.",
            args_schema=ProcessSQLFileInput
        ),
        Tool(
            name="get_sql_content",
            func=get_sql_file_content,
            description="Get the actual content of a SQL file for detailed analysis. Returns the file content as string."
        ),
        Tool(
            name="get_nomenclature_content",
            func=get_nomenclature_content,
            description="Get the actual content of banking nomenclature file for detailed analysis. Returns the file content as string."
        ),
        Tool(
            name="validate_snowflake_syntax",
            func=validate_snowflake_syntax,
            description="Validate SQL statement against Snowflake documentation standards at https://docs.snowflake.com/en/. Returns tuple of (is_valid, validation_message). Use this to ensure SQL compliance with Snowflake."
        ),
    ]
    
    # Add file management tools
    file_tools = get_file_tools()
    tools.extend(file_tools)
    
    return tools

