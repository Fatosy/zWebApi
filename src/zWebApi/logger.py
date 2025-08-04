# src/zWebApi/logger.py
"""zWebApi 日志配置和管理。"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
import glob

# --- 定义日志文件名 ---
LOG_FILENAME = "weblog.log"

# --- 自定义日志格式器 ---
class zWebApiLogFormatter(logging.Formatter):
    """自定义日志格式化器。"""
    def format(self, record):
        # 获取当前时间
        dt = datetime.fromtimestamp(record.created)
        # 格式化时间
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        # 获取日志级别 (INFO, ERROR, WARNING, DEBUG, CRITICAL)
        level_tag = record.levelname
        # 获取文件名（record.pathname 是完整路径）
        filename = os.path.basename(record.pathname)
        # 构建自定义消息格式: [级别][年月日时分秒][文件名][行号]: 消息
        log_message = f"[{level_tag}][{time_str}][{filename}][{record.lineno}]: {record.getMessage()}"
        # 如果有异常信息，也添加进去
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        return log_message

# --- 配置日志记录器 ---
def configure_logger(log_level: int = logging.INFO, logs_dir: str = "."):
    """
    配置 zWebApiLog 的全局日志记录器。

    Args:
        log_level (int): 日志级别。默认为 INFO。
        logs_dir (str): 存放日志文件的目录。默认为当前目录 ('.')。
    """
    # 设置日志目录为项目根目录下的 log 文件夹
    log_directory = os.path.join(logs_dir, "logs")
    # 确保日志目录存在
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, LOG_FILENAME)

    # 获取或创建 'zWebApi' 记录器
    logger = logging.getLogger("zWebApi")
    logger.setLevel(log_level)

    # 避免重复添加处理器
    if not logger.handlers:
        # 1. 文件处理器 (带轮转)
        # when='D' 表示按天轮转, interval=10 表示每10天轮转一次，backupCount=6 表示保留6个历史文件
        file_handler = TimedRotatingFileHandler(
            log_file_path, when="D", interval=10, backupCount=6, encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = zWebApiLogFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 2. 控制台处理器 (用于开发)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = zWebApiLogFormatter() # 可以使用不同格式
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        logger.info(f"zWebApi 日志已配置，日志文件: {log_file_path}")

    return logger

# --- 获取已配置的记录器实例 ---
def get_logger():
    """获取 'zWebApi' 记录器实例。"""
    return logging.getLogger("zWebApi")

# --- 清理旧日志文件 ---
def cleanup_old_logs(logs_dir: str = ".", keep_days: int = 30):
    """
    清理超过指定天数的日志文件。
    注意：TimedRotatingFileHandler 会自动处理轮转，这个函数是额外的清理保障。

    Args:
        logs_dir (str): 日志文件所在的目录。
        keep_days (int): 保留日志文件的天数。
    """
    logger = get_logger()
    try:
        log_file_pattern = os.path.join(logs_dir, f"{LOG_FILENAME}.*")
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        
        for logfile in glob.glob(log_file_pattern):
            try:
                date_str = logfile.split('.')[-1]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                if file_date < cutoff_time:
                    os.remove(logfile)
                    logger.info(f"已删除旧日志文件: {logfile}")
            except (ValueError, OSError) as e:
                logger.warning(f"无法处理日志文件 {logfile} 进行清理: {e}")
    except Exception as e:
        logger.error(f"执行日志清理时出错: {e}")
