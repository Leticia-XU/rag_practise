RAGFlow + Xinference + PaddleOCR GPU 部署实践

本文记录一个完整的 私有 RAG 系统部署过程，包括：

RAGFlow 0.24.0

Xinference（Embedding + Rerank）

外部 LLM（Qwen on H100）

PaddleOCR（GPU）

NVIDIA L4 GPU

目标：

提升 RAGFlow 对 PDF / 图片 / 扫描文档 的解析能力。
(T4 GPU could not run RAG, so change solution as:  H100 run Qianwen model + L4 run RAG,  Xinference and Paddleocr)
                    ┌──────────────┐
                    │   User Query  │
                    └──────┬───────┘
                           │
                     ┌─────▼─────┐
                     │  RAGFlow   │
                     │  (CPU)     │
                     └─────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │                              │
     ┌──────▼───────┐               ┌───────▼───────────┐
     │ Xinference   │               │ PaddleOCR L4 GPU │
     │ Embedding    │               │ (Image/PDF)      │
     │ Rerank       │               └───────┬──────────┘
     └──────┬───────┘                       │
            │                               │
      ┌─────▼──────┐                 ┌──────▼──────┐
      │ Vector DB  │                 │ Document    │
      │ (RAGFlow)  │                 │ Parsing     │
      └─────┬──────┘                 └─────────────┘
            │
      ┌─────▼─────┐
      │  LLM(H100) │
      │  Qwen      │
      └───────────┘
