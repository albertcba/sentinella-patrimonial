"""
Mòdul: verticals_anomalia.py

Detector d'anomalies de preu en bull put spreads (verticals venuts)
a partir de deltes i del mid real.

No toca cap estructura patrimonial: és un frontal independent.
"""

from dataclasses import dataclass
from typing import Literal


Semafor = Literal["VERD", "TARONJA", "VERMELL"]


@dataclass
class ResultatVertical:
    subjacent: str
    preu_subjacent: float
    expiry: str
    strike_curt: float
    strike_llarg: float
    delta_curt: float
    delta_llarg: float
    mid_real: float

    amplada: float
    credit_just: float
    anomalia: float
    semafor: Semafor
    missatge: str


def _calcular_probabilitats(delta_curt: float, delta_llarg: float) -> tuple[float, float, float]:
    """
    A partir dels deltes (puts) calcula:
    - P_A: probabilitat de guanyar (subjacent per sobre del strike curt)
    - P_B: probabilitat d'acabar entre strikes
    - P_C: probabilitat de pèrdua màxima (subjacent per sota del strike llarg)
    """
    abs_dc = abs(delta_curt)
    abs_dl = abs(delta_llarg)

    p_c = abs_dl
    p_b = abs_dc - abs_dl
    p_a = 1.0 - abs_dc

    # Protecció mínima per evitar valors estranys
    p_a = max(0.0, min(1.0, p_a))
    p_b = max(0.0, min(1.0, p_b))
    p_c = max(0.0, min(1.0, p_c))

    return p_a, p_b, p_c


def _calcular_credit_just(amplada: float, p_b: float, p_c: float) -> float:
    """
    Crèdit "just" segons risc:
    - P_C * amplada (pèrdua màxima)
    - P_B * amplada/2 (pèrdua mitjana entre strikes)
    """
    return p_c * amplada + p_b * (amplada / 2.0)


def _classificar_anomalia(anomalia: float, llindar: float = 0.05) -> tuple[Semafor, str]:
    """
    Dona un semàfor i un missatge curt segons la magnitud de l'anomalia.
    """
    if anomalia > llindar:
        return (
            "VERMELL",
            "Crèdit desproporcionat: els market makers paguen molt més del que indica el risc implícit.",
        )
    elif anomalia < -llindar:
        return (
            "TARONJA",
            "Crèdit minso: el spread no compensa el risc implícit.",
        )
    else:
        return (
            "VERD",
            "Preu normal: el crèdit és coherent amb el risc implícit.",
        )


def avaluar_vertical(
    subjacent: str,
    preu_subjacent: float,
    expiry: str,
    strike_curt: float,
    delta_curt: float,
    strike_llarg: float,
    delta_llarg: float,
    bid: float,
    mid: float,
    ask: float,
) -> ResultatVertical:
    """
    Avaluació d'un bull put spread (vertical venut) a partir de:
    - subjacent, preu, expiry
    - strike curt / llarg
    - delta curt / llarg (puts)
    - bid / mid / ask del vertical

    Retorna:
    - amplada
    - crèdit just
    - anomalia (mid_real - credit_just)
    - semàfor (VERD / TARONJA / VERMELL)
    - missatge curt
    """

    amplada = abs(strike_curt - strike_llarg)

    # 1. Probabilitats implícites
    p_a, p_b, p_c = _calcular_probabilitats(delta_curt, delta_llarg)

    # 2. Crèdit just segons risc
    credit_just = _calcular_credit_just(amplada, p_b, p_c)

    # 3. Anomalia de preu
    anomalia = mid - credit_just

    # 4. Semàfor i missatge
    semafor, missatge = _classificar_anomalia(anomalia)

    return ResultatVertical(
        subjacent=subjacent,
        preu_subjacent=preu_subjacent,
        expiry=expiry,
        strike_curt=strike_curt,
        strike_llarg=strike_llarg,
        delta_curt=delta_curt,
        delta_llarg=delta_llarg,
        mid_real=mid,
        amplada=amplada,
        credit_just=credit_just,
        anomalia=anomalia,
        semafor=semafor,
        missatge=missatge,
    )


# Exemple ràpid amb el cas GM 81/80
if __name__ == "__main__":
    gm = avaluar_vertical(
        subjacent="GM",
        preu_subjacent=50.0,      # valor orientatiu
        expiry="2026-06-12",
        strike_curt=81.0,
        delta_curt=-0.184,
        strike_llarg=80.0,
        delta_llarg=-0.086,
        bid=0.30,
        mid=0.32,
        ask=0.34,
    )

    print(gm)
    print(f"Semàfor: {gm.semafor}")
    print(f"Missatge: {gm.missatge}")
    print(f"Crèdit just: {gm.credit_just:.3f}")
    print(f"Anomalia: {gm.anomalia:.3f}")
