import os, gzip
from typing import Dict, List

class LocalProteinLoader:
    def __init__(self, fasta_path="data/human_proteome_uncompressed.fasta"):
        self.fasta_path = fasta_path
    
    def parse_fasta(self) -> List[Dict]:
        # 如果是 .gz 文件，先解压
        actual_path = self.fasta_path
        if self.fasta_path.endswith('.gz') or not os.path.exists(self.fasta_path):
            uncompressed = self.fasta_path.replace('.gz', '_uncompressed.fasta')
            if os.path.exists(uncompressed):
                actual_path = uncompressed
        
        if not os.path.exists(actual_path):
            print(f"文件不存在: {actual_path}")
            return []
        
        proteins = []
        current_id, current_name, current_seq = "", "", []
        
        with open(actual_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_id:
                        proteins.append({
                            "id": current_id,
                            "name": current_name,
                            "sequence": "".join(current_seq),
                            "length": len("".join(current_seq))
                        })
                    # UniProt 格式: >sp|P04637|P53_HUMAN ...
                    parts = line[1:].split('|')
                    if len(parts) >= 3:
                        current_id = parts[1]
                        current_name = parts[2].split(' OS=')[0] if ' OS=' in parts[2] else parts[2]
                    else:
                        current_id = line[1:].split()[0] if line[1:] else "unknown"
                        current_name = line[1:].strip()
                    current_seq = []
                else:
                    current_seq.append(line)
        
        if current_id:
            proteins.append({
                "id": current_id,
                "name": current_name,
                "sequence": "".join(current_seq),
                "length": len("".join(current_seq))
            })
        
        print(f"✅ 加载 {len(proteins)} 条蛋白质序列")
        return proteins