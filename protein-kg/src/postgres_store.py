"""
PostgreSQL 存储：蛋白质元数据表
"""
import psycopg2
from typing import List, Dict

class PostgresProteinStore:
    """将清洗后的蛋白质数据存入 PostgreSQL"""
    
    def __init__(self, dbname="protein_kg", user="postgres", password="postgres"):
        self.conn = psycopg2.connect(
            host="localhost",
            dbname=dbname,
            user=user,
            password=password
        )
        self._init_tables()
    
    def _init_tables(self):
        """建表"""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS proteins (
                    uniprot_id VARCHAR(20) PRIMARY KEY,
                    name TEXT NOT NULL,
                    gene VARCHAR(50),
                    organism VARCHAR(200),
                    sequence TEXT NOT NULL,
                    length INTEGER,
                    source VARCHAR(50),
                    source_id VARCHAR(50),
                    hash VARCHAR(12),
                    function_text TEXT,
                    imported_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_proteins_hash ON proteins(hash);
                CREATE INDEX IF NOT EXISTS idx_proteins_gene ON proteins(gene);
                CREATE INDEX IF NOT EXISTS idx_proteins_length ON proteins(length);
            """)
            self.conn.commit()
        print("✅ PostgreSQL 表已就绪")
    
    def insert_protein(self, protein: Dict):
        """插入单个蛋白质"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO proteins (uniprot_id, name, gene, organism, sequence, length, source, source_id, hash, function_text)
                VALUES (%(uniprot_id)s, %(name)s, %(gene)s, %(organism)s, %(sequence)s, %(length)s, %(source)s, %(source_id)s, %(hash)s, %(function_text)s)
                ON CONFLICT (uniprot_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    sequence = EXCLUDED.sequence,
                    length = EXCLUDED.length,
                    imported_at = NOW()
            """, protein)
        self.conn.commit()
    
    def insert_batch(self, proteins: List[Dict]):
        """批量插入"""
        for i, p in enumerate(proteins):
            self.insert_protein(p)
            if (i + 1) % 50 == 0:
                print(f"  已插入 {i+1}/{len(proteins)}")
        self.conn.commit()
        print(f"✅ 批量插入完成: {len(proteins)} 条")
    
    def query_by_gene(self, gene: str) -> List[Dict]:
        """按基因名查询"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT uniprot_id, name, length, organism FROM proteins WHERE gene = %s", (gene,))
            return [dict(zip(['id','name','length','organism'], row)) for row in cur.fetchall()]
    
    def query_by_length_range(self, min_len: int, max_len: int) -> List[Dict]:
        """按序列长度范围查询"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT uniprot_id, name, length FROM proteins WHERE length BETWEEN %s AND %s ORDER BY length", (min_len, max_len))
            return [dict(zip(['id','name','length'], row)) for row in cur.fetchall()]
    
    def get_stats(self) -> Dict:
        """获取数据库统计"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), AVG(length), MAX(length) FROM proteins")
            count, avg_len, max_len = cur.fetchone()
            cur.execute("SELECT source, COUNT(*) FROM proteins GROUP BY source")
            sources = dict(cur.fetchall())
        return {
            "total_proteins": count,
            "avg_length": round(avg_len, 1) if avg_len else 0,
            "max_length": max_len or 0,
            "by_source": sources
        }
    
    def close(self):
        self.conn.close()