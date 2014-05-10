(ns clj-sample.core
  (:gen-class)
  (:require [clj-http.client :as client])
  (:require [clojure.tools.cli :refer [parse-opts]])
  (:import (java.text NumberFormat) (javax.swing JFrame JLabel)))


;; Programming clojure in the ignorant style

(def cli-args
     ["-u" "--url URL" "The URL you want to process"])

(defn -main
  "I don't do a whole lot ... yet."
  [& args]
  ;; work around dangerous default behaviour in Clojure
  (alter-var-root #'*read-eval* (constantly false))
  (doto (JFrame. "Test")
    ; (.add (JLabel. (.toString (client/get "http://fernandoipar.com"))))
    (.add (JLabel. "Just a test"))
    (.pack)
    (.setDefaultCloseOperation JFrame/EXIT_ON_CLOSE)
    (.setVisible true)))


