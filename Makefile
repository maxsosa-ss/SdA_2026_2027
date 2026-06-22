PYTHON = PYTHONPATH=. .SdA/Scripts/python.exe

.PHONY: help sync-complete sync-u6m run-ambulatorio

help:
	@echo "Targets disponibles:"
	@echo "  sync-complete     Extrae y stagea el historico completo de ambulatorio"
	@echo "  sync-u6m          Extrae y stagea los ultimos 6 meses de ambulatorio"
	@echo "  run-ambulatorio   Transforma y carga resultados de ambulatorio a GSheets"

sync-complete:
	$(PYTHON) -c "\
from src.extract.ambulatorio import extract_complete; \
from src.stage.ambulatorio import stage_complete; \
stage_complete(extract_complete())"

sync-u6m:
	$(PYTHON) -c "\
from src.extract.ambulatorio import extract_u6m; \
from src.stage.ambulatorio import stage_u6m; \
stage_u6m(extract_u6m())"

run-ambulatorio:
	$(PYTHON) src/pipelines/ambulatorio.py
