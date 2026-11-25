import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import sharp from 'sharp';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),dir=path.join(root,'artifacts/release/figures');
for(const f of await fs.readdir(dir))if(f.endsWith('.svg'))await sharp(path.join(dir,f),{density:180}).png().toFile(path.join(dir,f.replace('.svg','.png')));
console.log('Rendered notebook figures as embedded PNG');
