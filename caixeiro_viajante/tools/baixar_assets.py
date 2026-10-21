"""Importa somente GLB, texturas e licenças de pacotes CC0 oficiais da Kenney.

Os ZIPs ficam em .cache; nenhum código dos pacotes é executado.
Execute com o Python do ambiente virtual, a partir da raiz do projeto.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
from zipfile import ZipFile
import json

RAIZ = Path(__file__).resolve().parents[1]
PACOTES = {
    "suburban": ("city-kit-suburban", "2c871b7af2-1745479373/kenney_city-kit-suburban_20.zip"),
    "commercial": ("city-kit-commercial", "a742d900eb-1753115042/kenney_city-kit-commercial_2.1.zip"),
    "industrial": ("city-kit-industrial", "0ec35b139d-1788171848/kenney_city-kit-industrial_2.0.zip"),
    "roads": ("city-kit-roads", "74288c9459-1791628607/kenney_city-kit-roads.zip"),
    "cars": ("car-kit", "1a312ec241-1775131960/kenney_car-kit.zip"),
    "nature": ("nature-kit", "37ac38a37b-1677698939/kenney_nature-kit.zip"),
}
SELECAO = {
    "suburban": {"building-type-a", "building-type-b", "building-type-c", "building-type-f", "building-type-h", "building-type-j"},
    "commercial": {"building-a", "building-b", "building-c", "building-d", "building-e", "building-f"},
    "industrial": {"building-a", "building-b", "building-c", "building-e", "shipping-container-a"},
    "roads": {"light-curved", "traffic-light", "dumpster", "construction-barrier", "construction-cone"},
    "cars": {"delivery", "van", "sedan"},
    "nature": {"tree_detailed", "tree_oak", "tree_default", "tree_detailed_dark", "plant_bush"},
}


def importar(item):
    chave, (slug, arquivo) = item
    url = f"https://kenney.nl/media/pages/assets/{slug}/{arquivo}"
    cache = RAIZ / ".cache" / "assets" / f"{chave}.zip"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        with urlopen(Request(url, headers={"User-Agent": "NEXUS-Logistics/2.0"}), timeout=45) as resposta:
            dados = resposta.read(60_000_001)
        if len(dados) > 60_000_000:
            raise ValueError("Pacote maior que o limite de segurança.")
        cache.write_bytes(dados)
    destino = RAIZ / "assets" / "kenney" / chave
    with ZipFile(cache) as pacote:
        licenca = next(n for n in pacote.namelist() if "license" in n.lower() and n.endswith(".txt"))
        texto = pacote.read(licenca).decode("utf-8-sig")
        if "CC0" not in texto:
            raise ValueError(f"Licença CC0 não encontrada em {chave}.")
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "License.txt").write_text(texto, encoding="utf-8")
        modelos = []
        for nome in pacote.namelist():
            caminho = PurePosixPath(nome)
            if ".." in caminho.parts or caminho.is_absolute():
                raise ValueError("Caminho inválido no pacote.")
            if not any(p in ("GLB format", "GLTF format") for p in caminho.parts):
                continue
            if caminho.suffix.lower() not in (".glb", ".png", ".jpg"):
                continue
            if caminho.suffix.lower() == ".glb" and caminho.stem not in SELECAO[chave]:
                continue
            indice = next(i for i, p in enumerate(caminho.parts) if p in ("GLB format", "GLTF format"))
            relativo = Path(*caminho.parts[indice + 1:])
            alvo = destino / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(pacote.read(nome))
            if alvo.suffix == ".glb":
                modelos.append(alvo.stem)
    print(f"{chave}: {len(modelos)} modelos GLB, licença CC0 conferida.", flush=True)
    return chave, {"autor": "Kenney", "licenca": "CC0-1.0", "pagina": f"https://kenney.nl/assets/{slug}",
                   "download": url, "sha256_zip": sha256(cache.read_bytes()).hexdigest(),
                   "formato": "GLB", "modelos": sorted(modelos)}


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as executor:
        manifesto = dict(executor.map(importar, PACOTES.items()))
    (RAIZ / "assets" / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
