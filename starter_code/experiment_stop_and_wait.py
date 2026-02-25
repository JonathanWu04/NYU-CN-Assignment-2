#!/usr/bin/env python3
import subprocess
import re
import matplotlib.pyplot as plt
import sys


def run_sim(rtt, ticks, seed=1, loss_ratio=0.0):
	cmd = [
		sys.executable,
		'starter_code/run_reliability_simulation.py',
		'--seed', str(seed),
		'--rtt-min', str(rtt),
		'--ticks', str(ticks),
	]
	if loss_ratio is not None and loss_ratio > 0.0:
		cmd += ['--loss-ratio', str(loss_ratio)]
	cmd += ['stop-and-wait']
	print('Running:', ' '.join(cmd))
	proc = subprocess.run(cmd, capture_output=True, text=True)
	out = proc.stdout + proc.stderr
	m = re.search(r"Maximum in order received sequence number\s*(\d+)", out)
	if not m:
		raise RuntimeError(f"Failed to parse simulator output for rtt={rtt} loss={loss_ratio}\nOutput:\n{out}")
	return int(m.group(1))


def experiment(rtts, ticks=1000, seed=1):
	loss_settings = [0.0, 0.01, 0.02, 0.05, 0.1]
	results = {loss: [] for loss in loss_settings}
	for loss in loss_settings:
		for r in rtts:
			max_in_order = run_sim(r, ticks, seed=seed, loss_ratio=loss)
			results[loss].append(max_in_order)
	return results


def plot_results(rtts, results, ticks, outname='stop_and_wait_throughput.png'):
	inv_rtt = [1.0 / r for r in rtts]
	plt.figure()
	for loss, data in results.items():
		throughput = [(m + 1) / ticks for m in data]
		label = f"sim loss={loss*100:.0f}%"
		plt.plot(inv_rtt, throughput, marker='o', label=label)
	ideal = [1.0 / r for r in rtts]
	plt.plot(inv_rtt, ideal, '--', label='ideal 1/RTT')
	plt.xlabel('1/RTT_min')
	plt.ylabel('Throughput (packets/tick)')
	plt.title(f'Stop-and-Wait throughput vs 1/RTT_min (ticks={ticks})')
	plt.legend()
	plt.grid(True)
	plt.savefig(outname)
	print('Saved', outname)


if __name__ == '__main__':
	rtts = [5, 10, 20, 50, 100]
	ticks = 1000
	results = experiment(rtts, ticks=ticks, seed=1)
	plot_results(rtts, results, ticks)
