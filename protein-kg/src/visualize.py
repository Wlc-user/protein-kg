"""出图：数据分布 + 检索效果"""
import pickle, numpy as np, matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 1. 加载数据
with open('../data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)

lengths = [p['length'] for p in cleaned]

# 2. 序列长度分布
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

axes[0].hist(lengths, bins=50, color='#3498db', alpha=0.7)
axes[0].axvline(np.mean(lengths), color='red', linestyle='--', label=f'均值 {np.mean(lengths):.0f}aa')
axes[0].set_xlabel('序列长度 (aa)')
axes[0].set_ylabel('蛋白质数量')
axes[0].set_title(f'人类蛋白质组长度分布 (n={len(cleaned)})')
axes[0].legend()

# 3. 结构等级分布
tiers = {'实验证据': 0, '转录本证据': 0, '同源性': 0, '仅预测': 0, '不确定': 0}
for p in cleaned:
    t = p.get('structure_tier', 4)
    if t == 1: tiers['实验证据'] += 1
    elif t == 2: tiers['转录本证据'] += 1
    elif t == 3: tiers['同源性'] += 1
    elif t == 4: tiers['仅预测'] += 1
    else: tiers['不确定'] += 1

axes[1].pie(tiers.values(), labels=tiers.keys(), autopct='%1.1f%%', 
            colors=['#2ecc71','#3498db','#f39c12','#e74c3c','#95a5a6'])
axes[1].set_title('结构证据等级分布')

# 4. QPS（嵌入你的实测数据）
modes = ['串行', '并发4', '并发8', '并发16']
qps = [56914, 19499, 18365, 9250]
axes[2].bar(modes, qps, color=['#2ecc71','#3498db','#f39c12','#e74c3c'])
axes[2].set_ylabel('QPS')
axes[2].set_title('Faiss 检索压测')
for i, v in enumerate(qps):
    axes[2].text(i, v+1000, str(v), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('../reports/protein_platform_overview.png', dpi=150)
print('图片已保存到 reports/protein_platform_overview.png')
plt.close()