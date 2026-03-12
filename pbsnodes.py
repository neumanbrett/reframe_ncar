"""
pbsnodes.py - Dynamic NCAR node registry from ``pbsnodes -a``

Queries ``pbsnodes -a`` at import time to build a live node type registry.
Falls back to an empty dict if ``pbsnodes`` is unavailable (e.g. non-PBS
environments).  The :class:`NodeTypeSpec` shape is compatible with the
static registry in ``nodetypes.py`` so both modules are interchangeable in
test files.

Node type labelling
-------------------
- **GPU nodes** (``ngpus > 0``) are keyed by the *primary* GPU type, which
  is the first value in the comma-separated ``gpu_type`` PBS resource
  (e.g. ``a100,a100_80gb,a100_4way,...`` → ``a100``).
- **CPU-only nodes** are keyed by their ``cpu_type`` PBS resource.

Hardware fields (``ncpus``, ``mem``) within each group are set to the most
common value observed across all nodes of that type, to handle minor
per-node variance.

Public API
----------
NODE_TYPE_SPECS : dict[str, NodeTypeSpec]
    Full registry built at import time.

get_node_types(gpu_only, cpu_only) → dict[str, NodeTypeSpec]
get_cpu_node_types()               → dict[str, NodeTypeSpec]
get_gpu_node_types()               → dict[str, NodeTypeSpec]
get_all_nodes(node_type_label)     → list[NodeRecord]
"""

import subprocess
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class NodeRecord:
    """Raw attributes parsed from a single ``pbsnodes -a`` stanza."""
    hostname: str
    state:    str
    cpu_type: Optional[str]
    gpu_type: Optional[str]   # primary GPU label only (first CSV value)
    ncpus:    int
    ngpus:    int
    mem:      str             # normalised PBS string, e.g. '354GB'


@dataclass
class NodeTypeSpec:
    """
    Hardware and PBS resource specification for a node type.

    Compatible with the ``NodeTypeSpec`` in ``nodetypes.py``, with one
    additional field: ``hostnames`` lists every node that belongs to this
    type.
    """
    cpu_type:  Optional[str]   # PBS chunk resource ':cpu_type=<value>'
    gpu_type:  Optional[str]   # PBS chunk resource ':gpu_type=<value>'; None for CPU-only
    ncpus:     int             # Representative CPU core count for this type
    ngpus:     int             # GPU count per node (0 = CPU-only)
    mem:       str             # Representative usable memory (PBS string)
    tasks:     int             # Default MPI task count for single-node jobs
    hostnames: list = field(default_factory=list)  # All hostnames of this type
    descr:     str  = ''


# =============================================================================
# Parsing helpers
# =============================================================================

def _normalise_mem(mem_str: str) -> str:
    """Convert a PBS memory string to a whole-GB string.

    Examples::

        '362794mb'       → '354GB'
        '1524009mb'      → '1488GB'
        '520064184kb'    → '495GB'
        '16gb'           → '16GB'
    """
    s = mem_str.strip().lower()
    if s.endswith('kb'):
        gb = int(s[:-2]) // (1024 * 1024)
    elif s.endswith('mb'):
        gb = int(s[:-2]) // 1024
    elif s.endswith('gb'):
        gb = int(s[:-2])
    else:
        gb = int(s) // (1024 ** 3)
    return f'{gb}GB'


def _make_record(d: dict) -> NodeRecord:
    """Build a :class:`NodeRecord` from a raw key/value dict."""
    gpu_type_raw = d.get('resources_available.gpu_type', '')
    # Keep only the primary label (first CSV token, e.g. 'a100' from 'a100,a100_80gb,...')
    gpu_type = gpu_type_raw.split(',')[0] if gpu_type_raw else None

    return NodeRecord(
        hostname = d['hostname'],
        state    = d.get('state', 'unknown'),
        cpu_type = d.get('resources_available.cpu_type'),
        gpu_type = gpu_type,
        ncpus    = int(d.get('resources_available.ncpus', 0)),
        ngpus    = int(d.get('resources_available.ngpus', 0)),
        mem      = _normalise_mem(d.get('resources_available.mem', '0mb')),
    )


def parse_pbsnodes(output: str) -> list:
    """Parse the text output of ``pbsnodes -a`` into a list of :class:`NodeRecord`.

    Parameters
    ----------
    output : str
        Raw stdout from ``pbsnodes -a``.

    Returns
    -------
    list[NodeRecord]
        One record per node.  Nodes whose state contains ``offline`` or
        ``down`` are excluded so tests are not submitted to unavailable nodes.
    """
    records = []
    current: dict = {}

    for line in output.splitlines():
        if not line:
            continue
        if not line[0].isspace():
            # New node stanza — flush the previous one
            if current.get('hostname'):
                rec = _make_record(current)
                state = rec.state.lower()
                if 'offline' not in state and 'down' not in state:
                    records.append(rec)
            current = {'hostname': line.strip()}
        else:
            m = re.match(r'\s+(\S+)\s*=\s*(.+)', line)
            if m:
                current[m.group(1)] = m.group(2).strip()

    # Flush the last stanza
    if current.get('hostname'):
        rec = _make_record(current)
        state = rec.state.lower()
        if 'offline' not in state and 'down' not in state:
            records.append(rec)

    return records


# =============================================================================
# Node-type registry builder
# =============================================================================

def _node_label(node: NodeRecord) -> str:
    """Return the canonical type label for a node.

    GPU nodes are labelled by primary ``gpu_type``; CPU-only nodes by
    ``cpu_type``.
    """
    if node.ngpus > 0 and node.gpu_type:
        return node.gpu_type
    return node.cpu_type or 'unknown'


def _most_common(values):
    """Return the most frequently occurring value in *values*."""
    counts: dict = defaultdict(int)
    for v in values:
        counts[v] += 1
    return max(counts, key=counts.__getitem__)


def _floor_pow2(n: int) -> int:
    """Return the largest power of 2 that is <= *n*.

    Used to choose a default MPI task count that satisfies power-of-2
    domain decomposition requirements common in atmospheric/ocean models.

    Examples::

        _floor_pow2(34)  -> 32
        _floor_pow2(62)  -> 32
        _floor_pow2(36)  -> 32
        _floor_pow2(64)  -> 64
        _floor_pow2(128) -> 128
        _floor_pow2(96)  -> 64
    """
    if n < 1:
        return 1
    return 1 << (n.bit_length() - 1)


def build_node_type_specs(nodes: list) -> dict:
    """Group *nodes* by type label and build a :class:`NodeTypeSpec` dict.

    Parameters
    ----------
    nodes : list[NodeRecord]
        Parsed node records (e.g. from :func:`parse_pbsnodes`).

    Returns
    -------
    dict[str, NodeTypeSpec]
        Keys are type labels (e.g. ``'cascadelake'``, ``'a100'``).
        ``NodeTypeSpec.hostnames`` lists every node in that group.
    """
    groups: dict = defaultdict(list)
    for node in nodes:
        groups[_node_label(node)].append(node)

    specs = {}
    for label, group in sorted(groups.items()):
        representative = group[0]

        # Use the most common hardware values to handle per-node variance
        ncpus = _most_common([n.ncpus for n in group])
        mem   = _most_common([n.mem   for n in group])
        ngpus = _most_common([n.ngpus for n in group])

        cpu_type = representative.cpu_type
        gpu_type = representative.gpu_type if ngpus > 0 else None
        hostnames = sorted(n.hostname for n in group)

        # Default task count: GPU nodes use ngpus; CPU nodes use the largest
        # power of 2 <= ncpus to satisfy typical MPI domain decomposition.
        tasks = ngpus if ngpus > 0 else _floor_pow2(ncpus)

        # Human-readable description
        parts = []
        if cpu_type:
            parts.append(cpu_type)
        if gpu_type:
            parts.append(f'{ngpus}x {gpu_type}')
        parts.append(f'{ncpus} CPUs')
        parts.append(mem)
        parts.append(f'({len(hostnames)} nodes)')

        specs[label] = NodeTypeSpec(
            cpu_type  = cpu_type,
            gpu_type  = gpu_type,
            ncpus     = ncpus,
            ngpus     = ngpus,
            mem       = mem,
            tasks     = tasks,
            hostnames = hostnames,
            descr     = ', '.join(parts),
        )

    return specs


# =============================================================================
# Live query
# =============================================================================

def query_pbsnodes() -> list:
    """Run ``pbsnodes -a`` and return a list of :class:`NodeRecord`.

    Returns an empty list if ``pbsnodes`` is not on the PATH or times out,
    so callers on non-PBS systems fail gracefully.
    """
    try:
        result = subprocess.run(
            ['pbsnodes', '-a'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return parse_pbsnodes(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return []


# =============================================================================
# Module-level registry — built once at import time
# =============================================================================

_all_nodes: list = query_pbsnodes()
NODE_TYPE_SPECS: dict = build_node_type_specs(_all_nodes)


# =============================================================================
# Public helpers
# =============================================================================

def get_node_types(gpu_only: bool = False, cpu_only: bool = False) -> dict:
    """Return the node type registry with optional filtering.

    Parameters
    ----------
    gpu_only : bool
        If True, return only types with GPUs (``ngpus > 0``).
    cpu_only : bool
        If True, return only CPU-only types (``ngpus == 0``).

    Raises
    ------
    ValueError
        If both *gpu_only* and *cpu_only* are True.
    """
    if gpu_only and cpu_only:
        raise ValueError('gpu_only and cpu_only are mutually exclusive')
    if gpu_only:
        return {k: v for k, v in NODE_TYPE_SPECS.items() if v.ngpus > 0}
    if cpu_only:
        return {k: v for k, v in NODE_TYPE_SPECS.items() if v.ngpus == 0}
    return dict(NODE_TYPE_SPECS)


def get_cpu_node_types() -> dict:
    """Return only CPU-only node types."""
    return get_node_types(cpu_only=True)


def get_gpu_node_types() -> dict:
    """Return only GPU node types."""
    return get_node_types(gpu_only=True)


def get_all_nodes(node_type_label: str = None) -> list:
    """Return individual :class:`NodeRecord` objects.

    Parameters
    ----------
    node_type_label : str, optional
        If given, return only nodes whose type label matches
        (e.g. ``'cascadelake'``).  If None, return all nodes.
    """
    if node_type_label is None:
        return list(_all_nodes)
    return [n for n in _all_nodes if _node_label(n) == node_type_label]
