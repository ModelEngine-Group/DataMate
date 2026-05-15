import os
import torch
import torch_npu
import numpy as np
import faiss
import json
import re
# 直接使用 sentence_transformers（避免 modelscope 的 Python 3.9 兼容性问题）
from sentence_transformers import SentenceTransformer
# 屏蔽警告
import warnings
warnings.filterwarnings("ignore")

RULE_TEXT_TRANSLATION = str.maketrans({
    "（": "(",
    "）": ")",
    "【": "[",
    "】": "]",
    "，": ",",
    "：": ":",
    "；": ";",
    "“": "\"",
    "”": "\"",
    "‘": "'",
    "’": "'",
})

RULE_TEXT_TRANSLATION = str.maketrans({
    "\uFF08": "(",
    "\uFF09": ")",
    "\u3010": "[",
    "\u3011": "]",
    "\uFF0C": ",",
    "\uFF1A": ":",
    "\uFF1B": ";",
    "\u201C": "\"",
    "\u201D": "\"",
    "\u2018": "'",
    "\u2019": "'",
})


def normalize_term_text(text):
    text = (text or "").strip().lower()
    if not text:
        return ""
    text = text.translate(RULE_TEXT_TRANSLATION)
    return re.sub(r"\s+", "", text)

class MedicalNormalizer:
    def __init__(self, model_dir, batch_size=24, use_l1_cache=True):
        # 1. 路径检查
        if not os.path.exists(model_dir):
            raise ValueError(f"❌ 路径不存在: {model_dir}")
        
        # 检查关键文件是否存在
        config_path = os.path.join(model_dir, 'config.json')
        if not os.path.exists(config_path):
             raise ValueError(f"❌ 错误：在 {model_dir} 下找不到 config.json，请确认路径正确。")

        # 批处理大小配置（用于向量编码）
        self.batch_size = batch_size
        # 是否启用 L1 缓存（高频词精确匹配）
        self.use_l1_cache = use_l1_cache
        
        print(f">>> [Normalizer] 正在加载本地向量模型: {model_dir} (batch_size={batch_size}, use_l1_cache={use_l1_cache})")

        # 2. 硬件设备检测
        # 优先检测昇腾 NPU，其次检测 CUDA GPU，最后使用 CPU
        if hasattr(torch, 'npu') and torch.npu.is_available():
            self.device = 'npu:0'  # 使用 'gpu' 表示加速设备
            print(f">>> [Device] 使用昇腾 NPU ({torch.npu.get_device_name(0)})")
        else:
            self.device = 'cpu'
            print(">>> [Device] 使用 CPU")

        # 3. 加载向量化模型
        try:
            self.encoder = SentenceTransformer(model_dir, device=self.device)
            print(">>> [Normalizer] 模型加载成功！")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print("提示：请确保安装了依赖 pip install sentence-transformers faiss-cpu (或 faiss-gpu 如果使用 CUDA)")
            raise e

        # 4. 初始化知识库 (模拟 ICD-10 数据)
        self._init_knowledge_base()
        self._init_curated_rules()

    def _init_knowledge_base(self):
        """
        初始化标准术语库
        这里模拟了一些数据，实际生产中应从数据库加载
        """
        print(">>> [Index] 正在构建标准库索引...")
        
        # 从 JSON 文件加载 L1 缓存和标准术语库
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # --- L1: 内存缓存 (高频词精确匹配，按需启用) ---
        if self.use_l1_cache:
            l1_cache_path = os.path.join(script_dir, "l1_cache.json")
            with open(l1_cache_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)

            # 统一转换为:
            #   self.l1_cache: { name: {"std_name": ..., "code": ...}, ... }
            # 兼容老格式：
            # 1) { name: code, ... }
            # 2) [ {"name": "...", "code": "..."}, ... ]
            # 3) [ {"name": "...", "std_name": "...", "code": "..."}, ... ]
            mapping = {}
            if isinstance(raw, dict):
                for name, code in raw.items():
                    if name is None or code is None:
                        continue
                    name_s = str(name)
                    code_s = str(code)
                    mapping[name_s] = {
                        "std_name": name_s,  # 老格式默认 std_name = name
                        "code": code_s,
                    }
            elif isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name")
                    code = item.get("code")
                    if name is None or code is None:
                        continue
                    std_name = item.get("std_name") or name
                    mapping[str(name)] = {
                        "std_name": str(std_name),
                        "code": str(code),
                    }
            else:
                print(f">>> [Warning] 未识别的 l1_cache 格式: {type(raw)}, 已忽略 L1 缓存")

            self.l1_cache = mapping
            print(f">>> [Index] 已加载 L1 缓存，共 {len(self.l1_cache)} 条高频术语")
        else:
            # 禁用 L1 缓存时，使用空字典占位，后续逻辑统一判断 self.use_l1_cache
            self.l1_cache = {}
            print(">>> [Index] 已禁用 L1 缓存，仅使用向量检索")

        # --- L2: 向量库 (模糊匹配) ---
        # 标准词列表
        std_terms_path = os.path.join(script_dir, "std_terms.json")
        with open(std_terms_path, 'r', encoding='utf-8') as f:
            self.std_terms = json.load(f)

        # 尝试从磁盘加载已构建的索引，避免重复构建
        index_path = os.path.join(script_dir, "std_terms.index")
        if os.path.exists(index_path):
            # 直接从文件加载 Faiss 索引（CPU）
            self.index = faiss.read_index(index_path)
            self.dim = self.index.d
            print(f">>> [Index] 已从文件加载索引: {index_path}")
        else:
            # 1. 计算所有标准词的向量
            std_names = [item["name"] for item in self.std_terms]
            vectors = self._get_embeddings(std_names)
            
            # 2. 构建 Faiss 索引（CPU）
            self.dim = vectors.shape[1]
            # 使用内积索引 (IndexFlatIP)。因为向量已归一化，内积等价于余弦相似度
            self.index = faiss.IndexFlatIP(self.dim)
            
            self.index.add(vectors)
            # 将索引保存到磁盘，供下次直接加载
            faiss.write_index(self.index, index_path)
            print(f">>> [Index] 索引构建完成并已保存到: {index_path}，包含 {len(self.std_terms)} 条术语")

    def _init_curated_rules(self):
        self.curated_rules = {}
        rules_path = os.environ.get("MEDCLEANSTD_TERM_RULES_JSON", "").strip()
        if not rules_path:
            return
        if not os.path.exists(rules_path):
            print(f">>> [Rules] 跳过静态规则，文件不存在: {rules_path}")
            return

        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                raw_rules = json.load(f)
        except Exception as exc:
            print(f">>> [Rules] 读取静态规则失败: {exc}")
            return

        loaded = 0
        for item in raw_rules if isinstance(raw_rules, list) else []:
            text = (item.get("text") or "").strip()
            std_name = (item.get("std_name") or "").strip()
            std_code = (item.get("std_code") or "").strip()
            normalized_text = normalize_term_text(text)
            if not normalized_text or not std_name or not std_code:
                continue
            if normalized_text in self.curated_rules:
                continue
            self.curated_rules[normalized_text] = {
                "std_name": std_name,
                "std_code": std_code,
            }
            loaded += 1

        print(f">>> [Rules] 已加载 {loaded} 条静态标准化规则: {rules_path}")

    def _get_embeddings(self, texts):
        """
        将文本转换为向量（支持分批处理以控制显存占用）
        :param texts: 字符串或字符串列表
        :return: numpy array，形状为 (n, dim)，已归一化
        """
        # sentence_transformers 可以直接处理字符串或列表
        if isinstance(texts, str):
            texts = [texts]
        
        # 如果文本数量较少，直接处理
        if len(texts) <= self.batch_size:
            embeddings = self.encoder.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,  # 自动归一化
                show_progress_bar=False,
                batch_size=self.batch_size
            )
        else:
            # 分批处理，避免一次性占用过多显存
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                batch_embeddings = self.encoder.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=self.batch_size
                )
                all_embeddings.append(batch_embeddings)
            embeddings = np.vstack(all_embeddings)
        
        # 确保是 float32 类型（Faiss 要求）
        vecs = np.array(embeddings, dtype='float32')
        
        return vecs

    def normalize(self, text):
        """
        核心接口：标准化
        :param text: 输入实体文本 (如 "尤下腹痛")，或字符串列表
        :return: 标准化结果字典，或结果字典列表
        """
        # 支持批量输入：如果传入列表，走并行标准化流程
        if isinstance(text, (list, tuple)):
            return self.normalize_batch(list(text))

        if not text:
            return None

        # 复用批量接口，避免重复代码
        return self.normalize_batch([text])[0]

    def normalize_batch(self, texts):
        """
        并行标准化多个实体
        :param texts: 字符串列表
        :return: 与输入一一对应的结果字典列表
        """
        if not texts:
            return []

        # 预分配结果列表
        results = [None] * len(texts)

        # 需要走向量检索的样本索引和文本
        pending_indices = []
        pending_texts = []

        for i, t in enumerate(texts):
            if not t:
                results[i] = None
                continue

            # 1. 先查 L1 缓存（O(1) 查表，极快；可通过 use_l1_cache 关闭）
            normalized_text = normalize_term_text(t)

            if normalized_text in self.curated_rules:
                entry = self.curated_rules[normalized_text]
                results[i] = {
                    "std_name": entry["std_name"],
                    "std_code": entry["std_code"],
                    "score": 1.0,
                    "source": "Curated_Rule"
                }
            elif self.use_l1_cache and t in self.l1_cache:
                entry = self.l1_cache[t]
                # 兼容老格式：entry 可能是 str(code)
                if isinstance(entry, dict):
                    std_name = entry.get("std_name", t)
                    code = entry.get("code")
                else:
                    std_name = t
                    code = entry
                results[i] = {
                    "std_name": std_name,
                    "std_code": code,
                    "score": 1.0,
                    "source": "L1_Cache"
                }
            else:
                pending_indices.append(i)
                pending_texts.append(t)

        # 2. 对未命中缓存的文本，使用向量模型 + Faiss 批量并行检索
        if pending_texts:
            query_vecs = self._get_embeddings(pending_texts)  # 形状 (n, dim)

            # 并行批量搜索：如果查询向量数量很大，分批搜索以避免内存问题
            # Faiss 的 search 方法本身已经支持批量并行搜索
            search_batch_size = 2000  # 每次搜索的向量数量上限
            
            if len(query_vecs) <= search_batch_size:
                # 一次性批量搜索（并行）
                D, I = self._search_batch(query_vecs, 1)
                self._process_search_results(D, I, pending_indices, results)
            else:
                # 分批搜索，每批并行处理
                for i in range(0, len(query_vecs), search_batch_size):
                    batch_vecs = query_vecs[i:i + search_batch_size]
                    batch_indices = pending_indices[i:i + search_batch_size]
                    
                    # 批量并行搜索
                    D, I = self._search_batch(batch_vecs, 1)
                    self._process_search_results(D, I, batch_indices, results)

        return results

    def normalize_batch(self, texts):
        if not texts:
            return []

        results = [None] * len(texts)
        pending_indices = []
        pending_texts = []

        for i, t in enumerate(texts):
            if not t:
                results[i] = None
                continue

            normalized_text = normalize_term_text(t)
            if normalized_text in self.curated_rules:
                entry = self.curated_rules[normalized_text]
                results[i] = {
                    "std_name": entry["std_name"],
                    "std_code": entry["std_code"],
                    "score": 1.0,
                    "source": "Curated_Rule",
                }
                continue

            if self.use_l1_cache and t in self.l1_cache:
                entry = self.l1_cache[t]
                if isinstance(entry, dict):
                    std_name = entry.get("std_name", t)
                    code = entry.get("code")
                else:
                    std_name = t
                    code = entry
                results[i] = {
                    "std_name": std_name,
                    "std_code": code,
                    "score": 1.0,
                    "source": "L1_Cache",
                }
                continue

            pending_indices.append(i)
            pending_texts.append(t)

        if pending_texts:
            query_vecs = self._get_embeddings(pending_texts)
            search_batch_size = 2000
            if len(query_vecs) <= search_batch_size:
                D, I = self._search_batch(query_vecs, 1)
                self._process_search_results(D, I, pending_indices, results)
            else:
                for i in range(0, len(query_vecs), search_batch_size):
                    batch_vecs = query_vecs[i:i + search_batch_size]
                    batch_indices = pending_indices[i:i + search_batch_size]
                    D, I = self._search_batch(batch_vecs, 1)
                    self._process_search_results(D, I, batch_indices, results)

        return results

    def _search_batch(self, query_vecs, k):
        """
        批量并行搜索（Faiss 内部已优化并行）
        :param query_vecs: 查询向量，形状 (n, dim)
        :param k: 返回 Top-k 结果
        :return: (D, I) 距离和索引
        """
        # Faiss 的 search 方法对批量查询已经是并行的
        # 如果索引在 GPU 上，会自动使用 GPU 并行加速
        D, I = self.index.search(query_vecs, k)
        return D, I

    def _process_search_results(self, D, I, pending_indices, results):
        """
        处理搜索结果并填充到结果列表
        :param D: 距离矩阵
        :param I: 索引矩阵
        :param pending_indices: 待处理索引列表
        :param results: 结果列表（会被修改）
        """
        threshold = 0.75
        
        for j, idx_in_original in enumerate(pending_indices):
            score = float(D[j][0])
            term_idx = int(I[j][0])

            if score > threshold:
                match_term = self.std_terms[term_idx]
                results[idx_in_original] = {
                    "std_name": match_term["name"],
                    "std_code": match_term["code"],
                    "score": round(score, 4),
                    "source": "Vector_Retrieval"
                }
            else:
                results[idx_in_original] = {
                    "std_name": None,
                    "std_code": None,
                    "score": round(score, 4),
                    "source": "Unmapped_Low_Score"
                }

# --- 单元测试 ---
if __name__ == "__main__":
    # 指向您本地的具体路径
    local_path = "./model/bge-small-zh-v1.5"
    
    # 防止设备冲突（昇腾使用 ASCEND_RT_VISIBLE_DEVICES，CUDA 使用 CUDA_VISIBLE_DEVICES）
    # os.environ["ASCEND_RT_VISIBLE_DEVICES"] = "0"  # 昇腾 NPU
    # os.environ["CUDA_VISIBLE_DEVICES"] = "1"  # NVIDIA GPU
    
    try:
        norm = MedicalNormalizer(local_path)
        
        print("\n" + "="*60)
        print(f"{'原词':<12} | {'标准词':<12} | {'ICD编码':<8} | {'分数':<6} | {'来源'}")
        print("-" * 60)
        
        test_cases = [
            "急性阑尾炎",    # 在缓存里
            "尤下腹痛",      # 错别字 -> 右下腹疼痛
            "头孢",          # 模糊 -> 头孢菌素类药物
            "肚子疼",        # 语义 -> 右下腹疼痛 (可能)
            "未知的火星病"    # 应该不匹配
        ]
        
        for text in test_cases:
            res = norm.normalize(text)
            print(f"{text:<12} | {str(res['std_name']):<12} | {str(res['std_code']):<8} | {res['score']:<6} | {res['source']}")
            
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
