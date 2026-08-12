# 参与贡献

发现和审计功能必须保持只读。新增适配器必须能够容忍可选文件缺失，不得暴露密钥、Token、登录状态等敏感信息，并且必须提供基于隔离夹具的自动化测试。

不要在没有独立设计审查和明确授权边界的情况下，加入自动删除、移动或修改 Agent 配置的功能。

提交变更前运行：

```bash
python -m unittest discover -s tests -v
python path/to/skill-creator/scripts/quick_validate.py skills/skill-governance
```

