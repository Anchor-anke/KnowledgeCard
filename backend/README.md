# KnowledgeCard AI 总结测试后端

这是一个用于验证「资料 → AI 总结 → 知识卡草稿」效果的本地后端原型。

当前能力：

- 接收文本或包含可复制文字的 PDF；
- 调用 OpenAI-compatible `/chat/completions` 接口；
- 返回总结、重点、知识卡草稿和质量提醒；
- 使用内存保存任务，支持轮询处理状态；
- AI 生成的卡片统一标记为 `USER_DRAFT`，不会自动进入现有学习流。

当前限制：

- 仅用于本地测试，重启后任务和结果会清空；
- PDF 暂不支持扫描件和 OCR；
- 暂无正式登录、数据库、对象存储和权限隔离；
- API Key 只从本地环境变量读取，不能提交到 Git。

## 启动

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，至少设置：

```dotenv
AI_BASE_URL=https://api.xiaomimimo.com/v1
AI_API_KEY=你的本地API_KEY
AI_MODEL=mimo-v2.5-pro
```

默认配置使用 Xiaomi MiMo；`AI_BASE_URL` 也可以替换为任何兼容
OpenAI Chat Completions 接口的服务地址。MiMo 支持使用 Bearer Token，
后端不会把 API Key 返回给客户端或写入日志。

启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

打开接口文档：

<http://127.0.0.1:8000/docs>

## 测试文本总结

创建任务：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/summaries/text \
  -H 'Content-Type: application/json' \
  -d '{"title":"项目管理基础","text":"项目是临时性的工作，运营是持续性的工作。项目有明确的开始和结束。"}'
```

响应中的 `task_id` 用于查询：

```bash
curl http://127.0.0.1:8000/api/v1/summaries/summary_xxx
```

## 测试 PDF 总结

```bash
curl -X POST http://127.0.0.1:8000/api/v1/summaries/pdf \
  -F 'title=我的学习资料' \
  -F 'file=@/绝对路径/资料.pdf'
```

处理成功后，`result` 结构类似：

```json
{
  "summary": "资料总体总结",
  "key_points": [
    {"title": "重点一", "detail": "重点解释"}
  ],
  "cards": [
    {
      "title": "知识点标题",
      "conclusion": "一句话结论",
      "explanation": "简明解释",
      "example": "应用例子",
      "recall_prompt": "回忆问题",
      "reference_answer": "参考答案",
      "source_locator": "第 1 页",
      "status": "USER_DRAFT"
    }
  ],
  "quality_warnings": []
}
```

## 移动端联调

移动端模拟器访问电脑服务时不能使用 `127.0.0.1`，需要把 API 地址改成电脑在局域网中的 IP，例如：

```text
http://192.168.1.100:8000
```

当前 `mobile/` 仍使用 Mock 数据；本后端先独立验证 AI 结果，下一步再把上传页、任务进度页和草稿审核页接入这些接口。
