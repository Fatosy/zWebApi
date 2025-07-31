# src/myframework/exceptions.py
"""MyFramework 的自定义异常。"""

class Panic(Exception):
    """
    自定义异常类，用于返回标准化的错误响应。

    当抛出时，它将被全局异常处理器捕获
    并格式化为如下 JSON 响应：
    {
        "code": 500,
        "msg": "内部服务器错误",
        "error": "发生了一个错误",
        "data": null
    }
    """

    def __init__(self, code: int = 500, msg: str = "内部服务器错误", error: str = "", data = None):
        """
        初始化 Panic 异常。

        参数:
            code (int): HTTP 状态码和应用程序错误码。默认为 500。
            msg (str): 用户友好的消息。默认为 "内部服务器错误"。
            error (str): 更详细的错误描述或技术信息。默认为空字符串。
             响应中包含的可选数据。默认为 None。
        """
        self.code = code
        self.msg = msg
        self.error = error
        self.data = data
        # 使用默认消息调用基类构造函数，用于 str(exc)
        super().__init__(self.msg) 

    def __repr__(self):
        return f"Panic(code={self.code}, msg='{self.msg}', error='{self.error}', data={self.data})"
