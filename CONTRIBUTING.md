# Contributing

Keep discovery and audit read-only. New adapters must tolerate missing optional files, expose no secrets, and include fixture-based tests. Do not add automatic deletion or configuration mutation without a separate design review and an explicit approval boundary.

Run before submitting changes:

```bash
python -m unittest discover -s tests -v
python path/to/skill-creator/scripts/quick_validate.py skills/skill-governance
```

