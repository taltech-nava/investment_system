export interface InstrumentClass {
  id: number;
  name: string;
}

export interface Instrument {
  id: number;
  ticker: string;
  name: string;
  currency: string;
  class_id: number;
}
