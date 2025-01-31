# Makefile for generating lecture presentations

# Directories
LECTURES_DIR = lectures
REVEAL_DIR = output/reveal
BEAMER_DIR = output/beamer
TEMPLATES_DIR = templates

# Pandoc settings
# -V revealjs-url=https://unpkg.com/reveal.js@4.5.0
PANDOC = pandoc
PANDOC_COMMON_OPTS = --standalone --slide-level 2
REVEAL_OPTS = -t revealjs
# -V colortheme=nord \
 
BEAMER_OPTS = -t beamer \
              -V aspectratio=169 \
							-V theme=metropolis \
							-V colortheme=owl \
              --pdf-engine=xelatex

# Find all markdown lecture files
LECTURE_MDS = $(wildcard $(LECTURES_DIR)/*.md)
REVEAL_HTMLS = $(patsubst $(LECTURES_DIR)/%.md,$(REVEAL_DIR)/%.html,$(LECTURE_MDS))
BEAMER_PDFS = $(patsubst $(LECTURES_DIR)/%.md,$(BEAMER_DIR)/%.pdf,$(LECTURE_MDS))

# Default target
all: reveal beamer

# Create output directories
$(REVEAL_DIR) $(BEAMER_DIR):
	mkdir -p $@

# Generate Reveal.js presentations
reveal: $(REVEAL_DIR) $(REVEAL_HTMLS)

$(REVEAL_DIR)/%.html: $(LECTURES_DIR)/%.md
	$(PANDOC) $(PANDOC_COMMON_OPTS) $(REVEAL_OPTS) $< -o $@

# Generate Beamer PDFs
beamer: $(BEAMER_DIR) $(BEAMER_PDFS)

$(BEAMER_DIR)/%.pdf: $(LECTURES_DIR)/%.md
	$(PANDOC) $(PANDOC_COMMON_OPTS) $(BEAMER_OPTS) $< -o $@

# Clean up generated files
clean:
	rm -rf $(REVEAL_DIR) $(BEAMER_DIR)

.PHONY: all reveal beamer clean
