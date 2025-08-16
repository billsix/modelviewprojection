(package-initialize)

(load-file "~/.emacs.d/helm.el")
(load-file "~/.emacs.d/preferences.el")

;; theme
(load-theme 'modus-vivendi t)
(global-auto-revert-mode)
(setq auto-revert-avoid-polling t)

;; Disable eglot hooks for python-mode
(remove-hook 'python-mode-hook 'eglot-ensure)

(required 'dap-mode)
(required 'dap-python)
(dap-mode)

(use-package lsp-mode
  :init
  ;; set prefix for lsp-command-keymap (expected by lsp-ui)
  (setq lsp-keymap-prefix "C-c l")
  :hook ((python-mode . (lambda ()
                          (require 'lsp-mode)
                          (lsp-deferred)))
         (lsp-mode . yas-minor-mode))
  :config
  (setq lsp-pylsp-server-command "pylsp")
  )
