import json, time, sys, os
import requests
from tqdm import tqdm

def extract_ids(fasta_path):
    ids = []
    with open(fasta_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('>'):
                parts = line.split('|')
                if len(parts) >= 2:
                    ids.append(parts[1])
    return ids

def fetch_by_search(ids, output_json):
    results = {}
    batch_size = 100
    total = len(ids)
    
    for i in tqdm(range(0, total, batch_size), desc='通过 search API 获取'):
        batch = ids[i:i+batch_size]
        query_parts = [f'accession:{acc}' for acc in batch]
        query = ' OR '.join(query_parts)
        
        url = 'https://rest.uniprot.org/uniprotkb/search'
        params = {
            'query': query,
            'fields': 'accession,comment(FUNCTION)',
            'format': 'json',
            'size': batch_size
        }
        
        success = False
        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, headers={'Accept': 'application/json'})
                resp.raise_for_status()
                data = resp.json()
                for entry in data.get('results', []):
                    acc = entry.get('primaryAccession')
                    func_text = 'Function not annotated.'
                    for comment in entry.get('comments', []):
                        if comment.get('commentType') == 'FUNCTION':
                            func_text = ' '.join([t.get('value','') for t in comment.get('texts',[])])
                            break
                    results[acc] = func_text
                success = True
                break
            except Exception as e:
                print(f'\n⚠️ 批次 {i//batch_size + 1} 尝试 {attempt+1} 失败: {e}')
                time.sleep(2 ** attempt)
        if not success:
            print(f'❌ 批次 {i//batch_size + 1} 彻底失败，填充默认值')
            for acc in batch:
                results[acc] = 'Function not annotated.'
        time.sleep(0.5)

    proteins = [{'id': aid, 'name': aid, 'function': func} for aid, func in results.items()]
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(proteins, f, ensure_ascii=False, indent=2)
    print(f'✅ 成功获取 {len(proteins)} 个蛋白质的功能信息，已保存到 {output_json}')

if __name__ == '__main__':
    fasta_path = sys.argv[1] if len(sys.argv) > 1 else 'data/human_proteome_uncompressed.fasta'
    output_path = 'data/all_proteins.json'
    print('🔍 提取 ID...')
    ids = extract_ids(fasta_path)
    print(f'   共 {len(ids)} 个 ID')
    fetch_by_search(ids, output_path)
