Private RAG Deployment Guide (Fully On-Premise)
。

## 🛠️ 第一阶段：系统环境预热
在 Ubuntu 24.04 上执行，确保内核参数满足 Elasticsearch 客户端与 Docker 容器的需求。

```Bash
# 1. 提升内存映射限制（Elasticsearch 运行必备）
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# 2. 安装 Docker 与 Docker-Compose
sudo apt update && sudo apt install docker.io docker-compose-v2 -y
sudo systemctl start docker && sudo systemctl enable docker
```

## 🧠 第二阶段：启动 Qwen2-7B 推理后端
使用 vLLM 启动 AWQ 量化版模型。针对 T4 (16GB) 显存，我们优化了 gpu-memory-utilization 以预留 OCR 解析空间。

```Bash
#进入虚拟环境
conda activate llm_eval

# 使用 nohup 在后台启动模型，防止 SSH 断开导致退出
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-7B-Instruct-AWQ \
  --quantization awq \
  --gpu-memory-utilization 0.80 \
  --max-model-len 4096 \
  --enforce-eager \
  --port **** > vllm.log 2>&1 &

# 验证启动状态（查看日志）
tail -f vllm.log

#测试模型是否启动，查看uid
 curl http://localhost:****/v1/models

```

原理: --max-model-len 4096 确保了长文档阅读能力，同时 0.80 的显存利用率留出了约 3GB 缓冲区给系统与 RAGFlow 的图形处理。

## 📦 第三阶段：部署 RAGFlow 

1. 克隆仓库:

```Bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/docker
```

2. 启动ragflow-cpu

   ragflow 0.24.0版本不再内置embedding和rerank模型，因此不需要修改 docker-compose.yml，禁用GPU:

一键启动:

```Bash
sudo docker compose up -d ragflow-cpu
```

## 📦 第四阶段：部署 Xinference 

1. 用 Xinference 在同一台服务器提供 Embedding + Rerank（CPU）:
   
1）起一个 Xinference（CPU）容器

在宿主机创建持久化目录（避免模型每次重下）：
```Bash
mkdir -p /opt/xinference
```
启动 Xinference（CPU 镜像）：

```Bash
docker run -d --name xinference \
  -p 9997:9997 \
  -e XINFERENCE_HOME=/data \
  -v /opt/xinference:/data \
  xprobe/xinference:latest-cpu \
  xinference-local -H 0.0.0.0
```

说明：xprobe/xinference:latest-cpu 是官方提供的 CPU 用法之一；端口默认服务在 9997。

2）在 Xinference 里启动两个模型（Embedding + Rerank）

进入容器：

```Bash
docker exec -it xinference bash
```
启动 embedding（bge-m3）：
```Bash
xinference launch --model-type embedding --model-name bge-m3
```

启动 rerank（bge-reranker-v2-m3）：
```Bash
xinference launch --model-type rerank --model-name bge-reranker-v2-m3
```

## ⚙️  第五阶段：RAGFlow UI 接入大模型 
 
1. 在 RAGFlow UI 里接入 Xinference（Embedding + Rerank）

在浏览器上访问 http://<服务器IP> 进入UI

注册账号

#右上角头像（或你的 Logo） → Model providers → 添加 Xinference。

UID: bge-m3

Embedding 的 Base URL 填：

http://172.17.0.1:9997/v1

最大token数：512

UID: bge-reranker-v2-m3
Rerank 要单独用这个 Base URL（非常关键）：

http://172.17.0.1:9997/v1/rerank

最大token数：512



2. 在 RAGFlow UI 里接入Qwen2 

在浏览器上访问 http://<服务器IP> 进入UI：

#右上角头像（或你的 Logo） → Model providers →添加LLM
接入 Qwen2:

Provider: OpenAI-compatible

Base URL: http://172.17.0.1:****/v1

Model Name: Qwen/Qwen2-7B-Instruct-AWQ

最大token数： 4096


3.保存后，设置ragflow默认模型配置

#右上角头像（或你的 Logo） → Model providers ->设置默认模型：

LLM 选 Qwen/Qwen2-7B-Instruct-AWQ

Embedding 选 bge-m3

Rerank 选 bge-reranker-v2-m3

## 🌍 第六阶段：创建知识库，上传文档

## 🌍 第七阶段：跨国协作设置 (Prompt)
为德国同事设置 System Prompt，确保跨语言理解：

"You are an AI assistant for a private engineering library. The source documents are Chinese design files. Please answer the user in English/German. Explicitly mention the page numbers and figure names when referencing diagrams."

## 🛑 其他：管理与维护

#1. 查看状态: nvidia-smi 监控显存，确保 Usage 控制在 15GB 以下。

#2. 测试embedding模型是否启用

进入 ragflow 容器：
```Bash
docker exec -it docker-ragflow-cpu-1 bash
```
测试：
```Bash
curl http://172.17.0.1:9997/v1/models
```
如果能返回 JSON，说明能用。

#3. 防火墙: 
确保云安全组开启 80 (Web) 和 **** (vLLM API) , embedding端口9997。

