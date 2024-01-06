#######################################################################
 I used Rust as a non-obvious data exploration tool and it was great
#######################################################################

:date:
   2021-10-01 18:00

:tags:
   rust, lune, programming

..

   This post was originally published on `Lune Blog
   <https://lune.co/post/i-used-rust-as-a-non-obvious-data-exploration-tool-and-it-was-great>`_.

   `Lune <https://lune.co>`_, where I help fighting the climate crisis, kindly allowed
   me to republish it here.

**************
 How it began
**************

I was presented with a task recently: ingest a spreadsheet coming from a
potential customer and make some carbon emission estimations based on its contents.

What may seem like not a particularly interesting undertaking become
something a tad more exciting, and that's for three reasons:

#. The exact meaning of the columns, relationships between them, the
   data ranges etc. all had to be figured out as they weren't
   immediately obvious (and there were *a lot* of columns)

#. The calculations required interacting with several underspecified,
   undocumented and third-party databases/datasets. The databases
   contained plenty of incorrect (or incorrectly formatted) data, just
   to spice things up.

#. I decided to use Rust for the assignment, which turned it into a bit
   of a fun experiment.

What follows is a description of some issues encountered when dealing
with external data and why Rust turned out to be an appropriate tool for
the job.

(Note: despite Rust being somewhat overrepresented in my writing, Lune's
codebase is still by a large margin mostly TypeScript, with Rust
used in a few strategic places. I *would* like to see more Rust at Lune,
but I don't want to give a false impression regarding the status quo.)

****************************
 The external data troubles
****************************

The data came to me as `Comma-Separated Values (CSV)
<https://en.wikipedia.org/wiki/Comma-separated_values>`_ files. While
`CSV has many flaws
<https://www.bitsondisk.com/writing/2021/retire-the-csv/>`_ this is
neither the time nor place to reiterate those – fortunately none of them
presented themselves in this situation (despite its weaknesses, I
still find CSV superior to almost any other data exchange format that's
out there in terms of accessibility and interoperability).

After loading up the CSVs I had to make sense of them. That involved
going through 30+ columns of data and figuring out:

-  What are their types (some values, like telephone numbers, should be
   treated as text even if they contain only digits)?
-  Is a particular column even relevant to us?
-  If we do – is that column required to be set?
-  What's the data range (or the set of possible values, if you will)?
-  And finally, the most tricky and complex one: what's the relationship
   between the columns?

Remember: the data was undocumented. Figuring out all of the above
required me to...

*******************
 Iterate quickly
*******************

The process looked like this:

-  Column ``A`` is sometimes set to a number

-  Column ``B`` is an enum (so it can be either ``value1``, ``value2``
   or ``value3``)

-  If column ``B`` is set to ``value2`` we expect columns ``C`` and
   ``D`` to be set to non-empty values because there seems to be a
   connection and ``B``\'s ``value2`` seems to be correlated to those
   columns being set.

-  Correspondingly, if ``B`` is *not* set to ``value2`` we'll expect
   ``C`` and ``D`` to be not set either

-  But wait, in few cases ``C`` and ``D`` are set even though ``B`` is
   empty. Turns out ``C`` and ``D``\'s presence is what we should follow
   and we need to basically ignore ``B`` altogether

-  ``E`` is set to a number, always

-  Remember ``A``? When it's not set we need to calculate it based on
   ``F`` and ``G``

-  Also: ``A`` can also be sometimes set to zero (not null, regular
   number zero) in which case we also want to treat it as null because
   zero is definitely not a valid value in that context

-  ``F``\'s format seems to be conditional on the value of column ``H``

-  Column ``I`` contains geographic coordinates

-  Oh, but the longitudes in ``I`` are sometimes outside the usual ``[0, 180]``
   range. Some values are just totally wrong, some are off by 360
   degrees (which means we can calculate the actual longitude from
   ``longitude mod 360``)

-  ...and so on, and so forth

(Difficult to keep track of? It's even more difficult when you're actually
just figuring this out on the fly.)

In the process I wrote an application that:

-  Ingested the data from mutliple CSV sources
-  Decoded the data according to the set of heuristics I developed
-  Made several assertions to make sure there were no surprises at later
   stages (there were anyway, just fewer of them)
-  Combined the data together
-  Made several Lune emission estimates API calls to perform
   calculations
-  Produced a CSV as the output

The repetitive trial-and-error process required me to constantly, often
(some issues appeared only after combining the datasets together or when
calling the API) and quickly update the code and rerun it. With this in
mind...

***********
 Why Rust?
***********

I needed a language that:

#. Is statically typed (at least optionally)
#. On top of that: is strongly typed (as few automatic conversions
   between types as possible)
#. Provides explicit and precise error handling
#. Allows for fast edit-(build)-run cycle
#. Is expressive and supports high-level programming (so you don't get
   begged down by memory management, string parsing etc.)
#. Gives me a high level of if-it-builds-it-runs confidence

Note that this writeup is *not* meant to convince you that the features
I'm mentioning here are necessarily and objectively valuable or that you
should care about them – this is not the purpose of this post. I'm merely
explaining how I made the decision that I did given the set of requirements
I had.

Let me go through the list, provide a few details and explain why I
picked Rust among the languages I am comfortable with for this sort of
task (the contenders were Python and TypeScript).

#. Static typing

   Even though for the majority of my career I used Python, which is a
   dynamic language, I became convinced that static typing is a crucial
   part of producing a high-quality, correct, stable software.

   Don't get me wrong: there are definitely many pieces of functioning,
   high-quality software written in dynamic languages. It's just that
   the dynamic nature never helps, in my experience. Static typing
   eliminates whole classes of errors (that, in dynamic languages,
   you'll only learn about at runtime, sometimes in production, at the
   worst possible time). What isn't "tested" by the compiler has to be
   tested outside the type system, sometimes manually.

   Rust and TypeScript are good here, but Python has type hints and
   there are tools like `Mypy <http://mypy-lang.org/>`_ which, while not
   built-in, provide a large degree of static type safety. I've been
   using Mypy extensively and I can't imagine writing more than fifty
   lines of Python code without them.

#. Strong typing

   Weak typing (so: the absence of strong typing) is just a source of
   weird programming errors that sometimes pop up, in my experience. I've
   found that when I actually want to convert a value from one type to
   another it's better to do it explicitly, if only for error handling:
   parsing a string as integer doesn't have to succeed and when it fails
   it better be handled. All three languages do well here – TS hides a
   lot of the underlying JavaScript quirks – but Rust and Python
   do a somewhat better job (mixing ints and strings is difficult to
   do accidentally).

#. Error handling

   I grew to dislike exception-based error handling for one simple
   reason: you never know what operation can fail and what are the
   possible exceptions that you get.

   It's relatively easy to remember that Python's

   .. code-block:: python

      some_dictionary[key]

   can fail with ``KeyError`` when ``key`` is not in
   ``some_dictionary``. It's somewhat more difficult to know (and
   remember!) that JavaScript's

   .. code-block:: javascript

      new Intl.NumberFormat(
          // ...
      )

   can raise ``RangeError`` and ``TypeError``, at least in some strange
   OS/browser configurations.

   (And I'm not even mentioning cases of error hiding like
   ``parseInt('123a')`` returning ``123`` in JavaScript.)

   In Rust you can't unintentionally ignore the fact that

   .. code-block:: rust

      hash_map.get(key)

   returns an `Option
   <https://doc.rust-lang.org/std/option/enum.Option.html>`_ which you
   then have to explicitly handle:

   .. code-block:: rust

      match hash_map.get(key) {
          None => println!("The value is not here"),
          Some(value) => println!("We have {}", value),
      }

   (granted, you can simply `unwrap()
   <https://doc.rust-lang.org/std/option/enum.Option.html#method.unwrap>`_
   it, if you know what you're doing and actually want this kind of
   value-or-panic behavior.)

   You won't be surprised to learn that I find Rust's model better than
   the alternatives.

#. Fast edit-(build)-run cycle

   I spent over two days on this task, editing and rerunning the
   application many, many times. Every second that I spent staring at
   the terminal waiting for the program to build and run was a second I
   was taken out of the flow.

   The more quickly I saw the results of my change the sooner I could go
   back to deep work.

   Even though `Rust has reputation for long compilation times
   <https://endler.dev/2020/rust-compile-times/>`_ I haven't found it an
   issue in this case. The build and startup of the final application
   was taking around 2.2 seconds.

   For comparison:

   -  Transpiling a skeleton TypeScript app that merely imports CSV and
      HTTP client libraries takes 2.9 seconds on my machine with about
      0.3 seconds spent on starting it up.

   -  Running Mypy on a skeleton Python app takes about 0.3 seconds with
      less than 0.1 seconds of startup time.

   Python is the winner here, which is not totally unexpected.

#. Expressiveness

   All three languages allow for high-level programming, have iterators,
   automatic memory management (Rust: compile-time decided
   allocation/deallocation, others: runtime GC), arrays, `map()`,
   `filter()`, classes/structs, methods etc. and are fairly similar in
   those regards. Only Rust has the following though (with great
   compile-time support at that):

   -  `if` and `match` blocks are expressions:

      .. code-block:: rust

         let message = if username == "" {
             format!("Please log in")
         } else {
             format!("Hello, {}!", username)
         };

         // or
         let distance = match route {
             Route::Distance(value) => value,
             Route::AddressToAddress(address1, address2) => resolve_addresses(address1, address2),
             Route::AirportToAirport(airport1, airport2) => resolve_airports(airport1, airport2),
         };

   -  Exhaustiveness checks on `pattern matching
      <https://doc.rust-lang.org/book/ch18-01-all-the-places-for-patterns.html>`_.
      Let's say your program accepts commands in a string form, like
      this:

      .. code-block:: rust

         let command = get_string_command();

         match command {
             "ping" => println!("pong"),
             "sync" => synchronize_state(),
             "quit" => quit(),
             "whoami" => println!("You are logged in as {}", get_current_user()),
         };

      The Rust compiler will complain about it:

      ::

         error[E0004]: non-exhaustive patterns: `&_` not covered
          --> test.rs:4:11
           |
         4 |     match command {
           |           ^^^^^^^ pattern `&_` not covered
           |
           = help: ensure that all possible cases are being handled, possibly by adding wildcards or more match arms
           = note: the matched value is of type `&str`

      Basically it'll force you to handle *all* the cases, like this:

      .. code-block:: rust

         match command {
             "ping" => println!("pong"),
             "sync" => synchronize_state(),
             "quit" => quit(),
             "whoami" => println!("You are logged in as {}", get_current_user()),
             other => println!("Unknown command {}", other),
         };

   I find Rust to offer me the best experience here. (And I haven't even
   mentioned `the value ownership handling
   <https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html>`_
   (which eliminates a whole range of memory safety and race condition
   errors), `tagged unions
   <https://doc.rust-lang.org/rust-by-example/custom_types/enum.html>`_
   etc.)

#. If-it-builds-it-runs confidence

   Not much to add: the last thing I want to have, when iterating
   quickly on an application while in the flow, is random runtime
   errors. Static typing is particularly important on this front – with
   dynamic typing all too often an incorrectly-typed value is produced
   in one place but it actually blows up the application in another,
   remote (both in space and time) location. Strong typing also helps
   here and extra expressiveness eliminates some errors associated with
   repetitive boilerplate.

As you can see, Rust fared quite well in all the areas that I cared
about.

*************
 Conclusions
*************

I've seen the following heuristic mentioned many times on the Internet:

-  If you have a 10 line of code it's fine to use Bash (or any other
   kind of shell)

-  If you have between 10 and 1000 lines of code that's a job for a more
   serious programming language (like Python or Ruby) because shell
   programming stops being sufficient (more complex error handling,
   string handling, arrays being used, conditonal behavior etc.), but
   you don't want to get "too serious" because it'll slow you down

-  For problems over 1000 lines of code you better use a Real
   Programming Language (read: Java, C++ etc.)

I hope that this post provides a counterexample to that, demonstrating
that Rust is a viable option when you want to just "get things done"
quickly and reliably. The same mechanisms that make Rust suitable for
large scale applications can greatly aid in the development of smaller
scale programs.

My data exploration application ended up at around a thousand lines of
code and Rust's features were arguably valuable almost all the way there.
