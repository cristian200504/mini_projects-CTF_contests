-module(purgatory_runner).
-export([main/1]).

main(Args) ->
    try run(Args)
    catch
        error:terminated -> halt(0)
    end.

run([OldPath, NewPath]) ->
    load(OldPath),
    Worker = purgatory:boot(),
    load(NewPath),
    io:put_chars("purgatory validator\n"),
    prompt(Worker);
run(_) ->
    done("usage: purgatory_runner old.beam new.beam", 2).

prompt(Worker) ->
    io:put_chars("passphrase> "),
    case io:get_line("") of
        eof -> halt(0);
        Line ->
            Worker ! {check, self(), unicode:characters_to_binary(string:trim(Line))},
            receive
                {verdict, true} -> done(os:getenv("FLAG"), 0);
                {verdict, false} -> io:put_chars("denied\n"), prompt(Worker)
            end
    end.

load(Path) ->
    {ok, Bin} = file:read_file(Path),
    {module, purgatory} = code:load_binary(purgatory, Path, Bin).

done(Text, Status) -> io:format("~s~n", [Text]), halt(Status).
