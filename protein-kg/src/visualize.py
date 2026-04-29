import pickle, numpy as np, matplotlib.pyplot as plt

plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

with open('data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)

lengths = [p['length'] for p in cleaned]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# 图1：序列长度分布
axes[0].hist(lengths, bins=80, color='#3498db', alpha=0.8, edgecolor='white', linewidth=0.5)
axes[0].axvline(np.mean(lengths), color='red', linewidth=2, linestyle='--', 
                label=f'Mean: {np.mean(lengths):.0f} aa')
axes[0].axvline(np.median(lengths), color='green', linewidth=2, linestyle='--', 
                label=f'Median: {np.median(lengths):.0f} aa')
axes[0].set_xlabel('Sequence Length (aa)')
axes[0].set_ylabel('Number of Proteins')
axes[0].set_title(f'Human Proteome Length Distribution\n(n={len(cleaned)})')
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# 图2：QPS Benchmark（大号数字）
modes = ['Serial', 'x4 Threads', 'x8 Threads', 'x16 Threads']
qps = [56914, 19499, 18365, 9250]
colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
bars = axes[1].bar(modes, qps, color=colors, alpha=0.9, edgecolor='white', linewidth=1)
axes[1].set_ylabel('Queries Per Second (QPS)')
axes[1].set_title('Faiss IVF Retrieval Benchmark\n(10,000 proteins, 128-dim vectors)')
for bar, v in zip(bars, qps):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1500, 
                 f'{v:,}', ha='center', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

# 图3：检索延迟分布
lats_p50 = 0.1
lats_p99 = 1.1
x = ['P50 (Median)', 'P99 (99th %)']
y = [lats_p50, lats_p99]
bars = axes[2].bar(x, y, color=['#3498db', '#e74c3c'], alpha=0.9, 
                   edgecolor='white', linewidth=1, width=0.4)
axes[2].set_ylabel('Latency (ms)')
axes[2].set_title('Retrieval Latency Distribution\n(2,000 queries)')
for bar, v in zip(bars, y):
    axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                 f'{v} ms', ha='center', fontsize=14, fontweight='bold')
axes[2].set_ylim(0, max(y) * 1.5)
axes[2].grid(True, alpha=0.3, axis='y')

plt.tight_layout(pad=3.0)
plt.savefig('reports/protein_platform_overview.png', dpi=200, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print('Done: reports/protein_platform_overview.png')
plt.close()