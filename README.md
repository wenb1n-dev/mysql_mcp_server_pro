[![简体中文](https://img.shields.io/badge/简体中文-点击查看-orange)](README-zh.md)
[![English](https://img.shields.io/badge/English-Click-yellow)](README.md)

# mcp_mysql_server

## Introduction
mcp_mysql_server_pro is not just about MySQL CRUD operations, but also includes database anomaly analysis capabilities and makes it easy for developers to extend with custom tools.

- Supports both STDIO and SSE modes
- Supports multiple SQL execution, separated by ";"
- Supports querying database table names and fields based on table comments
- Supports SQL execution plan analysis
- Supports Chinese field to pinyin conversion
- Supports table lock analysis
- Supports database health status analysis
- Supports permission control with three roles: readonly, writer, and admin
    ```
    "readonly": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],  # Read-only permissions
    "writer": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE"],  # Read-write permissions
    "admin": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", 
             "CREATE", "ALTER", "DROP", "TRUNCATE"]  # Administrator permissions
    ```
- Supports prompt template invocation

## Tool List
| Tool Name                  | Description                                                                                                                                                                                                              |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| execute_sql                | SQL execution tool that can execute ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"] commands based on permission configuration                            |
| get_chinese_initials       | Convert Chinese field names to pinyin initials                                                                                                                                                                           |
| get_db_health_running      | Analyze MySQL health status (connection status, transaction status, running status, lock status detection)                                                                                                               |
| get_table_desc             | Search for table structures in the database based on table names, supporting multi-table queries                                                                                                                         |
| get_table_index            | Search for table indexes in the database based on table names, supporting multi-table queries                                                                                                                            |
| get_table_lock             | Check if there are row-level locks or table-level locks in the current MySQL server                                                                                                                                      |
| get_table_name             | Search for table names in the database based on table comments and descriptions                                                                                                                                          |
| get_db_health_index_usage  | Get the index usage of the currently connected mysql database, including redundant index situations, poorly performing index situations, and the top 5 unused index situations with query times greater than 30 seconds  | 

## Prompt List
| Prompt Name                | Description                                                                                                                           |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------| 
| analyzing-mysql-prompt    | This is a prompt for analyzing MySQL-related issues                                                                                    |
| query-table-data-prompt   | This is a prompt for querying table data using tools. If description is empty, it will be initialized as a MySQL database query assistant |

## Usage Instructions

### SSE Mode

- Use uv to start the service

Add the following content to your mcp client tools, such as cursor, cline, etc.

mcp json as follows:
```
{
  "mcpServers": {
    "operateMysql": {
      "name": "operateMysql",
      "description": "",
      "isActive": true,
      "baseUrl": "http://localhost:9000/sse"
    }
  }
}
```

Modify the .env file content to update the database connection information with your database details:
```
# MySQL Database Configuration
MYSQL_HOST=192.168.xxx.xxx
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=a_llm
MYSQL_ROLE=readonly  # Optional, default is 'readonly'. Available values: readonly, writer, admin
```

Start commands:
```
# Download dependencies
uv sync

# Start
uv run server.py
```

### STDIO Mode

Add the following content to your mcp client tools, such as cursor, cline, etc.

mcp json as follows:
```
{
  "mcpServers": {
      "operateMysql": {
        "isActive": true,
        "name": "operateMysql",
        "command": "uv",
        "args": [
          "--directory",
          "G:\\python\\mysql_mcp\\src",  # Replace this with your project path
          "run",
          "server.py",
          "--stdio"
        ],
        "env": {
          "MYSQL_HOST": "192.168.xxx.xxx",
          "MYSQL_PORT": "3306",
          "MYSQL_USER": "root",
          "MYSQL_PASSWORD": "root",
          "MYSQL_DATABASE": "a_llm",
          "MYSQL_ROLE": "readonly"  # Optional, default is 'readonly'. Available values: readonly, writer, admin
       }
    }
  }
}    
```

## Custom Tool Extensions
1. Add a new tool class in the handles package, inherit from BaseHandler, and implement get_tool_description and run_tool methods

2. Import the new tool in __init__.py to make it available in the server

## Examples
1. Create a new table and insert data, prompt format as follows:
```
# Task
   Create an organizational structure table with the following structure: department name, department number, parent department, is valid.
# Requirements
 - Table name: t_admin_rms_zzjg
 - Field requirements: string type uses 'varchar(255)', integer type uses 'int', float type uses 'float', date and time type uses 'datetime', boolean type uses 'boolean', text type uses 'text', large text type uses 'longtext', large integer type uses 'bigint', large float type uses 'double'
 - Table header needs to include primary key field, serial number XH varchar(255)
 - Table must include these fixed fields at the end: creator-CJR varchar(50), creation time-CJSJ datetime, modifier-XGR varchar(50), modification time-XGSJ datetime
 - Field naming should use tool return content
 - Common fields need indexes
 - Each field needs comments, table needs comment
 - Generate 5 real data records after creation
```

2. Query data based on table comments, prompt as follows:
```
Query Zhang San's data from the user information table
```

3. Analyze slow SQL, prompt as follows:
```
select * from t_jcsjzx_hjkq_cd_xsz_sk xsz
left join t_jcsjzx_hjkq_jcd jcd on jcd.cddm = xsz.cddm 
Based on current index situation, review execution plan and provide optimization suggestions in markdown format, including table index status, execution details, and optimization recommendations
```

4. Analyze SQL deadlock issues, prompt as follows:
```
update t_admin_rms_zzjg set sfyx = '0' where xh = '1' is stuck, please analyze the cause
```

5. Analyze the health status prompt as follows
```
Check the current health status of MySQL
```