(require 'package)
(add-to-list 'package-archives '("melpa" . "https://melpa.org/packages/") t)
(package-initialize)

(setq package-selected-packages
      '(lsp-mode
        yasnippet
        lsp-treemacs
        helm-lsp
        projectile
        hydra
        flycheck
        company
        avy
        which-key
        helm-xref
        dape
        dap-mode
        blacken

        elpy

        material-theme
        dracula-theme
        monokai-theme
        zenburn-theme

        fold-this
        yafolding

        org-modern

        discover
        yafolding
        fold-this
        better-defaults
        magit
        markdown-mode
        markdown-preview-mode
        ))

(when (cl-find-if-not #'package-installed-p package-selected-packages)
  (package-refresh-contents)
  (mapc #'package-install package-selected-packages))
