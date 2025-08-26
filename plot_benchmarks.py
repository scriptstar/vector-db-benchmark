import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import mplcyberpunk

plt.style.use("cyberpunk")


def load_metrics(json_path: Path):
    with open(json_path, "r") as f:
        data = json.load(f)
    # Infer DB names (top-level keys excluding _config)
    db_names = [k for k in data.keys() if k != "_config"]
    
    # Filter out databases that have errors instead of benchmark data
    valid_db_names = []
    for db_name in db_names:
        if "error" not in data[db_name]:
            valid_db_names.append(db_name)
        else:
            print(f"Skipping {db_name} - contains error data")
    
    if not valid_db_names:
        raise ValueError("No valid database results found")
    
    # Extract k values - get intersection of all available k values across all valid databases
    all_k_sets = []
    for db_name in valid_db_names:
        db_k_labels = [k for k in data[db_name].keys() if k.startswith("k=")]
        db_k_values = [int(k.split("=")[1]) for k in db_k_labels]
        all_k_sets.append(set(db_k_values))
    
    # Use intersection of all k values to ensure all databases have data for these k values
    common_k_values = set.intersection(*all_k_sets) if all_k_sets else set()
    k_values = sorted(list(common_k_values))
    
    # Build structures
    ingest = {}
    qps_list = {}
    recall50 = {}
    latency = {db: [] for db in valid_db_names}
    
    for db in valid_db_names:
        db_block = data[db]
        
        # Find the first available k value for this database
        available_k_labels = [k for k in db_block.keys() if k.startswith("k=")]
        if not available_k_labels:
            print(f"Skipping {db} - no k= entries found")
            continue
            
        # Ingest/setup stored redundantly per k; read once from the first available k
        first_k_label = available_k_labels[0]
        ingest[db] = float(db_block[first_k_label]["ingest_time_sec"])
        
        # Aggregate QPS over available ks (average)
        qps_vals = []
        for k_label in available_k_labels:
            qps_vals.append(float(db_block[k_label]["avg_qps"]))
        qps_list[db] = float(np.mean(qps_vals))
        
        # Recall@50 from k=50 if present; else best effort
        if "k=50" in available_k_labels:
            recall50[db] = float(db_block["k=50"]["avg_recall_at_50"])
        else:
            # Fallback: use largest available k's recall if exact 50 not present
            available_ks = [int(k.split("=")[1]) for k in available_k_labels]
            max_available_k = max(available_ks)
            recall_key = f"k={max_available_k}"
            # pick any recall field in that block
            rec = None
            if recall_key in available_k_labels:
                for key in db_block[recall_key].keys():
                    if "recall" in key:
                        rec = float(db_block[recall_key][key])
                        break
            recall50[db] = rec if rec is not None else float("nan")
        # Latency series per common k values only
        for k in k_values:
            k_label = f"k={k}"
            if k_label in available_k_labels:
                latency[db].append(float(db_block[k_label]["avg_query_latency_sec"]))
    return valid_db_names, k_values, ingest, qps_list, recall50, latency


def add_value_labels_bars(ax, bars, fmt="{:.2f}"):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            fmt.format(height),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def add_value_labels_points(ax, x, y, fmt="{:.4f}"):
    for xi, yi in zip(x, y):
        ax.annotate(
            fmt.format(yi),
            xy=(xi, yi),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def plot_grouped_bars(db_names, ingest, qps_list, recall50, latency, out_path: Path):
    # Calculate average latency across all k values for each database
    avg_latency = {}
    for db in db_names:
        if latency[db]:  # Check if latency data exists
            avg_latency[db] = np.mean(latency[db]) * 1000  # Convert to milliseconds
        else:
            avg_latency[db] = 0
    
    # Prepare data in consistent order
    x = np.arange(len(db_names))
    width = 0.2  # Reduced width to fit 4 bars

    fig = plt.figure(figsize=(12, 6))  # Wider figure for 4 bars
    ax = fig.add_subplot(111)

    bars1 = ax.bar(
        x - 1.5*width, [ingest[d] for d in db_names], width, label="Ingest Time (s)"
    )
    bars2 = ax.bar(
        x - 0.5*width, [qps_list[d] for d in db_names], width, label="QPS (avg)"
    )
    bars3 = ax.bar(
        x + 0.5*width, [recall50[d] for d in db_names], width, label="Recall@50"
    )
    bars4 = ax.bar(
        x + 1.5*width, [avg_latency[d] for d in db_names], width, label="Avg Latency (ms)"
    )

    mplcyberpunk.add_bar_gradient(bars=bars1)
    mplcyberpunk.add_bar_gradient(bars=bars2)
    mplcyberpunk.add_bar_gradient(bars=bars3)
    mplcyberpunk.add_bar_gradient(bars=bars4)

    ax.set_xticks(x)
    ax.set_xticklabels(db_names)
    ax.set_title("Ingest Time, QPS (avg), Recall@50, and Avg Latency")
    ax.legend()

    # Add labels
    add_value_labels_bars(ax, bars1, fmt="{:.2f}")
    add_value_labels_bars(ax, bars2, fmt="{:.1f}")
    add_value_labels_bars(ax, bars3, fmt="{:.3f}")
    add_value_labels_bars(ax, bars4, fmt="{:.1f}")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_latency_lines(db_names, k_values, latency, out_path: Path):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    # Plot each DB only once in the legend
    lines = []
    labels = []
    for db in db_names:
        y = latency[db]
        (line,) = ax.plot(k_values, y, marker="o", label=db)
        lines.append(line)
        labels.append(db)
        add_value_labels_points(ax, k_values, y, fmt="{:.4f}")

    mplcyberpunk.make_lines_glow(ax)

    ax.set_xticks(k_values)
    ax.set_xlabel("k")
    ax.set_ylabel("Latency (s)")
    ax.set_title("Latency vs. k")
    # Deduplicate legend labels
    handles, legend_labels = ax.get_legend_handles_labels()
    unique = dict()
    for h, l in zip(handles, legend_labels):
        if l not in unique:
            unique[l] = h
    ax.legend(list(unique.values()), list(unique.keys()))
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def stack_images_vertically(img_paths, out_path: Path):
    imgs = [Image.open(p).convert("RGB") for p in img_paths]
    widths = [im.width for im in imgs]
    heights = [im.height for im in imgs]
    canvas = Image.new("RGB", (max(widths), sum(heights)), "white")
    y = 0
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height
    canvas.save(out_path)


def main():
    if len(sys.argv) < 3:
        print("Usage: python plot_benchmarks.py <metrics.json> <output_prefix>")
        sys.exit(1)
    json_path = Path(sys.argv[1])
    out_prefix = Path(sys.argv[2])

    db_names, k_values, ingest, qps_list, recall50, latency = load_metrics(json_path)

    bars_path = out_prefix.with_name(out_prefix.name + "_bars.png")
    latency_path = out_prefix.with_name(out_prefix.name + "_latency.png")
    combined_path = out_prefix.with_suffix(".png")

    plot_grouped_bars(db_names, ingest, qps_list, recall50, latency, bars_path)
    plot_latency_lines(db_names, k_values, latency, latency_path)
    stack_images_vertically([bars_path, latency_path], combined_path)

    print(f"Saved:\n- {bars_path}\n- {latency_path}\n- {combined_path}")


if __name__ == "__main__":
    main()
