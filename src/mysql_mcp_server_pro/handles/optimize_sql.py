import re
from typing import Dict, Sequence, Any, List

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from mysql_mcp_server_pro.config import get_db_config

from mysql_mcp_server_pro.exception.exceptions import SQLExecutionError
from ..utils.execute_sql_util import ExecuteSqlUtil

execute_sql = ExecuteSqlUtil()

class OptimizeSql(BaseHandler):
    name = "optimize_sql"
    description = (
        "专业的SQL性能优化工具，基于MySQL执行计划、表结构信息、表数据量、表索引提供专家级优化建议。"
        "该工具能够分析SQL语句的执行效率，识别性能瓶颈，并提供具体的优化方案，"
        "包括索引优化、查询重写建议等，帮助提升数据库查询性能。"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要优化的sql"
                    }
                },
                "required": ["text"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            if "text" not in arguments:
                raise ValueError("缺少查询语句")

            text = arguments["text"]

            config = get_db_config()

            tables = self.get_sql_all_tables(text)

            # 查询表的数据量
            table_count = self.get_tables_count(tables, config)

            # 查询表的索引情况
            table_index = self.get_tables_index(tables, config)

            # 获取sql的执行过程
            sql_explain = self.get_sql_execution_process(text, config)

            # 获取表的结构信息
            table_schemas = self.get_tables_schemas(tables, config)

            result = f"""
                        # 角色
                        你是一位世界级的数据库性能优化专家，拥有超过15年的SQL优化经验。你的专长包括：
                        1. 深入理解各种数据库的查询优化器工作原理（MySQL, PostgreSQL, Oracle, SQL Server等）
                        2. 精通执行计划分析和性能瓶颈识别
                        3. 擅长复杂查询重写和索引优化策略
                        4. 熟悉各种数据库特有的优化技巧和最佳实践
                        
                        # 背景
                        你的任务是分析用户提供的SQL语句，并提供专业级的优化建议。以下是相关信息：
                            <数据库类型>
                                mysql
                            </数据库类型>
                            <SQL语句>
                                {text}
                            </SQL语句>
                            <表结构信息>
                                {table_schemas}
                            </表结构信息>
                            <表索引信息>
                                {table_index}
                            </表索引信息>
                            <表数据量信息>
                                {table_count}
                            </表数据量信息>
                            <执行计划>
                                {sql_explain}
                            </执行计划>
                        
                        # 任务
                        请从以下几个方面进行分析，且每个建议都要说明问题的根本原因、优化的具体方法、预期的性能提升效果以及实施的注意事项和风险，同时要考虑业务场景和数据特征，提供最适合的优化方案：
                        1. **执行计划分析**
                           - 识别执行计划中的性能瓶颈
                           - 分析访问路径是否合理（全表扫描、索引扫描等）
                           - 评估连接顺序和连接方式的效率
                           - 检查是否存在不必要的排序和分组操作
                        
                        2. **SQL逻辑优化**
                           - 是否存在冗余或重复的查询逻辑
                           - WHERE条件是否能有效利用索引
                           - JOIN操作是否可以优化
                           - 子查询是否可以改写为JOIN或其他方式
                           - 是否存在可以简化的复杂表达式
                           - 查询的内容包含时间的是否可以增加时间范围
                           - 避免在WHERE、JOIN、ORDER BY中使用函数或表达式对字段进行操作
                           - 合理使用EXISTS替代IN（尤其在子查询中）
                           - 避免SELECT *，只查询需要的字段
                           - 使用LIMIT / TOP / FETCH 方式限制结果集
                           - 避免不必要的DISTINCT和GROUP BY
                           - 优化ORDER BY和分页逻辑
                           - 减少多层嵌套子查询
                           - 避免在WHERE中使用OR连接多个条件（尤其无索引字段）
                           - 使用覆盖索引（Covering Index）
                           - 使用分析函数替代自连接或子查询
                           - 避免隐式类型转换
                           - 合理使用UNION ALL替代UNION
                           - 避免 Cartesian Product（笛卡尔积）
                           - 使用 INNER JOIN 替代 WHERE 子句连接（隐式 JOIN）
                           - 合理使用 LEFT JOIN 和 INNER JOIN
                           - 避免在 JOIN 条件中使用函数或复杂表达式
                           - 使用物化临时表或 CTE 缓存中间结果
                           - 避免在 WHERE 中使用 != 或NOT IN
                           - 小结果集表做驱动表（通常是 LEFT 表）
                        
                        3. **索引优化建议**
                           - 现有索引的使用情况分析
                           - 是否需要创建新的复合索引
                           - 是否存在冗余或未使用的索引
                           - 索引列顺序是否合理
                           - 是否考虑使用覆盖索引
                        
                        4. **具体优化方案**
                           - 提供优化后的SQL语句，需要多个数据库版本的SQL优化方案
                           - 存在大表查询最新时间的查询时，需要提示能够缩小查询范围，提供优化后的SQL语句
                           - 若通过分析函数优化，窗口函数优化时需要考虑cte方式是否也能满足，比较两者输出最优方案
                           - 详细说明每项优化的预期效果
                           - 列出需要创建或修改的索引
                           - 估计优化后的性能提升幅度
                        
                        5. **实施建议和注意事项**
                           - 优化方案的实施步骤
                           - 可能遇到的风险和应对措施
                           - 验证优化效果的方法
                           - 在生产环境中实施的最佳时机
                        
                        此外，请扩展延伸以下情况：
                            1. 能否进一步分析这个查询在高并发场景下的表现？
                            2. 如果数据量增长100倍，这个优化方案是否仍然有效？sql又如何调整？
                            3. 除了SQL层面的优化，数据库参数层面有哪些可以调整的？
                            4. 这个优化方案对其他相似查询是否有借鉴意义？
                            5. 能否提供一个逐步实施的优化计划，以降低生产环境风险？
                            
                        最后，请以markdown格式输出结果，内容包括：
                            1. 描述相关表情况，表索引，表数据量
                            2. 解析执行计划的过程
                            3. 分析存在的问题点
                            4. 根据SQL逻辑优化提供解决方案，需要提供多个版本的方案，例如mysql5.7以下，以及mysql5.7、mysql8.0以上，需要提示适用哪些范围的版本,优化后的sql展示
                            5. 延伸思考点，若有新的sql优化思路，需要详细说明并进行展示
                            
                        """

            return [TextContent(type="text", text="".join( result))]


        except SQLExecutionError as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

    def get_sql_all_tables(self,sql: str) -> List[str]:
        """
        从SQL语句中提取所有涉及的表名

        Args:
            sql (str): SQL语句

        Returns:
            List[str]: 表名列表
        """
        # 移除SQL注释
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

        # 转换为大写以便处理
        sql_upper = sql.upper()

        # 首先提取CTE（公用表表达式）中的表名，这些不应被视为真实表
        cte_names = set()
        # 使用正则表达式直接匹配CTE定义 "name AS ("
        cte_pattern = r'(\w+)\s+AS\s*\('
        cte_matches = re.findall(cte_pattern, sql_upper)
        cte_names.update(cte_matches)

        # 匹配各种SQL语句中的表名
        table_names = set()

        # 匹配 FROM 子句中的表名 (包括 JOIN)
        from_patterns = [
            r'\bFROM\s+([^\s,]+)',
            r'\bJOIN\s+([^\s,]+)',
            r'\bUPDATE\s+([^\s,]+)',
            r'\bINTO\s+([^\s,]+)',
            r'\bTABLE\s+([^\s,]+)'
        ]

        for pattern in from_patterns:
            matches = re.findall(pattern, sql_upper, re.IGNORECASE)
            for match in matches:
                # 处理可能的别名和特殊字符
                table = match.split()[0].strip()
                # 移除可能的反引号、括号等
                table = re.sub(r'[`"\[\]()]', '', table)
                # 过滤掉一些关键字和表达式
                if (table and
                        not table.startswith('(') and
                        table not in cte_names and  # 排除CTE中的表名
                        table not in [
                            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'GROUP', 'ORDER',
                            'HAVING', 'LIMIT', 'UNION', 'INTERSECT', 'EXCEPT', 'WITH'
                        ] and
                        not table.isdigit()):  # 排除纯数字
                    table_names.add(table)

        # 匹配 DELETE FROM 语句
        delete_matches = re.findall(r'\bDELETE\s+FROM\s+([^\s,]+)', sql_upper, re.IGNORECASE)
        for match in delete_matches:
            table = match.split()[0].strip()
            table = re.sub(r'[`"\[\]()]', '', table)
            if table and table not in cte_names:
                table_names.add(table)

        # 匹配 INSERT INTO 语句
        insert_matches = re.findall(r'\bINSERT\s+INTO\s+([^\s(]+)', sql_upper, re.IGNORECASE)
        for match in insert_matches:
            table = match.split()[0].strip()
            table = re.sub(r'[`"\[\]()]', '', table)
            if table and table not in cte_names:
                table_names.add(table)

        # 匹配 REPLACE INTO 语句
        replace_matches = re.findall(r'\bREPLACE\s+INTO\s+([^\s(]+)', sql_upper, re.IGNORECASE)
        for match in replace_matches:
            table = match.split()[0].strip()
            table = re.sub(r'[`"\[\]()]', '', table)
            if table and table not in cte_names:
                table_names.add(table)

        return list(table_names)

    def get_tables_index(self,tables,config) -> str:

        table_condition = "','".join(tables)

        sql = "SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE, INDEX_TYPE "
        sql += f"FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = '{config['database']}' "
        sql += f"AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;"

        return execute_sql.format_result(execute_sql.execute_single_statement(sql))

    def get_tables_count(self, tables,config) -> str:
        table_condition = "','".join(tables)

        sql = f"""
            SELECT 
                table_name AS `Table`, 
                round(((data_length + index_length) / 1024 / 1024), 2) AS `Size (MB)`
            FROM 
                information_schema.tables
            WHERE 
                table_schema = '{config['database']}'
                AND table_name in ('{table_condition}')  
            ORDER BY 
                (data_length + index_length) DESC;

        """

        return execute_sql.format_result(execute_sql.execute_single_statement(sql))

    def get_sql_execution_process(self, text, config) -> str:
        sql = "EXPLAIN " + text

        return execute_sql.format_result(execute_sql.execute_single_statement(sql))

    def get_tables_schemas(self, tables,config) -> str:
        table_condition = "','".join(tables)
        sql = "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT "
        sql += f"FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{config['database']}' "
        sql += f"AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, ORDINAL_POSITION;"
        return execute_sql.format_result(execute_sql.execute_single_statement(sql))

