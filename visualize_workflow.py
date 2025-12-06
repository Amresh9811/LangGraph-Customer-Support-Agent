"""
Visualize the SkylarIQ workflow graph

This script generates a text-based visualization of the 11-stage workflow.
"""

import yaml
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def load_stages():
    """Load stage definitions from config"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get("stages", [])


def visualize_workflow():
    """Generate workflow visualization"""
    stages = load_stages()

    print("\n" + "="*80)
    print("SKYLARIQ WORKFLOW VISUALIZATION")
    print("="*80)

    print("\nWorkflow Graph:")
    print("-"*80)

    # Linear flow visualization
    print("\n    START")
    print("      │")

    for i, stage in enumerate(stages):
        name = stage['name']
        emoji = stage.get('emoji', '')
        mode = stage.get('mode', 'deterministic')
        abilities = stage.get('abilities', [])
        server = stage.get('server', 'unknown')

        # Stage box
        print(f"      ▼")
        print(f"   ┌─────────────────┐")
        print(f"   │ {emoji} {name:<14}│")
        print(f"   └─────────────────┘")

        # Mode indicator
        if mode == "non-deterministic":
            print(f"      ⚡ {mode.upper()}")

        # Server indicator
        server_symbol = "🌐" if server == "atlas" else "💾"
        print(f"      {server_symbol} Server: {server}")

        # Abilities
        print(f"      📋 Abilities ({len(abilities)}):")
        for ability in abilities:
            print(f"         • {ability}")

        # Special routing for ASK stage
        if name == "ASK":
            print(f"      │")
            print(f"      ├─ [needs clarification] → WAIT")
            print(f"      └─ [no clarification] → RETRIEVE")
            print(f"      │")
            print(f"   (merge)")

    print("      │")
    print("      ▼")
    print("     END")
    print()

    # Summary statistics
    print("\n" + "="*80)
    print("WORKFLOW STATISTICS")
    print("="*80)

    total_stages = len(stages)
    deterministic = sum(1 for s in stages if s.get('mode') == 'deterministic')
    non_deterministic = sum(1 for s in stages if s.get('mode') == 'non-deterministic')
    total_abilities = sum(len(s.get('abilities', [])) for s in stages)
    atlas_abilities = sum(
        len(s.get('abilities', []))
        for s in stages
        if s.get('server') == 'atlas'
    )
    common_abilities = sum(
        len(s.get('abilities', []))
        for s in stages
        if s.get('server') == 'common'
    )

    print(f"\nTotal Stages: {total_stages}")
    print(f"  • Deterministic: {deterministic}")
    print(f"  • Non-deterministic: {non_deterministic}")
    print(f"\nTotal Abilities: {total_abilities}")
    print(f"  • Atlas Server: {atlas_abilities}")
    print(f"  • Common Server: {common_abilities}")

    # Stage details table
    print("\n" + "="*80)
    print("STAGE DETAILS")
    print("="*80)
    print(f"\n{'Stage':<15} {'Mode':<20} {'Server':<10} {'Abilities':<10}")
    print("-"*80)

    for stage in stages:
        name = stage['name']
        emoji = stage.get('emoji', '')
        mode = stage.get('mode', 'deterministic')
        server = stage.get('server', 'unknown')
        ability_count = len(stage.get('abilities', []))

        mode_display = mode if mode == "deterministic" else "NON-DETERMINISTIC ⚡"

        print(f"{emoji} {name:<12} {mode_display:<20} {server:<10} {ability_count}")

    print("\n" + "="*80)
    print("\nLegend:")
    print("  🌐 = Atlas Server (External system interactions)")
    print("  💾 = Common Server (Internal operations)")
    print("  ⚡ = Non-deterministic routing")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        visualize_workflow()
    except Exception as e:
        print(f"Error visualizing workflow: {e}")
        raise
