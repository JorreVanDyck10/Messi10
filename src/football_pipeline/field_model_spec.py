"""Pinned model provenance; dependency-free so the setup can bootstrap a clean machine."""

UPSTREAM_URL = "https://github.com/mguti97/PnLCalib"
UPSTREAM_REVISION = "8c87391d6f4ea40c5e4d65e61529916c7a49ce62"
RELEASE_WEIGHTS = {
    "keypoints": {
        "name": "SV_kp",
        "sha256": "7ea78fa76aaf94976a8eca428d6e3c59697a93430cba1a4603e20284b61f5113",
    },
    "lines": {
        "name": "SV_lines",
        "sha256": "d72f4ed71734a2e3df9fa084f666e9b8adaef21bf69bac8952d6d3f970ff7455",
    },
}
