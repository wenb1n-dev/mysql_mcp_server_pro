from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler

from mysql_mcp_server_pro.handles import (
    ExecuteSQL
)

execute_sql = ExecuteSQL()

class GetTableLock(BaseHandler):
    name = "get_table_lock"
    description = (
        "获取当前mysql服务器行级锁、表级锁情况(Check if there are row-level locks or table-level locks in the current MySQL server  )"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {

                }
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        use_result = await self.get_table_use(arguments)
        lock_result_5 = await self.get_table_lock_for_mysql5(arguments)
        lock_result_8 = await self.get_table_lock_for_mysql8(arguments)
        
        # 合并两个结果
        combined_result = []
        combined_result.extend(use_result)
        combined_result.extend(lock_result_5)
        combined_result.extend(lock_result_8)
        
        return combined_result

    """
        获取表级锁情况
    """
    async def get_table_use(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SHOW OPEN TABLES WHERE In_use > 0;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

    """
        获取行级锁情况--mysql5.6
    """
    async def get_table_lock_for_mysql5(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SELECT p2.`HOST` 被阻塞方host,  p2.`USER` 被阻塞方用户, r.trx_id 被阻塞方事务id, "
            sql += "r.trx_mysql_thread_id 被阻塞方线程号,TIMESTAMPDIFF(SECOND, r.trx_wait_started, CURRENT_TIMESTAMP) 等待时间, "
            sql += "r.trx_query 被阻塞的查询, l.lock_table 阻塞方锁住的表, m.`lock_mode` 被阻塞方的锁模式, "
            sql += "m.`lock_type` '被阻塞方的锁类型(表锁还是行锁)', m.`lock_index` 被阻塞方锁住的索引, "
            sql += "m.`lock_space` 被阻塞方锁对象的space_id, m.lock_page 被阻塞方事务锁定页的数量, "
            sql += "m.lock_rec 被阻塞方事务锁定记录的数量, m.lock_data 被阻塞方事务锁定记录的主键值, "
            sql += "p.`HOST` 阻塞方主机, p.`USER` 阻塞方用户, b.trx_id 阻塞方事务id,b.trx_mysql_thread_id 阻塞方线程号, "
            sql += "b.trx_query 阻塞方查询, l.`lock_mode` 阻塞方的锁模式, l.`lock_type` '阻塞方的锁类型(表锁还是行锁)',"
            sql += "l.`lock_index` 阻塞方锁住的索引,l.`lock_space` 阻塞方锁对象的space_id,l.lock_page 阻塞方事务锁定页的数量,"
            sql += "l.lock_rec 阻塞方事务锁定行的数量,  l.lock_data 阻塞方事务锁定记录的主键值,"
            sql += "IF(p.COMMAND = 'Sleep', CONCAT(p.TIME, ' 秒'), 0) 阻塞方事务空闲的时间 "
            sql += "FROM information_schema.INNODB_LOCK_WAITS w "
            sql += "INNER JOIN information_schema.INNODB_TRX b ON b.trx_id = w.blocking_trx_id "
            sql += "INNER JOIN information_schema.INNODB_TRX r ON r.trx_id = w.requesting_trx_id "
            sql += "INNER JOIN information_schema.INNODB_LOCKS l ON w.blocking_lock_id = l.lock_id AND l.`lock_trx_id` = b.`trx_id` "
            sql += "INNER JOIN information_schema.INNODB_LOCKS m ON m.`lock_id` = w.`requested_lock_id` AND m.`lock_trx_id` = r.`trx_id` "
            sql += "INNER JOIN information_schema.PROCESSLIST p ON p.ID = b.trx_mysql_thread_id "
            sql += "INNER JOIN information_schema.PROCESSLIST p2 ON p2.ID = r.trx_mysql_thread_id "
            sql += "ORDER BY 等待时间 DESC;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

    """
        获取行级锁情况--mysql8
    """
    async def get_table_lock_for_mysql8(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        try:
            sql = "SELECT p2.HOST AS '被阻塞方host',p2.USER AS '被阻塞方用户',r.trx_id AS '被阻塞方事务id', "
            sql += "r.trx_mysql_thread_id AS '被阻塞方线程号',TIMESTAMPDIFF(SECOND, r.trx_wait_started, CURRENT_TIMESTAMP) AS '等待时间',"
            sql += "r.trx_query AS '被阻塞的查询',dlr.OBJECT_SCHEMA AS '被阻塞方锁库',dlr.OBJECT_NAME AS '被阻塞方锁表',"
            sql += "dlr.LOCK_MODE AS '被阻塞方锁模式', dlr.LOCK_TYPE AS '被阻塞方锁类型',dlr.INDEX_NAME AS '被阻塞方锁住的索引',"
            sql += "dlr.LOCK_DATA AS '被阻塞方锁定记录的主键值',p.HOST AS '阻塞方主机',p.USER AS '阻塞方用户',b.trx_id AS '阻塞方事务id',"
            sql += "b.trx_mysql_thread_id AS '阻塞方线程号',b.trx_query AS '阻塞方查询',dlb.LOCK_MODE AS '阻塞方锁模式',"
            sql += "dlb.LOCK_TYPE AS '阻塞方锁类型',dlb.INDEX_NAME AS '阻塞方锁住的索引',dlb.LOCK_DATA AS '阻塞方锁定记录的主键值',"
            sql += "IF(p.COMMAND = 'Sleep', CONCAT(p.TIME, ' 秒'), 0) AS '阻塞方事务空闲的时间' "
            sql += "FROM performance_schema.data_lock_waits w "
            sql += "JOIN performance_schema.data_locks dlr ON w.REQUESTING_ENGINE_LOCK_ID = dlr.ENGINE_LOCK_ID "
            sql += "JOIN performance_schema.data_locks dlb ON w.BLOCKING_ENGINE_LOCK_ID = dlb.ENGINE_LOCK_ID "
            sql += "JOIN information_schema.innodb_trx r ON w.REQUESTING_ENGINE_TRANSACTION_ID = r.trx_id "
            sql += "JOIN information_schema.innodb_trx b ON w.BLOCKING_ENGINE_TRANSACTION_ID = b.trx_id "
            sql += "JOIN information_schema.processlist p ON b.trx_mysql_thread_id = p.ID "
            sql += "JOIN information_schema.processlist p2 ON r.trx_mysql_thread_id = p2.ID "
            sql += "ORDER BY '等待时间' DESC;"

            return await execute_sql.run_tool({"query": sql})
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]