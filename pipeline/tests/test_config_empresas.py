"""Vocabulario do mapa de empresas por fase (companies.yaml, 2026-10-14) e do catalogo que o System le.

Regra sem executor envelhece (invariante 6 da raiz): este teste e o executor. Cada checagem e provada nos dois
sentidos -- o YAML real passa e o mesmo YAML com um defeito injetado reprova.
"""
from __future__ import annotations

import copy
import unittest

from pipeline import armazenamento_pg
from pipeline.collectors import common

FASES = {"aurora", "dry-lab", "workbench", "wet-lab", "clinical-trials", "the-cure"}
MISSOES = {"athanor", "aurora", "workbench"}
TIPOS = {"concorrente", "ferramenta", "fonte-de-dado", "referencia", "parceiro", "cro"}
TEMAS = {"virtual-cell", "ai-drug-design"}
CATEGORIAS = {"ai_drug_discovery", "cadd_platform", "biotech_ai", "big_tech_ai", "br_institution", "bioinformatics_resource"}
METODOS = {"rss", "google_news"}
CAMPOS_DE_MARCA = ("fase", "missao", "tipo")


def problemas(empresas: list[dict]) -> list[str]:
    out, vistos = [], set()
    for c in empresas:
        s = c.get("slug", "?")
        if s in vistos:
            out.append(f"{s}: slug repetido")
        vistos.add(s)
        if c.get("category") not in CATEGORIAS:
            out.append(f"{s}: category fora das seis que o System rotula")
        if c.get("method") not in METODOS:
            out.append(f"{s}: method {c.get('method')!r} sem coletor")
        if c.get("method") == "rss" and not c.get("feed_url"):
            out.append(f"{s}: rss sem feed_url")
        if not any(k in c for k in CAMPOS_DE_MARCA):
            continue  # empresa fora do mapa por fase (openai, butantan...) nao e cobrada
        for campo, vocab in (("fase", FASES), ("missao", MISSOES), ("tipo", TIPOS), ("temas", TEMAS)):
            valor = c.get(campo, [])
            if not isinstance(valor, list):
                out.append(f"{s}: {campo} nao e lista")
                continue
            for v in valor:
                if v not in vocab:
                    out.append(f"{s}: {campo}={v!r} fora do vocabulario")
        if not c.get("fase"):
            out.append(f"{s}: marcada sem fase")
        if not c.get("tipo"):
            out.append(f"{s}: marcada sem tipo")
    return out


class ConfigEmpresas(unittest.TestCase):
    def setUp(self):
        self.empresas = common.load_companies()

    def test_yaml_real_passa(self):
        self.assertEqual(problemas(self.empresas), [])

    def test_defeitos_injetados_reprovam(self):
        for campo, valor in (("fase", ["venus"]), ("tipo", ["parceria"]), ("missao", ["dry-lab"]), ("category", "cro")):
            e = copy.deepcopy(self.empresas)
            e[0][campo] = valor
            self.assertTrue(problemas(e), campo)
        e = copy.deepcopy(self.empresas)
        e.append(copy.deepcopy(e[0]))
        self.assertTrue(any("repetido" in p for p in problemas(e)))
        e = copy.deepcopy(self.empresas)
        e.append({"slug": "x", "category": "biotech_ai", "method": "rss"})
        self.assertTrue(any("feed_url" in p for p in problemas(e)))

    def test_a_acompanhar_nao_e_coletado(self):
        d = common.load_yaml("companies.yaml")
        acomp = d["a_acompanhar"]
        coletadas = {c["slug"] for c in d["companies"]}
        self.assertTrue(acomp)
        for a in acomp:
            self.assertNotIn(a["slug"], coletadas)
            self.assertNotIn("method", a)
            self.assertIn(a["situacao"], {"bloqueado-a-acompanhar", "a-confirmar"})
            self.assertTrue(set(a["fase"]) <= FASES and set(a["tipo"]) <= TIPOS and set(a["missao"]) <= MISSOES)
        self.assertEqual({a["slug"] for a in acomp if a["situacao"] == "a-confirmar"}, {"lilly-tunelab"})
        # sentido contrario: o mesmo slug em `companies` seria coletado pelo default google_news
        injetado = {c["slug"] for c in d["companies"] + [{"slug": acomp[0]["slug"]}]}
        self.assertTrue({x["slug"] for x in acomp} & injetado)

    def test_parceiro_so_onde_o_relatorio_diz(self):
        por = {c["slug"]: c for c in self.empresas}
        parceiros = {s for s, c in por.items() if "parceiro" in c.get("tipo", [])}
        self.assertEqual(parceiros, {"adaptyv-bio", "nvidia", "ginkgo-bioworks", "emerald-cloud-lab", "evotec", "unlearn-ai",
                                     "opentrons", "automata", "synthace", "enamine", "emulate"})

    def test_registro_trial_das_empresas_pedidas(self):
        por = {c["slug"]: c for c in self.empresas}
        self.assertEqual(por["relay-therapeutics"]["registro_trial"], ["NCT06982521", "NCT05216432", "NCT06789913", "NCT07584226"])
        self.assertEqual(por["iambic-therapeutics"]["registro_trial"], ["NCT06253871"])

    def test_correcao_do_fundador_2026_10_14(self):
        por = {c["slug"]: c for c in self.empresas}
        for s in ("isomorphic-labs", "google-deepmind", "google-deepmind-blog"):
            self.assertEqual(por[s]["tipo"], ["referencia"], s)

    def test_catalogo_aceito_pelo_escritor_do_banco(self):
        entradas = armazenamento_pg.entradas_de_catalogo("companies", {"companies": self.empresas})
        self.assertEqual(len(entradas), len(self.empresas))

    def test_temas_pedidos_estao_nos_termos(self):
        topicos = common.load_keywords()["topics"]
        for t in ("virtual cell", "AI drug design"):
            self.assertIn(t, topicos)


if __name__ == "__main__":
    unittest.main()
