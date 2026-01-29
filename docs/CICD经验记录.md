# CI/CD 经验记录

## 问题：outputs_complete 目录在 CI/CD 环境中未生成

### 问题描述
- 本地运行 `python3 run_complete.py` 正常生成 `outputs_complete/` 目录和 PDF 文件
- CI/CD 环境（GitHub Actions）中 `outputs_complete/` 目录始终未生成
- 所有 CI/CD 测试步骤都显示 "success"，但 outputs 目录不存在

### 环境对比

| 环境 | 工作目录 | 结果 |
|------|----------|------|
| 本地 macOS | 项目根目录 | ✅ outputs_complete/ 存在 |
| GitHub Actions (ubuntu-latest) | ? | ❌ outputs_complete/ 不存在 |

### 排查过程

1. **检查目录是否存在** - CI/CD 显示 outputs_complete/ NOT FOUND
2. **增加详细日志** - 添加 `ls -laR` 输出
3. **提前创建目录** - 在 run_complete.py 开始时创建 outputs_complete/
4. **检查工作目录** - 未确认 CI/CD 的实际工作目录

### 可能原因

1. **工作目录不同** - CI/CD 可能不在项目根目录执行
2. **权限问题** - 某些原因导致目录创建失败
3. **run_complete.py 未正确执行** - 可能有隐藏的错误

### 尝试的解决方案

1. ✅ 在 run_complete.py 开头创建 outputs_complete/
2. ✅ 使用 `Path.mkdir(parents=True, exist_ok=True)`
3. ✅ 添加详细日志输出
4. ❌ outputs_complete/ 仍未生成

### 待验证

1. CI/CD 的实际工作目录是什么？
2. run_complete.py 是否真的被调用？
3. 是否有错误被静默忽略？

### 下一步

1. 在 CI/CD 中添加 `pwd` 和 `ls -la` 输出
2. 验证 run_complete.py 是否被正确执行
3. 检查是否有隐藏的错误输出
4. 考虑使用绝对路径创建目录

---

## 经验教训

1. **CI/CD 环境与本地环境不同** - 不能假设工作目录相同
2. **详细日志很重要** - 没有日志很难调试 CI/CD 问题
3. **Artifact 上传需要目录存在** - 上传前需要验证目录存在

---

## 相关文件

- `.github/workflows/test.yml` - CI/CD 配置
- `run_complete.py` - 入口脚本
- `test_reporter.py` - 测试报告生成器
