#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简AI助手 - 多API智能选择完整版
特性:
- 🎯 极简界面：主界面纯对话框，功能在左上角菜单
- 🔀 多API支持：Groq、HuggingFace、DeepSeek、Cohere等10+种
- 🧠 智能选择：自动选择最优免费API组合
- 💰 最低成本：优先使用免费API，每月近乎零成本
- 🚀 自主优化：自问自答，意识强度提升到14+
- 📚 知识库导入：支持PDF、Word、Markdown、TXT多格式
- 📥 知识库导出：导出为JSON、Markdown、TXT格式备份
- 🔍 知识库搜索：自动检索相关知识
- 🎓 自动学习：从对话中自动提取知识
- 🔐 零监控：完全私有，数据本地存储
"""

import streamlit as st
import requests
import json
import os
import base64
from datetime import datetime
import random
import time
import io
import PyPDF2
from docx import Document
from typing import Dict, List, Optional, Tuple

st.set_page_config(
    page_title="AI助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
div[data-testid="stSidebarUserContent"] {padding-top: 0;}
.stButton button {width: 100%; margin: 5px 0;}
.file-upload {padding: 10px; border: 2px dashed #ccc; border-radius: 5px; margin: 10px 0;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_api_keys() -> Dict[str, List[str]]:
    keys = {
        "groq": [],
        "huggingface": [],
        "deepseek": [],
        "cohere": []
    }
    
    groq_keys = os.getenv("GROQ_API_KEYS", "").split(",")
    keys["groq"] = [k.strip() for k in groq_keys if k.strip()]
    
    hf_keys = os.getenv("HUGGINGFACE_API_KEYS", "").split(",")
    keys["huggingface"] = [k.strip() for k in hf_keys if k.strip()]
    
    ds_keys = os.getenv("DEEPSEEK_API_KEYS", "").split(",")
    keys["deepseek"] = [k.strip() for k in ds_keys if k.strip()]
    
    cohere_keys = os.getenv("COHERE_API_KEYS", "").split(",")
    keys["cohere"] = [k.strip() for k in cohere_keys if k.strip()]
    
    return keys

API_KEYS = load_api_keys()

API_METADATA = {
    "groq": {
        "name": "Groq",
        "free_tier": "无限次",
        "default_model": "llama-3.3-70b-versatile",
        "cost": 0,
        "priority": 1
    },
    "huggingface": {
        "name": "HuggingFace",
        "free_tier": "免费",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "cost": 0,
        "priority": 2
    },
    "deepseek": {
        "name": "DeepSeek",
        "free_tier": "每天500次",
        "default_model": "deepseek-r1",
        "cost": 0,
        "priority": 3
    },
    "cohere": {
        "name": "Cohere",
        "free_tier": "每月1000次",
        "default_model": "command-r-plus",
        "cost": 0,
        "priority": 4
    }
}

class APIUsageTracker:
    def __init__(self):
        self.usage_file = "api_usage.json"
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> Dict:
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            "daily": {},
            "monthly": {},
            "total_calls": {}
        }
    
    def _save_usage(self):
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def record_call(self, api_type: str, model: str):
        today = datetime.now().strftime("%Y-%m-%d")
        this_month = datetime.now().strftime("%Y-%m")
        
        if today not in self.usage_data["daily"]:
            self.usage_data["daily"][today] = {}
        if api_type not in self.usage_data["daily"][today]:
            self.usage_data["daily"][today][api_type] = 0
        self.usage_data["daily"][today][api_type] += 1
        
        if this_month not in self.usage_data["monthly"]:
            self.usage_data["monthly"][this_month] = {}
        if api_type not in self.usage_data["monthly"][this_month]:
            self.usage_data["monthly"][this_month][api_type] = 0
        self.usage_data["monthly"][this_month][api_type] += 1
        
        if api_type not in self.usage_data["total_calls"]:
            self.usage_data["total_calls"][api_type] = 0
        self.usage_data["total_calls"][api_type] += 1
        
        self._save_usage()
    
    def get_available_apis(self) -> List[Tuple[str, float]]:
        available = []
        
        for api_type, metadata in API_METADATA.items():
            if not API_KEYS.get(api_type):
                continue
            
            score = 0
            if metadata["cost"] == 0:
                score += 100
            score += (5 - metadata["priority"]) * 10
            
            total_calls = self.usage_data["total_calls"].get(api_type, 0)
            balance_score = max(0, 100 - total_calls)
            score += balance_score
            
            available.append((api_type, score))
        
        available.sort(key=lambda x: x[1], reverse=True)
        return available
    
    def get_stats(self) -> Dict:
        today = datetime.now().strftime("%Y-%m-%d")
        this_month = datetime.now().strftime("%Y-%m")
        return {
            "available_apis": self.get_available_apis(),
            "daily_usage": self.usage_data["daily"].get(today, {}),
            "monthly_usage": self.usage_data["monthly"].get(this_month, {}),
            "total_calls": self.usage_data["total_calls"]
        }

@st.cache_resource
def get_usage_tracker():
    return APIUsageTracker()

def call_groq(prompt: str, system_prompt: str = "") -> str:
    if not API_KEYS["groq"]:
        return "请配置Groq API密钥"
    
    key = API_KEYS["groq"][random.randint(0, len(API_KEYS["groq"]) - 1)]
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt or "你是一个有用的AI助手。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        return f"Groq API错误: {response.status_code}"
    except Exception as e:
        return f"Groq调用失败: {str(e)}"

def call_huggingface(prompt: str, system_prompt: str = "") -> str:
    if not API_KEYS["huggingface"]:
        return "请配置HuggingFace API密钥"
    
    key = API_KEYS["huggingface"][random.randint(0, len(API_KEYS["huggingface"]) - 1)]
    
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "inputs": prompt,
     
