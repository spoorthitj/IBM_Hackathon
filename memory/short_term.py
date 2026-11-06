"""
Memory — Short-Term Agent Memory
Session-scoped context buffer. Agents read each other's outputs as context.
"""
from datetime import datetime

_buffer: dict[str, list[dict]] = {}   # agent_name → list of memory entries
_shared: list[dict] = []              # shared cross-agent context


def store(agent_name: str, key: str, value: str, shared: bool = True):
    """Store a memory entry for an agent."""
    entry = {
        "ts":    datetime.utcnow().isoformat(),
        "agent": agent_name,
        "key":   key,
        "value": value[:2000],
    }
    if agent_name not in _buffer:
        _buffer[agent_name] = []
    _buffer[agent_name].append(entry)
    if shared:
        _shared.append(entry)


def recall(agent_name: str, max_entries: int = 3) -> str:
    """Recall relevant context for an agent (its own + shared from upstream agents)."""
    lines = []
    # Own memory
    for e in (_buffer.get(agent_name, []))[-max_entries:]:
        lines.append(f"[{e['key']}] {e['value'][:300]}")
    # Shared from other agents (most recent 3)
    others = [e for e in _shared[-6:] if e["agent"] != agent_name]
    for e in others[-3:]:
        lines.append(f"[{e['agent']} → {e['key']}] {e['value'][:200]}")
    return "\n".join(lines) if lines else ""


def get_all_shared() -> list[dict]:
    return list(_shared)


def clear():
    _buffer.clear()
    _shared.clear()
