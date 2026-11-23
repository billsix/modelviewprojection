;; -*- no-byte-compile: t; lexical-binding: nil -*-
(define-package "magit" "20261117.1103"
  "A Git porcelain inside Emacs."
  '((emacs         "28.1")
    (compat        "31.1")
    (cond-let      "1.1")
    (llama         "1.0")
    (magit-section "4.7")
    (seq           "2.24")
    (transient     "0.13")
    (with-editor   "3.6"))
  :url "https://github.com/magit/magit"
  :commit "5e21bac5304c931cccbe16073758e2c464e40298"
  :revdesc "5e21bac5304c"
  :keywords '("git" "tools" "vc")
  :authors '(("Marius Vollmer" . "marius.vollmer@gmail.com")
             ("Jonas Bernoulli" . "emacs.magit@jonas.bernoulli.dev"))
  :maintainers '(("Jonas Bernoulli" . "emacs.magit@jonas.bernoulli.dev")
                 ("Kyle Meyer" . "kyle@kyleam.com")))
