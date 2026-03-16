原先T4 GPU 搭建的RAG 运行时存在2个问题：中文图片无法解析（用Paddleocr优化）, 问答时很容易触发上下文token上限， 
优化配置如下:  一台H100专门跑Qianwen model，上下文设置为2048； 一台L4跑 Xinference 和 Paddleocr

这里描述差异点：
1. 部署 Xinference（Embedding + Rerank），GPU打开
docker run -d \
  --name xinference \
  --gpus all \
  -p 9997:9997 \
  xinference/xinference:latest

2. 构建OCR API服务
   Dockerfile
   app.py

3. 启动
   docker build --no-cache -t paddleocr-api:gpu .
   docker rm -f paddleocr || true
   docker run -d --name paddleocr --gpus all \
      -v paddleocr_models:/root/.paddleocr \
      -e OCR_LANG=ch -e OCR_USE_GPU=true -e OCR_MAX_CONCURRENCY=1 \
      -p 8891:8891 \
      paddleocr-api:gpu
   
4. 测试OCR API
curl -s http://127.0.0.1:8891/health 
{"status":"ok","gpu":true,"lang":"ch","max_concurrency":1}

5. RAGFlow ui上对接paddleocr和qianwen model
