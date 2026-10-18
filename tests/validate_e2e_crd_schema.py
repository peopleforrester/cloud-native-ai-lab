# ABOUTME: Offline checks of the E2E suite's CRD schema validator and Helm chart CRD reader.
# ABOUTME: Uses small hand-written schemas and an in-memory chart, so it runs without the network.

import io
import tarfile
from typing import Any

import pytest
import yaml

from tests.e2e import crd_schema

SPEC: dict[str, Any] = {
    "type": "object",
    "required": ["type"],
    "properties": {
        "type": {"type": "string", "enum": ["Declarative", "BYO"], "default": "Declarative"},
        "port": {"type": "integer", "format": "int32", "minimum": 1},
        "target": {
            "x-kubernetes-int-or-string": True,
            "anyOf": [{"type": "integer"}, {"type": "string"}],
        },
        "name": {"type": "string", "pattern": "^[a-z-]+$", "maxLength": 8},
        "labels": {"type": "object", "additionalProperties": {"type": "string"}},
        "raw": {"type": "object", "x-kubernetes-preserve-unknown-fields": True},
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "kind": {"type": "string"}},
                "x-kubernetes-validations": [
                    {"rule": "has(self.kind)", "message": "kind must be set"},
                    {"rule": "self.kind == oldSelf.kind", "message": "kind is immutable"},
                ],
            },
            "x-kubernetes-list-type": "map",
            "x-kubernetes-list-map-keys": ["name"],
        },
    },
    "x-kubernetes-validations": [
        {"rule": "self.type == 'Declarative' || has(self.byo)", "message": "BYO needs byo"}
    ],
}


def _errors(value: dict[str, Any]) -> list[str]:
    return crd_schema.validate(SPEC, crd_schema.apply_defaults(SPEC, value), ".spec")


class TestValidate:
    def test_valid_object_passes(self) -> None:
        value = {
            "port": 3000,
            "target": "http",
            "name": "tools",
            "labels": {"app": "x"},
            "raw": {"anything": {"goes": 1}},
            "tools": [{"name": "a", "kind": "MCPServer"}],
        }
        assert _errors(value) == []

    def test_unknown_fields_are_rejected_at_any_depth(self) -> None:
        value = {"systemPrompt": "x", "tools": [{"name": "a", "kind": "K", "extra": 1}]}
        assert _errors(value) == [
            ".spec.systemPrompt: unknown field",
            ".spec.tools[0].extra: unknown field",
        ]

    def test_default_is_applied_before_required_and_cel(self) -> None:
        assert _errors({}) == []
        assert crd_schema.apply_defaults(SPEC, {}) == {"type": "Declarative"}

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ({"port": True}, ".spec.port: must be integer, got bool"),
            ({"port": 0}, ".spec.port: 0 is less than the minimum 1"),
            ({"port": 2**31}, f".spec.port: {2**31} out of int32 range"),
            ({"target": 1.5}, ".spec.target: must be an integer or a string, got float"),
            ({"type": "Remote"}, ".spec.type: 'Remote' is not one of ['Declarative', 'BYO']"),
            ({"name": "Tools"}, ".spec.name: 'Tools' does not match '^[a-z-]+$'"),
            ({"name": "too-long-x"}, ".spec.name: longer than maxLength 8"),
            ({"labels": {"app": 1}}, ".spec.labels.app: must be string, got int"),
            (
                {"tools": [{"name": "a", "kind": "K"}] * 2},
                ".spec.tools: list-type map has duplicate keys",
            ),
            ({"tools": [{"name": "a"}]}, ".spec.tools[0]: kind must be set"),
            ({"port": None}, ".spec.port: must not be null"),
        ],
    )
    def test_value_errors(self, value: dict[str, Any], expected: str) -> None:
        errors = _errors(value)
        assert any(error.startswith(expected) for error in errors), errors

    def test_object_level_cel_rule_runs(self) -> None:
        errors = _errors({"type": "BYO"})
        assert len(errors) == 1 and "BYO needs byo" in errors[0], errors

    def test_transition_rule_is_not_run_on_create(self) -> None:
        assert not any("immutable" in error for error in _errors({"tools": [{"kind": "K"}]}))

    def test_unsupported_keyword_fails_loudly(self) -> None:
        schema = {"type": "object", "oneOf": [{"required": ["a"]}]}
        assert crd_schema.validate(schema, {}) == [
            ".: schema uses ['oneOf'], which this validator does not support"
        ]

    def test_unchecked_format_fails_loudly(self) -> None:
        errors = crd_schema.validate({"type": "string", "format": "ipv4"}, "10.0.0.1")
        assert errors == [".: '10.0.0.1' uses format 'ipv4', which this validator does not check"]


def _crd(group: str, kind: str, version: str = "v1") -> str:
    return yaml.safe_dump(
        {
            "apiVersion": "apiextensions.k8s.io/v1",
            "kind": "CustomResourceDefinition",
            "spec": {
                "group": group,
                "names": {"kind": kind},
                "scope": "Namespaced",
                "versions": [
                    {
                        "name": version,
                        "served": True,
                        "schema": {
                            "openAPIV3Schema": {
                                "type": "object",
                                "properties": {
                                    "apiVersion": {"type": "string"},
                                    "kind": {"type": "string"},
                                    "metadata": {"type": "object"},
                                    "spec": {
                                        "type": "object",
                                        "properties": {"a": {"type": "string"}},
                                    },
                                },
                            }
                        },
                    }
                ],
            },
        }
    )


def _chart(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


PARENT_CHART = """
name: parent
dependencies:
  - {name: on-crds, condition: kept.enabled}
  - {name: off-crds, condition: dropped.enabled}
"""


class TestChartCrds:
    def test_reads_templates_and_enabled_subcharts_only(self) -> None:
        chart = _chart(
            {
                "parent/Chart.yaml": PARENT_CHART,
                "parent/values.yaml": "kept: {enabled: true}\ndropped: {enabled: false}\n",
                "parent/templates/NOTES.txt": "{{ .Values.kept }}",
                "parent/templates/a.yaml": _crd("a.example", "Alpha"),
                "parent/charts/on-crds/Chart.yaml": "name: on-crds\n",
                "parent/charts/on-crds/templates/b.yaml": _crd("b.example", "Beta"),
                "parent/charts/off-crds/Chart.yaml": "name: off-crds\n",
                "parent/charts/off-crds/templates/c.yaml": _crd("c.example", "Gamma"),
            }
        )
        assert sorted(crd_schema.chart_crds(chart)) == [
            ("a.example/v1", "Alpha"),
            ("b.example/v1", "Beta"),
        ]

    def test_templated_crd_fails_loudly(self) -> None:
        chart = _chart(
            {
                "parent/Chart.yaml": "name: parent\n",
                "parent/templates/a.yaml": "{{- if .Values.x }}\n" + _crd("a.example", "Alpha"),
            }
        )
        with pytest.raises(AssertionError, match="is a Helm template"):
            crd_schema.chart_crds(chart)

    def test_validate_object_skips_metadata_but_needs_a_name(self) -> None:
        chart = _chart(
            {"p/Chart.yaml": "name: p\n", "p/templates/a.yaml": _crd("a.example", "Alpha")}
        )
        crd = crd_schema.chart_crds(chart)[("a.example/v1", "Alpha")]
        obj = {"apiVersion": "a.example/v1", "kind": "Alpha", "spec": {"a": "x"}}
        assert (
            crd_schema.validate_object(crd, {**obj, "metadata": {"name": "n", "labels": {}}}) == []
        )
        assert crd_schema.validate_object(crd, {**obj, "metadata": {}}) == [
            ".metadata.name: required"
        ]
        assert crd_schema.validate_object(crd, {**obj, "metadata": {"name": "n"}, "b": 1}) == [
            ".b: unknown field"
        ]
