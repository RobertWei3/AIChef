import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_ingestion():
    print("Testing Ingestion (测试导入)...")
    payload = {"path": "data/sample_recipes.json"}
    try:
        response = requests.post(f"{BASE_URL}/ingest", json=payload)
        response.raise_for_status()
        print("✅ Ingestion Successful (导入成功):", response.json())
    except Exception as e:
        print("❌ Ingestion Failed (导入失败):", e)
        sys.exit(1)

def test_generation():
    print("\nTesting Generation (测试生成)...")
    payload = {
        "ingredients": ["鸡肉", "面条"],
        "preferences": "简单快速"
    }
    try:
        response = requests.post(f"{BASE_URL}/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        if "recipe_text" in data:
            print("✅ Generation Successful (生成成功)")
            print("Preview (预览):", data["recipe_text"][:100] + "...")
        else:
            print("❌ Generation returned unexpected format (格式错误):", data)
    except Exception as e:
        print("❌ Generation Failed (生成失败):", e)

def test_fusion():
    print("\nTesting Fusion (测试融合)...")
    payload = {
        "ingredients": ["面包", "芝士"]
    }
    try:
        response = requests.post(f"{BASE_URL}/fusion", json=payload)
        response.raise_for_status()
        data = response.json()
        if "recipe_text" in data:
            print("✅ Fusion Successful (融合成功)")
        else:
            print("❌ Fusion returned unexpected format (格式错误):", data)
    except Exception as e:
        print("❌ Fusion Failed (融合失败):", e)

if __name__ == "__main__":
    # Ensure server is up (user needs to run it, but we can try to ping)
    try:
        requests.get(BASE_URL)
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please run 'uvicorn main:app --reload' in a separate terminal.")
        sys.exit(1)

    test_ingestion()
    test_generation()
    test_fusion()
