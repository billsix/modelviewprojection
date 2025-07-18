(package-initialize)

(load-file "~/.emacs.d/helm.el")
(load-file "~/.emacs.d/preferences.el")

;; theme
(load-theme 'modus-vivendi t)
(global-auto-revert-mode)
(setq auto-revert-avoid-polling t)
