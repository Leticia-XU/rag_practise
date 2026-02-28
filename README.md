# rag_practise
# 📚 Qwen2-7B-Instruct-AWQ(T4 GPU) + RAGFlow(CPU ) + Xinference(CPU) ，单机  RAG 实战总结

## 🎯 项目目标

构建一个基于私有中文设计文档的 RAG 系统，实现：

- 上传 PDF / Word 设计文档（含图片）
- 支持跨语言检索（中文文档 → 英文/德文提问）
- AI 自动检索知识库并给出专业建议
- 单机部署，llm模型用T4, embedding和rerank用CPU 运行

使用对象：海外（德国）同事

---

# 🏗 系统架构
用户（英文/德文提问）

↓

RAGFlow Assistant

↓

Embedding（bge-m3）

↓

Elasticsearch 向量检索

↓

Rerank（bge-reranker-v2-m3）

↓

Qianwen 生成回答


# 🧩 技术栈

| 组件 | 作用 |
|------|------|
| RAGFlow 0.24.0 | RAG 框架 |
| Xinference | 本地模型推理服务 |
| Qianwen | LLM |
| bge-m3 | 多语言 embedding |
| bge-reranker-v2-m3 | 精排模型 |
| Elasticsearch | 向量存储 |
| MinIO | 原始文档存储 |
| MySQL | 元数据 |

# ⚙ Docker 部署结构(docker ps --format "{{.Names}}")
xinference

docker-ragflow-cpu-1

docker-redis-1

docker-minio-1

docker-es01-1

docker-mysql-1




# 🧠 关键注意事项

1️⃣ RAGFlow 不再内置 embedding

从 0.22+ 开始：

不再自带 bge 模型

必须外接模型服务（如 Xinference）

2️⃣ TopK vs TopN 区别
| 参数   | 含义                 |
| ---- | ------------------ |
| TopK | 向量召回数量             |
| TopN | rerank 后送给 LLM 的数量 |

Xinference(CPU) 模型下，推荐值：
TopK = 10
TopN = 3

3️⃣ Search vs Chat 区别

功能	是否调用 LLM

Search	❌ 否

Chat	✅ 是


Search 仅调试召回是否正确

Chat 才是完整 RAG 流程

4️⃣ bge-m3 适合跨语言

中文文档

英文/德文提问

多语言向量空间统一

不建议使用 bge-large-zh（仅中文）

5️⃣ embedding进度查询

docker stats

如果 xinference CPU > 200%，说明正在计算。


