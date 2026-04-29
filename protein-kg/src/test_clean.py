from local_loader import LocalProteinLoader
from data_cleaner import ProteinDataCleaner

loader = LocalProteinLoader('../data/human_proteome_uncompressed.fasta')
raw = loader.parse_fasta()
print('原始: ' + str(len(raw)) + ' 条')

if len(raw) > 0:
    cleaner = ProteinDataCleaner()
    cleaned = cleaner.clean_batch(raw, 'UniProt')
    print('清洗后: ' + str(len(cleaned)) + ' 条')
    
    for p in cleaned[:3]:
        pid = p.get('uniprot_id', '?')
        name = p.get('name', '')[:60]
        length = p.get('length', 0)
        tier = p.get('structure_tier', '?')
        print('  ' + pid + ': ' + name + ' | ' + str(length) + 'aa | tier=' + str(tier))