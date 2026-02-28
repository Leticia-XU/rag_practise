Private RAG Deployment Guide (Fully On-Premise)

🛠️ 第一阶段：系统环境预热
在 Ubuntu 24.04 上执行，确保内核参数满足 Elasticsearch 客户端与 Docker 容器的需求。

Bash
# 1. 提升内存映射限制（Elasticsearch 运行必备）
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# 2. 安装 Docker 与 Docker-Compose
sudo apt update && sudo apt install docker.io docker-compose-v2 -y
sudo systemctl start docker && sudo systemctl enable docker
🧠 第二阶段：部署 Qwen2-7B 推理后端
使用 vLLM 启动 AWQ 量化版模型。针对 T4 (16GB) 显存，我们优化了 gpu-memory-utilization 以预留 OCR 解析空间。

Bash
# 使用 nohup 在后台启动模型，防止 SSH 断开导致退出
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-7B-Instruct-AWQ \
  --quantization awq \
  --gpu-memory-utilization 0.80 \
  --max-model-len 4096 \
  --enforce-eager \
  --port 7777 > vllm.log 2>&1 &

# 验证启动状态（查看日志）
tail -f vllm.log
原理: --max-model-len 4096 确保了长文档阅读能力，同时 0.80 的显存利用率留出了约 3GB 缓冲区给系统与 RAGFlow 的图形处理。

📦 第三阶段：部署 RAGFlow (对接外部云 ES)
本方案弃用 Docker 内置 ES，改用云端专用 ES 7.10.2 以节省本地内存。

克隆仓库:

Bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/docker
配置环境变量 (.env):
修改以下字段以对接你的云 ES 实例：

Bash
ELASTICSEARCH_HOSTS=http://<你的云ES内网IP>:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=<你的密码>
STACK_VERSION=7.10.2
精简 docker-compose.yml:

原因: 物理内存受限，需删除/注释掉本地 es01 服务块。

操作: 在 docker-compose.yml 中删除 elasticsearch 服务定义，并移除 ragflow-server 对其的 depends_on。

一键启动:

Bash
sudo docker compose up -d
⚙️ 第四阶段：Web UI 配置 (关键优化)
访问 http://<服务器IP> 进入后台：

接入 Qwen2:

Provider: OpenAI-compatible

Base URL: http://<服务器内网IP>:7777/v1

Model Name: Qwen2-7B-Instruct-AWQ

显存保卫设置:

进入 System Model Settings。

将 Embedding Model (BAAI/bge-m3) 的 Device 强制设为 CPU。

原因: BGE-M3 在 CPU 跑速度尚可，但能节省 1-2GB 宝贵显存供 Qwen2 稳定运行。

解析模板:

创建数据集时选择 General。该模板会调用 OCR 自动识别中文设计稿中的图片和表格。

🌍 跨国协作设置 (Prompt)
为德国同事设置 System Prompt，确保跨语言理解：

"You are an AI assistant for a private engineering library. The source documents are Chinese design files. Please answer the user in English/German. Explicitly mention the page numbers and figure names when referencing diagrams."

🛑 管理与维护
查看状态: nvidia-smi 监控显存，确保 Usage 控制在 15GB 以下。

更新模型参数:

Bash
# 查找并关闭 vLLM
pkill -f vllm
# 修改命令后再次执行 nohup 启动
防火墙: 确保云安全组开启 80 (Web) 和 7777 (vLLM API) 端口。
