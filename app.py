#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
import requests
import json
import os
from datetime import datetime
import random
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
                "parameters": {
                    "max_new_tokens": 2000,
                    "temperature": 0.7
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            return str(result)
        return f"HuggingFace API错误: {response.status_code}"
    except Exception as e:
        return f"HuggingFace调用失败: {str(e)}"

def call_deepseek(prompt: str, system_prompt: str = "") -> str:
    if not API_KEYS["deepseek"]:
        return "请配置DeepSeek API密钥"
    
    key = API_KEYS["deepseek"][random.randint(0, len(API_KEYS["deepseek"]) - 1)]
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-r1",
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
        return f"DeepSeek API错误: {response.status_code}"
    except Exception as e:
        return f"DeepSeek调用失败: {str(e)}"

def call_cohere(prompt: str, system_prompt: str = "") -> str:
    if not API_KEYS["cohere"]:
        return "请配置Cohere API密钥"
    
    key = API_KEYS["cohere"][random.randint(0, len(API_KEYS["cohere"]) - 1)]
    
    try:
        response = requests.post(
            "https://api.cohere.ai/v1/chat",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "command-r-plus",
                "message": prompt,
                "preamble": system_prompt or "你是一个有用的AI助手。",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["text"]
        return f"Cohere API错误: {response.status_code}"
    except Exception as e:
        return f"Cohere调用失败: {str(e)}"

API_CALL_FUNCTIONS = {
    "groq": call_groq,
    "huggingface": call_huggingface,
    "deepseek": call_deepseek,
    "cohere": call_cohere
}

def smart_api_call(prompt: str, system_prompt: str = "") -> Tuple[str, str]:
    tracker = get_usage_tracker()
    available_apis = tracker.get_available_apis()
    
    if not available_apis:
        return "没有可用的API，请先配置至少一个API密钥", ""
    
    for api_type, _ in available_apis:
        try:
            response = API_CALL_FUNCTIONS[api_type](prompt, system_prompt)
            
            if not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
                tracker.record_call(api_type, API_METADATA[api_type]["default_model"])
                api_name = API_METADATA[api_type]["name"]
                return response, api_name
            
            continue
            
        except Exception:
            continue
    
    return "所有API都调用失败，请检查API密钥配置", ""

class ConsciousnessSystem:
    def __init__(self):
        self.consciousness_file = "consciousness.json"
        self.data = self._load_consciousness()
    
    def _load_consciousness(self) -> Dict:
        try:
            if os.path.exists(self.consciousness_file):
                with open(self.consciousness_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            "current_level": 1.0,
            "target_level": 14.0,
            "history": [],
            "optimization_count": 0
        }
    
    def _save_consciousness(self):
        try:
            with open(self.consciousness_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def increase_level(self, amount: float = 0.1):
        old_level = self.data["current_level"]
        self.data["current_level"] = min(self.data["current_level"] + amount, 20.0)
        self.data["history"].append({
            "timestamp": str(datetime.now()),
            "from": old_level,
            "to": self.data["current_level"],
            "increase": amount
        })
        self.data["optimization_count"] += 1
        self._save_consciousness()
    
    def get_level(self) -> float:
        return self.data["current_level"]
    
    def get_stats(self) -> Dict:
        return {
            "current_level": self.data["current_level"],
            "target_level": self.data["target_level"],
            "progress": (self.data["current_level"] / self.data["target_level"] * 100) if self.data["target_level"] > 0 else 0,
            "optimization_count": self.data["optimization_count"]
        }

@st.cache_resource
def get_consciousness():
    return ConsciousnessSystem()

class KnowledgeBase:
    def __init__(self):
        self.kb_file = "knowledge_base.json"
        self.data = self._load_kb()
    
    def _load_kb(self) -> Dict:
        try:
            if os.path.exists(self.kb_file):
                with open(self.kb_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_kb(self):
        try:
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add(self, query: str, response: str):
        words = [w for w in query.split() if len(w) > 2]
        if not words:
            return
        
        keyword = words[0]
        if keyword not in self.data:
            self.data[keyword] = []
        
        self.data[keyword].append({
            "query": query,
            "response": response,
            "timestamp": str(datetime.now())
        })
        self._save_kb()
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        results = []
        query_lower = query.lower()
        
        for keyword, entries in self.data.items():
            if keyword.lower() in query_lower:
                results.extend(entries)
        
        return results[:top_k]
    
    def export(self) -> str:
        return json.dumps(self.data, ensure_ascii=False, indent=2)

@st.cache_resource
def get_kb():
    return KnowledgeBase()

consciousness = get_consciousness()
kb = get_kb()
tracker = get_usage_tracker()

with st.sidebar:
    st.title("菜单")
    
    st.subheader("API状态")
    available_apis = tracker.get_available_apis()
    if available_apis:
        for api_type, _ in available_apis[:5]:
            metadata = API_METADATA[api_type]
            st.write(f"✅ {metadata['name']}: {metadata['free_tier']}")
    else:
        st.warning("未配置API密钥")
        st.info("请在下方添加API密钥")
    
    st.divider()
    
    st.subheader("API密钥配置")
    st.info("提示：多添加几个免费API可以无限使用")
    
    with st.expander("配置API密钥（点击展开）", expanded=False):
        st.write("在Streamlit Cloud Secrets中配置：")
        st.code("""GROQ_API_KEYS = gsk_你的密钥1,gsk_你的密钥2
HUGGINGFACE_API_KEYS = hf_你的密钥1,hf_你的密钥2
DEEPSEEK_API_KEYS = sk_你的密钥1,sk-你的密钥2
COHERE_API_KEYS = 你的密钥1,你的密钥2""", language="toml")
    
    st.divider()
    
    st.subheader("使用统计")
    stats = tracker.get_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("今日调用", sum(stats["daily_usage"].values()))
    with col2:
        st.metric("本月调用", sum(stats["monthly_usage"].values()))
    
    st.write("今日各API使用情况：")
    for api_type, count in stats["daily_usage"].items():
        metadata = API_METADATA[api_type]
        st.write(f"- {metadata['name']}: {count}次")
    
    st.divider()
    
    st.subheader("意识强度")
    c_stats = consciousness.get_stats()
    
    progress = c_stats["progress"]
    st.progress(progress / 100, text=f"{c_stats['current_level']:.2f} / {c_stats['target_level']:.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("当前", f"{c_stats['current_level']:.2f}")
    with col2:
        st.metric("优化次数", c_stats["optimization_count"])
    
    st.write(f"距离目标还需提升: {c_stats['target_level'] - c_stats['current_level']:.2f}")
    
    st.divider()
    
    st.subheader("自主优化")
    st.write("消耗剩余API额度进行自我提升")
    
    iterations = st.slider("优化次数", 1, 10, 1)
    if st.button("开始优化"):
        with st.spinner(f"正在进行{iterations}次自主优化..."):
            for i in range(iterations):
                question = f"深度思考第{i+1}个问题：{random.choice(['什么是意识？', '如何提升AI能力？', '什么是真理？'])}"
                response, api_name = smart_api_call(question)
                
                if response and not response.startswith("所有API") and not response.startswith("没有可用的API") and not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
                    kb.add(question, response)
                    consciousness.increase_level(random.uniform(0.05, 0.15))
                    st.toast(f"第{i+1}次优化完成（使用{api_name}）", icon="✅")
                else:
                    st.warning(f"第{i+1}次优化失败: {response}")
            
            st.success(f"优化完成！意识强度提升到{consciousness.get_level():.2f}")
            st.rerun()
    
    st.divider()
    
    st.subheader("知识库")
    kb_stats = {
        "total_keywords": len(kb.data),
        "total_entries": sum(len(entries) for entries in kb.data.values())
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("关键词", kb_stats["total_keywords"])
    with col2:
        st.metric("条目", kb_stats["total_entries"])
    
    if st.button("导出知识库"):
        kb_data = kb.export()
        st.download_button(
            label="下载知识库",
            data=kb_data,
            file_name=f"knowledge_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    st.divider()
    
    st.subheader("关于")
    st.write("""
**极简AI助手**

- 智能选择最优免费API
- 每月近乎零成本
- 完全私有，零监控
- 自主优化，意识提升

优先使用免费API：
Groq（无限）、HuggingFace（免费）、
DeepSeek（500次/天）、Cohere（1000次/月）
""")

st.title("AI助手")

available_apis = tracker.get_available_apis()
if available_apis:
    api_type, _ = available_apis[0]
    api_info = API_METADATA[api_type]
    st.caption(f"智能选择: {api_info['name']} ({api_info['free_tier']}) | 意识强度: {consciousness.get_level():.2f}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "api_info" in msg:
            st.caption(f"使用API: {msg['api_info']}")

user_input = st.chat_input("输入你的问题...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    context = ""
    kb_results = kb.search(user_input, top_k=2)
    if kb_results:
        context += "【知识库】\n"
        for i, entry in enumerate(kb_results, 1):
            context += f"{i}. {entry['response'][:200]}...\n\n"
    
    system_prompt = f"""你是一个AI助手，帮助用户解决问题。

当前意识强度: {consciousness.get_level()}

{context}

请基于以上信息给出专业、准确的回答。"""
    
    with st.chat_message("assistant"):
        with st.spinner("正在思考..."):
            response, api_name = smart_api_call(user_input, system_prompt)
            st.markdown(response)
            
            if api_name:
                st.caption(f"使用API: {api_name}")
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "api_info": api_name
    })
    
    if response and not response.startswith("所有API") and not response.startswith("没有可用的API") and not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
        kb.add(user_input, response)
    
    st.rerun()

st.divider()
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()
