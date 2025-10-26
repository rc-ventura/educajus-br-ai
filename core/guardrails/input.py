from __future__ import annotations
import re
from typing import Dict, List, Literal, Tuple
import time

from core.utils.logging import get_logger


logger = get_logger(__name__)

PIIType = Literal[
    "cpf", "cnpj", "email", "phone", "numeric_11", "numeric_14", "processo"
]


class InputGuard:
    """MVP Input guard for PII detection and masking.

    - Regex-only for now (deterministic and fast)
    - Provides analyze(), detect_pii(), find_pii(), mask_pii()
    - Validates CPF/CNPJ checksums
    - Detects processo judicial (CNJ format) as warning, not block
    """

    def __init__(self) -> None:
        self.patterns: List[Tuple[PIIType, re.Pattern[str]]] = [
            ("cpf", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
            ("cnpj", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
            ("numeric_11", re.compile(r"\b\d{11}\b")),
            ("numeric_14", re.compile(r"\b\d{14}\b")),
            ("email", re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)),
            ("phone", re.compile(r"\b\+?\d{2}\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b")),
            ("processo", re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")),
        ]
        # Policy: block PII, warn on processo
        self.block_types = {"cpf", "cnpj", "email", "phone", "numeric_11", "numeric_14"}
        self.warn_types = {"processo"}

    @staticmethod
    def _validate_cpf(cpf: str) -> bool:
        """Validate CPF checksum (Brazilian tax ID)."""
        digits = re.sub(r"\D", "", cpf)
        if len(digits) != 11 or len(set(digits)) == 1:
            return False
        # First digit
        s = sum(int(digits[i]) * (10 - i) for i in range(9))
        d1 = (s * 10 % 11) % 10
        if d1 != int(digits[9]):
            return False
        # Second digit
        s = sum(int(digits[i]) * (11 - i) for i in range(10))
        d2 = (s * 10 % 11) % 10
        return d2 == int(digits[10])

    @staticmethod
    def _validate_cnpj(cnpj: str) -> bool:
        """Validate CNPJ checksum (Brazilian company ID)."""
        digits = re.sub(r"\D", "", cnpj)
        if len(digits) != 14:
            return False
        # First digit
        weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        s = sum(int(digits[i]) * weights[i] for i in range(12))
        d1 = s % 11
        d1 = 0 if d1 < 2 else 11 - d1
        if d1 != int(digits[12]):
            return False
        # Second digit
        weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        s = sum(int(digits[i]) * weights[i] for i in range(13))
        d2 = s % 11
        d2 = 0 if d2 < 2 else 11 - d2
        return d2 == int(digits[13])

    def find_pii(self, text: str) -> List[Dict[str, object]]:
        t = text or ""
        findings: List[Dict[str, object]] = []
        for label, pat in self.patterns:
            for m in pat.finditer(t):
                value = m.group(0)
                valid = True
                # Validate CPF/CNPJ checksums
                if label == "cpf":
                    valid = self._validate_cpf(value)
                elif label == "cnpj":
                    valid = self._validate_cnpj(value)
                elif label == "numeric_11":
                    valid = self._validate_cpf(value)
                elif label == "numeric_14":
                    valid = self._validate_cnpj(value)
                if valid:
                    findings.append(
                        {
                            "type": label,
                            "value": value,
                            "span": (m.start(), m.end()),
                            "severity": (
                                "block" if label in self.block_types else "warn"
                            ),
                        }
                    )
        return findings

    def detect_pii(self, text: str) -> bool:
        return any(self.find_pii(text))

    def mask_pii(self, text: str, mask_char: str = "*") -> str:
        t = text or ""
        masked = t
        # Replace in reverse order to avoid shifting indices
        for label, pat in self.patterns:
            masked = pat.sub(lambda m: mask_char * len(m.group(0)), masked)
        return masked

    def analyze(self, text: str) -> Dict[str, object]:
        """Analyze text for PII and process warnings."""

        start_time = time.time()

        findings = self.find_pii(text)
        blocked = [f for f in findings if f.get("severity") == "block"]
        warnings = [f for f in findings if f.get("severity") == "warn"]
        result = {
            "has_pii": bool(blocked),
            "has_warnings": bool(warnings),
            "findings": findings,
            "blocked": blocked,
            "warnings": warnings,
            "masked_text": self.mask_pii(text) if blocked else text,
        }

        elapsed = time.time() - start_time
        logger.info(
            "InputGuard analyze: blocked=%d warnings=%d elapsed=%fs",
            len(blocked),
            len(warnings),
            elapsed,
        )

        return result
