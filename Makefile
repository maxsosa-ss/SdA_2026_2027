PYTHON = .SdA/Scripts/python.exe

.PHONY: help sync-complete sync-u6m

help:
	@echo "Targets disponibles:"
	@echo "  sync-complete   Extrae y carga el historico completo de ambulatorio"
	@echo "  sync-u6m        Extrae y carga los ultimos 6 meses de ambulatorio"

sync-complete:
	$(PYTHON) -c "\
from src.extract.ambulatorio import extract_complete; \
from src.load.ambulatorio import load_complete; \
load_complete(extract_complete())"

sync-u6m:
	$(PYTHON) -c "\
from src.extract.ambulatorio import extract_u6m; \
from src.load.ambulatorio import load_u6m; \
load_u6m(extract_u6m())"
