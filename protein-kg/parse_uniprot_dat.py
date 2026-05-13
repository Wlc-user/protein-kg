import gzip
import json
from tqdm import tqdm

def parse_function(dat_gz_path, output_json):
    # 直接读取二进制内容，完全在内存中解压，避免文件句柄权限问题
    with open(dat_gz_path, 'rb') as f:
        compressed = f.read()
    print("文件读取成功，正在解压...")
    text = gzip.decompress(compressed).decode('utf-8')
    lines = text.splitlines()
    print(f"解压完成，共 {len(lines)} 行")

    proteins = []
    current = None
    in_function = False
    func_lines = []

    for line in tqdm(lines, desc="解析条目"):
        if line.startswith("ID   "):
            # 保存上一个条目
            if current:
                if func_lines:
                    current["function"] = " ".join(func_lines).strip()
                else:
                    current["function"] = "Function not annotated."
                proteins.append(current)
            # 开始新条目
            entry_id = line[5:].strip().split()[0]
            current = {"id": entry_id, "name": entry_id, "function": ""}
            func_lines = []
            in_function = False
        elif current and line.startswith("CC   -!- FUNCTION:"):
            in_function = True
            text_part = line.split("FUNCTION:")[-1].strip()
            func_lines.append(text_part)
        elif current and in_function:
            if line.startswith("CC       ") and not line.startswith("CC   -!-"):
                func_lines.append(line[9:].strip())
            else:
                in_function = False

    # 处理最后一个条目
    if current:
        if func_lines:
            current["function"] = " ".join(func_lines).strip()
        else:
            current["function"] = "Function not annotated."
        proteins.append(current)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(proteins, f, ensure_ascii=False, indent=2)
    print(f"✅ 解析完成，共 {len(proteins)} 个蛋白质，保存至 {output_json}")

if __name__ == "__main__":
    parse_function("data/uniprot_sprot_human.dat.gz", "data/all_proteins.json")