"""Probe real CUDA forward/backward kernels, not just the presence of a GPU."""

import json


def probe():
    import torch

    result = {
        "torch": torch.__version__,
        "cuda_build": torch.version.cuda,
        "available": torch.cuda.is_available(),
        "ready": False,
        "gpus": [],
    }
    if not result["available"]:
        result["error"] = (
            "Geen bruikbare CUDA-GPU. Gebruik de laptopinstallatie en een recente NVIDIA-driver."
        )
        return result
    try:
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            result["gpus"].append(
                {
                    "index": i,
                    "name": p.name,
                    "memory_gib": round(p.total_memory / 1024**3, 2),
                    "capability": list(torch.cuda.get_device_capability(i)),
                }
            )
        if any(g["capability"][0] >= 12 for g in result["gpus"]):
            version = tuple(int(x) for x in (torch.version.cuda or "0.0").split(".")[:2])
            if version < (12, 8):
                raise RuntimeError(
                    "RTX 50 vereist de CUDA 12.8-variant; gebruik Setup-Laptop.ps1 in een nieuwe checkout."
                )
        x = torch.ones((32, 32), device="cuda", requires_grad=True)
        (x @ x).sum().backward()
        torch.cuda.synchronize()
        if not torch.isfinite(x.grad).all():
            raise RuntimeError("Niet-eindige GPU-gradiënten")
        result["ready"] = True
    except (RuntimeError, AssertionError) as exc:
        result["error"] = str(exc)
    return result


if __name__ == "__main__":
    result = probe()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ready"] else 1)
