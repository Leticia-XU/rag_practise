FROM paddlepaddle/paddle:3.3.0-gpu-cuda11.8-cudnn8.9

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
# 防止 pip 缓存导致版本飘
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

RUN python -m pip install -U pip setuptools wheel \
 # 1) 彻底卸掉 numpy/opencv（以及可能存在的残留）
 && python -m pip uninstall -y numpy opencv-python opencv-python-headless || true \
 # 2) 先装 numpy 1.x（关键）
 && python -m pip install --force-reinstall "numpy==1.26.4" \
 # 3) 装 opencv 时禁止依赖解析，避免它把 numpy 升级到 2.x（关键）
 && python -m pip install --no-deps --force-reinstall "opencv-python-headless==4.9.0.80" \
 # 4) 再装 paddleocr 和 API 依赖（让它们自己用现成的 numpy1）
 && python -m pip install \
    "paddleocr==2.7.0.3" \
    "fastapi==0.110.0" \
    "uvicorn==0.27.1" \
    "anyio==3.7.1" \
    "pdf2image" \
    "pillow" \
    "python-multipart" \
 # 5) 最后再强制把 numpy 拉回 1.26.4，防止上面任何包把它升级（兜底）
 && python -m pip install --force-reinstall "numpy==1.26.4"

WORKDIR /app
COPY app.py /app/app.py

EXPOSE 8891
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8891", "--workers", "1"]
