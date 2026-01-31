# CI/CD 经验记录

## 问题：outputs_complete 目录在 CI/CD 中未生成文件

### 问题描述
- ✅ artifact 上传功能正常（Simple Artifact Test 验证）
- ❌ 主测试 (run_complete.py) 中 outputs_complete 目录没有文件
- ❌ evidence-pdf 和 outputs artifact 始终为 0

### 验证结果

| 测试 | 状态 | 说明 |
|------|------|------|
| Simple Artifact Test | ✅ artifact 生成 | 创建文件后上传正常 |
| 主测试 (run_complete.py) | ❌ 无 artifact | outputs_complete 目录为空 |

### 可能原因

1. **run_complete.py 执行问题**
   - LLM API 调用超时或失败
   - 代码执行过程中出现错误
   - 生成的 PDF 文件被删除或覆盖

2. **目录创建时机问题**
   - outputs_complete 目录在某个步骤后被删除
   - 文件生成在 artifact 上传之后

### 下一步排查

1. 在 artifact 上传前显示 outputs_complete 目录的详细内容
2. 检查 run_complete.py 的执行日志
3. 验证 PDF 文件是否真的被创建

---

## 已验证的功能

1. ✅ GitHub Actions CI/CD 配置正确
2. ✅ Mock 测试正常
3. ✅ Test reporter 正常
4. ✅ Artifact 上传功能正常（需要目录中有文件）
5. ✅ YAML 语法正确

---

## 待解决问题

1. run_complete.py 在 CI/CD 环境中未生成 outputs_complete 文件
2. 需要增加更详细的调试信息
