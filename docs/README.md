# ISS
[![Build Status](https://travis-ci.org/Lanny/ISS.svg?branch=master)](https://travis-ci.org/Lanny/ISS)

ISS is a modern BBS spiritually descended from software of the golden age of webforums, most notably vB3 and UBB. Design tenets are:

- Javascript should be optional, UI shouldn't second guess user agents
- Should be at least somewhat usable on a potato using an EDGE connection
- Performance and correctness over feature richness
- Responsive pages
- Should be able to withstand the spamocalypse 
- Development using notepad is highly encouraged

# Why would I use ISS? Why would I not?

ISS is designed for _pseudonymous variable length discussion_. Discussion is structured into threads pertaining to a topic, threads are organized under forums or sections. Members post under pseudonyms. If you've used a typical webforum like vBulletin or PHPBB you've seen the basic model that ISS follows.

This model of discussion has found success in both broad general communities and narrow specialty discussion. Unlike blogging platforms, direct continued discussion is prioritized over short form commentary on longer articles. Post length limits are typically liberal and support both short and long form response. The pseudonymous mode allows users to develop a voice and develop ideas over a length of time while providing many of the social advantages of anonymous posting.

This model is generally not well equipped for "personal broadcast" sorts of communication (e.g. the use case served by Twitter or Facebook) as the thread rather than the individual user is the central unit of organization. Long form publication with little or no discussion is typically better served by the myriad blogging options available today. While ISS can easily facilitate reddit/HN style link aggregation or question/answer use cases, it does not make special affordance for these and they may be better served by other software.

As mentioned, ISS is not the first piece of software in this niche. From an administrator's perspective the primary benefits of ISS over the competition are support for a broad range of browsers/devices (including very low end client hardware and useragents that don't support javascript) and lower minimum server hardware requirements and better server performance in most cases. The major drawback of ISS is that it has an underdeveloped extensions/plugins system and third party ecosystem relative to major competitors.

# Why ISS?

vBulletin 3 was basically reasonable software. I won't say it was good. It had issues: some jank in the auth system, hacky search, PHP... But it worked. You could run it on cheap shared hosting, you could scrape and automate it with a little elbow grease, it indexed well, it was usable and performant on a wide range of browsers. Administration was possible for an adventurous layman and administrators controlled their content rather than being beholden to a specific hosting platform. Most importantly it facilitated pseudonymous variable length discussion well and did little to get in the way of that.

Technologically we provably had everything we needed to create a sufficient piece of forum software in the early 2000s. But vB3 reached end of life in 2007, its successor in vB4 suffered from bloat, abuse of AJAX where it wasn't necessary, and an almost absurdly bad/slow/overly abstract database design. PHPBB has gone down the same road. In general forum software has just become too complex when BBSs were basically solved over a decade ago.

The strengths of vB3 are what ISS attempts to reproduce and preserve. What ISS offers on top of this a clean modern codebase, more reasonable database design, support for useragents that don't have JS execution, or with JS disabled, and generally better client-side performance through more sane/modern resource usage, caching, and delivery strategies.

# How you can help

One of the biggest things you can do to help is to use ISS. More users means more eyes on the software, helping to flush out bugs and guide development by understanding what is needed from users.

You can also help document ISS, currently most documentation is aimed at developers. While ISS is designed to be intuitive to users, administration and setup is more complex and not well documented.

Lastly if you are code-savvy you can help in the development of ISS. New contributors are always welcome. Check out the github issues page if you want some ideas about where to start, or feel free to work features that aren't documented there. If you have an idea but want input or technical direction before beginning work feel free to open a new issue. Read the [DEVNOTES](../docs/DEVNOTES.md) for how to set up a development environment and a technical overview of the project.
