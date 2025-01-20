import glob
import json
import os
import shutil
import subprocess
import matplotlib.pyplot as plt


def run_benchmarks():
    # Ensure the `.benchmarks` folder exists
    os.makedirs(".benchmarks", exist_ok=True)

    # Run pytest benchmarks and save results
    print("Running benchmarks...")
    result = subprocess.run(
        ["pytest", "benchmarks/catch_all.py", "--benchmark-save=benchmark_results"],
        capture_output=True,
        text=True
    )
    print(result.stdout)


def load_benchmark_results(file_path):
    """Load the benchmark results from the provided JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def plot_relative_performance(results):
    """Plot relative performance for different benchmark groups."""
    benchmarks = results["benchmarks"]

    # Extract and format data
    names = []
    ops = []
    for bm in benchmarks:
        group = bm.get("group", "")
        library = "dataclass-wizard" if "wizard" in bm["name"] else "dataclasses-json"
        formatted_name = f"{group} ({library})"
        names.append(formatted_name)
        ops.append(bm["stats"]["ops"])

    # Calculate relative performance (ratio of each ops to the slowest ops)
    baseline = min(ops)
    relative_performance = [op / baseline for op in ops]

    # Plot bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.barh(names, relative_performance, color="skyblue")
    plt.xlabel("Performance Relative to Slowest (times faster)")
    plt.title("Catch All: Relative Performance of dataclass-wizard vs dataclasses-json")
    plt.tight_layout()

    # Add data labels to the bars
    for bar, rel_perf in zip(bars, relative_performance):
        plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                 f"{rel_perf:.1f}x", va="center")

    # Save and display the plot
    plt.savefig("catch_all.png")
    plt.show()


def find_latest_benchmark_file():
    """Find the most recent benchmark result file."""
    benchmark_dir = ".benchmarks"
    pattern = os.path.join(benchmark_dir, "**", "*.json")
    files = glob.glob(pattern, recursive=True)
    if not files:
        raise FileNotFoundError("No benchmark files found.")
    latest_file = max(files, key=os.path.getctime)  # Find the most recently created file
    return latest_file


if __name__ == "__main__":
    # Step 1: Run benchmarks
    run_benchmarks()

    # Step 2: Find the latest benchmark results file
    benchmark_file = find_latest_benchmark_file()
    print(f"Latest benchmark file: {benchmark_file}")

    # Step 3: Load the benchmark results
    if os.path.exists(benchmark_file):
        results = load_benchmark_results(benchmark_file)

        # Step 4: Plot results
        plot_relative_performance(results)

    else:
        print(f"Benchmark file not found: {benchmark_file}")

    # Step 5: Move the generated image to docs folder for easy access
    shutil.copy("catch_all.png", "docs/")
