#!/bin/bash

# --- 获取 Conda 环境名称 ---
# 优先使用命令行第一个参数作为环境名，如果没有提供则使用默认值 'pyup'
CONDA_ENV_NAME="${1:-uppy}"
shift # 移除第一个参数（环境名），剩下的参数用于后续处理

# --- 初始化 Conda ---
# 确保 conda 命令可用
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到 'conda' 命令。请确保 Anaconda 或 Miniconda 已正确安装。"
    exit 1
fi

# 初始化 conda 的 shell 功能
# 这对于在脚本中使用 'conda activate' 是必要的
# 'conda shell.bash hook' 会输出设置环境所需的命令，然后我们用 eval 执行它们
eval "$(conda shell.bash hook)"

# --- 激活指定的 Conda 环境 ---
if ! conda activate "$CONDA_ENV_NAME"; then
    echo "错误: 无法激活 Conda 环境 '$CONDA_ENV_NAME'。请检查环境是否存在。"
    exit 1
fi

echo "已激活 Conda 环境: $CONDA_ENV_NAME"

# --- 获取操作命令 ---
COMMAND="$1"

# --- 执行操作 ---
case "$COMMAND" in
    build)
        echo "执行: python -m build"
        python -m build
        ;;
    upload)
        API_TOKEN="$2"
        if [ -z "$API_TOKEN" ]; then
            echo "错误: upload 需要 API token。用法: $0 <env_name> upload <api_token>"
            exit 1
        fi
        if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
            echo "错误: dist 目录不存在或为空。请先运行 build 命令。"
            exit 1
        fi
        echo "执行: twine upload dist/* (自动输入 token)"
        expect << EOF
spawn twine upload dist/*
expect "Enter your API token:"
send "$API_TOKEN\r"
expect eof
EOF
        ;;
    delete)
        echo "执行: 删除 dist 和 *.egg-info"
        rm -rf dist src/*.egg-info
        echo "清理完成。"
        ;;
    *)
        echo "用法: $0 [<conda_env_name>] {build|upload <api_token>|delete}"
        echo "  <conda_env_name> : 要激活的 Conda 环境名称 (默认: pyup)"
        echo "  build            : 运行 python -m build"
        echo "  upload <token>   : 运行 twine upload 并自动输入 API token"
        echo "  delete           : 删除 dist/ 和 *.egg-info 目录"
        exit 1
        ;;
esac