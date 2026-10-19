cardweaver
==========

A domain-specific language (DSL) for card weaving instructions, with included card weaving instruction synthesis functionality. Possible applications include:

- translating patterns for other kinds of band weaving, using cross stitch patterns as the basis of card weaving patterns, etc.
- checking that the card weaving instructions produce the pattern you think it will
- testing out different designs and patterns in a computational manner

The original motivation for this project is the fact that card weaving instructions are mind-bogglingly low-level. It is unintuitive and difficult to imagine what the instructions should be to produce a pattern. Card weaving instruction books direct the reader to design their patterns by first deciding the colors that go in the holes, and then experimenting with different lengths of forward/backward instructions, but this does not help when a weaver has a clear vision of what they want to weave, but figuring out the instructions to create it is tedious.

## Implementation
There are two parts to programmatically generating card weaving instructions.

First, a card weaving DSL has been implemented in Scala and Racket. The DSLs in both languages can be translated from one to the other. (TODO) The DSL in either language can be utilized to generate patterns. Both Scala and Racket are functional programming languages, which lends itself well to creating small, reusable pattern-generating functions. Scala is strongly typed and is meant to be the main entry point for the user of the DSL, since type errors will alert you to errors before you ever run your code. Racket, in contrast, is dynamically typed, which means that you won't know there's an error until you run the program. 

Second, a program synthesis tool has been implemented in Racket that generates card weaving instructions, given a pattern (TODO). This is the main purpose for the Racket version of the DSL, which is produced by the program synthesis tool and can be translated back into Scala (TODO) if so desired, or manipulated directly in Racket.

