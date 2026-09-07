(if (= "--worker" (get (dyn :args) 1))
  (do
    ((fn []
      (def env (table/proto-flatten (fiber/getenv (fiber/current))))
      
      # ban all the things
      (sandbox
        :asm :chroot :env :ffi :fs :hrtime :modules
        :net :signal :subprocess :threads :unmarshal)
      
      # ban all the things
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

      # ban all the things
      (defn forbidden-form? [x]
        (case (type x)
          :keyword (= x :macro)
          :core/u64 true
          :core/s64 true
          :tuple (some forbidden-form? x)
          :array (some forbidden-form? x)
          :struct (some forbidden-form? (pairs x))
          :table (some forbidden-form? (pairs x))
          false))

      (prin "sandbox> ")
      (flush)

      (def parser (parser/new))
      (var form nil)
      (var size 0)
      (while (nil? form)
        (def chunk (file/read stdin 4096))
        (unless chunk (error "unexpected end of input"))
        (+= size (length chunk))
        (when (> size 0x20000) (error "request too large"))
        (parser/consume parser chunk)
        (when (= :error (parser/status parser))
          (error (parser/error parser)))
        (when (parser/has-more parser)
          (set form (parser/produce parser))))

      (when (forbidden-form? form)
        (error "forbidden form"))

      (def thunk (compile form env "submission"))
      (unless (= :function (type thunk))
        (error (get thunk :error "compile error")))

      (sandbox :all)
      (def fiber (fiber/new thunk :t env))
      (def result (resume fiber))
      (if (= :dead (fiber/status fiber))
        result
        (propagate result fiber))))
    (os/exit 0)))

((fn []
  (defn pump [src dst]
    (try
      (forever
        (def chunk (ev/read src 4096))
        (if (nil? chunk) (break))
        (ev/write dst chunk))
      ([err] nil)))

  (defn serve [stream]
    (defer (net/close stream)
      (def worker
        (os/spawn ["/usr/local/bin/janet" "server.janet" "--worker"] :p {:in :pipe :out :pipe :err :pipe}))
      (ev/spawn (pump stream (worker :in)) (ev/close (worker :in)))
      (ev/spawn (pump (worker :out) stream))
      (ev/spawn (pump (worker :err) stream))
      (:wait worker)))

  (def listener (net/listen "0.0.0.0" 1337))
  (print "Janet service listening on 0.0.0.0:1337")
  (forever (serve (net/accept listener)))))
