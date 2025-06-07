FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y libjpeg-devel zlib-devel && yum clean all

COPY lambda_function.py ./
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["lambda_function.handler"]