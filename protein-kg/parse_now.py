import gzip, json
from tqdm import tqdm

def parse_function(gz_path, out_path):
    # 以二进制模式直接读取（不会触发 gzip 内部打开文件的权限问题）
    with open(gz_path, 'rb') as f:
        raw = f.read()
    text = gzip.decompress(raw).decode('utf-8')
    lines = text.splitlines()
    
    proteins, cur, func_lines, in_func = [], None, [], False
    for line in tqdm(lines, desc='解析'):
        if line.startswith('ID   '):
            if cur:
                cur['function'] = ' '.join(func_lines).strip() or 'Function not annotated.'
                proteins.append(cur)
            eid = line[5:].strip().split()[0]
            cur = {'id': eid, 'name': eid, 'function': ''}
            func_lines, in_func = [], False
        elif cur and line.startswith('CC   -!- FUNCTION:'):
            in_func = True
            func_lines.append(line.split('FUNCTION:')[-1].strip())
        elif cur and in_func:
            if line.startswith('CC       ') and not line.startswith('CC   -!-'):
                func_lines.append(line[9:].strip())
            else:
                in_func = False
    if cur:
        cur['function'] = ' '.join(func_lines).strip() or 'Function not annotated.'
        proteins.append(cur)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(proteins, f, ensure_ascii=False, indent=2)
    print(f'✅ 解析完成，共 {len(proteins)} 个蛋白质，保存至 {out_path}')

if __name__ == '__main__':
    parse_function('data/uniprot_sprot_human.dat.gz', 'data/all_proteins.json')
