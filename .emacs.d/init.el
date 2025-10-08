(package-initialize)

(load-file "~/.emacs.d/helm.el")
(load-file "~/.emacs.d/preferences.el")

;; theme
(load-theme 'modus-vivendi t)
;(load-theme 'material t)
;(load-theme 'dracula t)
;(load-theme 'monokai t)
;(load-theme 'zenburn t)

(global-auto-revert-mode)
(setq auto-revert-avoid-polling t)

;; Disable eglot hooks for python-mode
(remove-hook 'python-mode-hook 'eglot-ensure)


(use-package lsp-mode
  :hook ((python-mode . lsp-deferred))
  :commands (lsp lsp-deferred)
  :init
  (setq lsp-keymap-prefix "C-c l"))

(use-package lsp-pyright
  :after lsp-mode
  :hook (python-mode . (lambda ()
                         (require 'lsp-pyright)
                         (lsp-deferred)))  ; or just (lsp)
  :config
  ;; Optional: configure Pyright
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
