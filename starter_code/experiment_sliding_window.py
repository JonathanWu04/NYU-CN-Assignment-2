#!/usr/bin/env python3
import subprocess
import re
import matplotlib.pyplot as plt
import sys


def run_sim(rtt, ticks, window, seed=1, loss_ratio=0.0):
    cmd = [
        sys.executable,
        'starter_code/run_reliability_simulation.py',
        '--seed', str(seed),
        '--rtt-min', str(rtt),
        '--ticks', str(ticks),
    ]
    # global options (like loss-ratio) must come before subcommand
    if loss_ratio is not None and loss_ratio > 0.0:
        cmd += ['--loss-ratio', str(loss_ratio)]
    # subcommand and its specific options
    cmd += ['sliding-window']
    cmd += ['--window-size', str(window)]
    print('Running:', ' '.join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    m = re.search(r"Maximum in order received sequence number\s*(\d+)", out)
    if not m:
        raise RuntimeError(f"Failed to parse simulator output for rtt={rtt} window={window} loss={loss_ratio}\nOutput:\n{out}")
    return int(m.group(1))


def experiment(rtts, window_sizes, ticks=1000, seed=1):
    loss_settings = [0.0, 0.01, 0.02, 0.05, 0.1]
    # results[loss][window] = list of max_in_order for each rtt (same order as rtts)
    results = {loss: {w: [] for w in window_sizes} for loss in loss_settings}
    for loss in loss_settings:
        for w in window_sizes:
            for r in rtts:
                max_in_order = run_sim(r, ticks, window=w, seed=seed, loss_ratio=loss)
                results[loss][w].append(max_in_order)
    return results


def plot_results(rtts, window_sizes, results, ticks, out_prefix='sliding_window_throughput'):
    inv_rtt = [1.0 / r for r in rtts]
    for loss, data in results.items():
        plt.figure()
        # assign a color per window size and use it for both measured and ideal lines
        colors = plt.rcParams['axes.prop_cycle'].by_key().get('color', plt.cm.tab10.colors)
        sorted_ws = sorted(data.keys())
        for idx, w in enumerate(sorted_ws):
            color = colors[idx % len(colors)]
            max_list = data[w]
            throughput = [(m + 1) / ticks for m in max_list]
            plt.plot(inv_rtt, throughput, marker='o', label=f'W={w}', color=color)
            # ideal W/RTT line with same color but dashed and lighter
            ideal = [float(w) / r for r in rtts]
            plt.plot(inv_rtt, ideal, linestyle='--', color=color, alpha=0.5)
        plt.xlabel('1/RTT_min')
        plt.ylabel('Throughput (packets/tick)')
        plt.title(f'Sliding-Window throughput vs 1/RTT_min (loss={loss*100:.0f}%)')
        plt.legend()
        plt.grid(True)
        safe_loss = str(loss).replace('.', 'p')
        outname = f'{out_prefix}_loss{safe_loss}.png'
        plt.savefig(outname)
        print('Saved', outname)


if __name__ == '__main__':
    rtts = [5, 10, 20, 50, 100]
    window_sizes = [1, 2, 4, 8, 16]
    ticks = 1000
    results = experiment(rtts, window_sizes, ticks=ticks, seed=1)
    plot_results(rtts, window_sizes, results, ticks)
