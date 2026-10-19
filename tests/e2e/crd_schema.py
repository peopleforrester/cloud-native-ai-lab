# ABOUTME: Reads CRDs out of a packaged Helm chart and validates objects against their schemas.
# ABOUTME: Applies defaults, rejects unknown fields as strict field validation does, and runs CEL.

import base64
import copy
import io
import re
import tarfile
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import celpy
import yaml

# Keywords this validator enforces or knows to have no effect on a create. A schema using any
# other keyword fails validation by name, so a pin bump that adopts one is reported, not ignored.
SUPPORTED_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "anyOf",
        "default",
        "description",
        "enum",
        "example",
        "format",
        "items",
        "maxItems",
        "maxLength",
        "maxProperties",
        "maximum",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "nullable",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
        "x-kubernetes-int-or-string",
        "x-kubernetes-list-map-keys",
        "x-kubernetes-list-type",
        "x-kubernetes-map-type",
        "x-kubernetes-preserve-unknown-fields",
        "x-kubernetes-validations",
    }
)

INT_RANGES = {"int32": (-(2**31), 2**31 - 1), "int64": (-(2**63), 2**63 - 1)}

_CEL = celpy.Environment()


@dataclass(frozen=True)
class CRDVersion:
    """One version of a CustomResourceDefinition, as the chart ships it."""

    source: str
    group: str
    version: str
    kind: str
    scope: str
    served: bool
    schema: dict[str, Any]


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _type_ok(expected: str, value: Any) -> bool:
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "integer": _is_int,
        "number": lambda v: _is_int(v) or isinstance(v, float),
        "boolean": lambda v: isinstance(v, bool),
    }
    return checks[expected](value)


def _format_error(fmt: str, value: Any) -> str | None:
    """Return why `value` does not match `fmt`, or None when it does."""
    if fmt in INT_RANGES:
        low, high = INT_RANGES[fmt]
        return None if not _is_int(value) or low <= value <= high else f"out of {fmt} range"
    if not isinstance(value, str):
        return None
    if fmt == "byte":
        try:
            base64.b64decode(value, validate=True)
        except ValueError:
            return "is not base64"
        return None
    if fmt == "date-time":
        try:
            datetime.fromisoformat(value)
        except ValueError:
            return "is not an RFC 3339 date-time"
        return None
    if fmt == "uri":
        # The API server uses Go's url.ParseRequestURI: an absolute URI or an absolute path.
        parsed = urllib.parse.urlparse(value)
        return None if parsed.scheme or value.startswith("/") else "is not an absolute URI"
    return f"uses format {fmt!r}, which this validator does not check"


def apply_defaults(schema: dict[str, Any], value: Any) -> Any:
    """Return a copy of `value` with schema defaults filled in, as the API server does on create."""
    value = copy.deepcopy(value)
    _fill_defaults(schema, value)
    return value


def _fill_defaults(schema: dict[str, Any], value: Any) -> None:
    if isinstance(value, dict):
        for name, sub in schema.get("properties", {}).items():
            if name not in value and "default" in sub:
                value[name] = copy.deepcopy(sub["default"])
            if name in value:
                _fill_defaults(sub, value[name])
        extra = schema.get("additionalProperties")
        if isinstance(extra, dict):
            for name, item in value.items():
                if name not in schema.get("properties", {}):
                    _fill_defaults(extra, item)
    elif isinstance(value, list) and isinstance(schema.get("items"), dict):
        for item in value:
            _fill_defaults(schema["items"], item)


def validate(schema: dict[str, Any], value: Any, path: str = "", strict: bool = True) -> list[str]:
    """Return every way `value` breaks `schema`, one message per problem, prefixed by its path.

    `strict` rejects fields the schema does not declare. anyOf branches are checked without it:
    a structural schema declares every field outside anyOf, so branches only constrain values.
    """
    where = path or "."
    unsupported = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unsupported:
        return [f"{where}: schema uses {unsupported}, which this validator does not support"]

    if value is None:
        return [] if schema.get("nullable") else [f"{where}: must not be null"]

    if schema.get("x-kubernetes-int-or-string"):
        if not (_is_int(value) or isinstance(value, str)):
            return [f"{where}: must be an integer or a string, got {type(value).__name__}"]
    elif "type" in schema and not _type_ok(schema["type"], value):
        return [f"{where}: must be {schema['type']}, got {type(value).__name__}"]

    errors: list[str] = []
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if "format" in schema:
        problem = _format_error(schema["format"], value)
        if problem:
            errors.append(f"{where}: {value!r} {problem}")

    if isinstance(value, str):
        errors += _check_string(schema, value, where)
    elif _is_int(value) or isinstance(value, float):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{where}: {value} is less than the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{where}: {value} is greater than the maximum {schema['maximum']}")
    elif isinstance(value, dict):
        errors += _check_object(schema, value, path, strict)
    elif isinstance(value, list):
        errors += _check_array(schema, value, path, strict)

    if "anyOf" in schema:
        branches = [validate(branch, value, path, strict=False) for branch in schema["anyOf"]]
        if all(branches):
            errors.append(f"{where}: matches none of anyOf: {branches}")

    errors += _check_cel(schema, value, where)
    return errors


def _check_string(schema: dict[str, Any], value: str, where: str) -> list[str]:
    errors: list[str] = []
    if "minLength" in schema and len(value) < schema["minLength"]:
        errors.append(f"{where}: shorter than minLength {schema['minLength']}")
    if "maxLength" in schema and len(value) > schema["maxLength"]:
        errors.append(f"{where}: longer than maxLength {schema['maxLength']}")
    # The API server matches patterns unanchored, as Go's regexp.MatchString does.
    if "pattern" in schema and not re.search(schema["pattern"], value):
        errors.append(f"{where}: {value!r} does not match {schema['pattern']!r}")
    return errors


def _check_object(
    schema: dict[str, Any], value: dict[str, Any], path: str, strict: bool
) -> list[str]:
    where = path or "."
    errors: list[str] = []
    properties: dict[str, Any] = schema.get("properties", {})
    extra = schema.get("additionalProperties")
    for name in schema.get("required", []):
        if name not in value:
            errors.append(f"{where}: missing required field {name!r}")
    if "minProperties" in schema and len(value) < schema["minProperties"]:
        errors.append(f"{where}: fewer than minProperties {schema['minProperties']}")
    if "maxProperties" in schema and len(value) > schema["maxProperties"]:
        errors.append(f"{where}: more than maxProperties {schema['maxProperties']}")
    for name, item in value.items():
        child = f"{path}.{name}"
        if name in properties:
            errors += validate(properties[name], item, child, strict)
        elif isinstance(extra, dict):
            errors += validate(extra, item, child, strict)
        elif (
            strict and extra is not True and not schema.get("x-kubernetes-preserve-unknown-fields")
        ):
            errors.append(f"{child}: unknown field")
    return errors


def _check_array(schema: dict[str, Any], value: list[Any], path: str, strict: bool) -> list[str]:
    where = path or "."
    errors: list[str] = []
    if "minItems" in schema and len(value) < schema["minItems"]:
        errors.append(f"{where}: fewer than minItems {schema['minItems']}")
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        errors.append(f"{where}: more than maxItems {schema['maxItems']}")
    list_type = schema.get("x-kubernetes-list-type")
    if list_type == "set" and len({repr(item) for item in value}) != len(value):
        errors.append(f"{where}: list-type set has duplicate items")
    if list_type == "map":
        keys = [
            tuple(repr(item.get(key)) for key in schema.get("x-kubernetes-list-map-keys", []))
            for item in value
            if isinstance(item, dict)
        ]
        if len(set(keys)) != len(keys):
            errors.append(f"{where}: list-type map has duplicate keys")
    if isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            errors += validate(schema["items"], item, f"{path}[{index}]", strict)
    return errors


def _check_cel(schema: dict[str, Any], value: Any, where: str) -> list[str]:
    """Run the schema's x-kubernetes-validations rules with `self` bound to `value`."""
    errors: list[str] = []
    for rule in schema.get("x-kubernetes-validations", []):
        text = rule["rule"]
        if rule.get("optionalOldSelf") or "messageExpression" in rule:
            errors.append(
                f"{where}: CEL rule {text!r} uses a field this validator does not support"
            )
            continue
        if re.search(r"\boldSelf\b", text):
            # A transition rule compares an update with the stored object; a create has none.
            continue
        try:
            result = _CEL.program(_CEL.compile(text)).evaluate({"self": celpy.json_to_cel(value)})
        except (celpy.CELParseError, celpy.CELEvalError) as err:
            errors.append(f"{where}: CEL rule {text!r} could not be evaluated: {err}")
            continue
        if not (isinstance(result, celpy.celtypes.BoolType) and bool(result)):
            message = rule.get("message") or f"failed rule: {text}"
            errors.append(f"{where}: {message} (CEL: {text}, result: {result!r})")
    return errors


def _chart_files(chart_tgz: bytes) -> dict[str, bytes]:
    """Read the regular files of a packaged chart into memory. Nothing is written to disk."""
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(chart_tgz), mode="r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile():
                handle = archive.extractfile(member)
                assert handle is not None, f"Cannot read {member.name} from the chart"
                files[member.name] = handle.read()
    return files


def _enabled(condition: str, values: dict[str, Any]) -> bool:
    """Evaluate a Chart.yaml dependency condition as Helm does: the first path that resolves wins."""
    for dotted in condition.split(","):
        node: Any = values
        for part in dotted.strip().split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, bool):
            return node
    return True


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge `override` onto `base`, as Helm merges parent values onto a subchart's."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _crd_sources(files: dict[str, bytes], root: str, values: dict[str, Any]) -> list[str]:
    """List the chart's CRD files that `helm install` with these values would apply."""
    chart = yaml.safe_load(files[f"{root}/Chart.yaml"])
    own_values = yaml.safe_load(files.get(f"{root}/values.yaml", b"")) or {}
    merged = _merge(own_values, values)
    assert not any(
        name.startswith(f"{root}/charts/") and name.endswith(".tgz") for name in files
    ), f"{root} packages a subchart as a .tgz, which this reader does not unpack"
    sources = [
        name
        for name in files
        if name.endswith((".yaml", ".yml"))
        and name.startswith((f"{root}/crds/", f"{root}/templates/"))
    ]
    for dependency in chart.get("dependencies", []):
        assert "tags" not in dependency, f"{root}: dependency tags are not supported"
        name = dependency.get("alias") or dependency["name"]
        if "condition" in dependency and not _enabled(dependency["condition"], merged):
            continue
        sub_values = merged.get(name, {})
        sources += _crd_sources(files, f"{root}/charts/{dependency['name']}", sub_values)
    return sources


def chart_crds(chart_tgz: bytes) -> dict[tuple[str, str], CRDVersion]:
    """Index every CRD version a default install of the chart applies by (apiVersion, kind)."""
    files = _chart_files(chart_tgz)
    roots = {name.split("/", 1)[0] for name in files}
    assert len(roots) == 1, f"Expected one chart directory in the archive, found {sorted(roots)}"
    index: dict[tuple[str, str], CRDVersion] = {}
    for source in _crd_sources(files, roots.pop(), {}):
        text = files[source].decode()
        assert "{{" not in text, f"{source} is a Helm template; render it before validating"
        for doc in yaml.safe_load_all(text):
            if not doc or doc.get("kind") != "CustomResourceDefinition":
                continue
            spec = doc["spec"]
            for version in spec["versions"]:
                crd = CRDVersion(
                    source=source,
                    group=spec["group"],
                    version=version["name"],
                    kind=spec["names"]["kind"],
                    scope=spec["scope"],
                    served=bool(version.get("served")),
                    schema=version["schema"]["openAPIV3Schema"],
                )
                index[(f"{crd.group}/{crd.version}", crd.kind)] = crd
    return index


def validate_object(crd: CRDVersion, obj: dict[str, Any]) -> list[str]:
    """Validate a manifest as `kubectl apply` with strict field validation would on create.

    metadata is ObjectMeta, which the API server checks itself rather than through the CRD
    schema, so only the presence of a name is checked here.
    """
    errors: list[str] = []
    if not crd.served:
        errors.append(f"{obj.get('apiVersion')} {crd.kind} is not served")
    metadata = obj.get("metadata")
    if not isinstance(metadata, dict) or not metadata.get("name"):
        errors.append(".metadata.name: required")
    body = {key: value for key, value in obj.items() if key != "metadata"}
    schema = {
        **crd.schema,
        "properties": {
            key: value
            for key, value in crd.schema.get("properties", {}).items()
            if key != "metadata"
        },
    }
    return errors + validate(schema, apply_defaults(schema, body))
