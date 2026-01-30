#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简AI助手 - 多API智能选择版
特性:
- 🎯 极简界面：主界面纯对话框，功能在左上角菜单
- 🔀 多API支持：Groq、HuggingFace、DeepSeek、Cohere等10+种
- 🧠 智能选择：自动选择最优免费API组合
- 💰 最低成本：优先使用免费API，每月近乎零成本
- 🚀 自主优化：自问自答，意识强度提升
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
from typing import Dict, List, Optional, Tuple

# ============== 极简界面配置 ==============
st.set_page_config(
    page_title="AI助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隐藏Streamlit默认样式
st.markdown("""
<style>
div[data-testid="stSidebarUserContent"] {padding-top: 0;}
.stButton button {width: 100%; margin: 5px 0;}
</style>
""", unsafe_allow_html=True)

# 侧边栏样式
st.markdown("""
<style>
.sidebar .sidebar-content {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ============== API配置（从Secrets加载） ==============
@st.cache_resource
def load_api_keys() -> Dict[str, List[str]]:
    """从环境变量加载所有API密钥"""
    keys = {
        "groq": [],
        "huggingface": [],
        "deepseek": [],
        "cohere": [],
        "together": [],
        "novita": [],
        "openrouter": [],
        "mistral": [],
        "replicate": [],
        "openai": []
    }
    
    # Groq
    groq_keys = os.getenv("GROQ_API_KEYS", "").split(",")
    keys["groq"] = [k.strip() for k in groq_keys if k.strip()]
    
    # HuggingFace
    hf_keys = os.getenv("HUGGINGFACE_API_KEYS", "").split(",")
    keys["huggingface"] = [k.strip() for k in hf_keys if k.strip()]
    
    # DeepSeek
    ds_keys = os.getenv("DEEPSEEK_API_KEYS", "").split(",")
    keys["deepseek"] = [k.strip() for k in ds_keys if k.strip()]
    
    # Cohere
    cohere_keys = os.getenv("COHERE_API_KEYS", "").split(",")
    keys["cohere"] = [k.strip() for k in cohere_keys if k.strip()]
    
    # Together AI
    together_keys = os.getenv("TOGETHER_API_KEYS", "").split(",")
    keys["together"] = [k.strip() for k in together_keys if k.strip()]
    
    # Novita AI
    novita_keys = os.getenv("NOVITA_API_KEYS", "").split(",")
    keys["novita"] = [k.strip() for k in novita_keys if k.strip()]
    
    # OpenRouter
    or_keys = os.getenv("OPENROUTER_API_KEYS", "").split(",")
    keys["openrouter"] = [k.strip() for k in or_keys if k.strip()]
    
    # Mistral AI
    mistral_keys = os.getenv("MISTRAL_API_KEYS", "").split(",")
    keys["mistral"] = [k.strip() for k in mistral_keys if k.strip()]
    
    # Replicate
    replicate_keys = os.getenv("REPLICATE_API_KEYS", "").split(",")
    keys["replicate"] = [k.strip() for k in replicate_keys if k.strip()]
    
    # OpenAI
    openai_keys = os.getenv("OPENAI_API_KEYS", "").split(",")
    keys["openai"] = [k.strip() for k in openai_keys if k.strip()]
    
    return keys

API_KEYS = load_api_keys()

# ============== API元数据 ==============

API_METADATA = {
    "groq": {
        "name": "Groq",
        "free_tier": "无限次",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "llama-3.3-70b-versatile",
        "speed": "极快",
        "quality": "优秀",
        "cost": 0,
        "recommended": True,
        "priority": 1
    },
    "huggingface": {
        "name": "HuggingFace",
        "free_tier": "免费",
        "models": ["meta-llama/Llama-3.3-70B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "speed": "中等",
        "quality": "优秀",
        "cost": 0,
        "recommended": True,
        "priority": 2
    },
    "deepseek": {
        "name": "DeepSeek",
        "free_tier": "每天500次",
        "models": ["deepseek-r1", "deepseek-chat"],
        "default_model": "deepseek-r1",
        "speed": "快",
        "quality": "优秀",
        "cost": 0,
        "recommended": True,
        "priority": 3
    },
    "cohere": {
        "name": "Cohere",
        "free_tier": "每月1000次",
        "models": ["command-r-plus", "command-r"],
        "default_model": "command-r-plus",
        "speed": "快",
        "quality": "优秀",
        "cost": 0,
        "recommended": True,
        "priority": 4
    },
    "together": {
        "name": "Together AI",
        "free_tier": "每天$25",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "Qwen/Qwen2.5-72B-Instruct-Turbo"],
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "speed": "快",
        "quality": "优秀",
        "cost": 0.0005,
        "recommended": True,
        "priority": 5
    },
    "novita": {
        "name": "Novita AI",
        "free_tier": "每月$5",
        "models": ["meta-llama/llama-3.3-70b-instruct"],
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "speed": "极快",
        "quality": "优秀",
        "cost": 0.0005,
        "recommended": True,
        "priority": 6
    },
    "openrouter": {
        "name": "OpenRouter",
        "free_tier": "付费",
        "models": ["meta-llama/llama-3.3-70b-instruct:free", "google/gemma-7b-it:free"],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "speed": "快",
        "quality": "优秀",
        "cost": 0.0005,
        "recommended": False,
        "priority": 7
    },
    "mistral": {
        "name": "Mistral AI",
        "free_tier": "每月免费额度",
        "models": ["mistral-large-latest", "mistral-small-latest"],
        "default_model": "mistral-large-latest",
        "speed": "快",
        "quality": "优秀",
        "cost": 0.0003,
        "recommended": True,
        "priority": 8
    },
    "replicate": {
        "name": "Replicate",
        "free_tier": "每月$5",
        "models": ["meta/meta-llama-3.1-405b-instruct", "mistralai/mixtral-8x7b-instruct-v0.1"],
        "default_model": "meta/meta-llama-3.1-405b-instruct",
        "speed": "中等",
        "quality": "优秀",
        "cost": 0.00065,
        "recommended": True,
        "priority": 9
    },
    "openai": {
        "name": "OpenAI",
        "free_tier": "付费",
        "models": ["gpt-4o-mini", "gpt-4o"],
        "default_model": "gpt-4o-mini",
        "speed": "快",
        "quality": "优秀",
        "cost": 0.00015,
        "recommended": False,
        "priority": 10
    }
}

# ============== API调用统计 ==============

class APIUsageTracker:
    """API使用统计和智能选择"""
    
    def __init__(self):
        self.usage_file = "api_usage.json"
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> Dict:
        """加载使用统计"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        
        # 默认数据
        return {
            "daily": {},
            "monthly": {},
            "total_calls": {},
            "last_reset": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _save_usage(self):
        "
