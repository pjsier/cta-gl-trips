.PHONY: all

.INTERMEDIATE: data/cta_gtfs.zip

all: data/trip_line_segments.json

data/trip_line_segments.json: data/routes.txt
	python3 data/process_gtfs.py

data/routes.txt: data/cta_gtfs.zip
	unzip -d data $< && touch $@

data/cta_gtfs.zip:
	wget http://www.transitchicago.com/downloads/sch_data/google_transit.zip -O $@