# src/myframework/app.py
import uvicorn
import traceback
import os
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import List, Optional, Any
# --- 新增导入 ---
from .exceptions import Panic
from .utils import register_routes
# --- 新增导入日志模块 ---
from . import logger

# --- 辅助函数：读取日志文件 ---
def _read_log_file(lines: int = 100):
    """读取日志文件的最后 N 行。"""
    log_path = os.path.join(".", logger.LOG_FILENAME) # 假设在项目根目录
    if not os.path.exists(log_path):
        return "日志文件不存在。"
    try:
        # 使用 'tail' 逻辑读取大文件末尾，这里简单实现
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            # 返回最后 'lines' 行
            return "".join(all_lines[-lines:])
    except Exception as e:
        return f"读取日志文件时出错: {e}"

def _patch_app_with_run(app: FastAPI):
    """动态地向 FastAPI 应用实例添加 'run' 方法。"""
    def run(self, host="127.0.0.1", port=8000, **uvicorn_kwargs):
        """
        启动 Uvicorn 服务器。
        
        参数:
            host (str): 要绑定的主机。默认为 "127.0.0.1"。
            port (int): 要绑定的端口。默认为 8000。
            **uvicorn_kwargs: 传递给 uvicorn.run 的其他关键字参数。
        """
        # 在启动服务前配置日志
        logger.configure_logger(log_level=logging.INFO, logs_dir=".")
        uvicorn.run(self, host=host, port=port, **uvicorn_kwargs)
    app.run = run.__get__(app, FastAPI)

# --- 更新：Panic 异常处理器，添加日志记录 ---
async def panic_exception_handler(request: Request, exc: Panic):
    """
    处理自定义 Panic 异常。
    """
    # --- 记录 Panic 日志 ---
    log_msg = f"Panic 异常: Code={exc.code}, Msg='{exc.msg}', Error='{exc.error}'"
    if exc.data is not None:
        log_msg += f", Data={exc.data}"
    logger.get_logger().error(log_msg, exc_info=True) # exc_info=True 会记录堆栈

    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "msg": exc.msg,
            "error": exc.error,
            "data": exc.data
        },
    )

# --- 更新：全局异常处理器，添加日志记录 ---
async def global_exception_handler(request: Request, exc: Exception):
    """全局处理所有未处理的异常。"""
    # --- 记录详细异常日志 ---
    logger.get_logger().error(f"未处理的异常: {type(exc).__name__}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": "内部服务器错误",
            "error": "服务器遇到了一个未曾预料的状况，导致无法完成对请求的处理。",
            "data": None
        },
    )

# --- 更新：HTTP 异常处理器，添加日志记录 (可选，根据严重性) ---
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 Starlette HTTP 异常。"""
    # 对于 4xx 客户端错误，可以记为警告；5xx 服务器错误记为错误
    log_level = logging.WARNING if 400 <= exc.status_code < 500 else logging.ERROR
    logger.get_logger().log(
        log_level, 
        f"HTTP 异常 {exc.status_code}: {exc.detail} - URL: {request.url}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": exc.detail,
            "error": exc.detail,
            "data": None
        },
    )

# --- 更新：验证异常处理器，添加日志记录 ---
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理 FastAPI 请求验证错误。"""
    # 记录验证错误日志
    logger.get_logger().warning(f"请求验证失败: {exc.errors()} - URL: {request.url}")
    
    errors = exc.errors()
    msg = "请求参数验证失败"
    error_details = []
    if errors:
        msg = errors[0].get('msg', msg)
        error_details = errors

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "msg": msg,
            "error": error_details,
            "data": None
        },
    )

def create_app(
    title: str = "My App",
    cors_origins: Optional[List[str]] = None,
    cors_allow_credentials: bool = True,
    cors_allow_methods: List[str] = ["*"],
    cors_allow_headers: List[str] = ["*"],
    enable_cors: bool = True,
):
    """创建 FastAPI 应用实例的工厂函数。"""
    # --- 在创建应用时就配置日志 ---
    logger.configure_logger(log_level=logging.INFO, logs_dir=".")
    app_logger = logger.get_logger()
    app_logger.info(f"正在创建应用: {title}")

    app = FastAPI(title=title)

    # 注册异常处理器
    app.add_exception_handler(Panic, panic_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app_logger.info("全局异常处理器已注册。")

    if enable_cors:
        if cors_origins is None:
            cors_origins = ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=cors_allow_credentials,
            allow_methods=cors_allow_methods,
            allow_headers=cors_allow_headers,
        )
        app_logger.info(f"CORS 已启用，允许的来源: {cors_origins}")

    # --- 新增：添加内置的日志查看接口 ---
    from pydantic import BaseModel
    from typing import Optional

    class LogQuery(BaseModel):
        lines: Optional[int] = 100 # 默认返回最后100行

    api_prefix = f"/{title.lower().replace(' ', '_')}"
    @app.get(f"{api_prefix}/api/error/logs", response_class=PlainTextResponse) # 使用 PlainTextResponse 返回纯文本
    async def get_error_logs(query: LogQuery = None):
        """获取错误日志内容。"""
        app_logger.info("收到查看日志的请求。")
        num_lines = query.lines if query and query.lines else 100
        log_content = _read_log_file(lines=num_lines)
        return log_content

    @app.get("/")
    async def root():
        welcome_msg = f"欢迎使用 {title} API!"
        app_logger.info(welcome_msg)
        return {"message": welcome_msg, "api_base_path": api_prefix}

    try:
        register_routes(app, base_prefix=api_prefix)
        app_logger.info("路由注册完成。")
    except Exception as e:
        app_logger.critical(f"路由注册失败: {e}", exc_info=True)
        raise # 重新抛出，让应用启动失败

    _patch_app_with_run(app)
    app_logger.info("应用创建完成。")
    return app
