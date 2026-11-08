(package-initialize)
;; Byte-compile each vendored package that has no .elc yet, through package.el's own
;; compile (package-recompile), the same path package-install uses. The .elc land in
;; the bind-mounted elpa/ and persist, so later starts find them and compile nothing;
;; a package whose files cannot all compile (compat's compat-2x.el backports on a
;; newer Emacs) still gets its other .elc and is not retried on every start.
(dolist (entry package-alist)
  (let ((desc (cadr entry)))
    (unless (directory-files-recursively (package-desc-dir desc) "\\.elc\\'")
      (with-demoted-errors "Error while compiling: %S"
        (package-recompile desc)))))

(load-file "~/.emacs.d/helm.el")
(load-file "~/.emacs.d/preferences.el")

;; theme
;(load-theme 'modus-vivendi t)
;(load-theme 'material t)
(load-theme 'dracula t)
;(load-theme 'monokai t)
;(load-theme 'zenburn t)

(global-auto-revert-mode)
(setq auto-revert-avoid-polling t)

;; Disable eglot hooks for python-mode
(remove-hook 'python-mode-hook 'eglot-ensure)

(use-package yafolding
  :ensure t
  :hook (prog-mode . yafolding-mode))


(use-package lsp-mode
  :hook ((python-mode . lsp-deferred))
  :commands (lsp lsp-deferred)
  :init
  (setq lsp-keymap-prefix "C-c l"))

;; Editor language server: pyright, via lsp-pyright. pyright-langserver is
;; npm-installed by entrypoint/04-install-emacs.sh. The format.sh and
;; type-check gates run ty; pyright serves the editor only (completion, hover,
;; signature help, and its own in-editor diagnostics, which can differ from ty's).
(use-package lsp-pyright
  :after lsp-mode
  :hook (python-mode . (lambda ()
                         (require 'lsp-pyright)
                         (lsp-deferred)))
  :config
  (setq lsp-pyright-typechecking-mode "basic"
        lsp-pyright-auto-import-completions t))

;; set the LSP root for this project
(require 'lsp-mode)

(setq lsp-auto-guess-root nil)

(defun my-lsp-root (&rest _)
  "/mvp/")

(advice-add 'lsp--calculate-root :override #'my-lsp-root)

(add-hook 'prog-mode-hook #'lsp-deferred)

;; Make sure dap-mode never loads
(setq lsp-enable-dap-auto-configure nil)

(with-eval-after-load 'lsp-mode
    (setq lsp-enable-dap-auto-configure nil))

;; Enable hideshow (hs-minor-mode) in all programming modes so code regions
;; (functions, blocks) can be folded/collapsed.  Toggle a block with
;; `C-c @ C-c`; hide-all / show-all with `C-c @ C-M-h` / `C-c @ C-M-s`.
(add-hook 'prog-mode-hook #'hs-minor-mode)
