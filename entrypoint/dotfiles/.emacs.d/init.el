(package-initialize)
(byte-recompile-directory package-user-dir 0)

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

;; Type checker: ty (Astral) -- mvp's single checker, matching the format.sh
;; gate. ty ships an LSP via `ty server`; register it as a custom lsp-mode client
;; (needs no MELPA package). The lsp-mode block above already hooks
;; python-mode -> lsp-deferred, so this client starts on open.
;; (This lsp-mode version also ships a built-in `lsp-python-ty' client; the custom
;; stanza below is the verified-working one and is kept for that reason.)
(with-eval-after-load 'lsp-mode
  (lsp-register-client
   (make-lsp-client
    :new-connection (lsp-stdio-connection '("ty" "server"))
    :activation-fn (lsp-activate-on "python")
    :server-id 'ty
    :priority 1)))

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
