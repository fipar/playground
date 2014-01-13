(ns clj-sample.core
  (:gen-class)
  (:require [clj-http.client :as client])
  (:require [clojure.tools.cli :refer [parse-opts]]))


;; Programming clojure in the ignorant style

(def cli-args
     ["-u" "--url URL" "The URL you want to process"])

(defn -main
  "I don't do a whole lot ... yet."
  [& args]
  ;; work around dangerous default behaviour in Clojure
  (alter-var-root #'*read-eval* (constantly false))
  (let [options (parse-opts args cli-args)]
    (println (client/get (:url options)))))

