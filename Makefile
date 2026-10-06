.PHONY: check render update

check:
	python3 -m unittest discover -s tests -v
	@for file in Formula/*.rb; do ruby -c "$$file" || exit; done

# Rebuild formulas after editing templates. This removes existing bottle blocks;
# regenerate bottles through the PR workflow before publishing.
render:
	python3 scripts/update-formulas.py --render

# Check latest stable tags. Explicit snapshots are opt-in via scripts/update-formulas.py.
update:
	python3 scripts/update-formulas.py
