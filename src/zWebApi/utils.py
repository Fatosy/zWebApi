# src/myframework/utils.py
import os
import importlib.util
import logging
from fastapi import FastAPI, APIRouter
from .signature_enforcer import enforce_signature
# --- 新增导入日志记录器 ---
from . import logger

def register_routes(app: FastAPI, actions_dir: str = "action", base_prefix: str = ""):
    """
    扫描 'action' 目录并自动注册路由器。
    在此过程中强制执行函数签名。
    """
    app_logger = logger.get_logger()
    app_logger.info(f"开始扫描 Action 目录: {actions_dir}")
    
    if not os.path.isdir(actions_dir):
        error_msg = f"未找到 Action 目录 '{actions_dir}'。"
        app_logger.error(error_msg)
        print(error_msg) # 保持原有的 print 作为备用
        return

    for module_name in os.listdir(actions_dir):
        module_path = os.path.join(actions_dir, module_name)
        if os.path.isdir(module_path):
            router_file = os.path.join(module_path, f"{module_name}.py")
            if os.path.isfile(router_file):
                app_logger.debug(f"正在导入模块: {router_file}")
                spec = importlib.util.spec_from_file_location(f"action.{module_name}.{module_name}", router_file)
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    app_logger.debug(f"成功导入模块: {router_file}")
                except Exception as e:
                    error_msg = f"从 {router_file} 导入路由器失败: {e}"
                    app_logger.error(error_msg, exc_info=True)
                    print(error_msg)
                    continue # 跳过这个模块，继续处理其他模块

                router = getattr(module, 'router', None)
                if isinstance(router, APIRouter):
                    try:
                        enforce_signature(router)
                        module_prefix = f"/{module_name}"
                        full_prefix = f"{base_prefix}{module_prefix}"
                        
                        app.include_router(router, prefix=full_prefix)
                        success_msg = f"已注册（并强制执行签名）来自 {router_file} 的路由器，完整前缀为 {full_prefix}"
                        app_logger.info(success_msg)
                        print(success_msg)
                    except Exception as e: # 捕获 enforce_signature 或 include_router 可能抛出的异常
                        error_msg = f"注册路由器 {router_file} 时失败: {e}"
                        app_logger.error(error_msg, exc_info=True)
                        print(error_msg)
                        # 可以选择 raise 或者 continue
                else:
                    warn_msg = f"在 {router_file} 中未找到有效的 'router'"
                    app_logger.warning(warn_msg)
                    print(warn_msg)

    app_logger.info("Action 目录扫描和路由注册完成。")
