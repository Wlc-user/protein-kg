"""
处理真实的20431条蛋白质数据
"""
from src.etl_integrated import IntegratedETLPipeline
import json
import os

# 找到您的真实数据文件
# 可能是 data/processed/proteins.json 或其他位置
real_data_path = "data/your_real_proteins.json"  # 改成实际路径

if os.path.exists(real_data_path):
    print("开始处理真实数据...")
    integrated = IntegratedETLPipeline(ner_mode="simple")
    
    # 处理前1000条测试
    result = integrated.run_from_existing_data(real_data_path, limit=1000)
    
    # 导出完整图谱
    integrated.export_kg("data/kg_real_export.json")
    
    print(f"✅ 处理完成！节点数: {integrated.kg_storage.get_stats()['total_nodes']}")
else:
    print(f"未找到数据文件: {real_data_path}")
    print("请确认您的ETL输出文件位置")