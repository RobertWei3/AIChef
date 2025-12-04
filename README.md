# 🥦 AIChef - Fridge Rescue Assistant

> **"Don't know what to cook with your leftovers? Let AI Chef save the day!"**

![App Demo](image_21c592.jpg)

## 📖 Introduction

**AIChef** is an intelligent cooking assistant powered by **RAG (Retrieval-Augmented Generation)** technology. Unlike traditional recipe search engines, AIChef focuses on the **"Fridge Rescue"** scenario.

Users simply input the ingredients currently available in their fridge (e.g., *"I only have half an onion and two eggs"*). The system will:
1.  **Retrieve**: Search through a local vector database (ChromaDB) containing 10,000+ recipes to find the most relevant culinary inspirations.
2.  **Generate**: Use a Large Language Model (LLM) to act as a creative chef, teaching users how to adapt existing recipes to their limited ingredients—turning "leftovers" into delicious meals.

## ✨ Key Features

* **🥗 Smart Ingredient Matching**: Uses semantic search to understand ingredients (e.g., suggesting chicken if pork is missing).
* **💡 Adaptive Cooking Instructions**: The AI doesn't just copy-paste recipes; it intelligently modifies steps based on what you actually have.
* **⚡ Fast Local Retrieval**: Built on ChromaDB and BAAI Embeddings for millisecond-level response times.
* **💬 Interactive UI**: A clean, chat-based interface built with Streamlit, featuring streaming responses and recipe citations.
* **🔌 Flexible LLM Support**: Compatible with any OpenAI-style API (SiliconFlow Qwen, DeepSeek, Google Gemini, etc.).

## 🛠 Tech Stack

* **Frontend**: Streamlit, React, Node, HTML
* **Backend Logic**: Python, LangChain
* **Vector Database**: ChromaDB, FAISS
* **Embedding Model**: BAAI/bge-small-zh-v1.5 (HuggingFace)
* **LLM**: OpenAI-compatible APIs (SiliconFlow, DeepSeek, Google Gemini)

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone [https://github.com/your-username/AIChef.git](https://github.com/your-username/AIChef.git)
cd AIChef

# Create and activate a virtual environment (Recommended)
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
# or using uv
uv add requirements.txt