import json

with open("/var/data/lvdthieu/thesis/benchmark/data/intrinsic/check.json", "r") as f:
    x = json.loads(json.load(f)["builder_output_intrinsic"])

with open("/var/data/lvdthieu/thesis/benchmark/data/intrinsic/check1.json", "w") as f:
    json.dump(x, f)