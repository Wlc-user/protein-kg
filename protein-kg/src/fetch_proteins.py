import sys
sys.path.insert(0, 'src')
from data_loader import ProteinDataLoader
import requests

loader = ProteinDataLoader()

keywords = ['tumor', 'kinase', 'oncogene', 'apoptosis', 'DNA repair']
all_ids = set()

for kw in keywords:
    url = f'{loader.BASE_URL}/search?query=({kw})+AND+(reviewed:true)&size=10'
    r = requests.get(url, headers={'Accept': 'application/json'})
    if r.status_code == 200:
        results = r.json().get('results', [])
        for p in results:
            pid = p['primaryAccession']
            all_ids.add(pid)
        print(f'{kw}: {len(results)} 条')

print(f'\n总计: {len(all_ids)} 个蛋白质')

for pid in list(all_ids)[:5]:
    data = loader.fetch_protein(pid)
    if data:
        print(f'  {pid}: {data["name"][:50]} ({data["length"]}aa)')