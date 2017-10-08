# CTA GTFS WebGL Visualization

This is a modified version of the TripsLayer example on the [deck.gl](http://deck.gl) website.

### Usage
Clone this repository, create the trip data with `make all`, and then run
```
npm install
npm start
```

### Modifying Data

To pull CTA data for a different time frame, change the `START_TIME` and `END_TIME` time strings,
delete the `data/trip_line_segments.json` file, and run `make all`.