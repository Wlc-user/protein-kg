import json, time, requests
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
    batch_size = 500  # 一次取500条，大幅减少请求次数
    total = len(ids)
    for i in tqdm(range(0, total, batch_size), desc='加速获取中'):
        batch = ids[i:i+batch_size]
        query = ' OR '.join([f'accession:{acc}' for acc in batch])
        url = 'https://rest.uniprot.org/uniprotkb/search'
        params = {'query': query, 'fields': 'accession,comment(FUNCTION)',
                  'format': 'json', 'size': batch_size}
        for attempt in range(2):
            try:
                resp = requests.get(url, params=params,
                                    headers={'Accept': 'application/json',
                                             'User-Agent': 'PythonProteinKG/1.0'})
                resp.raise_for_status()
                for entry in resp.json().get('results', []):
                    acc = entry['primaryAccession']
                    func = 'Function not annotated.'
                    for com in entry.get('comments', []):
                        if com.get('commentType') == 'FUNCTION':
                            func = ' '.join([t.get('value','') for t in com.get('texts',[])])
                            break
                    results[acc] = func
                break
            except Exception as e:
                print(f'\n⚠️ 批次失败: {e}')
                time.sleep(1)
        else:
            for acc in batch:
                results.setdefault(acc, 'Function not annotated.')
        time.sleep(0.2)  # 降低等待时间
    proteins = [{'id':k, 'name':k, 'function':v} for k,v in results.items()]
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(proteins, f, ensure_ascii=False, indent=2)
    print(f'✅ 完成，{len(proteins)} 个蛋白质 -> {output_json}')

if __name__ == '__main__':
    ids = extract_ids('data/human_proteome_uncompressed.fasta')
    print(f'共 {len(ids)} 个 ID，批大小 500，预计 5-8 分钟')
    fetch_by_search(ids, 'data/all_proteins.json')
