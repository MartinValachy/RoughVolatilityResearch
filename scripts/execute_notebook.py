from pathlib import Path
import nbformat,sys,json,datetime,hashlib
from nbclient import NotebookClient
R=Path(__file__).resolve().parents[1]
nb=nbformat.read(R/'notebooks/formula_audit.ipynb',as_version=4)
# Explicit kernel command prevents picking a global Python installation.
from jupyter_client.manager import KernelManager
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
client=NotebookClient(nb,timeout=180,resources={'metadata':{'path':str(R)}},km=km)
client.execute();nbformat.write(nb,R/'notebooks/formula_audit.ipynb')
runid=datetime.datetime.now(datetime.timezone.utc).strftime('formulas_%Y%m%dT%H%M%SZ')
run=R/'runs'/runid;run.mkdir()
meta={'run_id':runid,'status':'completed','python_executable':sys.executable,'python_version':sys.version,'code_cells_executed':sum(c.cell_type=='code' for c in nb.cells),'notebook_sha256':hashlib.sha256((R/'notebooks/formula_audit.ipynb').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(run/'metadata.json').write_text(json.dumps(meta,indent=2));(R/'results/latest_formulas.json').write_text(json.dumps(meta,indent=2))
print('Executed',sum(c.cell_type=='code' for c in nb.cells),'code cells using',sys.executable)
