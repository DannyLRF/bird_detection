FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# 设置工作目录
WORKDIR ${LAMBDA_TASK_ROOT}

# 复制requirements文件
COPY requirements-container.txt .

# 更新pip并安装依赖
RUN pip install --upgrade pip && \
    pip install -r requirements-container.txt --no-cache-dir

# 复制Lambda函数代码
COPY lambda_function.py .

# 设置命令
CMD [ "lambda_function.lambda_handler" ]