"""Source intake; no imputation of missing core par tenors."""
import csv,hashlib,json
from datetime import datetime
from pathlib import Path
import numpy as np
FIELDS=['6 Mo','1 Yr','2 Yr','3 Yr','5 Yr','7 Yr','10 Yr','20 Yr','30 Yr']
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_history(root):
    rows=[];receipts=[]
    for year in [2024,2025]:
        path=Path(root)/'data/raw'/f'treasury_par_{year}.csv'
        with path.open(newline='') as f:
            reader=csv.DictReader(f)
            for row in reader:
                d=datetime.strptime(row['Date'],'%m/%d/%Y').date()
                if d.year!=year:raise ValueError('Source year mismatch')
                try:y=[float(row[k])/100 for k in FIELDS]
                except (KeyError,ValueError):raise ValueError(f'Missing required tenor on {d}')
                if not np.all(np.isfinite(y)):raise ValueError('Nonfinite source rate')
                rows.append(dict(date=d.isoformat(),par=y))
        receipts.append(dict(path=str(path.relative_to(root)),sha256=digest(path),year=year,source=f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={year}'))
    rows.sort(key=lambda r:r['date'])
    if len({r['date'] for r in rows})!=len(rows):raise ValueError('Duplicate date')
    return rows,receipts
