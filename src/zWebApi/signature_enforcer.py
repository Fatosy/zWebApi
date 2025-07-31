# src/myframework/signature_enforcer.py
"""强制执行路由处理函数的特定函数签名。"""
import inspect
import functools
import logging
from fastapi import params
from pydantic import BaseModel
from typing import Any, Callable, Dict, List, Optional, get_type_hints
from .exceptions import Panic
# --- 新增导入日志记录器 ---
from . import logger

# --- 定义允许的参数名称 ---
ALLOWED_PARAM_NAMES = {"query", "body"}
# --- 定义参数到 FastAPI 依赖类型的映射 ---
PARAM_TO_DEPENDENCY_TYPE = {
    "query": params.Query,
    "body": params.Body,
}

def _create_enforced_wrapper(original_func: Callable, allowed_params: List[str]):
    """
    创建一个包装函数，该函数强制执行允许的参数名称
    并为 'query' 和 'body' 注入 FastAPI 依赖项。
    """
    sig = inspect.signature(original_func)
    type_hints = get_type_hints(original_func)
    
    new_params = []
    param_annotations = {}
    
    old_params = list(sig.parameters.values())
    if old_params and old_params[0].name == 'self':
        new_params.append(old_params[0])
        old_params = old_params[1:]

    for param_name in allowed_params:
        if param_name in {p.name for p in old_params}:
            original_param = next(p for p in old_params if p.name == param_name)
            param_type = type_hints.get(param_name, Any)
            
            dependency_type = PARAM_TO_DEPENDENCY_TYPE.get(param_name, params.Query)
            
            new_param = inspect.Parameter(
                param_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=dependency_type(default=original_param.default),
                annotation=param_type
            )
            new_params.append(new_param)
            param_annotations[param_name] = param_type
        else:
            pass
            
    new_sig = sig.replace(parameters=new_params)

    if inspect.iscoroutinefunction(original_func):
        async def wrapper(*args, **kwargs):
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in ALLOWED_PARAM_NAMES}
            try:
                return await original_func(*args, **filtered_kwargs)
            except Exception as e:
                # --- 记录路由处理函数内部的异常 ---
                logger.get_logger().error(
                    f"路由处理函数 '{original_func.__name__}' 内部发生异常: {e}", 
                    exc_info=True
                )
                # 重新抛出异常，让全局异常处理器捕获
                raise 
    else:
        def wrapper(*args, **kwargs):
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in ALLOWED_PARAM_NAMES}
            try:
                return original_func(*args, **filtered_kwargs)
            except Exception as e:
                logger.get_logger().error(
                    f"路由处理函数 '{original_func.__name__}' 内部发生异常: {e}", 
                    exc_info=True
                )
                raise

    wrapper.__signature__ = new_sig
    wrapper.__annotations__ = param_annotations
    functools.update_wrapper(wrapper, original_func)
    
    return wrapper

def enforce_signature(router):
    """
    检查并强制执行 APIRouter 内所有路由处理函数的签名。
    就地修改路由器。
    """
    # --- 记录开始强制签名 ---
    logger.get_logger().debug(f"开始对路由器 {router.prefix if hasattr(router, 'prefix') else 'N/A'} 强制执行签名。")
    
    for route in router.routes:
        original_endpoint = route.endpoint
        sig = inspect.signature(original_endpoint)
        param_names = {p.name for p in sig.parameters.values() if p.name != 'self'}

        invalid_params = param_names - ALLOWED_PARAM_NAMES
        if invalid_params:
            error_msg = (
                f"路由函数 '{original_endpoint.__name__}' 使用了无效的参数名: {invalid_params}。 "
                f"仅允许使用参数名 {sorted(ALLOWED_PARAM_NAMES)}。"
            )
            logger.get_logger().error(error_msg)
            raise Panic(
                code=500,
                msg="路由签名强制执行失败",
                error=error_msg,
                data={"函数名": original_endpoint.__name__, "文件": inspect.getfile(original_endpoint)}
            )
        
        try:
            enforced_wrapper = _create_enforced_wrapper(original_endpoint, sorted(ALLOWED_PARAM_NAMES))
            route.endpoint = enforced_wrapper
            logger.get_logger().debug(f"已为路由处理函数 '{original_endpoint.__name__}' 强制执行签名。")
        except Exception as e:
            error_msg = f"无法为 '{original_endpoint.__name__}' 创建强制执行包装器: {str(e)}"
            logger.get_logger().critical(error_msg, exc_info=True)
            raise Panic(
                code=500,
                msg="路由签名强制执行失败",
                error=error_msg,
                data={"函数名": original_endpoint.__name__, "文件": inspect.getfile(original_endpoint)}
            )

    logger.get_logger().debug("路由器签名强制执行完成。")
    return router
