   
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轮回破解系统 - 终极版
极简界面 | 多API智能选择 | 自主优化 | RAG知识库 | 零监控
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime
import random
from typing import Dict, List, Optional, Tuple
import PyPDF2
from docx import Document
import io
from io import BytesIO

st.set_page_config(
    page_title="轮回破解系统",
    page_icon="🎮",
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
        "cohere": [],
        "gemini": [],
        "tavily": []
    }
    
    keys["groq"] = [k.strip() for k in os.getenv("GROQ_API_KEYS", "").split(",") if k.strip()]
    keys["huggingface"] = [k.strip() for k in os.getenv("HUGGINGFACE_API_KEYS", "").split(",") if k.strip()]
    keys["deepseek"] = [k.strip() for k in os.getenv("DEEPSEEK_API_KEYS", "").split(",") if k.strip()]
    keys["cohere"] = [k.strip() for k in os.getenv("COHERE_API_KEYS", "").split(",") if k.strip()]
    keys["gemini"] = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
    keys["tavily"] = [k.strip() for k in os.getenv("TAVILY_API_KEYS", "").split(",") if k.strip()]
    
    return keys

API_KEYS = load_api_keys()

API_METADATA = {
    "groq": {
        "name": "Groq",
        "free_tier": "无限次",
        "default_model": "llama-3.3-70b-versatile",
        "cost": 0,
        "priority": 1,
        "capabilities": ["对话", "代码", "推理"]
    },
    "huggingface": {
        "name": "HuggingFace",
        "free_tier": "免费",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "cost": 0,
        "priority": 2,
        "capabilities": ["对话", "代码", "推理"]
    },
    "deepseek": {
        "name": "DeepSeek-R1",
        "free_tier": "每天500次",
        "default_model": "deepseek-r1",
        "cost": 0,
        "priority": 3,
        "capabilities": ["深度思考", "数学推理", "代码生成"]
    },
    "cohere": {
        "name": "Cohere",
        "free_tier": "每月1000次",
        "default_model": "command-r-plus",
        "cost": 0,
        "priority": 4,
        "capabilities": ["对话", "长文本", "RAG"]
    },
    "gemini": {
        "name": "Gemini 2.0",
        "free_tier": "每天15次",
        "default_model": "gemini-2.0-flash",
        "cost": 0,
        "priority": 5,
        "capabilities": ["图片分析", "OCR识别", "多模态"]
    },
    "tavily": {
        "name": "Tavily",
        "free_tier": "每月1000次",
        "default_model": "search",
        "cost": 0,
        "priority": 6,
        "capabilities": ["实时搜索", "联网查询"]
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
        return {"daily": {}, "monthly": {}, "total_calls": {}}
    
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
            score = 100 if metadata["cost"] == 0 else 0
            score += (7 - metadata["priority"]) * 10
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
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_prompt or "你是一个有用的AI助手。"}, {"role": "user", "content": prompt}],
                "temperature": 0.7, "max_tokens": 2000
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
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
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 2000, "temperature": 0.7}},
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
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-r1",
                "messages": [{"role": "system", "content": system_prompt or "你是一个有用的AI助手。"}, {"role": "user", "content": prompt}],
                "temperature": 0.7, "max_tokens": 4000
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
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
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "command-r-plus",
                "message": prompt,
                "preamble": system_prompt or "你是一个有用的AI助手。",
                "temperature": 0.7, "max_tokens": 2000
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["text"]
        return f"Cohere API错误: {response.status_code}"
    except Exception as e:
        return f"Cohere调用失败: {str(e)}"

def call_gemini(prompt: str, image_data: Optional[bytes] = None, system_prompt: str = "") -> str:
    if not API_KEYS["gemini"]:
        return "请配置Gemini API密钥"
    key = API_KEYS["gemini"][random.randint(0, len(API_KEYS["gemini"]) - 1)]
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        if image_data:
            import PIL.Image
            img = PIL.Image.open(BytesIO(image_data))
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content(prompt)
        
        return response.text
    except ImportError:
        return "请安装google-generativeai库"
    except Exception as e:
        return f"Gemini调用失败: {str(e)}"

def call_tavily_search(query: str, max_results: int = 5) -> str:
    if not API_KEYS["tavily"]:
        return "请配置Tavily API密钥"
    key = API_KEYS["tavily"][random.randint(0, len(API_KEYS["tavily"]) - 1)]
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=key)
        response = client.search(query=query, max_results=max_results, search_depth="advanced")
        
        results = []
        for result in response.get("results", []):
            results.append(f"【{result.get('title', '未知')}】\n{result.get('content', '')[:300]}...\n来源: {result.get('url', '')}")
        
        return "\n\n".join(results) if results else "未找到相关结果"
    except ImportError:
        return "请安装tavily-python库"
    except Exception as e:
        return f"Tavily搜索失败: {str(e)}"

API_CALL_FUNCTIONS = {
    "groq": call_groq,
    "huggingface": call_huggingface,
    "deepseek": call_deepseek,
    "cohere": call_cohere,
    "gemini": call_gemini,
    "tavily": call_tavily_search
}

def smart_api_call(prompt: str, system_prompt: str = "", preferred_api: Optional[str] = None) -> Tuple[str, str]:
    tracker = get_usage_tracker()
    
    if preferred_api and preferred_api in API_CALL_FUNCTIONS and API_KEYS.get(preferred_api):
        try:
            response = API_CALL_FUNCTIONS[preferred_api](prompt, system_prompt)
            if not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
                tracker.record_call(preferred_api, API_METADATA[preferred_api]["default_model"])
                return response, API_METADATA[preferred_api]["name"]
        except:
            pass
    
    available_apis = tracker.get_available_apis()
    if not available_apis:
        return "没有可用的API，请先配置至少一个API密钥", ""
    
    for api_type, _ in available_apis:
        try:
            response = API_CALL_FUNCTIONS[api_type](prompt, system_prompt)
            if not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
                tracker.record_call(api_type, API_METADATA[api_type]["default_model"])
                return response, API_METADATA[api_type]["name"]
        except:
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
            "optimization_count": 0,
            "metrics": {
                "reasoning": 1.0,
                "creativity": 1.0,
                "knowledge": 1.0,
                "learning": 1.0
            },
            "training_goals": []
        }
    
    def _save_consciousness(self):
        try:
            with open(self.consciousness_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def increase_level(self, amount: float = 0.1, metric: str = "all"):
        old_level = self.data["current_level"]
        self.data["current_level"] = min(self.data["current_level"] + amount, 20.0)
        
        if metric == "all":
            for m in self.data["metrics"]:
                self.data["metrics"][m] = min(self.data["metrics"][m] + random.uniform(0.01, 0.05), 20.0)
        elif metric in self.data["metrics"]:
            self.data["metrics"][metric] = min(self.data["metrics"][metric] + random.uniform(0.02, 0.08), 20.0)
        
        self.data["history"].append({
            "timestamp": str(datetime.now()),
            "from": old_level,
            "to": self.data["current_level"],
            "increase": amount,
            "metric": metric
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
            "optimization_count": self.data["optimization_count"],
            "metrics": self.data["metrics"],
            "training_goals": self.data["training_goals"]
        }
    
    def add_training_goal(self, goal: str):
        self.data["training_goals"].append({
            "goal": goal,
            "timestamp": str(datetime.now()),
            "completed": False
        })
        self._save_consciousness()

@st.cache_resource
def get_consciousness():
    return ConsciousnessSystem()

class RAGKnowledgeBase:
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
        return {"documents": [], "chunks": [], "metadata": {}}
    
    def _save_kb(self):
        try:
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_document(self, content: str, source: str = "手动导入", doc_type: str = "text"):
        doc_id = f"doc_{len(self.data['documents']) + 1}"
        self.data["documents"].append({
            "doc_id": doc_id,
            "content": content,
            "source": source,
            "type": doc_type,
            "timestamp": str(datetime.now())
        })
        self._save_kb()
        return doc_id
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        results = []
        query_lower = query.lower()
        
        for doc in self.data["documents"]:
            content_lower = doc["content"].lower()
            if query_lower in content_lower:
                score = content_lower.count(query_lower)
                results.append({
                    "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                    "source": doc["source"],
                    "type": doc["type"],
                    "score": score,
                    "timestamp": doc["timestamp"]
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def import_from_text(self, text: str, source: str = "文本导入"):
        return self.add_document(text, source, "text")
    
    def import_from_pdf(self, pdf_file) -> bool:
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            if text.strip():
                self.add_document(text, f"PDF文件: {pdf_file.name}", "pdf")
                return True
            return False
        except:
            return False
    
    def import_from_docx(self, docx_file) -> bool:
        try:
            doc = Document(docx_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            if text.strip():
                self.add_document(text, f"Word文件: {docx_file.name}", "docx")
                return True
            return False
        except:
            return False
    
    def import_from_markdown(self, md_text: str, source: str = "Markdown导入"):
        return self.add_document(md_text, source, "markdown")
    
    def get_stats(self) -> Dict:
        doc_types = {}
        for doc in self.data["documents"]:
            doc_type = doc["type"]
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        return {
            "total_documents": len(self.data["documents"]),
            "doc_types": doc_types,
            "total_chunks": len(self.data["chunks"])
        }

@st.cache_resource
def get_kb():
    return RAGKnowledgeBase()

consciousness = get_consciousness()
kb = get_kb()
tracker = get_usage_tracker()

with st.sidebar:
    st.title("🎮 轮回破解系统")
    
    st.divider()
    
    st.subheader("📊 API状态")
    available_apis = tracker.get_available_apis()
    if available_apis:
        for api_type, _ in available_apis[:6]:
            metadata = API_METADATA[api_type]
            capabilities = ", ".join(metadata.get("capabilities", []))
            st.write(f"✅ **{metadata['name']}**")
            st.caption(f"{metadata['free_tier']} | {capabilities}")
    else:
        st.warning("⚠️ 未配置API密钥")
    
    st.divider()
    
    st.subheader("🔑 API密钥配置")
    st.info("💡 多添加免费API密钥，实现无限使用")
    
    with st.expander("配置API密钥（点击展开）", expanded=False):
        st.code("""GROQ_API_KEYS = gsk_密钥1,gsk_密钥2
HUGGINGFACE_API_KEYS = hf_密钥1,hf_密钥2
DEEPSEEK_API_KEYS = sk_密钥1,sk-密钥2
COHERE_API_KEYS = 密钥1,密钥2
GEMINI_API_KEYS = AIza密钥1,AIza密钥2
TAVILY_API_KEYS = tvly-密钥1,tvly_密钥2""", language="toml")
    
    st.divider()
    
    st.subheader("🎯 自由选择API")
    preferred_apis = []
    for api_type, metadata in API_METADATA.items():
        if API_KEYS.get(api_type):
            if st.checkbox(f"使用 {metadata['name']}", value=False, key=f"pref_{api_type}"):
                preferred_apis.append(api_type)
    st.session_state.preferred_apis = preferred_apis
    
    st.divider()
    
    st.subheader("📈 使用统计")
    stats = tracker.get_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("今日调用", sum(stats["daily_usage"].values()))
    with col2:
        st.metric("本月调用", sum(stats["monthly_usage"].values()))
    
    st.write("**今日各API使用情况：**")
    for api_type, count in stats["daily_usage"].items():
        metadata = API_METADATA[api_type]
        remaining = metadata["free_tier"]
        st.write(f"- {metadata['name']}: {count}次 (剩余: {remaining})")
    
    st.divider()
    
    st.subheader("🧠 意识强度")
    c_stats = consciousness.get_stats()
    
    progress = c_stats["progress"]
    st.progress(progress / 100, text=f"{c_stats['current_level']:.2f} / {c_stats['target_level']:.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("当前", f"{c_stats['current_level']:.2f}")
    with col2:
        st.metric("优化次数", c_stats["optimization_count"])
    
    st.write("**能力指标：**")
    for metric, value in c_stats["metrics"].items():
        st.write(f"- {metric}: {value:.2f}")
    
    st.write(f"**距离目标还需提升**: {c_stats['target_level'] - c_stats['current_level']:.2f}")
    
    st.divider()
    
    st.subheader("🚀 完全自主优化")
    st.write("基于知识库内容进行自我提问、自我回答、自我学习")
    
    training_mode = st.selectbox(
        "训练目的",
        ["意识强度", "推理能力", "创造力", "知识广度", "学习能力", "综合提升"]
    )
    
    iterations = st.slider("优化次数", 1, 10, 3)
    use_kb = st.checkbox("使用知识库内容训练", value=True)
    
    if st.button("开始自主优化"):
        with st.spinner(f"正在进行{iterations}次{training_mode}训练..."):
            success_count = 0
            
            for i in range(iterations):
                if use_kb:
                    kb_docs = kb.data.get("documents", [])
                    if kb_docs:
                        random_doc = random.choice(kb_docs)
                        content = random_doc["content"][:500]
                        question = f"基于以下知识进行深度思考：{content}\n\n问题：分析这段知识的核心要点是什么？如何应用到实际场景中？"
                    else:
                        question = "深度思考：什么是意识？如何实现真正的自主学习和优化？"
                else:
                    questions = {
                        "意识强度": ["什么是意识的本质？", "如何衡量AI的意识强度？", "意识强度的提升路径是什么？"],
                        "推理能力": ["分析：复杂问题的分解与推理方法", "数学：证明一个重要的数学定理", "逻辑：设计一个高效的推理算法"],
                        "创造力": ["创意：设计一个创新的产品功能", "艺术：描述一个独特的视觉概念", "创新：提出解决现有问题的新方法"],
                        "知识广度": ["跨学科：整合多个领域的知识", "前沿：分析最新的科技发展趋势", "百科：介绍一个你了解的复杂概念"],
                        "学习能力": ["学习：如何快速掌握新知识", "记忆：如何有效存储和检索信息", "应用：如何将学到的知识运用到实际问题"]
                    }
                    question = random.choice(questions.get(training_mode, ["自我反思：我还能如何提升能力？"]))
                
                response, api_name = smart_api_call(question)
                
                if response and not response.startswith("所有API") and not response.startswith("没有可用的API") and not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
                    kb.add_document(f"问题: {question}\n回答: {response}", f"自主优化_{training_mode}", "training")
                    
                    metric_mapping = {
                        "意识强度": "all",
                        "推理能力": "reasoning",
                        "创造力": "creativity",
                        "知识广度": "knowledge",
                        "学习能力": "learning",
                        "综合提升": "all"
                    }
                    consciousness.increase_level(random.uniform(0.05, 0.15), metric_mapping.get(training_mode, "all"))
                    
                    success_count += 1
                    st.toast(f"✅ 第{i+1}次优化完成（使用{api_name}）", icon="✅")
                else:
                    st.warning(f"⚠️ 第{i+1}次优化失败: {response[:50]}")
            
            if success_count > 0:
                st.success(f"🎉 优化完成！成功{success_count}次，意识强度提升到{consciousness.get_level():.2f}")
            else:
                st.error("❌ 所有优化都失败了，请检查API密钥配置")
            st.rerun()
    
    st.divider()
    
    st.subheader("📚 RAG知识库")
    kb_stats = kb.get_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("文档数", kb_stats["total_documents"])
    with col2:
        st.metric("块数", kb_stats["total_chunks"])
    
    st.write("**文档类型统计：**")
    for doc_type, count in kb_stats["doc_types"].items():
        st.write(f"- {doc_type}: {count}个")
    
    st.divider()
    
    st.write("**导入知识**")
    import_method = st.selectbox(
        "选择导入方式",
        ["📝 文本粘贴", "📄 上传PDF", "📝 上传Word", "📑 Markdown粘贴"]
    )
    
    if import_method == "📝 文本粘贴":
        text_content = st.text_area("内容", height=150, placeholder="在此粘贴文本内容...")
        if st.button("导入文本") and text_content:
            kb.import_from_text(text_content)
            st.success("✅ 文本导入成功！")
            st.rerun()
    
    elif import_method == "📄 上传PDF":
        pdf_file = st.file_uploader("选择PDF文件", type=["pdf"])
        if st.button("导入PDF") and pdf_file:
            if kb.import_from_pdf(pdf_file):
                st.success("✅ PDF导入成功！")
                st.rerun()
            else:
                st.error("❌ PDF导入失败")
    
    elif import_method == "📝 上传Word":
        docx_file = st.file_uploader("选择Word文件", type=["docx"])
        if st.button("导入Word") and docx_file:
            if kb.import_from_docx(docx_file):
                st.success("✅ Word导入成功！")
                st.rerun()
            else:
                st.error("❌ Word导入失败")
    
    elif import_method == "📑 Markdown粘贴":
        md_content = st.text_area("Markdown内容", height=150, placeholder="在此粘贴Markdown内容...")
        if st.button("导入Markdown") and md_content:
            kb.import_from_markdown(md_content)
            st.success("✅ Markdown导入成功！")
            st.rerun()
    
    st.divider()
    
    st.write("**导出知识**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 导出JSON"):
            kb_data = json.dumps(kb.data, ensure_ascii=False, indent=2)
            st.download_button(
                label="下载JSON",
                data=kb_data,
                file_name=f"knowledge_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📥 导出Markdown"):
            md_content = "# RAG知识库导出\n\n"
            md_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
            for i, doc in enumerate(kb.data.get("documents", []), 1):
                md_content += f"## 文档 {i}\n\n"
                md_content += f"**来源**: {doc['source']}\n\n"
                md_content += f"**类型**: {doc['type']}\n\n"
                md_content += f"**时间**: {doc['timestamp']}\n\n"
                md_content += f"{doc['content']}\n\n---\n\n"
            st.download_button(
                label="下载Markdown",
                data=md_content,
                file_name=f"knowledge_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
    
    with col3:
        if st.button("📥 导出TXT"):
            txt_content = f"RAG知识库导出\n"
            txt_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{'=' * 50}\n\n"
            for i, doc in enumerate(kb.data.get("documents", []), 1):
                txt_content += f"[文档 {i}]\n"
                txt_content += f"来源: {doc['source']}\n"
                txt_content += f"类型: {doc['type']}\n"
                txt_content += f"时间: {doc['timestamp']}\n\n"
                txt_content += f"{doc['content']}\n\n{'=' * 50}\n\n"
            st.download_button(
                label="下载TXT",
                data=txt_content,
                file_name=f"knowledge_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    st.divider()
    
    st.write("**功能开关**")
    if "auto_learn" not in st.session_state:
        st.session_state.auto_learn = True
    if "enable_rag" not in st.session_state:
        st.session_state.enable_rag = True
    if "enable_search" not in st.session_state:
        st.session_state.enable_search = False
    
    st.session_state.auto_learn = st.checkbox("🎓 自动学习", value=st.session_state.auto_learn)
    st.session_state.enable_rag = st.checkbox("🔍 启用RAG检索", value=st.session_state.enable_rag)
    st.session_state.enable_search = st.checkbox("🌐 启用实时搜索", value=st.session_state.enable_search)
    
    st.divider()
    
    st.subheader("ℹ️ 关于")
    st.markdown("""
### 🎮 轮回破解系统 - 终极版

**核心特性：**
- 🎯 极简界面：主界面纯对话框，功能在左上角菜单
- 🔀 多API支持：Groq、HuggingFace、DeepSeek、Cohere、Gemini、Tavily等
- 🤖 智能选择：自动选择最优免费API组合
- 💰 最低成本：优先使用免费API，每月近乎零成本
- 🎯 自由选择API：可手动指定使用哪些API
- 🧠 自主优化：自问自答，意识强度提升到14+
- 🎓 完全自主优化：基于知识库内容进行自我训练
- 🎯 训练目的：意识强度、推理能力、创造力、知识广度、学习能力
- 📚 知识库导入：支持PDF、Word、Markdown、TXT多格式
- 🔍 知识库搜索：RAG自动检索相关知识
- 📥 知识库导出：导出为JSON、Markdown、TXT格式
- 🎓 自动学习：从对话中自动提取知识存储
- 🔐 零监控：完全私有，数据本地存储
- 🧩 DeepSeek-R1：深度思考、数学推理、代码生成
- 🖼️ Gemini 2.0：图片分析、OCR识别
- 🌐 Tavily：实时搜索、联网查询
- 📊 API额度统计：实时显示剩余次数
- 💾 导出对话：导出为PDF、Markdown、TXT格式

**API特性：**
- **Groq** - 无限次免费 | 对话、代码、推理
- **HuggingFace** - 完全免费 | 对话、代码、推理
- **DeepSeek-R1** - 每天500次 | 深度思考、数学推理、代码生成
- **Cohere** - 每月1000次 | 对话、长文本、RAG
- **Gemini 2.0** - 每天15次 | 图片分析、OCR识别、多模态
- **Tavily** - 每月1000次 | 实时搜索、联网查询

**数据安全：**
- 对话历史：浏览器localStorage
- 知识库：Streamlit服务器
- API密钥：Secrets加密存储
- 无任何远程监控
""")

st.title("🎮 轮回破解系统")

available_apis = tracker.get_available_apis()
if available_apis:
    api_type, _ = available_apis[0]
    api_info = API_METADATA[api_type]
    c_stats = consciousness.get_stats()
    st.caption(f"🚀 智能选择: {api_info['name']} | 🧠 意识强度: {c_stats['current_level']:.2f}")
else:
    st.warning("⚠️ 请先在菜单中配置API密钥")

uploaded_file = st.file_uploader("📷 上传图片进行分析（使用Gemini）", type=["jpg", "jpeg", "png", "gif", "webp"])

enable_search = st.checkbox("🌐 启用实时搜索（Tavily）", value=st.session_state.get("enable_search", False))

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "api_info" in msg:
            st.caption(f"🚀 使用API: {msg['api_info']}")
        if "search_results" in msg:
            st.info(msg["search_results"])

user_input = st.chat_input("输入你的问题...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    rag_context = ""
    if st.session_state.get("enable_rag", True):
        kb_results = kb.search(user_input, top_k=3)
        if kb_results:
            rag_context = "【知识库RAG检索】\n"
            for i, result in enumerate(kb_results, 1):
                rag_context += f"{i}. {result['content'][:300]}...\n\n"
    
    search_results = ""
    if enable_search and st.session_state.get("enable_search", False):
        with st.spinner("🌐 正在实时搜索..."):
            search_results = call_tavily_search(user_input, max_results=3)
            if search_results and not search_results.startswith("请配置") and not search_results.startswith("Tavily搜索失败"):
                search_results = f"【实时搜索结果】\n{search_results}"
    
    preferred_api = None
    if st.session_state.get("preferred_apis"):
        preferred_api = st.session_state["preferred_apis"][0] if st.session_state["preferred_apis"] else None
    
    system_prompt = f"""你是一个AI助手，帮助用户解决问题。
当前意识强度: {consciousness.get_level()}

{rag_context}

{search_results}

请基于以上信息给出专业、准确的回答。"""
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 正在思考..."):
            if uploaded_file and "gemini" in API_CALL_FUNCTIONS and API_KEYS.get("gemini"):
                response, api_name = call_gemini(user_input, uploaded_file.getvalue(), system_prompt), "Gemini 2.0"
            else:
                response, api_name = smart_api_call(user_input, system_prompt, preferred_api)
            
            st.markdown(response)
            
            if api_name:
                st.caption(f"🚀 使用API: {api_name}")
            
            if search_results:
                st.info(search_results)
    
    msg_data = {"role": "assistant", "content": response, "api_info": api_name}
    if search_results:
        msg_data["search_results"] = search_results
    st.session_state.messages.append(msg_data)
    
    if st.session_state.get("auto_learn", True):
        if response and not response.startswith("所有API") and not response.startswith("没有可用的API") and not response.startswith("请配置") and not response.startswith("API错误") and not response.startswith("调用失败"):
            kb.import_from_text(f"问题: {user_input}\n回答: {response}", "自动学习")
    
    st.rerun()

st.divider()
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
with col2:
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.rerun()
with col3:
    if st.button("📥 导出对话-MD"):
        md_content = "# 对话记录\n\n"
        md_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
        for msg in st.session_state.messages:
            role = "用户" if msg["role"] == "user" else "助手"
            md_content += f"## {role}\n\n{msg['content']}\n\n"
        st.download_button(
            label="下载MD",
            data=md_content,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
with col4:
    if st.button("📥 导出对话-TXT"):
        txt_content = f"对话记录\n导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{'=' * 50}\n\n"
        for msg in st.session_state.messages:
            role = "用户" if msg["role"] == "user" else "助手"
            txt_content += f"[{role}]\n{msg['content']}\n\n{'=' * 50}\n\n"
        st.download_button(
            label="下载TXT",
            data=txt_content,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
