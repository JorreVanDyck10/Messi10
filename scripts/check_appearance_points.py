
from pathlib import Path
import torch

path = Path("artifacts/broadcast-players-v1/roles_teams.pt")

if not path.is_file():
    print(f"Checkpoint not found: {path}")
    raise SystemExit(1)

state = torch.load(
    path,
    map_location="cpu",
    weights_only=True
)

print("\n=== APPEARANCE CHECKPOINT DIAGNOSTIC ===")
print(f"File exists: {path.is_file()}")
print(f"File size: {path.stat().st_size:,} bytes")

print("\nAvailable fields:")
for key, value in state.items():
    if isinstance(value, dict):
        print(f"  {key}: dictionary ({len(value)} entries)")
    elif isinstance(value, torch.Tensor):
        print(f"  {key}: tensor {tuple(value.shape)}")
    else:
        print(f"  {key}: {value}")

print("\nRequired fields:")
for key in ("role_names", "team_names", "backbone", "role_head", "team_head"):
    print(f"  {key}: {'PRESENT' if key in state else 'MISSING'}")

print("\n=== END ===")
