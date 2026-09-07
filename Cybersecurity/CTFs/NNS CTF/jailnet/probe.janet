(def env (table/proto-flatten (fiber/getenv (fiber/current))))
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
(each k (sort (keys env))
  (print k " " (type (get env k))))
