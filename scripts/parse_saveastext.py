"""Parser for Microsoft Access SaveAsText export files.

Parses the hierarchical Begin/End block structure produced by Access
SaveAsText, extracting controls, data bindings, event handlers, VBA
code-behind, and subform references.

Uses recursive descent for block structure (not ad-hoc regex).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# ── Encoding helpers ──────────────────────────────────────────────

def read_saveastext(filepath: Path) -> str:
    """Read a SaveAsText export file, auto-detecting encoding.

    Access SaveAsText on Windows typically produces UTF-16-LE.
    Falls back through common encodings.
    """
    raw = filepath.read_bytes()

    # Try encodings in order of likelihood
    for enc in ("utf-16-le", "utf-16", "utf-8-sig", "utf-8", "cp874", "cp1252"):
        try:
            text = raw.decode(enc)
            # Sanity check: should contain "Begin" and "End" keywords
            if "Begin" in text and "End" in text:
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue

    # Final fallback with replacement
    return raw.decode("utf-8", errors="replace")


# ── Recursive descent parser ─────────────────────────────────────

# Control types we extract
CONTROL_TYPES = {
    "TextBox", "ComboBox", "CommandButton", "Subform", "ListBox",
    "Label", "CheckBox", "OptionButton", "Image", "TabControl",
    "OptionGroup", "ToggleButton", "BoundObjectFrame",
    "UnboundObjectFrame", "Line", "Rectangle", "PageBreak",
    "CustomControl", "ObjectFrame",
}

# Section names (Access form/report sections)
SECTION_NAMES = {"Section"}

# Event properties to look for
EVENT_PROPERTIES = {
    "OnClick", "OnDblClick", "OnOpen", "OnClose", "BeforeUpdate",
    "AfterUpdate", "OnChange", "OnGotFocus", "OnLostFocus", "OnEnter",
    "OnExit", "OnCurrent", "OnActivate", "OnDeactivate", "OnLoad",
    "OnUnload", "BeforeInsert", "AfterInsert", "BeforeDelConfirm",
    "AfterDelConfirm", "OnDirty", "OnError", "OnFilter", "OnApplyFilter",
    "OnTimer", "OnFormat", "OnPrint", "OnRetreat", "OnNoData",
    "OnPage",
}

# Top-level properties of interest
TOP_PROPERTIES = {
    "RecordSource", "Caption", "DefaultView", "Filter", "OrderBy",
    "OnOpen", "OnClose", "OnCurrent", "AllowAdditions", "AllowDeletions",
    "AllowEdits", "OrderByOn", "HasModule", "Modal", "PopUp",
    "NavigationButtons", "ScrollBars", "RecordSelectors",
    "DividingLines", "DataEntry", "Width", "Height",
}

# Control properties of interest
CONTROL_PROPERTIES = {
    "Name", "ControlSource", "RowSource", "RowSourceType", "Caption",
    "DefaultValue", "ValidationRule", "InputMask", "Visible", "Enabled",
    "Locked", "SourceObject", "ColumnCount", "BoundColumn",
    "LimitToList", "Format", "DecimalPlaces", "StatusBarText",
    "ControlTipText", "Left", "Top", "Width", "Height",
    "FontName", "FontSize", "FontWeight",
}


class SaveAsTextParser:
    """Recursive descent parser for SaveAsText export format."""

    def __init__(self, text: str):
        self.lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.pos = 0

    def peek(self) -> str | None:
        """Return the current line without advancing, or None if at end."""
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            stripped = line.strip()
            if stripped:
                return stripped
            self.pos += 1
        return None

    def advance(self) -> str | None:
        """Return the current line and advance, or None if at end."""
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            self.pos += 1
            stripped = line.strip()
            if stripped:
                return stripped
        return None

    def raw_advance(self) -> str | None:
        """Return raw line and advance (preserving whitespace)."""
        if self.pos < len(self.lines):
            line = self.lines[self.pos]
            self.pos += 1
            return line
        return None

    def parse_top_level(self) -> dict[str, Any]:
        """Parse the full file, returning structured data."""
        result: dict[str, Any] = {
            "version": None,
            "type": None,  # "Form" or "Report"
            "properties": {},
            "sections": [],
            "controls": [],
            "code_behind": "",
            "vba_procedures": [],
        }

        # Parse version header
        while self.peek() is not None and not self.peek().startswith("Begin"):
            line = self.advance()
            if line and "=" in line:
                # Strip BOM from first line
                line = line.lstrip("\ufeff")
                key, val = self._parse_property_line(line)
                if key == "Version":
                    result["version"] = val

        # Parse main Begin block (Form or Report)
        current = self.peek()
        if current and current.startswith("Begin"):
            block_type = current.split(None, 1)[1] if " " in current else ""
            result["type"] = block_type.strip()
            self.advance()  # consume "Begin Form" / "Begin Report"
            self._parse_block_contents(result, is_top_level=True)

        # Parse code-behind (everything after main block)
        code_lines = []
        while self.pos < len(self.lines):
            code_lines.append(self.lines[self.pos])
            self.pos += 1

        code_text = "\n".join(code_lines).strip()
        if code_text:
            result["code_behind"] = code_text
            result["vba_procedures"] = self._extract_vba_procedures(code_text)

        return result

    def _parse_block_contents(self, parent: dict, is_top_level: bool = False):
        """Parse contents between Begin and End of a block."""
        while True:
            current = self.peek()
            if current is None:
                break
            if current == "End":
                self.advance()  # consume End
                break

            # Nested Begin block (standalone "Begin" or "Begin Type")
            if current.startswith("Begin") and "=" not in current:
                parts = current.split(None, 1)
                block_type = parts[1] if len(parts) > 1 else ""
                self.advance()  # consume Begin line

                if block_type in CONTROL_TYPES:
                    control = self._parse_control(block_type)
                    parent.setdefault("controls", []).append(control)
                elif block_type == "Section":
                    section = self._parse_section()
                    parent.setdefault("sections", []).append(section)
                elif block_type == "":
                    # Anonymous Begin block (default property block or nested)
                    self._parse_anonymous_block(parent)
                else:
                    # Other named blocks -- skip binary data etc.
                    self._skip_block()
                continue

            # Property line
            if "=" in current:
                key, val = self._parse_property_line(current)
                self.advance()

                # "Property = Begin ... End" is a binary data block
                if val == "Begin" or val == " Begin":
                    self._skip_binary_block()
                    continue

                # Multi-line string continuation
                if isinstance(val, str) and val.startswith('"'):
                    val = self._read_multiline_string(val)

                if is_top_level and (key in TOP_PROPERTIES or key in EVENT_PROPERTIES):
                    parent["properties"][key] = val
                elif not is_top_level:
                    parent.setdefault("properties", {})[key] = val
                continue

            # Skip any other line
            self.advance()

    def _parse_property_line(self, line: str) -> tuple[str, str]:
        """Parse 'Key =Value' or 'Key = Value' into (key, value)."""
        # Handle "Key =Value" and "Key = Value"
        match = re.match(r"(\w+)\s*=\s*(.*)", line)
        if match:
            return match.group(1), match.group(2).strip()
        return line, ""

    def _read_multiline_string(self, first_val: str) -> str:
        """Reassemble a multi-line quoted string.

        SaveAsText wraps long strings across lines, each line surrounded
        by quotes. The continuation lines start with '"'.
        """
        parts = [first_val]
        while self.peek() is not None and self.peek().startswith('"'):
            parts.append(self.advance())
        # Each part is individually quoted: "text1" "text2" "text3"
        # Strip outer quotes from each part and concatenate
        stripped = []
        for part in parts:
            p = part.strip()
            if p.startswith('"') and p.endswith('"'):
                p = p[1:-1]
            stripped.append(p)
        full = "".join(stripped)
        # Unescape doubled quotes
        full = full.replace('""', '"')
        return full

    def _parse_control(self, control_type: str) -> dict[str, Any]:
        """Parse a control block (TextBox, ComboBox, etc.)."""
        control: dict[str, Any] = {
            "type": control_type,
            "properties": {},
            "events": {},
            "children": [],
        }

        while True:
            current = self.peek()
            if current is None:
                break
            if current == "End":
                self.advance()
                break

            if current.startswith("Begin") and "=" not in current:
                parts = current.split(None, 1)
                block_type = parts[1] if len(parts) > 1 else ""
                self.advance()

                if block_type in CONTROL_TYPES:
                    child = self._parse_control(block_type)
                    control["children"].append(child)
                elif block_type == "":
                    # Anonymous nested block (child controls)
                    self._parse_anonymous_block_for_control(control)
                else:
                    self._skip_block()
                continue

            if "=" in current:
                key, val = self._parse_property_line(current)
                self.advance()

                # Binary data block
                if val == "Begin" or val == " Begin":
                    self._skip_binary_block()
                    continue

                if isinstance(val, str) and val.startswith('"'):
                    val = self._read_multiline_string(val)

                if key in EVENT_PROPERTIES:
                    control["events"][key] = val
                elif key in CONTROL_PROPERTIES:
                    control["properties"][key] = val
                continue

            self.advance()

        return control

    def _parse_section(self) -> dict[str, Any]:
        """Parse a Section block (Detail, FormHeader, etc.)."""
        section: dict[str, Any] = {
            "name": "",
            "properties": {},
            "controls": [],
        }

        while True:
            current = self.peek()
            if current is None:
                break
            if current == "End":
                self.advance()
                break

            if current.startswith("Begin") and "=" not in current:
                parts = current.split(None, 1)
                block_type = parts[1] if len(parts) > 1 else ""
                self.advance()

                if block_type in CONTROL_TYPES:
                    control = self._parse_control(block_type)
                    section["controls"].append(control)
                elif block_type == "":
                    self._parse_anonymous_block_for_section(section)
                else:
                    self._skip_block()
                continue

            if "=" in current:
                key, val = self._parse_property_line(current)
                self.advance()

                # Binary data block
                if val == "Begin" or val == " Begin":
                    self._skip_binary_block()
                    continue

                if isinstance(val, str) and val.startswith('"'):
                    val = self._read_multiline_string(val)

                if key == "Name":
                    section["name"] = val.strip('"')
                section["properties"][key] = val
                continue

            self.advance()

        return section

    def _parse_anonymous_block(self, parent: dict):
        """Parse an anonymous Begin...End block (default property blocks or nested controls)."""
        while True:
            current = self.peek()
            if current is None:
                break
            if current == "End":
                self.advance()
                break

            if current.startswith("Begin"):
                parts = current.split(None, 1)
                block_type = parts[1] if len(parts) > 1 else ""
                self.advance()

                if block_type in CONTROL_TYPES:
                    control = self._parse_control(block_type)
                    parent.setdefault("controls", []).append(control)
                elif block_type == "Section":
                    section = self._parse_section()
                    parent.setdefault("sections", []).append(section)
                elif block_type == "":
                    self._parse_anonymous_block(parent)
                else:
                    self._skip_block()
                continue

            if "=" in current:
                self.advance()
                continue

            if current.endswith("= Begin") or current.endswith("=  Begin"):
                self.advance()
                self._skip_binary_block()
                continue

            self.advance()

    def _parse_anonymous_block_for_control(self, control: dict):
        """Parse anonymous Begin...End inside a control (child controls)."""
        while True:
            current = self.peek()
            if current is None:
                break
            if current == "End":
                self.advance()
                break

            if current.startswith("Begin"):
                parts = current.split(None, 1)
                block_type = parts[1] if len(parts) > 1 else ""
                self.advance()

                if block_type in CONTROL_TYPES:
                    child = self._parse_control(block_type)
                    control["children"].append(child)
                elif block_type == "":
                    self._parse_anonymous_block_for_control(control)
                else:
                    self._skip_block()
                continue

            if "=" in current:
                key, val = self._parse_property_line(current)
                self.advance()
                if isinstance(val, str) and val.startswith('"'):
                    val = self._read_multiline_string(val)
                if key in EVENT_PROPERTIES:
                    control["events"][key] = val
                elif key in CONTROL_PROPERTIES:
                    control["properties"][key] = val
                continue

            self.advance()

    def _parse_anonymous_block_for_section(self, section: dict):
        """Parse anonymous Begin...End inside a section."""
        while True:
            current = self.peek()
            if current is None:
                break
            if current == "End":
                self.advance()
                break

            if current.startswith("Begin"):
                parts = current.split(None, 1)
                block_type = parts[1] if len(parts) > 1 else ""
                self.advance()

                if block_type in CONTROL_TYPES:
                    control = self._parse_control(block_type)
                    section["controls"].append(control)
                elif block_type == "":
                    self._parse_anonymous_block_for_section(section)
                else:
                    self._skip_block()
                continue

            if "=" in current:
                self.advance()
                continue

            self.advance()

    def _skip_block(self):
        """Skip a Begin...End block (including nested)."""
        depth = 1
        while depth > 0 and self.pos < len(self.lines):
            line = self.lines[self.pos].strip()
            self.pos += 1
            if not line:
                continue
            if line.startswith("Begin") or line.endswith("= Begin") or line.endswith("=  Begin"):
                depth += 1
            elif line == "End":
                depth -= 1

    def _skip_binary_block(self):
        """Skip binary data lines until 'End'."""
        while self.pos < len(self.lines):
            line = self.lines[self.pos].strip()
            self.pos += 1
            if line == "End":
                break


    def _extract_vba_procedures(self, code: str) -> list[dict[str, str]]:
        """Extract VBA Sub/Function definitions from code-behind."""
        procs = []
        pattern = re.compile(
            r"(Private\s+|Public\s+)?(Sub|Function)\s+(\w+)\s*\(",
            re.IGNORECASE
        )
        for match in pattern.finditer(code):
            scope = (match.group(1) or "").strip()
            kind = match.group(2)
            name = match.group(3)

            # Try to identify event association
            # Pattern: controlName_EventName
            event_match = re.match(r"(\w+)_(\w+)", name)
            if event_match:
                control_name = event_match.group(1)
                event_name = event_match.group(2)
            else:
                control_name = ""
                event_name = ""

            procs.append({
                "scope": scope,
                "kind": kind,
                "name": name,
                "control": control_name,
                "event": event_name,
            })

        return procs


# ── Public API ────────────────────────────────────────────────────

def parse_form(filepath: Path) -> dict[str, Any]:
    """Parse a SaveAsText form export file.

    Returns structured dict with:
        - type: "Form"
        - properties: dict of form-level properties
        - sections: list of section dicts
        - controls: list of control dicts (all controls, flattened)
        - code_behind: str (VBA code text)
        - vba_procedures: list of procedure dicts
    """
    text = read_saveastext(filepath)
    parser = SaveAsTextParser(text)
    result = parser.parse_top_level()
    result["filename"] = filepath.name
    result["filepath"] = str(filepath)

    # Flatten all controls from sections and nested blocks
    all_controls = _flatten_controls(result)
    result["all_controls"] = all_controls

    return result


def parse_report(filepath: Path) -> dict[str, Any]:
    """Parse a SaveAsText report export file.

    Same format as forms but with report-specific properties.
    """
    text = read_saveastext(filepath)
    parser = SaveAsTextParser(text)
    result = parser.parse_top_level()
    result["filename"] = filepath.name
    result["filepath"] = str(filepath)

    all_controls = _flatten_controls(result)
    result["all_controls"] = all_controls

    return result


def _flatten_controls(parsed: dict) -> list[dict]:
    """Recursively collect all controls from sections and nested blocks."""
    controls = []

    def _collect(obj: dict):
        for ctrl in obj.get("controls", []):
            controls.append(ctrl)
            _collect(ctrl)  # recurse into children
            for child in ctrl.get("children", []):
                controls.append(child)
                _collect(child)
        for section in obj.get("sections", []):
            _collect(section)

    _collect(parsed)
    return controls


# ── CLI for testing ───────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_saveastext.py <file.txt>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    result = parse_form(path) if "report" not in str(path).lower() else parse_report(path)

    # Print summary
    print(f"Type: {result['type']}")
    print(f"Properties: {list(result['properties'].keys())}")
    print(f"Sections: {len(result.get('sections', []))}")
    print(f"All controls: {len(result.get('all_controls', []))}")
    print(f"Code-behind length: {len(result.get('code_behind', ''))}")
    print(f"VBA procedures: {len(result.get('vba_procedures', []))}")

    # Print controls summary
    for ctrl in result.get("all_controls", []):
        name = ctrl.get("properties", {}).get("Name", "?")
        ctype = ctrl.get("type", "?")
        source = ctrl.get("properties", {}).get("ControlSource", "")
        events = list(ctrl.get("events", {}).keys())
        print(f"  [{ctype}] {name}: source={source}, events={events}")
