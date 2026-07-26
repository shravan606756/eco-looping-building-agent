import sys
import argparse
from pathlib import Path

from utils.env_validator import EnvironmentValidator
from utils.workspace_reset import WorkspaceReset
from utils.report_reader import ReportReader
from optimizer.closed_loop_agent import ClosedLoopAgent
from config import OUTPUT_DIR


def print_banner():
    print("""
==================================================
  HONEYWELL ECO-LOOP AUTONOMOUS BUILDING AGENTS   
  AI-Powered Closed-Loop HVAC Optimization System 
==================================================
""")


def display_registered_tools(agent: ClosedLoopAgent):
    manifest = agent.registry.get_manifest()
    print("Discovered Registered Agentic Tools")
    print("-----------------------------------")
    for tool_info in manifest["tools"]:
        print(f"  • {tool_info['name']:<25} : {tool_info['description']}")
    print("-----------------------------------\n")


def run_interactive_menu():
    print_banner()
    validator = EnvironmentValidator()
    env_res = validator.validate_environment()

    if not env_res["valid"]:
        print("\n[ENVIRONMENT ERROR] Environment validation failed:")
        for err in env_res["errors"]:
            print(f"  [FAIL] {err}")
        sys.exit(1)

    reset_util = WorkspaceReset()
    agent = ClosedLoopAgent()

    while True:
        print("\n--- Developer Interactive Control Menu ---")
        print("1. Reset Workspace")
        print("2. Run Closed-Loop Optimization")
        print("3. Reset Workspace + Run Optimization")
        print("4. Show Registered Tools Manifest")
        print("5. Exit")
        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            print("\nExecuting Workspace Reset...")
            res = reset_util.reset_workspace()
            for act in res["actions"]:
                print(f"  [OK] {act}")
            print("Workspace reset completed successfully.")

        elif choice == "2":
            iters_str = input("Enter max iterations (default 3): ").strip()
            iters = int(iters_str) if iters_str.isdigit() else 3
            print(f"\nStarting Autonomous Optimization ({iters} iterations)...")
            out = agent.run_optimization(max_iterations=iters)
            ReportReader.print_executive_summary(OUTPUT_DIR, session_dir=out.get("session_dir", ""))

        elif choice == "3":
            iters_str = input("Enter max iterations (default 3): ").strip()
            iters = int(iters_str) if iters_str.isdigit() else 3
            print("\nExecuting Workspace Reset...")
            res = reset_util.reset_workspace()
            for act in res["actions"]:
                print(f"  [OK] {act}")

            print(f"\nStarting Autonomous Optimization ({iters} iterations)...")
            out = agent.run_optimization(max_iterations=iters)
            ReportReader.print_executive_summary(OUTPUT_DIR, session_dir=out.get("session_dir", ""))

        elif choice == "4":
            print()
            display_registered_tools(agent)

        elif choice == "5":
            print("\nExiting. Good luck with the Honeywell Hackathon!")
            sys.exit(0)
        else:
            print("Invalid option. Please enter 1-5.")


def main():
    parser = argparse.ArgumentParser(
        description="Honeywell Eco-Loop Building Agents — Autonomous HVAC Optimization Engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Safely clean the optimization workspace")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run closed-loop optimization (auto-cleans workspace first)")
    run_parser.add_argument("--iterations", type=int, default=3, help="Maximum optimization iterations (default: 3)")

    # Menu command
    menu_parser = subparsers.add_parser("menu", help="Launch developer interactive CLI menu")

    args = parser.parse_args()

    if args.command == "menu":
        run_interactive_menu()
        return

    print_banner()

    # Step 1: Environment Validation
    print("Checking Environment Requirements...")
    env_res = EnvironmentValidator.validate_environment()
    for chk in env_res["checks"]:
        print(f"  {chk['status']} {chk['item']}")

    if not env_res["valid"]:
        print("\n[FAIL] Environment validation failed:")
        for err in env_res["errors"]:
            print(f"  - {err}")
        sys.exit(1)
    print("[OK] Environment is ready.\n")

    reset_util = WorkspaceReset()

    if args.command == "reset":
        print("Executing Workspace Reset...")
        res = reset_util.reset_workspace()
        for act in res["actions"]:
            print(f"  [OK] {act}")
        print("\nWorkspace reset complete.\n")
        return

    if args.command == "run":
        # Auto-clean before run to ensure idempotency
        print("Executing Pre-Run Workspace Reset...")
        res = reset_util.reset_workspace()
        for act in res["actions"]:
            print(f"  [OK] {act}")
        print("Workspace reset complete.\n")

        # Step 3: Instantiate ClosedLoopAgent & Display Tools
        agent = ClosedLoopAgent()
        display_registered_tools(agent)

        # Step 4: Run Optimization
        print(f"Starting Closed-Loop Optimization (Max Iterations: {args.iterations})...\n")
        try:
            run_results = agent.run_optimization(max_iterations=args.iterations, output_root=OUTPUT_DIR)
            
            # Step 5: Post-Run Executive Summary
            ReportReader.print_executive_summary(OUTPUT_DIR, session_dir=run_results.get("session_dir", ""))

        except Exception as e:
            print(f"\n[ERROR] Optimization error encountered: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
