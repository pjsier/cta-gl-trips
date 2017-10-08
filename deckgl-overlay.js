import React, {Component} from 'react';
import DeckGL, {PolygonLayer} from 'deck.gl';
import TripsLayer from './trips-layer';

const LIGHT_SETTINGS = {
  lightsPosition: [-87.63, 41.87, 8000, -87.3, 42, 5000],
  ambientRatio: 0.05,
  diffuseRatio: 0.6,
  specularRatio: 0.8,
  lightsStrength: [2.0, 0.0, 0.0, 0.0],
  numberOfLights: 2
};

const ROUTE_COLORS = {
  'Red Line': [198, 12, 48],
  'Purple Line': [82, 35, 152],
  'Yellow Line': [249, 227, 0],
  'Blue Line': [0, 161, 222],
  'Pink Line': [226, 126, 166],
  'Green Line': [0, 155, 58],
  'Orange Line': [249, 70, 28],
  'Brown Line': [98, 54, 27]
};

export default class DeckGLOverlay extends Component {

  static get defaultViewport() {
    return {
      longitude: -87.63,
      latitude: 41.87,
      zoom: 11,
      maxZoom: 16,
      pitch: 45,
      bearing: 0
    };
  }

  render() {
    const {viewport, trips, trailLength, time} = this.props;

    if (!trips) {
      return null;
    }

    const layers = [
      new TripsLayer({
        id: 'trips',
        data: trips,
        getPath: d => d.segments,
        getColor: d => ROUTE_COLORS.hasOwnProperty(d.route) ? ROUTE_COLORS[d.route] : [255, 255, 255],
        opacity: 0.2,
        strokeWidth: 2,
        trailLength,
        currentTime: time
      })
    ];

    return (
      <DeckGL {...viewport} layers={layers} initWebGLParameters />
    );
  }
}
