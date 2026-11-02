"""Collects findings. FAIL = must fix; WARN = decide consciously; INFO = context."""
import json

ORDER = {"FAIL": 0, "WARN": 1, "INFO": 2}


class Report:
    def __init__(self):
        self.items = []
        self.metrics = {}

    def add(self, level, check, msg):
        self.items.append(dict(level=level, check=check, msg=msg))

    def fail(self, check, msg):
        self.add("FAIL", check, msg)

    def warn(self, check, msg):
        self.add("WARN", check, msg)

    def info(self, check, msg):
        self.add("INFO", check, msg)

    @property
    def failed(self):
        return any(i["level"] == "FAIL" for i in self.items)

    def print(self, title):
        print(f"\n{title}")
        for k, v in self.metrics.items():
            print(f"  {k:26} {v}")
        print()
        if not any(i["level"] in ("FAIL", "WARN") for i in self.items):
            print("  PASS  everything measured is within range — now look at the result yourself")
        for i in sorted(self.items, key=lambda i: ORDER[i["level"]]):
            print(f"  {i['level']:4}  [{i['check']}] {i['msg']}")

    def save(self, path):
        json.dump(dict(metrics=self.metrics, report=self.items), open(path, "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)
