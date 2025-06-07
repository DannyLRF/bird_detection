FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Avoid matplotlib/Pillow write issues
ENV MPLCONFIGDIR=/tmp
ENV ORT_LOGGING_LEVEL=WARNING

# Install OpenCV + NumPy only
RUN yum install -y mesa-libGL && \
    pip install --no-cache-dir \
        numpy==1.26.4 \
        pillow==10.3.0 \
        onnxruntime==1.15.1 \
        opencv-python-headless==4.9.0.80 \
        boto3==1.34.103 \
        botocore==1.34.103

# Copy files
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY utils.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]
