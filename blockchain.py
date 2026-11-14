"""Blockchain didática local (Python 3.10+, apenas biblioteca padrão).

Projeto EXCLUSIVAMENTE educacional: não é criptomoeda, não é distribuída e
não deve ser usada em produção. Dados devem ser sempre fictícios.
"""
from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

DIFICULDADE_MIN = 1
DIFICULDADE_MAX = 6
HASH_ANTERIOR_GENESE = "0" * 64
REGISTRO_GENESE = {
    "tipo": "genese",
    "participante": "sistema",
    "descricao": "Bloco gênese da cadeia didática",
}


def serializar_canonico(dados: Any) -> str:
    """JSON determinístico: chaves ordenadas, sem espaços, Unicode preservado,
    NaN/infinito rejeitados (ValueError)."""
    return json.dumps(
        dados,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def criar_registro(tipo: str, participante: str, descricao: str) -> dict[str, str]:
    """Valida e normaliza (strip) os três campos textuais de um registro."""
    campos = {"tipo": tipo, "participante": participante, "descricao": descricao}
    for nome, valor in campos.items():
        if not isinstance(valor, str):
            raise TypeError(f"O campo '{nome}' deve ser str")
        if not valor.strip():
            raise ValueError(f"O campo '{nome}' não pode ser vazio")
    return {nome: valor.strip() for nome, valor in campos.items()}


def _validar_dificuldade(dificuldade: Any) -> int:
    # bool é subclasse de int: rejeitamos explicitamente.
    if isinstance(dificuldade, bool) or not isinstance(dificuldade, int):
        raise TypeError("A dificuldade deve ser um inteiro")
    if not DIFICULDADE_MIN <= dificuldade <= DIFICULDADE_MAX:
        raise ValueError(
            f"A dificuldade deve estar entre {DIFICULDADE_MIN} e {DIFICULDADE_MAX}"
        )
    return dificuldade


@dataclass
class Bloco:
    indice: int
    timestamp: int
    registros: list[dict[str, str]]
    hash_anterior: str
    dificuldade: int
    nonce: int = 0
    hash: str = field(default="")

    def __post_init__(self) -> None:
        _validar_dificuldade(self.dificuldade)

    def conteudo_para_hash(self) -> dict[str, Any]:
        """Campos protegidos pelo hash. NÃO inclui o próprio campo 'hash'."""
        return {
            "indice": self.indice,
            "timestamp": self.timestamp,
            "registros": self.registros,
            "hash_anterior": self.hash_anterior,
            "nonce": self.nonce,
            "dificuldade": self.dificuldade,
        }

    def calcular_hash(self) -> str:
        texto = serializar_canonico(self.conteudo_para_hash())
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def minerar(self) -> int:
        """Incrementa o nonce até o hash começar com '0' * dificuldade.
        Armazena o hash e devolve o número de tentativas."""
        _validar_dificuldade(self.dificuldade)
        alvo = "0" * self.dificuldade
        self.nonce = 0
        tentativas = 1
        h = self.calcular_hash()
        while not h.startswith(alvo):
            self.nonce += 1
            tentativas += 1
            h = self.calcular_hash()
        self.hash = h
        return tentativas


class Blockchain:
    def __init__(self, dificuldade: int = 2) -> None:
        self.dificuldade = _validar_dificuldade(dificuldade)
        genese = Bloco(
            indice=0,
            timestamp=0,
            registros=[copy.deepcopy(REGISTRO_GENESE)],
            hash_anterior=HASH_ANTERIOR_GENESE,
            dificuldade=self.dificuldade,
        )
        genese.minerar()
        self.blocos: list[Bloco] = [genese]

    @property
    def ultimo_bloco(self) -> Bloco:
        return self.blocos[-1]

    def adicionar_bloco(
        self, registros: list[dict[str, str]], timestamp: int | None = None
    ) -> Bloco:
        """Valida entrada, copia, minera e anexa. Recusa cadeia já inválida."""
        if not self.validar():
            raise ValueError("Cadeia inválida: não é possível adicionar blocos")
        if not isinstance(registros, list) or not registros:
            raise ValueError("registros deve ser uma lista não vazia")
        copia = copy.deepcopy(registros)
        for r in copia:
            if not isinstance(r, dict):
                raise TypeError("Cada registro deve ser dict")
            criar_registro(r.get("tipo"), r.get("participante"), r.get("descricao"))
        if timestamp is None:
            timestamp = int(time.time())
        bloco = Bloco(
            indice=self.ultimo_bloco.indice + 1,
            timestamp=int(timestamp),
            registros=copia,
            hash_anterior=self.ultimo_bloco.hash,
            dificuldade=self.dificuldade,
        )
        bloco.minerar()
        self.blocos.append(bloco)
        return bloco


    def diagnosticar(self) -> list[str]:
        """Lista os problemas encontrados (vazia = cadeia íntegra).
        Só lê: nunca conserta a cadeia."""
        problemas: list[str] = []
        if not self.blocos:
            return ["cadeia vazia"]
        for i, b in enumerate(self.blocos):
            try:
                if b.indice != i:
                    problemas.append(f"bloco {i}: índice {b.indice} incorreto")
                dif_ok = (
                    not isinstance(b.dificuldade, bool)
                    and isinstance(b.dificuldade, int)
                    and DIFICULDADE_MIN <= b.dificuldade <= DIFICULDADE_MAX
                )
                if not dif_ok:
                    problemas.append(f"bloco {i}: dificuldade fora do intervalo 1 a 6")
                elif b.dificuldade != self.dificuldade:
                    problemas.append(f"bloco {i}: dificuldade diferente da cadeia")
                if not isinstance(b.hash, str) or b.hash != b.calcular_hash():
                    problemas.append(f"bloco {i}: hash armazenado não confere com o conteúdo")
                if dif_ok and not (isinstance(b.hash, str) and b.hash.startswith("0" * b.dificuldade)):
                    problemas.append(f"bloco {i}: prova de trabalho inválida")
                if i == 0:
                    if b.timestamp != 0 or b.hash_anterior != HASH_ANTERIOR_GENESE:
                        problemas.append("bloco 0: gênese com timestamp ou hash anterior incorreto")
                    if b.registros != [REGISTRO_GENESE]:
                        problemas.append("bloco 0: registro gênese alterado")
                elif b.hash_anterior != self.blocos[i - 1].hash:
                    problemas.append(f"bloco {i}: hash_anterior não aponta para o hash do bloco {i - 1}")
            except (TypeError, ValueError, OverflowError, AttributeError):
                problemas.append(f"bloco {i}: estrutura malformada")
        return problemas

    def validar(self) -> bool:
        """Confere gênese, índices, hashes, ligações, dificuldade e PoW.
        Devolve apenas booleano; use diagnosticar() para saber o motivo."""
        return not self.diagnosticar()
