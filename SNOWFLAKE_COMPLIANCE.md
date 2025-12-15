# Snowflake Compliance Verification

The SQL Processor tool now includes comprehensive Snowflake compliance verification to ensure all generated DDL and DML statements follow Snowflake documentation standards.

## Reference Documentation

All SQL statements are validated against the official Snowflake documentation:
**https://docs.snowflake.com/en/**

## Compliance Features

### 1. Evaluator Verification

The evaluator now **mandatorily checks** that all generated SQL statements are Snowflake-compliant. It will reject work if:

- SQL syntax is not compliant with Snowflake documentation
- Uses non-Snowflake data types or syntax
- Uses unsupported features (traditional indexes, certain CHECK constraints, etc.)
- Does not follow Snowflake-specific DDL/DML patterns
- Uses database-specific features not available in Snowflake
- Missing Snowflake-specific syntax (CREATE OR REPLACE, IF NOT EXISTS, etc.)
- Improper use of Snowflake identifiers (case sensitivity, quoting)
- Uses unsupported SQL functions or operations

### 2. Worker Instructions

The worker is instructed to:

- Use Snowflake-specific data types (VARCHAR, NUMBER, TIMESTAMP_NTZ, TIMESTAMP_LTZ, TIMESTAMP_TZ, BOOLEAN, etc.)
- Use Snowflake-specific functions and syntax
- Follow Snowflake naming conventions (case-sensitive identifiers when quoted)
- Use Snowflake-specific DDL syntax (CREATE OR REPLACE, IF NOT EXISTS, etc.)
- Use Snowflake-specific DML syntax (MERGE, COPY INTO, etc.)
- Avoid unsupported features (CHECK constraints in some contexts, traditional indexes, etc.)
- Use proper Snowflake schema and database references

### 3. Validation Tool

A new `validate_snowflake_syntax` tool is available that:

- Checks for unsupported Snowflake features
- Identifies potential issues and warnings
- Detects good Snowflake practices
- Provides detailed validation feedback

### 4. Generated File Headers

All generated DDL and DML files now include:

- **Snowflake Compliance Notes** section
- Reference to Snowflake documentation URL
- Validation status for each statement
- Snowflake-specific execution instructions
- Notes about Snowflake architecture compatibility

### 5. Statement-Level Comments

Each SQL statement includes:

- Snowflake compliance verification status
- Validation notes and warnings
- Reference to Snowflake documentation
- Notes about Snowflake-specific syntax used

## Validation Checks

The tool checks for:

### ❌ Unsupported Features
- Traditional `CREATE INDEX` (Snowflake uses automatic clustering)
- `AUTO_INCREMENT` (should be `AUTOINCREMENT` in Snowflake)

### ⚠️ Warnings
- `CHECK` constraints (may have limitations in Snowflake)

### ✅ Good Practices Detected
- `CREATE OR REPLACE` syntax
- `IF NOT EXISTS` clauses
- Snowflake timestamp types (TIMESTAMP_NTZ, TIMESTAMP_LTZ, TIMESTAMP_TZ)
- Snowflake data types (VARCHAR, NUMBER, BOOLEAN)
- `AUTOINCREMENT` (correct Snowflake syntax)

## Example Output

Generated files will include comments like:

```sql
-- ==========================================
-- SNOWFLAKE COMPLIANCE: Verified
-- ==========================================
-- Snowflake Documentation: https://docs.snowflake.com/en/
-- ✓ SNOWFLAKE COMPLIANT
-- Statement appears to follow Snowflake documentation standards.
-- ==========================================
```

## Success Criteria

The default success criteria now includes:

> "CRITICAL: All SQL statements must be compliant with Snowflake documentation at https://docs.snowflake.com/en/. Files must be ready for execution in Snowflake and audit."

## How It Works

1. **Worker** processes SQL files and applies banking nomenclature
2. **Validation Tool** checks each statement against Snowflake standards
3. **Comments Added** to each statement with validation results
4. **Evaluator** verifies Snowflake compliance before accepting work
5. **Files Generated** with comprehensive Snowflake compliance documentation

## Benefits

- ✅ Ensures all SQL is executable in Snowflake
- ✅ Prevents syntax errors and compatibility issues
- ✅ Documents Snowflake-specific features used
- ✅ Provides audit trail for compliance
- ✅ References official Snowflake documentation
- ✅ Catches unsupported features before execution

## References

- [Snowflake Documentation](https://docs.snowflake.com/en/)
- [Snowflake SQL Data Types](https://docs.snowflake.com/en/sql-reference/data-types.html)
- [Snowflake SQL Commands](https://docs.snowflake.com/en/sql-reference/sql-commands.html)
- [Snowflake SQL Functions](https://docs.snowflake.com/en/sql-reference/functions.html)

