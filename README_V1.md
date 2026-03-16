原先T4 GPU 运行存在2个问题：中文图片无法解析（用Paddleocr优化）, 问答时很容易触发上下文token上限， 优化配置如下:  一台H100专门跑Qianwen model，上下文设置为2048， 一台L4跑 Xinference 和 Paddleocr

这里描述差一點：
1. 部署 Xinference（Embedding + Rerank），GPU打开
docker run -d \
  --name xinference \
  --gpus all \
  -p 9997:9997 \
  xinference/xinference:latest

2. 构建OCR API服务
   
