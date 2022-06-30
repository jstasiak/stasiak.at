#####################################################
 Sea is not land or: More TypeScript type safety fun
#####################################################

:date:
   2022-07-12 11:00

:tags:
   programming, typescript, type safety, lune

(This text was originally published on `Lune Blog
<https://lune.co/blog/sea-is-not-land-or-more-typescript-type-safety-fun/>`_ on 2022-06-30. `Lune
<https://lune.co>`_, where I help fighting the climate crisis, kindly allowed me to republish it
here.)

******************
 Let there be sea
******************

Once upon a time I wrote some code to calculate sea distances between two sets of arbitrary
geographic coordinates (Lune uses calculations like this in `shipping emission estimates
<https://docs.lune.co/api-reference/endpoints-emission-estimates.html#estimate-shipping-emissions>`_).
It started with the following two interfaces:

.. code-block:: typescript

   type IFallibleSeaDistanceCalculatorError = ...
   type Km = Big

   interface IFallibleSeaDistanceCalculator {
       getDistance(
           source: GeographicCoordinates,
           destination: GeographicCoordinates,
       ): Promise<Result<Km, IFallibleSeaDistanceCalculatorError>>
   }

   interface IInfallibleSeaDistanceCalculator {
       getDistance(
           source: GeographicCoordinates,
           destination: GeographicCoordinates,
       ): Promise<Km>
   }

(``Result`` is a generic type coming from the `ts-results <https://github.com/vultix/ts-results>`_
library and it allows us to express the concept of success or failure at the type system level. At
Lune we don't particularly like exception-based error handling and we prefer error values.
``Result`` helps with that.)

One of the interfaces is for calculators that may fail (for any reason), the other is for
calculators that are guaranteed to work.

Why do we need this? It's a bit of a tangent, but: say we only have one interface *and* we want it
to express the fact that the calculation may fail (because *some* of the calculators may fail). In
that case the guaranteed-to-always-work implementation would also have to say it returns a
``Result``. If then we used that implementation somewhere we'd have to handle the error case –
technically possible according to the type system but not *really* possible because we know the
actual code.

In that situation we'd usually call the ``Result``'s `unwrap()
<https://github.com/vultix/ts-results#unwrap=>`_ method. The method either returns the success value
(in this case if the calculation was successful) or throws an exception. And we except this to
always be success so we don't even attempt to handle the impossible (in our mind, in the context)
exception.

This, however, puts us at risk of getting an unexpected exception in the future when someone changes
the currently guaranteed to always work calculator in a way that actually allows failures.

Having two interfaces, one for fallible calculators and another for infallible ones, resolves this
issue. The hypothetical situation describe in the paragraph above will now be picked up at compile
time. All things being equal replacing runtime errors with compile time errors is desirable for us.

(The explanation above is short, by necessity. The topics mentioned there deserve to be explored in
depth but this isn't the time for that.)

Anyway, back from the tangent. We then have some implementations of the interfaces (I'll skip the
``source`` and ``destination`` parameter references from now on, they're not important):

.. code-block:: typescript

   class ExternalServiceSeaDistanceCalculator
       implements IFallibleSeaDistanceCalculator {
       async getDistance(...): Promise<Result<Km, IFallibleSeaDistanceCalculatorError>> {
           // ...
       }
   }

   class Pub151SeaDistanceCalculator
       implements IFallibleSeaDistanceCalculator {
       async getDistance(...): Promise<Result<Km, IFallibleSeaDistanceCalculatorError>> {
           // ...
       }
   }

   class EstimateSeaDistanceCalculator
       implements IInfallibleSeaDistanceCalculator {
       async getDistance(...): Promise<Km> {
           // ...
       }
   }

Few words on the implementations:

-  ``ExternalServiceSeaDistanceCalculator`` uses, well, an external service, which may fail
   (there may be communication issues, the service may be down for maintenance etc.).

-  ``Pub151SeaDistanceCalculator`` uses data from the `Distances between ports
   <https://msi.nga.mil/api/publications/download?key=16694076/SFH00000/Pub151bk.pdf&type=view>`_
   publication (AKA Pub. 151). Due to some implementation details of the algorithm that we use
   this calculator may also fail.

-  ``EstimateSeaDistanceCalculator`` uses an algorithm that always succeeds and, consequently,
   always returns a value.

To tie all of these together we have this:

.. code-block:: typescript

   class FallbackSeaDistanceCalculator
       implements IInfallibleSeaDistanceCalculator
   {
       constructor(
           private readonly fallibleCalculators: IFallibleSeaDistanceCalculator[],
           private readonly infallibleCalculator: IInfallibleSeaDistanceCalculator,
       ) {}

       async getDistance(
           source: GeographicCoordinates,
           destination: GeographicCoordinates,
       ): Promise<Km> {
           for (const fallibleCalculator of this.fallibleCalculators) {
               const result = await fallibleCalculator.getDistance(source, destination)
               if (result.ok) {
                   return result.val
               }
           }
           return await this.infallibleCalculator.getDistance(source, destination)
       }
   }

The implementation basically presents a number of fallible calculators and one infallible one as an
infallible interface. The fallible calculators are tried one by one and, if none of them succeeded,
we use the infallible fallback calculator.

(Note how this class both implements *and* consumes ``IInfallibleSeaDistanceCalculator`` – in the
words of Colonel Hannibal Smith: `I love it when a plan comes together
<https://www.youtube.com/watch?v=7GL6LH6ufhM>`_.)

We then have this function that we use in our production code:

.. code-block:: typescript

   function getProductionSeaDistanceCalculator(): IInfallibleSeaDistanceCalculator {
       return new FallbackSeaDistanceCalculator(
           [
               new ExternalServiceSeaDistanceCalculator(...),
               new Pub151SeaDistanceCalculator(),
           ],
           new EstimateSeaDistanceCalculator(),
       )
   }

*******************************
 Let there be... land as well?
*******************************

There was some existing land distance calculation code but I didn't like the shape of it. At the
same time I really liked the sea distance calculation interfaces and the fallback mechanism
described above so I decided to do some refactoring.

I didn't want to duplicate the interfaces and the fallback class so I renamed them and made them
mode-independent. ``IFallibleSeaDistanceCalculator`` became ``IFallibleDistanceCalculator``,
``IInfallibleSeaDistanceCalculator`` was renamed to ``IInfallibleDistanceCalculator`` etc.

We got some new land-specific implementations:

.. code-block:: typescript

   class ExternalServiceLandDistanceCalculator
       implements IFallibleDistanceCalculator {
       async getDistance(...): Promise<Result<Km, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class EstimateLandDistanceCalculator
       implements IInfallibleDistanceCalculator {
       async getDistance(...): Promise<Km> {
           // ...
       }
   }

together with a corresponding ``getProductionLandDistanceCalculator()`` which mirrored
``getProductionSeaDistanceCalculator()``.

I converted the rest of the relevant code to use the new interfaces, pushed a branch, got it
reviewed, shipped.

Wham, bam, done.

But... is it really?

********************************
 Different things are different
********************************

After shipping the code there's been this nagging thought in the back of my head, something just
wasn't right.

This is what the code looked like after my refactoring:

.. code-block:: typescript

   interface IFallibleDistanceCalculator {
       getDistance(...): Promise<Result<Km, IFallibleDistanceCalculatorError>>
   }

   interface IInfallibleDistanceCalculator {
       getDistance(...): Promise<Km>
   }

   class FallbackDistanceCalculator
       implements IInfallibleDistanceCalculator
   {
       constructor(
           private readonly fallibleCalculators: IFallibleDistanceCalculator[],
           private readonly infallibleCalculator: IInfallibleDistanceCalculator,
       ) {}

       async getDistance(...): Promise<Km> {
           // ...
       }
   }

   class ExternalServiceSeaDistanceCalculator
       implements IFallibleDistanceCalculator {
       async getDistance(...): Promise<Result<Km, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class Pub151SeaDistanceCalculator
       implements IFallibleDistanceCalculator {
       async getDistance(...): Promise<Result<Km, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class EstimateSeaDistanceCalculator
       implements IInfallibleDistanceCalculator {
       async getDistance(...): Promise<Km> {
           // ...
       }
   }

   class ExternalServiceLandDistanceCalculator
       implements IFallibleDistanceCalculator {
       async getDistance(...): Promise<Result<Km, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class EstimateLandDistanceCalculator
       implements IInfallibleDistanceCalculator {
       async getDistance(...): Promise<Km> {
           // ...
       }
   }

   function getProductionSeaDistanceCalculator(): IInfallibleDistanceCalculator {
       // ...
   }

   function getProductionLandDistanceCalculator(): IInfallibleDistanceCalculator {
       // ...
   }

It's a big chunk of code, take your time.

...

In order to explain my issue with it, first I need to present the following question: why do do we
separate land and distance calculations in the first place?

The sea route between, say, Istanbul and Gdańsk will be different from the land route – by land it's
more or less a straight line, by sea we need to go around Europe – so we have to treat the
transportation modes differently. This is visible through some of the services we use only providing
us land distances and some only giving us sea distances. When it comes to our own calculations we
take mode-specific details into consideration.

For that reason we only use a sea distance calculator when estimating shipping something by sea (go
figure) and so on.

To summarize: using sea distance calculation where land distance is expected (and vice versa) is a
problem.

Unfortunately the code above doesn't prevent us from shooting ourselves in the foot here – since
there's only one ``IFallibleDistanceCalculator`` interface that both
``ExternalServiceSeaDistanceCalculator`` and ``ExternalServiceLandDistanceCalculator`` implement
they can be used interchangeably – not what we want at all. Similarly for
``IInfallibleDistanceCalculator``. As one of the consequences ``FallbackDistanceCalculator`` will
happily accept calculators of different kinds – sea and land, together – and return a value.

That last thing is what annoyed me the most. I mentioned that I prefer compile-time errors to
runtime errors, right? Well, this this is no error at all – just doing the wrong thing silently,
which I consider worse yet.

************
 Land ahoy!
************

(Sorry, couldn't resist the pun.)

As I said earlier in this post, I *really* didn't want to duplicate the interfaces (and the
``FallbackDistanceCalculator`` class on top of that) so this approach was a deal breaker for me.

Then it dawned on me: TypeScript has generics. There are generic classes, there are generic
interfaces, why don't we parameterize things a little and make them different this way while reusing
the code as much as possible?

I figured the simplest and the most straightforward (if not even the only reasonable) solution was
to parameterize the interfaces and the ``FallbackDistanceCalculator`` class in the type returned by
their ``getDistance()`` method. For that I went with `a little TypeScript trick borrowed I already
wrote about some time ago
<https://lune.co/blog/type-safety-units-and-how-not-to-crash-the-mars-climate-orbiter/>`_.

First I defined two fake (really, read the post above) types:

.. code-block:: typescript

   type SeaDistance = Km & { readonly __tag: unique symbol }
   type LandDistance = Km & { readonly __tag: unique symbol }

Then I modified the interfaces and the ``FallbackDistanceCalculator`` to read:

.. code-block:: typescript

   type DistanceType = SeaDistance | LandDistance

   interface IFallibleDistanceCalculator<T extends DistanceType> {
       getDistance(...): Promise<Result<T, IFallibleDistanceCalculatorError>>
   }

   interface IInfallibleDistanceCalculator<T extends DistanceType> {
       getDistance(...): Promise<T>
   }

   class FallbackDistanceCalculator<T extends DistanceType>
       implements IInfallibleDistanceCalculator<T>
   {
       constructor(
           private readonly fallibleCalculators: IFallibleDistanceCalculator<T>[],
           private readonly infallibleCalculator: IInfallibleDistanceCalculator<T>,
       ) {}

       async getDistance(
           source: ApiGeographicCoordinates,
           destination: ApiGeographicCoordinates,
       ): Promise<T> {
           for (const fallibleCalculator of this.fallibleCalculators) {
               const result = await fallibleCalculator.getDistance(source, destination)
               if (result.ok) {
                   return result.val
               }
           }
           return await this.infallibleCalculator.getDistance(source, destination)
       }
   }

The next step was to change the implementations to adapt to that:

.. code-block:: typescript

   class ExternalServiceSeaDistanceCalculator
       implements IFallibleDistanceCalculator<SeaDistance> {
       async getDistance(...):
           Promise<Result<SeaDistance, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class Pub151SeaDistanceCalculator
       implements IFallibleDistanceCalculator<SeaDistance> {
       async getDistance(...):
           Promise<Result<SeaDistance, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class EstimateSeaDistanceCalculator
       implements IInfallibleDistanceCalculator<SeaDistance> {
       async getDistance(...): Promise<SeaDistance> {
           // ...
       }
   }

   class ExternalServiceLandDistanceCalculator
       implements IFallibleDistanceCalculator<LandDistance> {
       async getDistance(...):
           Promise<Result<LandDistance, IFallibleDistanceCalculatorError>> {
           // ...
       }
   }

   class EstimateLandDistanceCalculator
       implements IInfallibleDistanceCalculator<LandDistance> {
       async getDistance(...): Promise<LandDistance> {
           // ...
       }
   }

   function getProductionSeaDistanceCalculator():
       IInfallibleDistanceCalculator<SeaDistance> {
       // ...
   }

   function getProductionLandDistanceCalculator():
       IInfallibleDistanceCalculator<LandDistance> {
       // ...
   }

And it worked!

*************************************
 What have we gained, s-pacifically?
*************************************

The last version of the code addresses all the issues I had:

-  Calculators of different kinds can't be mixed inside ``FallbackDistanceCalculator`` anymore

-  Sea calculator can't be used where land distance is expected (and the opposite way as well)

-  If we do something wrong we get a *compile-time* error like:

   ::

      src/config.ts:416:5 - error TS2322: Type 'FallbackDistanceCalculator<LandDistance>' is not assignable to type 'IInfallibleDistanceCalculator<SeaDistance>'.
      The types returned by 'getDistance(...)' are incompatible between these types.
        Type 'Promise<LandDistance>' is not assignable to type 'Promise<SeaDistance>'.
          Type 'LandDistance' is not assignable to type 'SeaDistance'.
            Type 'LandDistance' is not assignable to type '{ readonly __tag: unique symbol; }'.
              Types of property '__tag' are incompatible.
                Type 'typeof __tag' is not assignable to type 'typeof __tag'. Two different types with this name exist, but they are unrelated.

Granted, it's not the most ergonomic error message in the world but I'll take it.

I'm rather happy with this, both for the reasons of elegance and because I believe it will help in
developing and maintenance a solid piece of software which hopefully serves all Lune customers well.

What I came to realize is that there are sometimes non-obvious ways to make the code more dependable
by (ab)using various type system features.

I encourage you to explore this niche, it's a fun, rewarding and often beneficial endeavor.

Thank you for sticking around, I hope you enjoyed the read.
