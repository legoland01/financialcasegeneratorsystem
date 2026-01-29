# API问题排查记录

> 本文档记录实际遇到过的API问题及解决方案，避免重复踩坑。

---

## 1. SiliconFlow API Key Invalid 错误

### 问题描述
```
Error code: 401 - Api key is invalid
```

### 排查过程

#### Step 1: 确认API密钥是否正确
```bash
# 读取.env文件
cat .env
```

#### Step 2: 测试API连接
```bash
# 使用curl测试（重要：不要用代码，先用curl确认）
curl -s -X POST "https://api.siliconflow.cn/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model": "deepseek-ai/DeepSeek-V3.2", "messages": [{"role": "user", "content": "你好"}], "max_tokens": 10}'
```

#### Step 3: 检查API端点
- **错误端点**: `https://api.siliconflow.com/v1`
- **正确端点**: `https://api.siliconflow.cn/v1`

### 根本原因
SiliconFlow的API有两个域名：
- `api.siliconflow.cn` - 中国区（当前有效）
- `api.siliconflow.com` - 国际区（可能已失效）

### 解决方案
在 `.env` 文件中使用正确的配置：
```env
OPENAI_API_BASE=https://api.siliconflow.cn/v1
```

### 验证命令
```bash
# 测试API是否正常工作
python3 -c "
from src.utils.llm import LLMClient
llm = LLMClient(api_key='your-key', api_base='https://api.siliconflow.cn/v1')
print(llm.generate('你好'))
"
```

---

## 2. API密钥格式问题

### 常见错误
- API密钥包含多余空格
- API密钥被截断
- 使用了过期的测试密钥

### 检查方法
```bash
# 检查.env文件中的密钥格式
grep OPENAI_API_KEY .env

# 确保没有多余空格
cat .env | grep OPENAI_API_KEY | od -c
```

---

## 3. LLM调用超时问题

### 问题描述
LLM调用超过默认超时时间（600秒），但实际响应可能只需要30-60秒。

### 解决方案
1. **增加超时时间**：
   ```python
   llm_client = LLMClient(timeout=900)
   ```

2. **减少max_tokens**：
   ```python
   response = llm_client.generate(prompt, max_tokens=4096)
   ```

3. **使用更快的模型**：
   ```python
   model = "deepseek-ai/DeepSeek-V3.2"  # 当前使用的模型
   ```

---

## 4. 模拟模式 vs 真实API模式

### 识别当前模式
查看日志输出：
- `模拟模式:返回模拟响应` → 正在使用模拟模式
- `调用大模型，超时时间: xxx秒` → 正在使用真实API

### 切换到真实API
确保：
1. API密钥已正确设置在 `.env` 文件中
2. 代码中正确读取了环境变量
3. API端点配置正确

---

## 5. 快速排查清单

遇到API问题时，按以下顺序检查：

| 步骤 | 检查项 | 命令 |
|------|--------|------|
| 1 | API密钥是否存在 | `cat .env \| grep OPENAI_API_KEY` |
| 2 | API密钥格式 | `echo $OPENAI_API_KEY` |
| 3 | 端点配置 | `cat .env \| grep OPENAI_API_BASE` |
| 4 | curl测试 | `curl -X POST "https://api.siliconflow.cn/v1/chat/completions" ...` |
| 5 | Python测试 | `python3 -c "from src.utils.llm import LLMClient; llm=LLMClient(); print(llm.generate('test'))"` |

---

## 6. 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 401 | API密钥无效 | 检查密钥是否正确、是否过期 |
| 429 | 请求频率限制 | 降低调用频率 |
| 500 | 服务器内部错误 | 重试或稍后再试 |
| 503 | 服务不可用 | 稍后再试 |

---

## 7. 相关文件

| 文件 | 说明 |
|------|------|
| `.env` | API配置（密钥、端点、模型） |
| `src/utils/llm.py` | LLM客户端实现 |
| `src/services/evidence_file_generator.py` | 证据文件生成器 |
| `docs/测试报告_TR-2026-01-28-FULL.md` | 测试报告 |

---

## 8. 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-01-29 | 首次记录SiliconFlow API Key问题及解决方案 |
