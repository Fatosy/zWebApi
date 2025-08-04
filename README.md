# zWebApi
一个功能丰富、开箱即用的 Python Web 框架，基于 FastAPI 构建。它旨在通过约定优于配置的原则，简化 API 开发流程，提供自动路由、统一异常处理、日志记录和可扩展工具集。

![](https://badge.fury.io/py/myframework.svg)  
![](https://img.shields.io/badge/License-MIT-yellow.svg)

## 目录
+ [特性](#特性)
+ [安装](#安装)
+ [快速开始](#快速开始)
    - [1. 项目结构](#1-项目结构)
    - [2. 创建应用 (](#2-创建应用-mainpy)`main.py`[)](#2-创建应用-mainpy)
    - [3. 定义路由 (](#3-定义路由-action)`action/`[)](#3-定义路由-action)
    - [4. 运行应用](#4-运行应用)
+ [核心概念](#核心概念)
    - [应用创建与配置](#应用创建与配置)
    - [路由自动注册](#路由自动注册)
    - [路由函数签名规范](#路由函数签名规范)
    - [统一响应与异常处理](#统一响应与异常处理)
        * [全局异常处理](#全局异常处理)
        * [自定义 ](#自定义-panic-异常)`Panic`[ 异常](#自定义-panic-异常)
    - [日志记录](#日志记录)
    - [工具模块](#工具模块)
+ [高级用法](#高级用法)
    - [CORS 配置](#cors-配置)
    - [使用框架日志](#使用框架日志)
+ [API 文档](#api-文档)
+ [贡献](#贡献)
+ [许可证](#许可证)

## 特性
+ **🚀**** 快速启动**: 基于 FastAPI 和 Uvicorn，提供异步高性能。
+ **🧭**** 自动路由注册**: 只需按约定在 `action/` 目录下组织代码，路由自动生效。
+ **🔒**** 路由签名强制**: 确保所有路由函数遵循统一的 `query`/`body` 参数规范。
+ **🛡️**** 统一异常处理**: 全局捕获异常，返回格式统一的 JSON 错误响应。
+ **🚨**** 自定义 **`Panic`** 异常**: 简单易用的自定义异常类，用于主动返回错误。
+ **📋**** 全面日志记录**: 自动记录应用启动、路由、异常等信息，支持文件和控制台输出，并提供日志查看接口。
+ **🛠️**** 可扩展工具模块**: 通过 `zWebApi.tools.*` 轻松访问和扩展框架功能。
+ **🌐**** CORS 支持**: 内置 CORS 中间件，轻松配置跨域资源共享。
+ **📦**** 易于打包和分发**: 标准 Python 包，可通过 `pip` 安装。

## 安装
```bash
pip install zWebApi
pip install zWebApi -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 打包
```bash
python -m build
twine upload dist/*
rm -rf dist src/*.egg-info
```

## 脚本打包
```bash
./py_build.sh <env_name> build
./py_build.sh <env_name> upload <pypi api token>
./py_build.sh <env_name> delete
```

## 快速开始
### 1. 项目结构
创建一个符合框架约定的项目目录结构：

```plain
my_project/
├── main.py              # 应用入口点
├── action/              # 路由定义目录 (必须)
│   └── user/            # 模块目录 (例如 'user')
│       └── user.py      # 路由文件 (必须与模块目录同名)
├── domain/              # 业务逻辑层 (可选，但推荐)
├── dao/                 # 数据访问层 (可选，但推荐)
├── utils/               # 项目通用工具 (可选)
└── zwebApi.log      # (运行后自动生成) 日志文件
```

### 2. 创建应用 (`main.py`)
这是你应用的入口文件。

```python
# main.py
from zWebApi import create_app

# 创建应用实例，并设置 API 标题和基础路径前缀
app = create_app(title="我的酷炫API")

# --- 可选：添加自定义中间件或配置 ---
# from fastapi.middleware import Middleware
# app.add_middleware(SomeMiddleware)

if __name__ == "__main__":
    # 使用框架封装的 run 方法启动服务器
    # 等效于 uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    app.run(host="0.0.0.0", port=8000, reload=True) # reload=True 适用于开发环境
```

### 3. 定义路由 (`action/`)
在 `action/` 目录下创建模块和路由文件。

**创建 **`action/user/user.py`

```python
# action/user/user.py
# 导入自定义异常
from zWebApi import zRouter, Panic
# 导入校验参数
from schema.user import (
    UserQueryParams,
    UserCreate,
    UserResponse
)

# 必须创建一个 APIRouter 实例，变量名必须为 'router'
router = zRouter(tags=["用户管理"]) # tags 用于 API 文档分组

# --- 定义路由处理函数 ---
# 注意：函数签名必须遵循规范，只使用 'query' 和 'body' 作为参数名，
# 且它们必须是 Pydantic BaseModel 或 None。

@router.get("/info")
async def get_user_info(query: UserQueryParams = None):
    """获取用户信息"""
    if query and query.user_id:
        # 模拟业务逻辑
        if query.user_id == 999:
            # 使用 Panic 异常返回自定义错误
            raise Panic(code=404, msg="用户未找到", error="请求的用户ID不存在。")
        return {
            "user_id": query.user_id,
            "name": f"User_{query.user_id}",
            "filter_used": query.name_filter
        }
    return {"message": "请提供 user_id 查询参数"}

@router.post("/create")
async def create_user(body: UserCreate = None):
    """创建新用户"""
    if body is None:
        # 使用 Panic 异常返回错误
        raise Panic(code=400, msg="请求体缺失", error="创建用户必须提供请求体。")
    
    # 模拟创建用户
    new_user = UserResponse(id=123, name=body.name, age=body.age)
    return {"message": "用户创建成功", "user": new_user}

```

在`schema/`目录下创建校验参数

**创建 **`schema/user.py`

```python
# --- 定义 Pydantic 模型用于参数校验 ---
from pydantic import BaseModel
from typing import Optional

# 查询参数模型
class UserQueryParams(BaseModel):
    user_id: Optional[int] = None
    name_filter: Optional[str] = None

# 请求体模型
class UserCreate(BaseModel):
    name: str
    age: int

# 响应体模型 (可选但推荐)
class UserResponse(BaseModel):
    id: int
    name: str
    age: int
```

### 4. 运行应用
在你的项目根目录 (`your_project/`) 下打开终端，运行：

```bash
python main.py
```

应用将在 `http://0.0.0.0:8000` 启动。

+ **API 根路径**: `http://localhost:8000/`
+ **用户模块路径**: `http://localhost:8000/我的酷炫api/user/...`
+ **API 文档**: `http://localhost:8000/docs`
+ **日志查看**: `http://localhost:8000/我的酷炫api/api/error/logs`

## 核心概念
### 应用创建与配置
使用 `zWebApi.create_app` 工厂函数创建 FastAPI 应用实例。

```python
app = create_app(
    title="My App",                    # API 标题，也用作基础路径前缀
    enable_cors=True,                  # 是否启用 CORS
    cors_origins=["*"],                # CORS 允许的源
    cors_allow_credentials=True,
    cors_allow_methods=["*"],
    cors_allow_headers=["*"]
)
```

### 路由自动注册
框架启动时会自动扫描 `action/` 目录。

+ 遍历 `action/` 下的每个子目录（如 `user/`）。
+ 在每个子目录中查找与目录同名的 Python 文件（如 `user.py`）。
+ 导入该文件，并查找名为 `router` 的 `APIRouter` 实例。
+ 将该 `router` 挂载到以目录名（如 `/user`）为前缀的路径下。
+ 最终的基础路径是 `/title` (title 转为小写并用下划线替换空格)。

### 路由函数签名规范
为了保持一致性并利用框架的校验功能，路由处理函数 **必须** 遵循以下签名：

+ **只接受** `query` 和 `body` 两个命名参数。
+ **参数类型** 必须是 Pydantic `BaseModel` 的子类或 `None`。
+ **默认值** 应为 `None` 以使其成为可选参数。
+ **参数名** 必须严格是 `query` 和/或 `body`。

**正确示例:**

```python
# 只有 query
async def get_items(query: ItemQueryParams = None): ...

# 只有 body
async def create_item(body: CreateItemRequest = None): ...

# 两者都有
async def update_item(query: UpdateQuery = None, body: UpdateItemRequest = None): ...
```

**错误示例 (会导致应用启动失败):**

```python
# 错误：使用了不允许的参数名 'item_id'
async def get_item(item_id: int): ...

# 错误：没有使用 BaseModel
async def search(name: str = ""): ...
```

### 统一响应与异常处理
#### 全局异常处理
框架自动注册了多个全局异常处理器，确保所有错误都返回统一的 JSON 格式：

```json
{
  "code": 400,
  "msg": "错误的请求",
  "error": "具体错误信息...",
  "data": null
}
```

+ `HTTPException`: 处理 FastAPI/Starlette 抛出的 HTTP 异常 (如 404, 403)。
+ `RequestValidationError`: 处理 Pydantic 模型校验失败 (422)。
+ `Exception`: 捕获所有未处理的服务器内部错误 (500)。
+ `Panic`: 处理用户自定义的 `Panic` 异常。

#### 自定义 `Panic` 异常
用户可以在任何地方（路由、domain、dao）主动抛出 `Panic` 来返回自定义错误。

```python
from zWebApi import Panic

# 在路由、服务或数据访问层
def some_business_logic(user_id):
    if user_id <= 0:
        # 主动抛出 Panic 异常
        raise Panic(
            code=400,                    # HTTP 状态码和业务码
            msg="无效的用户ID",           # 用户友好信息
            error="用户ID必须是正整数。", # 技术错误详情
            data={"provided_id": user_id} # 可选的附加数据
        )
```

### 日志记录
框架使用 Python `logging` 模块提供全面的日志功能。

+ **格式**: `[级别][年月日时分秒][文件名][行号]: 消息`
    - 例如: `[INFO][20240521180000][app.py][150]: 应用创建完成。`
    - 例如: `[ERROR][20240521180001][user.py][30]: 无效的用户ID`
+ **输出**: 同时记录到控制台（开发）和项目根目录下的 `weblog.log` 文件。
+ **轮转**: 使用 `TimedRotatingFileHandler`，默认每10天轮转一次日志文件。
+ **查看**: 提供内置 API 接口 `GET /<title>/api/error/logs` 查看日志内容。
    - 可通过 `?lines=N` 参数指定返回最后 N 行。

### 工具模块
框架提供了一个可扩展的 `tools` 包，用于存放通用功能模块。

**导入方式:**

```python
# 从框架内置工具导入
from zWebApi.tools.db.mysql import testsql, MySQLHelper

# 未来可扩展
# from zWebApi.tools.cache.redis_client import RedisManager
```

**创建自定义工具:**

在框架源码的 `src/zWebApi/tools/` 下创建新的子目录和 `.py` 文件即可。用户安装更新后的包即可使用。

## 高级用法
### CORS 配置
在 `create_app` 时配置 CORS：

```python
app = create_app(
    title="API",
    enable_cors=True,
    cors_origins=["http://localhost:3000", "https://myfrontend.com "],
    cors_allow_credentials=True,
    cors_allow_methods=["GET", "POST", "PUT", "DELETE"],
    cors_allow_headers=["*"],
)
```

### 使用框架日志
在你的项目代码中，可以使用框架配置好的日志记录器：

```python
# 在你的 action, domain, dao 等模块中
from zWebApi import get_logger

logger = get_logger()

@router.get("/some-path")
async def my_endpoint():
    logger.info("处理 /some-path 请求")
    try:
        # ... 业务逻辑 ...
        logger.debug("业务逻辑执行成功")
        return {"result": "ok"}
    except Exception as e:
        logger.error(f"处理请求时出错: {e}", exc_info=True)
        raise # 让全局异常处理器捕获
```

## API 文档
框架完全兼容 FastAPI 的自动生成文档功能。

+ **Swagger UI**: `http://<your-host>:<port>/docs`
+ **ReDoc**: `http://<your-host>:<port>/redoc`

## 贡献
欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证
本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

