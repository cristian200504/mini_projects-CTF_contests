(def orig (table/proto-flatten (fiber/getenv (fiber/current))))
(def env (table/proto-flatten orig))
(sandbox :asm :chroot :env :ffi :fs :hrtime :modules :net :signal :subprocess :threads :unmarshal)
(each k (keys env)
  (when (or
          (find |(string/has-prefix? $ (string k))
                ["debug" "fiber" "ev/" "file" "net/" "os/"
                 "module/" "bundle/" "int/"])
          (find |(string/find $ (string k))
                ["env" "flycheck" "loader" "source" "compile"
                 "eval" "mac" "marshal" "proto" "image" "parse"
                 "dyn" "global" "doc" "peg" "with" "ffi/defbind"])
          (find |(= k $) '[resume cancel yield propagate signal
                            trace untrace *debug* stdin stdout stderr
                            getline sandbox comptime compif compwhen
                            run-context dofile repl require import import* use
                            all-bindings native asm disasm hash
                            protect try defer edefer prompt label return
                            generate coro varfn tracev cli-main slurp spit
                            quit ffi/context]))
    (put env k nil)))
(defn value [entry]
  (or (get entry :value)
      (let [ref (get entry :ref)]
        (if ref (get ref 0)))))
(each rk (sort (keys orig))
  (when (nil? (get env rk))
    (def rv (value (get orig rk)))
    (when (or (function? rv) (cfunction? rv))
      (each sk (keys env)
        (when (= rv (value (get env sk)))
          (print rk " == " sk))))))
