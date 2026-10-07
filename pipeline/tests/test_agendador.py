"""O agendador do contêiner `radar`: o próximo horário em UTC e a recusa de horário inválido. Sem rede, sem banco."""
from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PIPELINE = Path(__file__).resolve().parents[1]
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

import agendador as ag  # noqa: E402

H = ag.ler_horarios(ag.PADRAO_UTC)


def utc(h: int, m: int, s: int = 0, dia: int = 2) -> datetime:
    return datetime(2026, 10, dia, h, m, s, tzinfo=timezone.utc)


class ProximoHorario(unittest.TestCase):
    def test_padrao_e_06_12_18_de_brasilia_em_utc(self):
        # decisions-log (gi), 2026-10-07: 06:00, 12:00 e 18:00 America/Sao_Paulo == 09:00, 15:00 e 21:00 UTC
        self.assertEqual(ag.PADRAO_UTC, "09:00,15:00,21:00")
        self.assertEqual(H, [(9, 0), (15, 0), (21, 0)])

    def test_o_disparo_em_utc_e_a_hora_de_parede_de_brasilia(self):
        # prova com o tzdata, não com a aritmética do código: cada disparo, visto em America/Sao_Paulo, cai em HORARIOS_LOCAIS
        try:
            sp = ZoneInfo(ag.FUSO_LOCAL)
        except ZoneInfoNotFoundError:
            self.skipTest("sem tzdata nesta máquina")
        esperado = [tuple(map(int, p.split(":"))) for p in ag.HORARIOS_LOCAIS.split(",")]
        t, vistos = utc(0, 0), []
        for _ in range(3):
            t = ag.proximo_horario(t, H)
            vistos.append((t.astimezone(sp).hour, t.astimezone(sp).minute))
        self.assertEqual(vistos, esperado)
        self.assertEqual(sp.utcoffset(utc(12, 0)), timedelta(hours=ag.FUSO_LOCAL_UTC_H))

    def test_para_utc_volta_o_dia_quando_passa_da_meia_noite(self):
        self.assertEqual(ag.para_utc("22:30,06:00", -3), "01:30,09:00")
        self.assertEqual(ag.para_utc("00:15", 2), "22:15")

    def test_antes_do_primeiro(self):
        self.assertEqual(ag.proximo_horario(utc(3, 0), H), utc(9, 0))

    def test_entre_dois(self):
        self.assertEqual(ag.proximo_horario(utc(12, 0), H), utc(15, 0))

    def test_no_minuto_exato_vai_para_o_seguinte(self):
        # quem acorda às 09:00:00,1 já está atrasado para as 09:00: nunca dispara duas vezes o mesmo horário
        self.assertEqual(ag.proximo_horario(utc(9, 0, 0) + timedelta(microseconds=100), H), utc(15, 0))

    def test_depois_do_ultimo_vai_para_amanha(self):
        self.assertEqual(ag.proximo_horario(utc(22, 0), H), utc(9, 0, dia=3))

    def test_relogio_com_outro_fuso_e_convertido(self):
        brasilia = timezone(timedelta(hours=-3))
        self.assertEqual(ag.proximo_horario(datetime(2026, 10, 2, 5, 59, tzinfo=brasilia), H), utc(9, 0))

    def test_horarios_fora_de_ordem_saem_ordenados(self):
        self.assertEqual(ag.ler_horarios("22:00, 10:00,16:00"), [(10, 0), (16, 0), (22, 0)])


class PontoUnico(unittest.TestCase):
    """O compose do System passa `RADAR_HORARIOS_UTC: ${RADAR_HORARIOS_UTC:-}`: variável vazia tem de cair no padrão do código."""

    def disparos(self, valor):
        saida = io.StringIO()
        with mock.patch.dict(os.environ, {"RADAR_HORARIOS_UTC": valor}), contextlib.redirect_stdout(saida):
            self.assertEqual(ag.main(["--proximos", "3"]), 0)
        return [datetime.fromisoformat(x) for x in saida.getvalue().split()]

    def test_variavel_vazia_usa_o_padrao_06_12_18_de_brasilia(self):
        # três disparos seguidos cobrem os três horários do padrão, nenhum outro
        self.assertEqual({(x.hour, x.minute) for x in self.disparos("")}, set(H))

    def test_variavel_so_com_espaco_usa_o_padrao(self):
        # `" "` é truthy: sem o strip, ler_horarios levantava e o contêiner (restart: unless-stopped) entrava em laço de reinício
        self.assertEqual({(x.hour, x.minute) for x in self.disparos("  ")}, set(H))

    def test_variavel_preenchida_vence_o_padrao(self):
        self.assertTrue(all((x.hour, x.minute) in [(10, 0), (16, 0), (22, 0)] for x in self.disparos("10:00,16:00,22:00")))


class HorarioInvalido(unittest.TestCase):
    def test_recusa(self):
        for ruim in ("", "9h40", "24:00", "09:60", "09:40,xx"):
            with self.subTest(ruim=ruim), self.assertRaises(ValueError):
                ag.ler_horarios(ruim)


if __name__ == "__main__":
    unittest.main()
