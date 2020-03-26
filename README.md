# Good News

Good News is a positive-news aggregation platform that attempts to address the subjective nature of "positivity" and "negativity". Currently the site scrapes articles from The Guardian and uses the IBM Tone Analyzer to tag each articles with sentiments. Our [index page](https://www.thefunk.tech/) shows all articles that have not been tagged with _fear_, _anger_, or _sadness_. The basic search in the navbar let's you filter by tag (if you filter with _joy_ then all articles that have the _joy_ tag will be shown).

![GoodNews](GoodNews_sample.png)

## Features

- filter by sentiment tag
- ... many soon to come!

## What's Next?

### For users

So far we have done nothing to address the subjectivity surrounding what is "good". We would like to address this in the following ways:

- investigate switching from IBM Tone Analyzer to an open source sentiment analysis tool in hopes of being able to fine tune models for our purposes
- Allow site users to make accounts. Users will be able to like and comment on articles. Likes will be used to customize user feed and hopefully show them the content they are most likely to enjoy. Comments will be run thru sentiment analysis in hopes of understanding how our users react to articles with specific tag combos.
- allow users to ban specific keywords or topics that may occur in articles so such articles do not appear in their feed.

### Tech wise

We would like to separate our frontend from our backend by using our backend web framework as a REST api for our db. We believe that using a tool such as React for frontend rendering will help simplify our code base, create a better looking product, and accelerate feature development.

## Contact & Contributing

Ideas, contributions, and discussion in general is always welcome. If you would like to get in touch or become involved in this project reach out to Ben at bencook400@gmail.com.


## License
This project is distributed under the MIT License. See [license](/LICENSE) for more information.

